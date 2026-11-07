"""Account, balance, and position endpoints confirmed in Finger_desk."""

from ..models import ApiResponse


class Accounts:
    def __init__(self, client):
        self._client = client

    def list(self) -> ApiResponse:
        # The observed server endpoint requires market and returns a session profile.
        return self.detail(market=0)

    def detail(self, market: int) -> ApiResponse:
        return self._client._get(
            "/api/mob/trade/order-entity/getTradeProfileResponse",
            params={"market": market},
        )

    def balance(self) -> ApiResponse:
        return self._client._get("/api/mob/trade/wallet-entity/getWalletHomePage")


class Positions:
    def __init__(self, client):
        self._client = client

    def list(self, *, account_id=None, order_status: int = 0, is_usd: bool = False) -> ApiResponse:
        if account_id is not None:
            raise ValueError(
                "Finger_desk endpoint has no account_id parameter; account context "
                "comes from the authenticated session."
            )
        return self._client._get(
            "/api/mob/trade/order-entity/getHoldingListByIsUsd",
            params={"type": order_status, "isUsd": str(is_usd).lower()},
        )
