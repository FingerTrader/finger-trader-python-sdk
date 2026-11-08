"""Account, balance, and position endpoints confirmed in Finger_desk."""

from ..models import ApiResponse


class Accounts:
    def __init__(self, client):
        self._client = client

    def list(self) -> ApiResponse:
        return self.detail()

    def detail(self, market: int | None = None) -> ApiResponse:
        # The active Desk API's login profile is session scoped; market is
        # retained for source compatibility with the previous SDK signature.
        del market
        return self._client._post("/app-api/v1/public/login-info")

    def balance(self) -> ApiResponse:
        return self._client._post("/app-api/v1/fund/get-spot-wallet")


class Positions:
    def __init__(self, client):
        self._client = client

    def list(
        self,
        *,
        account_id=None,
        order_status: int = 0,
        is_usd: bool = False,
        page: int = 1,
        page_size: int = 100,
        market_type: int | None = None,
    ) -> ApiResponse:
        if account_id is not None:
            raise ValueError(
                "Finger_desk endpoint has no account_id parameter; account context "
                "comes from the authenticated session."
            )
        if isinstance(page, bool) or not isinstance(page, int) or page < 1:
            raise ValueError("page must be a positive integer")
        if isinstance(page_size, bool) or not isinstance(page_size, int) or page_size < 1:
            raise ValueError("page_size must be a positive integer")
        if isinstance(order_status, bool) or not isinstance(order_status, int):
            raise ValueError("order_status must be the Finger Desk order type integer")
        return self._client._post(
            "/app-api/v1/order/get-holding-orders",
            {
                "page": page,
                "pageSize": page_size,
                "query": {
                    "marketType": market_type,
                    "orderType": order_status,
                    # Finger_desk CoinTypeEnum: USD=0, USDT=100.
                    "coinType": 0 if is_usd else 100,
                },
            },
        )
