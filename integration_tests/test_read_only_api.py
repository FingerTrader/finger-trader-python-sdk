"""Read-only HTTP calls against an explicitly configured Sandbox/Dev service."""

import pytest

from finger_trader import ApiResponse


def _assert_response(response: ApiResponse) -> None:
    assert isinstance(response, ApiResponse)
    # Preserve the backend schema; integration checks intentionally do not
    # impose a guessed DTO shape on these endpoints.
    assert response.data is not None


def test_authentication_is_available(live_client, integration_config):
    assert live_client.auth.check()
    if integration_config.auth_mode == "password":
        assert live_client._api.token


def test_market_list(live_client):
    _assert_response(live_client.market_data.markets())


def test_product_list(live_client, integration_config):
    _assert_response(live_client.market_data.symbols(market=integration_config.market))


def test_historical_bars(live_client, integration_config):
    if not integration_config.ticker or not integration_config.interval:
        pytest.skip("Set FINGER_TRADER_IT_TICKER and FINGER_TRADER_IT_INTERVAL for K-line checks")
    _assert_response(
        live_client.market_data.history(
            market=integration_config.market,
            ticker=integration_config.ticker,
            interval=integration_config.interval,
            limit=1,
            page=1,
        )
    )


def test_account_profile(live_client, integration_config):
    if integration_config.account_market is None:
        pytest.skip(
            "Set FINGER_TRADER_IT_ACCOUNT_MARKET to the server market enum for this account"
        )
    _assert_response(live_client.accounts.detail(market=integration_config.account_market))


def test_balance(live_client):
    _assert_response(live_client.accounts.balance())


def test_positions(live_client, integration_config):
    _assert_response(
        live_client.positions.list(
            order_status=integration_config.position_type,
            is_usd=integration_config.position_is_usd,
        )
    )
