"""Safety checks for opt-in integration-test configuration; no network calls."""

from dataclasses import fields

import pytest

from integration_tests.conftest import (
    IntegrationConfig,
    ProductionWriteBlocked,
    _https_url,
    _target,
    block_state_changing_calls,
)


def test_integration_url_allows_production_host_over_https(monkeypatch):
    monkeypatch.setenv(
        "FINGER_TRADER_IT_API_BASE_URL",
        "https://prod-api.fingertrader.com/finger-bff-app",
    )
    assert _https_url("FINGER_TRADER_IT_API_BASE_URL") == (
        "https://prod-api.fingertrader.com/finger-bff-app"
    )


def test_integration_url_requires_https_and_no_inline_credentials(monkeypatch):
    for value in (
        "http://sandbox.example.invalid/api",
        "https://user:pass@sandbox.example.invalid/api",
        "https://sandbox.example.invalid/api?token=value",
    ):
        monkeypatch.setenv("FINGER_TRADER_IT_API_BASE_URL", value)
        with pytest.raises(ValueError, match="HTTPS base URL"):
            _https_url("FINGER_TRADER_IT_API_BASE_URL")


def test_production_read_only_target_requires_its_own_confirmation(monkeypatch):
    monkeypatch.setenv("FINGER_TRADER_IT_TARGET", "production-read-only")
    monkeypatch.delenv("FINGER_TRADER_IT_CONFIRM_PRODUCTION_READ_ONLY", raising=False)
    with pytest.raises(ValueError, match="CONFIRM_PRODUCTION_READ_ONLY"):
        _target()

    monkeypatch.setenv("FINGER_TRADER_IT_CONFIRM_PRODUCTION_READ_ONLY", "YES")
    assert _target() == "production-read-only"


def test_integration_config_repr_hides_secrets():
    config = IntegrationConfig(
        target="sandbox",
        api_url="https://sandbox.example.invalid/api",
        auth_url="https://sandbox.example.invalid/auth",
        socket_auth_url="https://sandbox.example.invalid/socket",
        auth_mode="password",
        access_token="access-secret-test-value",
        oauth_basic_token="basic-secret-test-value",
        username="private-user-test-value",
        password="private-password-test-value",
        login_type=0,
        captcha_id="private-captcha-id",
        captcha_code="private-captcha-code",
        market="stock",
        ticker="TEST",
        interval="1d",
        account_market=0,
        position_is_usd=False,
        position_type=0,
        timeout=10,
    )
    rendered = repr(config)
    for secret_value in (
        "access-secret-test-value",
        "basic-secret-test-value",
        "private-user-test-value",
        "private-password-test-value",
        "private-captcha-id",
        "private-captcha-code",
    ):
        assert secret_value not in rendered
    assert all(
        not next(field for field in fields(config) if field.name == name).repr
        for name in (
            "access_token",
            "oauth_basic_token",
            "username",
            "password",
            "captcha_id",
            "captcha_code",
        )
    )


def test_read_only_guard_blocks_mutations_before_transport():
    class FakeClient:
        calls = []

        def _post(self, *args, **kwargs):
            self.calls.append((args, kwargs))
            return "read-only response"

    client = FakeClient()
    block_state_changing_calls(client)
    assert client._post("/app-api/v1/fund/get-spot-wallet") == "read-only response"
    with pytest.raises(ProductionWriteBlocked, match="/app-api/v1/order/create-order"):
        client._post("/app-api/v1/order/create-order", {"qty": "1"})
    assert len(client.calls) == 1
