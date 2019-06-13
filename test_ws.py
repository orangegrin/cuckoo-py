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

base_url = "wss://www.bitmex.com/realtime"
bitmex_ws = BitMEXWebsocket(endpoint=base_url, symbol='XBTUSD',api_key=None,api_secret=None)
bitmex_ws.sub_depth(['XBTUSD','ETHUSD','ETHM19'])

while True:
    symbol_depth = bitmex_ws.take_depth()
    time.sleep(1)