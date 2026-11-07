"""Mock-only tests for the public API and HTTP transport."""

import json
import unittest
from decimal import Decimal
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock, patch
from urllib.error import URLError

from finger_trader import APIError, FingerTraderClient, MarketBar, UnknownOutcomeError


class Response:
    def __init__(self, payload):
        self._body = BytesIO(json.dumps(payload).encode())

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None

    def read(self, size=-1):
        return self._body.read(size)


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.seen = []
        self.opener = Mock()

        def fake_open(request, timeout=None):
            self.seen.append(request)
            if request.full_url.endswith("/oauth2/token"):
                payload = {
                    "code": 0,
                    "success": True,
                    "message": "ok",
                    "data": {
                        "access_token": "test-access-token",
                        "refresh_token": "test-refresh-token",
                        "token_type": "Bearer",
                        "expires_in": 60,
                    },
                }
            else:
                payload = {
                    "code": 0,
                    "success": True,
                    "message": "ok",
                    "data": [{"ticker": "AAPL", "close": "12.30"}],
                }
            return Response(payload)

        self.opener.open.side_effect = fake_open
        self.builder = patch("finger_trader.transport.build_opener", return_value=self.opener)
        self.builder.start()
        self.addCleanup(self.builder.stop)

    def make_client(self, **kwargs):
        options = {
            "base_url": "https://mock.invalid/api",
            "auth_url": "https://mock.invalid/auth",
            "socket_auth_url": "https://mock.invalid/socket",
            "token": "test-access-token",
            "oauth_basic_token": "test-basic-token",
        }
        options.update(kwargs)
        return FingerTraderClient(**options)

    def test_market_mapping_and_auth_headers(self):
        client = self.make_client()
        client.market_data.history(market="stock", ticker="AAPL", interval="1d", limit=10)
        request = self.seen[-1]
        self.assertEqual(request.get_method(), "GET")
        self.assertIn("/api/mob/market/kline/getKline?", request.full_url)
        self.assertIn("market=stock", request.full_url)
        self.assertEqual(request.get_header("Authorization"), "Bearer test-access-token")
        self.assertEqual(request.get_header("Token"), "test-access-token")

    def test_trade_request_field_mapping_and_decimal(self):
        self.make_client().orders.submit(
            is_buy=True,
            is_usd=True,
            limit_time=0,
            market=1,
            order_id="client-order-1",
            order_type=1,
            price=Decimal("1.20"),
            quantity=2,
            ticker="AAPL",
            is_create=1,
        )
        payload = json.loads(self.seen[-1].data)
        self.assertEqual(payload["price"], "1.20")
        self.assertEqual(payload["quantity"], 2)
        self.assertEqual(payload["isCreate"], 1)
        self.assertEqual(payload["stopLose"], "0")

    def test_invalid_quantity_and_price_are_rejected_before_network(self):
        client = self.make_client()
        args = dict(
            is_buy=True,
            is_usd=True,
            limit_time=0,
            market=1,
            order_id="client-order-1",
            order_type=1,
            price=1,
            quantity=0,
            ticker="AAPL",
            is_create=1,
        )
        with self.assertRaises(ValueError):
            client.orders.submit(**args)
        args.update(quantity=1, price=-1)
        with self.assertRaises(ValueError):
            client.orders.submit(**args)
        self.assertEqual(self.seen, [])

    def test_token_login_form_repr_and_no_refresh_secret_copy(self):
        client = self.make_client(token=None)
        result = client.auth.login("user", "password", account_type=1)
        self.assertTrue(client.auth.is_authenticated)
        self.assertIn(b"grant_type=password", self.seen[-1].data)
        self.assertNotIn("test-access-token", repr(result))
        self.assertNotIn("test-refresh-token", repr(result))
        self.assertNotIn("test-access-token", repr(client))
        self.assertFalse(hasattr(client, "refresh_token"))

    def test_login_requires_explicit_oauth_client_credential(self):
        client = self.make_client(oauth_basic_token=None)
        with self.assertRaisesRegex(RuntimeError, "oauth_basic_token"):
            client.auth.login("user", "password", account_type=1)
        self.assertEqual(self.seen, [])

    def test_bar_decimal_parsing(self):
        bar = MarketBar.from_dict(
            {"t": 123, "o": "1.10", "h": "2", "l": "1", "c": "1.50", "v": "3"}
        )
        self.assertEqual(bar.close, Decimal("1.50"))

    def test_response_repr_hides_private_payload(self):
        client = self.make_client()
        response = client._api._unwrap({"account": "private-account", "token": "secret"})
        self.assertNotIn("private-account", repr(response))
        self.assertNotIn("secret", repr(response))

    def test_history_rejects_naive_datetime_and_nonpositive_paging(self):
        from datetime import datetime

        client = self.make_client()
        with self.assertRaisesRegex(ValueError, "timezone-aware"):
            client.market_data.history(
                market="stock", ticker="AAPL", interval="1d", start_time=datetime(2025, 1, 1)
            )
        with self.assertRaisesRegex(ValueError, "positive integer"):
            client.market_data.history(market="stock", ticker="AAPL", interval="1d", page=0)
        self.assertEqual(self.seen, [])

    def test_error_message_redacts_token_and_repr_hides_details(self):
        client = self.make_client()
        with patch.object(
            client._api._opener,
            "open",
            return_value=Response(
                {
                    "code": 401,
                    "success": False,
                    "message": "expired test-access-token",
                }
            ),
        ):
            with self.assertRaises(APIError) as caught:
                client._get("/private")
        self.assertNotIn("test-access-token", str(caught.exception))
        self.assertNotIn("test-access-token", repr(caught.exception))

    def test_redirect_is_rejected_without_following(self):
        client = self.make_client()
        self.opener.open.side_effect = __import__("urllib.error", fromlist=["HTTPError"]).HTTPError(
            "https://mock.invalid/api/private",
            302,
            "redirect",
            {"Location": "https://attacker.invalid/"},
            None,
        )
        with self.assertRaises(APIError):
            client._get("/private")
        self.assertEqual(self.opener.open.call_count, 1)

    def test_timeout_during_order_submission_is_unknown_outcome_and_not_retried(self):
        client = self.make_client()
        self.opener.open.side_effect = URLError("timed out")
        with self.assertRaises(UnknownOutcomeError) as caught:
            client.orders.submit(
                is_buy=True,
                is_usd=True,
                limit_time=0,
                market=1,
                order_id="client-order-2",
                order_type=1,
                price=1,
                quantity=2,
                ticker="AAPL",
                is_create=1,
            )
        self.assertEqual(caught.exception.code, "UNKNOWN_OUTCOME")
        self.assertEqual(self.opener.open.call_count, 1)

    def test_http_post_is_not_retried(self):
        client = self.make_client()
        self.opener.open.side_effect = URLError("timed out")
        with self.assertRaises(APIError):
            client.orders.cancel_limit("order-1")
        self.assertEqual(self.opener.open.call_count, 1)

    def test_transport_rejects_non_https_non_loopback_and_userinfo(self):
        for url in ("http://example.com/api", "https://user:pass@example.com/api"):
            with self.assertRaises(ValueError):
                FingerTraderClient(base_url=url)

    def test_websocket_json_parser_and_dedupe(self):
        from finger_trader.websocket import MarketWebSocket

        self.assertEqual(MarketWebSocket.parse_message(b'{"action":3,"msgType":1}')["action"], 3)
        with self.assertRaises(ValueError):
            MarketWebSocket.parse_message("[]")

    def test_websocket_quote_subscribe_unsubscribe_close_and_ticket_safety(self):
        from finger_trader.websocket import MarketWebSocket

        socket_impl = Mock()
        socket_impl.handshake_response = SimpleNamespace(status=101)
        websocket_module = SimpleNamespace(create_connection=Mock(return_value=socket_impl))
        with (
            patch.dict("sys.modules", {"websocket": websocket_module}),
            patch(
                "finger_trader.websocket.HTTPTransport.request",
                return_value=SimpleNamespace(data="ticket secret"),
            ),
        ):
            stream = MarketWebSocket("https://mock.invalid/socket", token="access-secret")
            stream.subscribe(["AAPL"])
            stream.unsubscribe("AAPL")
            sent = [json.loads(call.args[0]) for call in socket_impl.send.call_args_list]
            self.assertEqual(sent[0]["action"], 3)
            self.assertEqual(sent[0]["msgType"], 1)
            self.assertEqual(sent[0]["content"], {"tickerList": ["AAPL"]})
            self.assertEqual(sent[1]["content"], {"tickerList": []})
            self.assertNotIn("ticket secret", repr(stream))
            stream.close()
            socket_impl.close.assert_called_once()

    def test_websocket_timeout_sends_confirmed_keepalive_frame(self):
        from finger_trader.websocket import MarketWebSocket

        socket_impl = Mock()
        socket_impl.handshake_response = SimpleNamespace(status=101)
        socket_impl.recv.side_effect = TimeoutError("socket timed out")
        websocket_module = SimpleNamespace(create_connection=Mock(return_value=socket_impl))
        with (
            patch.dict("sys.modules", {"websocket": websocket_module}),
            patch(
                "finger_trader.websocket.HTTPTransport.request",
                return_value=SimpleNamespace(data="ticket"),
            ),
        ):
            stream = MarketWebSocket("https://mock.invalid/socket", heartbeat_interval=0.01)
            stream.connect()
            self.assertIsNone(stream.recv())
            keepalive = json.loads(socket_impl.send.call_args.args[0])
            self.assertEqual(keepalive["action"], 1)
            self.assertEqual(keepalive["msgType"], 0)
            self.assertEqual(keepalive["content"], "")
            stream.close()

    def test_websocket_disconnect_reconnects_and_resubscribes(self):
        from finger_trader.websocket import MarketWebSocket

        initial = Mock()
        initial.handshake_response = SimpleNamespace(status=101)
        initial.recv.side_effect = OSError("connection dropped")
        recovered = Mock()
        recovered.handshake_response = SimpleNamespace(status=101)
        recovered.recv.return_value = '{"action":3,"msgType":0,"msgId":"quote-1"}'
        reconnect = Mock(side_effect=[initial, recovered])
        websocket_module = SimpleNamespace(create_connection=reconnect)
        with (
            patch.dict("sys.modules", {"websocket": websocket_module}),
            patch(
                "finger_trader.websocket.HTTPTransport.request",
                return_value=SimpleNamespace(data="ticket"),
            ),
            patch("finger_trader.websocket.time.sleep"),
        ):
            stream = MarketWebSocket("https://mock.invalid/socket")
            stream.connect()
            stream.subscribe(["AAPL"])
            self.assertIsNone(stream.recv())
            self.assertEqual(reconnect.call_count, 2)
            resent = json.loads(recovered.send.call_args.args[0])
            self.assertEqual(resent["content"]["tickerList"], ["AAPL"])
            first = stream.recv()
            duplicate = stream.recv()
            self.assertEqual(first["msgId"], "quote-1")
            self.assertIsNone(duplicate)
            stream.close()

    def test_client_close_closes_managed_websocket(self):
        from finger_trader.websocket import MarketWebSocket

        client = self.make_client()
        client.websocket = Mock(return_value=Mock(spec=MarketWebSocket))
        managed = client.websocket()
        client._websockets.add(managed)
        client.close()
        managed.close.assert_called_once()

    def test_auth_error_does_not_retain_or_echo_password(self):
        client = self.make_client()
        self.opener.open.side_effect = None
        self.opener.open.return_value = Response(
            {
                "code": 400,
                "success": False,
                "message": "invalid password: supersecret",
            }
        )
        with self.assertRaises(APIError) as caught:
            client.auth.login("user", "supersecret", account_type=1)
        self.assertNotIn("supersecret", str(caught.exception))
        self.assertIsNone(caught.exception.details)


if __name__ == "__main__":
    unittest.main()
