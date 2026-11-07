"""Safety checks for opt-in integration-test configuration; no network calls."""

from dataclasses import fields

import pytest

from integration_tests.conftest import IntegrationConfig, _https_url


def test_integration_url_rejects_known_production_host(monkeypatch):
    monkeypatch.setenv(
        "FINGER_TRADER_IT_API_BASE_URL",
        "https://prod-api.fingertrader.com/finger-bff-app",
    )
    with pytest.raises(ValueError, match="known production host"):
        _https_url("FINGER_TRADER_IT_API_BASE_URL")


def test_integration_url_requires_https_and_no_inline_credentials(monkeypatch):
    for value in (
        "http://sandbox.example.invalid/api",
        "https://user:pass@sandbox.example.invalid/api",
        "https://sandbox.example.invalid/api?token=value",
    ):
        monkeypatch.setenv("FINGER_TRADER_IT_API_BASE_URL", value)
        with pytest.raises(ValueError, match="HTTPS base URL"):
            _https_url("FINGER_TRADER_IT_API_BASE_URL")


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
        login_type=1,
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
