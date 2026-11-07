import json
import unittest
from decimal import Decimal
from unittest.mock import patch
from io import BytesIO
from urllib.error import URLError

from finger_trader import APIError, MarketBar, FingerTraderClient


class Handler:
    seen=[]


class ClientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.base="https://mock.invalid"
    def setUp(self):
        Handler.seen.clear()
        def fake_open(request, timeout=None):
            body=request.data
            Handler.seen.append((request.get_method(),request.full_url,request.get_header("Authorization"),body))
            if request.full_url.endswith("/oauth2/token"):
                payload={"code":0,"success":True,"message":"ok","data":{"access_token":"a","refresh_token":"r","token_type":"Bearer","expires_in":60}}
            else: payload={"code":0,"success":True,"message":"ok","data":[{"ticker":"AAPL","close":"12.30"}]}
            return BytesIO(json.dumps(payload).encode())
        self.urlopen=patch("finger_trader.client.urlopen",side_effect=fake_open); self.urlopen.start()
    def tearDown(self): self.urlopen.stop()
    def client(self): return FingerTraderClient(base_url=self.base,auth_url=self.base,socket_auth_url=self.base,token="abc")
    def test_market_mapping_and_auth_headers(self):
        c=self.client(); c.market_data.history(market="stock",ticker="AAPL",interval="1d",limit=10)
        method,path,auth,_=Handler.seen[-1]
        self.assertEqual(method,"GET"); self.assertIn("/api/mob/market/kline/getKline?",path); self.assertIn("market=stock",path); self.assertEqual(auth,"Bearer abc")
    def test_trade_request_field_mapping(self):
        self.client().orders.submit(is_buy=True,is_usd=True,limit_time=0,market=1,order_id="",order_type=1,price=Decimal("1.20"),quantity=2,ticker="AAPL",is_create=1)
        payload=json.loads(Handler.seen[-1][3]); self.assertEqual(payload["price"],"1.20"); self.assertEqual(payload["isCreate"],1); self.assertEqual(payload["stopLose"],"0")
    def test_invalid_quantity_is_rejected_before_network(self):
        with self.assertRaises(ValueError): self.client().orders.submit(is_buy=True,is_usd=True,limit_time=0,market=1,order_id="",order_type=1,price=1,quantity=0,ticker="AAPL",is_create=1)
        self.assertEqual(Handler.seen,[])
    def test_token_login_form_and_token_state(self):
        c=self.client(); c.auth.login("u","p",account_type=1)
        self.assertTrue(c.auth.is_authenticated)
        self.assertIn(b"grant_type=password",Handler.seen[-1][3])
    def test_bar_decimal_parsing(self):
        b=MarketBar.from_dict({"t":123,"o":"1.10","h":"2","l":"1","c":"1.50","v":"3"})
        self.assertEqual(b.close,Decimal("1.50"))
    def test_error_payload(self):
        error=APIError.from_payload({"code":401,"message":"expired"},status=401,path="/x")
        self.assertEqual(error.code,401); self.assertEqual(error.message,"expired")
    def test_timeout_is_normalized_and_post_is_not_retried(self):
        c=self.client()
        with patch("finger_trader.client.urlopen",side_effect=URLError("timed out")) as call:
            with self.assertRaises(APIError) as caught: c.orders.cancel_limit("x")
        self.assertEqual(caught.exception.code,"NETWORK_ERROR"); self.assertEqual(call.call_count,1)
    def test_websocket_json_parser(self):
        from finger_trader.websocket import MarketWebSocket
        self.assertEqual(MarketWebSocket.parse_message(b'{"action":3,"msgType":1}')["action"],3)


if __name__ == "__main__": unittest.main()
