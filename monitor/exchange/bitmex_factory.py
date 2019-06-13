import json
import requests
import urllib
import time
import hashlib
import hmac
import configparser
import logging
import asyncio
from exchange.bitmex.apihub.bitmex_websocket import BitMEXWebsocket


class BitmexWsFactory(object):
    def __init__(self, api_key=None, api_secret=None):
        self.api_key =  api_key
        self.api_secret = api_secret
        self.base_url = "wss://www.bitmex.com/realtime"
        self.bitmex_ws = {}

        self.logger = logging.getLogger(__name__)
        
        handler = logging.FileHandler('log/bitmex_ws.log')
        formatter = logging.Formatter('%(asctime)s %(message)s')
        handler.setFormatter(formatter)
        self.logger.setLevel(level=logging.INFO)
        self.logger.addHandler(handler)

    def get_ws(self,symbol):
        if symbol in self.bitmex_ws:
            return self.bitmex_ws[symbol]

        self.bitmex_ws[symbol] = BitMEXWebsocket(endpoint=self.base_url, symbol=symbol, api_key=self.api_key, api_secret=self.api_secret)
        return self.bitmex_ws[symbol]

    def market_depth(self,ws):
        t = time.time()
        time_ms = int(round(t * 1000))
        time_int = int(t)

        if not ws.ws.sock:
            self.logger.info("reconnect ws "+ws.symbol)
            ws.connect(self.base_url)

        depth = ws.market_depth()
        if depth == None:
            return False
        bids = []
        asks = []
        
        for item in depth:
            item['time_int'] = time_int
            item['time_ms'] = time_ms
            if item['side'] == 'Sell':
                asks.append(item)
            elif item['side'] == 'Buy':
                bids.append(item)
        bids = sorted(bids, key=lambda x: x['price'],reverse=True)
        asks = sorted(asks, key=lambda x: x['price'])

        return {'bids':bids,'asks':asks}

