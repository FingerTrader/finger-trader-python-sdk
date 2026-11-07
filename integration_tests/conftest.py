"""Opt-in configuration for read-only live API verification."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from urllib.parse import urlsplit

import pytest

from finger_trader import APIError, FingerTraderClient


@dataclass(frozen=True)
class IntegrationConfig:
    target: str
    api_url: str
    auth_url: str
    socket_auth_url: str
    auth_mode: str
    access_token: str | None = field(repr=False)
    oauth_basic_token: str | None = field(repr=False)
    username: str | None = field(repr=False)
    password: str | None = field(repr=False)
    login_type: int | None
    captcha_id: str | None = field(repr=False)
    captcha_code: str | None = field(repr=False)
    market: str
    ticker: str | None
    interval: str | None
    account_market: int | None
    position_is_usd: bool
    position_type: int
    timeout: float


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ValueError(f"Missing required integration setting: {name}")
    return value


def _https_url(name: str) -> str:
    value = _required(name)
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(f"{name} must be an HTTPS base URL without user info, query, or fragment")
    return value.rstrip("/")


def _optional_int(name: str) -> int | None:
    value = os.environ.get(name, "").strip()
    return int(value) if value else None


def _flag(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized not in {"true", "false", "1", "0"}:
        raise ValueError(f"{name} must be true, false, 1, or 0")
    return normalized in {"true", "1"}


def _target() -> str:
    target = _required("FINGER_TRADER_IT_TARGET").lower()
    if target not in {"sandbox", "dev", "production-read-only"}:
        raise ValueError("FINGER_TRADER_IT_TARGET must be sandbox, dev, or production-read-only")
    if target == "production-read-only":
        if os.environ.get("FINGER_TRADER_IT_CONFIRM_PRODUCTION_READ_ONLY") != "YES":
            raise ValueError(
                "Set FINGER_TRADER_IT_CONFIRM_PRODUCTION_READ_ONLY=YES to confirm "
                "production read-only testing"
            )
    elif os.environ.get("FINGER_TRADER_IT_CONFIRM_NON_PROD") != "YES":
        raise ValueError("Set FINGER_TRADER_IT_CONFIRM_NON_PROD=YES to confirm non-production URLs")
    return target


@pytest.fixture(scope="session")
def integration_config() -> IntegrationConfig:
    if os.environ.get("FINGER_TRADER_IT_ENABLED") != "1":
        pytest.skip("Set FINGER_TRADER_IT_ENABLED=1 to opt in to live read-only API checks")

    target = _target()

    auth_mode = os.environ.get("FINGER_TRADER_IT_AUTH_MODE", "token").strip().lower()
    if auth_mode not in {"token", "password"}:
        pytest.fail("FINGER_TRADER_IT_AUTH_MODE must be token or password")

    login_type = _optional_int("FINGER_TRADER_IT_LOGIN_TYPE")
    return IntegrationConfig(
        target=target,
        api_url=_https_url("FINGER_TRADER_IT_API_BASE_URL"),
        auth_url=_https_url("FINGER_TRADER_IT_AUTH_URL"),
        socket_auth_url=_https_url("FINGER_TRADER_IT_SOCKET_AUTH_URL"),
        auth_mode=auth_mode,
        access_token=os.environ.get("FINGER_TRADER_IT_ACCESS_TOKEN") or None,
        oauth_basic_token=os.environ.get("FINGER_TRADER_IT_OAUTH_BASIC_TOKEN") or None,
        username=os.environ.get("FINGER_TRADER_IT_USERNAME") or None,
        password=os.environ.get("FINGER_TRADER_IT_PASSWORD") or None,
        login_type=login_type,
        captcha_id=os.environ.get("FINGER_TRADER_IT_CAPTCHA_ID") or None,
        captcha_code=os.environ.get("FINGER_TRADER_IT_CAPTCHA_CODE") or None,
        market=os.environ.get("FINGER_TRADER_IT_MARKET", "stock").strip().lower(),
        ticker=os.environ.get("FINGER_TRADER_IT_TICKER") or None,
        interval=os.environ.get("FINGER_TRADER_IT_INTERVAL") or None,
        account_market=_optional_int("FINGER_TRADER_IT_ACCOUNT_MARKET"),
        position_is_usd=_flag("FINGER_TRADER_IT_POSITION_IS_USD", False),
        position_type=int(os.environ.get("FINGER_TRADER_IT_POSITION_TYPE", "0")),
        timeout=float(os.environ.get("FINGER_TRADER_IT_TIMEOUT", "10")),
    )


@pytest.fixture(scope="session")
def live_client(integration_config: IntegrationConfig):
    config = integration_config
    kwargs = {
        "base_url": config.api_url,
        "auth_url": config.auth_url,
        "socket_auth_url": config.socket_auth_url,
        "timeout": config.timeout,
        # Endpoints are explicit HTTPS URLs; production mode is read-only guarded.
        "environment": "prod" if config.target == "production-read-only" else "dev",
    }
    if config.auth_mode == "token":
        if not config.access_token:
            pytest.skip("Token mode needs FINGER_TRADER_IT_ACCESS_TOKEN")
        client = FingerTraderClient(token=config.access_token, **kwargs)
    else:
        password_fields = (
            config.oauth_basic_token,
            config.username,
            config.password,
            config.login_type,
        )
        if not all(value is not None for value in password_fields):
            pytest.fail(
                "Password mode requires FINGER_TRADER_IT_OAUTH_BASIC_TOKEN, "
                "USERNAME, PASSWORD, and LOGIN_TYPE"
            )
        client = FingerTraderClient(oauth_basic_token=config.oauth_basic_token, **kwargs)
        try:
            client.auth.login(
                config.username,
                config.password,
                account_type=config.login_type,
                captcha_id=config.captcha_id,
                captcha_code=config.captcha_code,
            )
        except APIError as exc:
            # Do not let pytest tracebacks expose credential-bearing locals.
            raise RuntimeError(
                f"Sandbox/Dev OAuth failed (code={exc.code!r}, status={exc.status!r})"
            ) from None

    try:
        # Auth and the documented WebSocket ticket flow use separate transports.
        block_state_changing_calls(client)
        yield client
    finally:
        client.close()


class ProductionWriteBlocked(AssertionError):
    """A state-changing SDK endpoint was attempted by a live integration test."""


def block_state_changing_calls(client) -> None:
    """Guard every SDK state-changing API route before it reaches HTTP transport."""

    def reject_write(path, *args, **kwargs):
        raise ProductionWriteBlocked(path)

    client._post = reject_write
