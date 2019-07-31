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

import mysql.connector

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

sleep_time = 60*10;


mydb = mysql.connector.connect(
  host=config_json['mysql']['host'],
  user=config_json['mysql']['user'],
  passwd=config_json['mysql']['pwd'],
  database=config_json['mysql']['db']
)

mycursor = mydb.cursor()




while True:
    # 币安btc余额
    # binance_total_bal = binance_api.walletBalanceBTC()
    # # 需要扣除的币种
    # binance_btc_minus = binance_api._caculateBtcBal(minus_list)

    # 扣除后的余额
    # binance_bal = binance_total_bal - binance_btc_minus
    binance_bal = 0

    now = int(time.time())
    # bitmex 余额
    bitmex_bal = bitmex_api.walletBalanceBTC()
    position_bal = bitmex_api.getAllPosition()
    

    #套保盈亏
    xbtusd_margin = 0
    if position_bal != []:
        for pos in position_bal:
            if pos['symbol'] == 'XBTUSD':
                # xbtusd_margin = pos['realisedPnl']+pos['unrealisedPnl']
                xbtusd_margin = pos['unrealisedPnl']
                xbtusd_margin = xbtusd_margin/100000000
                break


    # 当前总余额
    latest_bal = binance_bal+bitmex_bal
    origin_bal = config_json['origin_bal']['binance']['BTC']['total'] + config_json['origin_bal']['bitmex']['BTC']['total']
    win_bal = latest_bal-origin_bal-xbtusd_margin

    win_rate = win_bal/origin_bal

    sql = "INSERT INTO settlement (create_time, final_bal, win_amount, protect_amount, win_rate) VALUES (%s, %s, %s, %s, %s)"
    val = (now, latest_bal, win_bal, xbtusd_margin, win_rate)
    mycursor.execute(sql, val)
    mydb.commit()

    # log_data = {
    #     # 'binance_total_bal':binance_total_bal,
    #     # 'binance_bal':binance_bal,
    #     'bitmex_bal':bitmex_bal,
    #     # 'latest_bal':latest_bal,
    #     # 'origin_bal':origin_bal,
    #     'win_bal': win_bal,
    #     'win_rate': win_rate
    # }

    # log_str = json.dumps(log_data)
    # logger.info(log_str)
    time.sleep(sleep_time)

