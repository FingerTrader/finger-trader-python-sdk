"""HTTP transport with bounded responses and redirects disabled."""

from __future__ import annotations

import json
import logging
import re
import ssl
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus, urlencode, urlsplit
from urllib.request import HTTPHandler, HTTPRedirectHandler, HTTPSHandler, Request, build_opener

from .exceptions import APIError, NetworkError
from .models import ApiResponse

MAX_RESPONSE_BYTES = 8 * 1024 * 1024
MAX_ERROR_BYTES = 4096
# Match AppPlatform.desktopUserAgent in Finger Desk's HTTP interceptor.
FINGER_DESK_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)


class _RejectRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class HTTPTransport:
    """Small sync HTTP transport. TLS verification is always enabled."""

    def __init__(self, base_url, timeout=10.0, *, token=None, token_type="Bearer", basic_auth=None):
        parsed = urlsplit(base_url)
        if parsed.scheme not in {"https", "http"} or not parsed.hostname:
            raise ValueError("base_url must be an absolute HTTPS URL")
        if parsed.username or parsed.password or parsed.fragment:
            raise ValueError("base_url must not include user info or a fragment")
        if parsed.scheme != "https" and parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
            raise ValueError("HTTP is only allowed for loopback development URLs")
        if not (0 < timeout <= 300):
            raise ValueError("timeout must be greater than 0 and at most 300 seconds")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.token, self.token_type, self.basic_auth = token, token_type, basic_auth
        self.log = logging.getLogger("finger_trader.http")
        self._opener = build_opener(
            _RejectRedirects(), HTTPSHandler(context=ssl.create_default_context()), HTTPHandler()
        )
        self._closed = False

    def request(
        self,
        method,
        path,
        *,
        params=None,
        body=None,
        form=False,
        authenticated=False,
        retry_safe=False,
        redact=(),
    ):
        if self._closed:
            raise RuntimeError("HTTP transport is closed")
        query = "?" + urlencode(params, doseq=True) if params else ""
        url = self.base_url + path + query
        headers = {
            "Accept": "application/json",
            "User-Agent": FINGER_DESK_USER_AGENT,
        }
        if method.upper() in {"POST", "PUT", "PATCH"}:
            headers["Content-Type"] = "application/json"
        payload = None
        if body is not None:
            if form:
                # Match Dio's application/x-www-form-urlencoded encoding:
                # null values become bare keys, while concrete values use
                # standard form encoding.
                encoded_fields = []
                for key, value in body.items():
                    if value is None:
                        encoded_fields.append(quote_plus(str(key)))
                    else:
                        encoded_fields.append(urlencode({key: value}))
                payload = "&".join(encoded_fields).encode()
                headers["Content-Type"] = "application/x-www-form-urlencoded"
            else:
                payload = json.dumps(body, separators=(",", ":"), default=_json_default).encode()
                headers["Content-Type"] = "application/json"
        if self.basic_auth:
            headers["Authorization"] = "Basic " + self.basic_auth
        if authenticated and self.token:
            headers["Authorization"] = f"{self.token_type} {self.token}"
            headers["token"] = self.token
        req = Request(url, data=payload, headers=headers, method=method.upper())
        # Do not include query values or headers in logs.
        self.log.debug("%s %s", method.upper(), path)
        attempts = 2 if retry_safe and method.upper() in {"GET", "HEAD"} else 1
        for attempt in range(attempts):
            try:
                with self._opener.open(req, timeout=self.timeout) as response:
                    raw = response.read(MAX_RESPONSE_BYTES + 1)
                    if len(raw) > MAX_RESPONSE_BYTES:
                        raise NetworkError(
                            "API response exceeds the 8 MiB limit",
                            code="RESPONSE_TOO_LARGE",
                            path=path,
                        )
                    try:
                        data = json.loads(raw) if raw else None
                    except (ValueError, UnicodeDecodeError):
                        raise NetworkError(
                            "API returned an invalid JSON response",
                            code="INVALID_RESPONSE",
                            path=path,
                        ) from None
                return self._unwrap(
                    data,
                    path,
                    self._secrets() + tuple(secret for secret in redact if secret),
                )
            except HTTPError as exc:
                raw = exc.read(MAX_ERROR_BYTES + 1)
                if len(raw) > MAX_ERROR_BYTES:
                    raw = raw[:MAX_ERROR_BYTES]
                try:
                    data = json.loads(raw) if raw else {}
                except (ValueError, UnicodeDecodeError):
                    data = {"message": raw.decode("utf-8", "replace")}
                error = APIError.from_payload(data, status=exc.code, path=path)
                error.message = self._redact(error.message, tuple(redact))
                raise error from None
            except (TimeoutError, URLError, OSError):
                if attempt + 1 == attempts:
                    # Do not chain low-level exceptions that may include request context.
                    raise NetworkError(
                        "Network request failed or timed out", code="NETWORK_ERROR", path=path
                    ) from None

    @staticmethod
    def _unwrap(data, path=None, secrets=()):
        if isinstance(data, dict) and "code" in data:
            has_success_envelope = "success" in data
            has_finger_desk_envelope = "data" in data and ("msg" in data or "message" in data)
            if not (has_success_envelope or has_finger_desk_envelope):
                return ApiResponse(data, raw=data)

            successful = (
                bool(data.get("success")) if has_success_envelope else data.get("code") in (0, "0")
            )
            if not successful:
                error = APIError.from_payload(data, path=path)
                for secret in secrets:
                    error.message = error.message.replace(secret, "[REDACTED]")
                raise error
            message = str(data.get("message", data.get("msg", "")))
            for secret in secrets:
                message = message.replace(secret, "[REDACTED]")
            return ApiResponse(data.get("data"), data.get("code"), message, data)
        return ApiResponse(data, raw=data)

    def _secrets(self):
        return tuple(value for value in (self.token, self.basic_auth) if value)

    def _redact(self, message, additional=()):
        for secret in self._secrets() + tuple(additional):
            if secret:
                message = message.replace(str(secret), "[REDACTED]")
        message = re.sub(
            r"(?i)(authorization\s*[:=]\s*)(?:bearer\s+)?[^\s,;]+", r"\1[REDACTED]", message
        )
        message = re.sub(
            r"(?i)((?:access_token|refresh_token|password|secret)\s*[:=]\s*)[^\s,;]+",
            r"\1[REDACTED]",
            message,
        )
        return message

    def close(self):
        self._closed = True


def _json_default(value):
    from decimal import Decimal

    if isinstance(value, Decimal):
        # JSON number token; preserve the Decimal's exact decimal representation.
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")
