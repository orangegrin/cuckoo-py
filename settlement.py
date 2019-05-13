from exchange.bitmex.apihub.bitmex import BitMEX
import json
import requests
import urllib
import time
import hashlib
import hmac
import configparser
import logging
from exchange_api import BinanceApi
from exchange_api import BitmexApi

config = configparser.ConfigParser()
config.read('config.ini')

api_key = config.get('bitmex','api_key')
api_secret = config.get('bitmex','api_secret')

binance_key = config.get('binance','api_key')
binance_secret = config.get('binance','api_secret')


binance_api = BinanceApi(binance_key,binance_secret)
bitmex_api = BitmexApi(api_key,api_secret)

minus_list = [
    {'asset':'EOS','total':1060},
    {'asset':'XRP','total':1000},
    {'asset':'ETH','total':46},
    {'asset':'BNB','total':4.08822561},
]

logger = logging.getLogger(__name__)

logger.setLevel(level=logging.INFO)
handler = logging.FileHandler('balance.log')
formatter = logging.Formatter('%(asctime)s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

sleep_time = 60*30;
while True:
    # 币安btc余额
    binance_btc_bal = binance_api.walletBalanceBTC()
    # 需要扣除的币种
    binance_btc_minus = binance_api._caculateBtcBal(minus_list)

    # 扣除后的余额
    binance_bal = binance_btc_bal - binance_btc_minus

    # bitmex 余额
    bitmex_bal = bitmex_api.walletBalanceBTC()

    # 当前总余额
    latest_bal = binance_bal+bitmex_bal
    origin_bal = 2.34730272 + 1.08420454
    win_btc = latest_bal-origin_bal
    win_rate = win_btc/origin_bal

    log_data = {
        'binance_bal':binance_bal,
        'bitmex_bal':bitmex_bal,
        'latest_bal':latest_bal,
        'origin_bal':origin_bal,
        'win_btc': win_btc,
        'win_rate': win_rate
    }

    log_str = json.dumps(log_data)
    logger.info(log_str)
    time.sleep(sleep_time)

