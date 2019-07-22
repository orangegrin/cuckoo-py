import json
from websocket import create_connection
from threading import Thread
import time
import traceback

class WebsocketClient():
    def __init__(self, ws_url="wss://api-pub.bitfinex.com/ws/2"):
        self.stop = False
        self.url = ws_url
        self.ws = create_connection(self.url)
        self.handle_fun = None
        self.data_cache = {}

    def sub(self,channel_symbol_pair):
        self.open()
        for channel,symbol in channel_symbol_pair:
            sub_msg = { "event": "subscribe", "channel": channel, "symbol": symbol}
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
                if isinstance(msg,dict) and msg.get("event","ping")== "ping":
                    print("Got fcoin ping msg or something unexpect: ",msg)
                else:
                    self.handle(msg)

    def make_ping(self):
        ping_msg={"event":"ping","cid":"sample.client.id"}
        self.ws.send(json.dumps(ping_msg))

    def handle(self, msg):

        if isinstance(msg,dict):
            if msg.get("event",None) == "subscribed":
                self.data_cache[msg['chanId']]={'bids':{},'asks':{},'symbol': msg['symbol'], 'pair': msg['pair'],'channel': msg['channel']}
            if msg.get("event",None) == "pong":
                return None
        elif isinstance(msg,list):
            chanid = msg[0]
            tmp_msg = msg[1]
            if not isinstance(msg[1][0],list):
                tmp_msg = [tmp_msg]

            if tmp_msg[0]=='hb':
                return None
                
            try:
                for price,count,amount in tmp_msg:
                    if count > 0:
                        if amount > 0:
                            self.data_cache[chanid]['bids'][price] = amount
                        elif amount < 0:
                            self.data_cache[chanid]['asks'][price] = abs(amount)
                    elif count == 0:
                        if amount == 1:
                            self.data_cache[chanid]['bids'].pop(price, None)
                        elif amount == -1:
                            self.data_cache[chanid]['asks'].pop(price, None)
            except Exception:
                print(traceback.format_exc())
                print("error msg:",tmp_msg)

        if self.handle_fun:
            self.handle_fun(self.data_cache)
        else:
            print(msg)
        return None
    def close(self):
        self.ws.close()
        self.closed()

    def closed(self):
        print("Socket Closed")
