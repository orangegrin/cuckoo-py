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

class MonitorPosition(object):
    def __init__(self):
        logger = logging.getLogger(__name__)
        logger.setLevel(level=logging.INFO)
        handler = logging.FileHandler('log/moni_position.log')
        formatter = logging.Formatter('%(asctime)s %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        self.logger = logger

        config = configparser.ConfigParser()
        config.read('config.ini')
        self.config = config

        self.bitmex_key = self.config.get('bitmex','api_key')
        self.bitmex_secret = self.config.get('bitmex','api_secret')

        self.binance_key = self.config.get('binance','api_key')
        self.binance_secret = self.config.get('binance','api_secret')

        self.bitmex_api = BitmexApi(self.bitmex_key,self.bitmex_secret)
        self.binance_api = BinanceApi(self.binance_key,self.binance_secret)

        self.redis_host = self.config.get('redis','host')
        self.redis_port = self.config.get('redis','port')

        pool = redis.ConnectionPool(host=self.redis_host, port=self.redis_port, decode_responses=True)
        self.redis_object = redis.Redis(connection_pool=pool)

    def read_json_config(self):
        json_file = "moni_config/position.json"
        with open(json_file,'r') as load_f:
            self.json_config = json.load(load_f)
        return self.json_config


    def run(self):
        bitmex_all_bal = self.bitmex_api.getAllPosition()
        binance_all_bal = self.binance_api.getAllBalance()

        json_config = self.read_json_config()
        origin_binance = json_config['origin_bal']['binance']
        origin_bitmex = json_config['origin_bal']['bitmex']

        for asset in json_config['asset']:
            redis_key = json_config['asset'][asset]['redis_key']
            bitmex_num = get_asset_num(bitmex_all_bal,asset)
            binance_num = get_asset_num(binance_num,asset)
            bitmex_origin_num = get_asset_num(origin_bitmex,asset)
            binance_origin_num = get_asset_num(origin_binance,asset)
            if bitmex_num + binance_num != bitmex_origin_num + binance_origin_num:
                json_log = {'msg':'position is not equal','asset':asset}
                json_log_str = json.dumps(json_log)
                logger.info(json_log_str)
            

    def get_asset_num(self,all_bal,asset):
        if asset in all_bal:
            return all_bal[asset]['total']
        else:
            return 0

moni_obj = MonitorPosition()
moni_obj.run()