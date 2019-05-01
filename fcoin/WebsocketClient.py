import json
from websocket import create_connection
from threading import Thread
import time

class WebsocketClient():
    def __init__(self, ws_url="wss://api.fcoin.com/v2/ws",subprotocols=["binary","base64"]):
        self.stop = False
        self.url = ws_url
        self.ws = create_connection(self.url)
        self.handle_fun = None

    def sub(self,topics):
        self.open()
        sub_msg = {
            "id": "tickers",
            "cmd": "sub",
            "args": topics,
        }
        subParams = json.dumps(sub_msg)
        self.ws.send(subParams)
        self.listen()

    def open(self):
        print("-- Subscribed! --")

    def listen(self):
        lastping_at=time.time()
        while not self.stop:
            try:
                msg = json.loads(self.ws.recv())
                if (time.time() - lastping_at) > 25:
                    lastping_at = time.time()
                    self.make_ping()
            except Exception:
                break
            else:
                if msg.get("type","ping")== "ping":
                    print("Got fcoin ping msg or something unexpect: ",msg)
                else:
                    self.handle(msg)

    def make_ping(self):
        ping_msg={"cmd":"ping","args":[int(time.time()*1000)],"id":"sample.client.id"}
        self.ws.send(json.dumps(ping_msg))

    def handle(self, msg):
        if self.handle_fun:
            self.handle_fun(msg)
        else:
            print(msg)

    def close(self):
        self.ws.close()
        self.closed()

    def closed(self):
        print("Socket Closed")
