"""Market WebSocket client using the optional ``websocket-client`` package."""
from __future__ import annotations
import json, time, uuid

class MarketWebSocket:
    def __init__(self, auth_base, *, token=None, timeout=10):
        self.auth_base, self.token, self.timeout = auth_base.rstrip("/"), token, timeout
        self._ws = None

    @staticmethod
    def parse_message(message):
        if isinstance(message, bytes): message = message.decode("utf-8")
        return json.loads(message)

    def connect(self):
        try: import websocket
        except ImportError as exc: raise RuntimeError("WebSocket support requires optional dependency websocket-client") from exc
        import urllib.request
        headers={}
        if self.token: headers={"Authorization": "Bearer "+self.token, "token":self.token}
        req=urllib.request.Request(self.auth_base+"/ws-api/v1/auth/build-ticket", data=b"{}", headers={**headers,"Content-Type":"application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=self.timeout) as r: envelope=json.loads(r.read())
        ticket=envelope.get("data")
        if isinstance(ticket,dict): ticket=ticket.get("data",ticket.get("ticket"))
        if not ticket: raise RuntimeError("Ticket response did not contain a ticket")
        self._ws=websocket.create_connection(self.auth_base.replace("https://","wss://").replace("http://","ws://")+"/ws?ticket="+str(ticket), timeout=self.timeout)
        return self

    def subscribe(self, tickers, *, market="stock", on_message=None):
        if self._ws is None: self.connect()
        # Finger_desk market sender uses action=3, msgType=SUBSCRIBE(1), content={tickerList:[...]}
        frame={"action":3,"msgType":1,"timestamp":str(int(time.time()*1000)),"msgId":uuid.uuid4().hex,"content":{"tickerList":list(tickers)}}
        self._ws.send(json.dumps(frame,separators=(",",":")))
        if on_message is None: return self
        while True:
            raw=self._ws.recv()
            if raw is None: break
            on_message(self.parse_message(raw))
        return self

    def recv(self): return self.parse_message(self._ws.recv())
    def close(self):
        if self._ws is not None: self._ws.close(); self._ws=None
