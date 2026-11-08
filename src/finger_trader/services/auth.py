"""Authentication service matching the Finger_desk OAuth contract."""

from __future__ import annotations

import time

from ..models import ApiResponse, AuthToken


class Auth:
    def __init__(self, client):
        self._client = client

    @property
    def is_authenticated(self) -> bool:
        expires = self._client.expires_at
        return bool(self._client._api.token) and (expires is None or time.time() < expires)

    def check(self) -> bool:
        """Return local token presence and expiry status; does not make a server call."""
        return self.is_authenticated

    def login(
        self,
        username: str,
        password: str,
        *,
        account_type: int,
        captcha_id: str | None = None,
        captcha_code: str | None = None,
    ) -> ApiResponse:
        """Use the existing OAuth2 password grant and store tokens in memory only."""
        if not self._client._auth.basic_auth:
            raise RuntimeError(
                "OAuth login requires oauth_basic_token from the service operator; "
                "no client credential is bundled."
            )
        data = {
            "username": username,
            "password": password,
            # Dio's form encoder writes a bare key for null DTO values (no '=');
            # HTTPTransport preserves that exact representation.
            "captchaId": captcha_id,
            "captchaCode": captcha_code,
            "grant_type": "password",
            "type": account_type,
        }
        response = self._client._auth.request(
            "POST",
            "/oauth2/token",
            body=data,
            form=True,
            redact=(username, password, captcha_id, captcha_code),
        )
        payload = response.data
        token = AuthToken(
            access_token=payload["access_token"],
            refresh_token=payload.get("refresh_token"),
            token_type=payload["token_type"],
            expires_in=payload.get("expires_in"),
        )
        self._client.set_token(token.access_token, token.token_type, token.expires_in)
        # Avoid retaining a second copy of secret material in response.raw.
        return ApiResponse(token, response.code, response.message)

    def captcha(self) -> ApiResponse:
        return self._client._auth.request("GET", "/api/v1/auth/captcha")

    def refresh(self):
        raise NotImplementedError(
            "Finger_desk contains no refresh-token request contract; "
            "authenticate again when expired."
        )
