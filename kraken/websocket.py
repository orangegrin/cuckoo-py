import json
from websocket import create_connection
from threading import Thread
import time
import traceback

class WebsocketClient():
    def __init__(self, ws_url="wss://ws.kraken.com"):
        self.stop = False
        self.url = ws_url
        self.ws = create_connection(self.url)
        self.handle_fun = None
        self.data_cache = {}

    def sub(self,channel="book",symbol_pair=["ETH/XBT","EOS/XBT","LTC/XBT","XRP/XBT"]):
        self.open()
        sub_msg = {
                "event": "subscribe",
                "pair": symbol_pair,
                "subscription": {
                    "name": channel
                }
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
                if isinstance(msg,dict) and msg.get("event","ping")== "ping":
                    print("Got fcoin ping msg or something unexpect: ",msg)
                else:
                    self.handle(msg)

    def make_ping(self):
        ping_msg={"event":"ping","cid":"sample.client.id"}
        self.ws.send(json.dumps(ping_msg))

    def handle(self, msg):

        if isinstance(msg,dict):
            if msg.get("status",None) == "subscribed":
                self.data_cache[msg['channelID']]={'bids':{},'asks':{},'pair': msg['pair']}
            if msg.get("event",None) == "pong":
                return None
        elif isinstance(msg,list):
            chanid = msg[0]
            tmp_msg = msg[1]
            
            if isinstance(tmp_msg,dict):
                if tmp_msg.get('as',None):
                    tmp_msg['a'] = tmp_msg['as']
                elif tmp_msg.get('bs',None):
                    tmp_msg['b'] = tmp_msg['bs']
                    
            try:
                for itemp in tmp_msg.get('a',[]):
                    price,amount,_timestamp = map(float,itemp)
                    if amount != 0:
                        self.data_cache[chanid]['asks'][price] = abs(amount)
                    elif amount == 1:
                        self.data_cache[chanid]['asks'].pop(price, None)
                for itemp in tmp_msg.get('b',[]):
                    price,amount,_timestamp = map(float,itemp)
                    if amount != 0:
                        self.data_cache[chanid]['bids'][price] = abs(amount)
                    elif amount == 1:
                        self.data_cache[chanid]['bids'].pop(price, None)
            except Exception:
                print(traceback.format_exc())
                print("error msg:",tmp_msg)

        if self.handle_fun:
            self.handle_fun(self.data_cache)
            # self.handle_fun(msg)
        else:
            print(msg)
        return None
    def close(self):
        self.ws.close()
        self.closed()

    def closed(self):
        print("Socket Closed")
