from exchange.bitmex.apihub.bitmex import BitMEX
import json
import requests
import urllib
import time
import hashlib
import hmac
import configparser
import logging
from monitor.exchange.binance_api import BinanceApi
from monitor.exchange.bitmex_api import BitmexApi

config = configparser.ConfigParser()
config.read('config.ini')

api_key = config.get('bitmex','api_key')
api_secret = config.get('bitmex','api_secret')

binance_key = config.get('binance','api_key')
binance_secret = config.get('binance','api_secret')


binance_api = BinanceApi(binance_key,binance_secret)
bitmex_api = BitmexApi(api_key,api_secret)



json_file = "settlement.json"
with open(json_file,'r') as load_f:
    config_json = json.load(load_f)

binance_origin_bal = config_json['origin_bal']['binance']
minus_bal = dict(config_json['origin_bal']['binance'])
minus_bal.pop('BTC')
minus_list = minus_bal.values()

logger = logging.getLogger(__name__)

logger.setLevel(level=logging.INFO)
handler = logging.FileHandler('log/balance.log')
formatter = logging.Formatter('%(asctime)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

bitmex_all_bal = bitmex_api.getAllPosition()
binance_all_bal = binance_api.getAllBalance()
print(bitmex_all_bal)
print(binance_all_bal)
