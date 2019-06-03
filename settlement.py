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
import redis
import argparse
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--settlement', type=str, help='the origin settlement json config')
parser.add_argument('--bitmex_key', type=str, help='the bitmex key')

parser.add_argument('--bitmex_secret', type=str, help='the bitmex secret')

parser.add_argument('--binance_key', type=str, help='the binance key')
parser.add_argument('--binance_secret', type=str, help='the binance secret')
parser.add_argument('--stratege_id', type=float, help='the stratege id')

args = parser.parse_args()


# config = configparser.ConfigParser()
# config.read('config.ini')

# api_key = config.get('bitmex','api_key')
# api_secret = config.get('bitmex','api_secret')

# binance_key = config.get('binance','api_key')
# binance_secret = config.get('binance','api_secret')

# json_file = "settlement.json"
# with open(json_file,'r') as load_f:
#     config_json = json.load(load_f)
# print(json.dumps(config_json))


bitmex_key = args.bitmex_key
bitmex_secret = args.bitmex_secret

binance_key = args.binance_key
binance_secret = args.binance_secret

#--settlement='{"origin_bal": {"binance": {"EOS": {"asset": "EOS", "total": 1060}, "ETH": {"asset": "ETH", "total": 113}, "LTC": {"asset": "LTC", "total": 100.009}, "BTC": {"asset": "BTC", "total": 14.76901981}, "BNB": {"asset": "BNB", "total": 4.79533414}}, "bitmex": {"BTC": {"asset": "BTC", "total": 7.90250209}}}}'
config_json = json.loads(args.settlement)

def run():
    bitmex_api = BitmexApi(bitmex_key,bitmex_secret)
    binance_api = BinanceApi(binance_key,binance_secret)

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

    sleep_time = 60*30;
    while True:
        # 币安btc余额
        binance_total_bal = binance_api.walletBalanceBTC()
        # 需要扣除的币种
        binance_btc_minus = binance_api._caculateBtcBal(minus_list)

        # 扣除后的余额
        binance_bal = binance_total_bal - binance_btc_minus

        # bitmex 余额
        bitmex_bal = bitmex_api.walletBalanceBTC()

        # 当前总余额
        latest_bal = binance_bal+bitmex_bal
        origin_bal = config_json['origin_bal']['binance']['BTC']['total'] + config_json['origin_bal']['bitmex']['BTC']['total']
        win_bal = latest_bal-origin_bal
        win_rate = win_bal/origin_bal

        log_data = {
            'binance_total_bal':binance_total_bal,
            'binance_bal':binance_bal,
            'bitmex_bal':bitmex_bal,
            'latest_bal':latest_bal,
            'origin_bal':origin_bal,
            'win_bal': win_bal,
            'win_rate': win_rate
        }
        print(log_data)

        log_str = json.dumps(log_data)
        logger.info(log_str)
        time.sleep(sleep_time)



run()