"""Read-only HTTP calls against an explicitly configured live service."""

import pytest

from finger_trader import APIError, ApiResponse, FingerTraderClient


def _assert_response(response: ApiResponse) -> None:
    assert isinstance(response, ApiResponse)
    # Preserve the backend schema; integration checks intentionally do not
    # impose a guessed DTO shape on these endpoints.
    assert response.data is not None


def test_authentication_is_available(live_client, integration_config):
    # A protected balance request below verifies server-side token acceptance;
    # check() itself intentionally reports only local token presence/expiry.
    assert live_client.auth.check()
    if integration_config.auth_mode == "password":
        assert live_client._api.token


def test_market_list(live_client):
    _assert_response(live_client.market_data.markets())


@pytest.mark.parametrize("market", ["stock", "forex", "crypto", "spot", "indices"])
def test_product_list_for_supported_markets(live_client, market):
    _assert_response(live_client.market_data.symbols(market=market))


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


def test_order_history(live_client):
    _assert_response(live_client.orders.history(page=1, limit=5))


def test_invalid_token_is_rejected(integration_config):
    """A deliberately invalid token must not gain access to a protected API."""
    client = FingerTraderClient(
        token="invalid-integration-test-token",
        base_url=integration_config.api_url,
        auth_url=integration_config.auth_url,
        socket_auth_url=integration_config.socket_auth_url,
        timeout=integration_config.timeout,
        environment="prod" if integration_config.target == "production-read-only" else "dev",
    )
    try:
        with pytest.raises(APIError) as error:
            client.accounts.balance()
        assert error.value.status in {401, 403}
    finally:
        client.close()


def test_live_client_blocks_all_state_changing_order_calls(live_client):
    """The live-client fixture rejects every order mutation before transport."""
    from integration_tests.conftest import ProductionWriteBlocked

    calls = [
        lambda: live_client.orders.submit(
            is_buy=True,
            is_usd=False,
            limit_time=0,
            market=0,
            order_id="",
            order_type=0,
            price="1",
            quantity=1,
            ticker="SAFETY-CHECK",
            is_create=1,
        ),
        lambda: live_client.orders.update_limit(order_id="safety-check", price="1"),
        lambda: live_client.orders.cancel_limit("safety-check"),
        lambda: live_client.orders.set_take_profit_loss(
            order_id="safety-check", stop_loss="0", take_profit="0"
        ),
    ]
    for call in calls:
        with pytest.raises(ProductionWriteBlocked):
            call()
