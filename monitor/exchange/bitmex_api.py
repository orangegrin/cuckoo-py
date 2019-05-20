from exchange.bitmex.apihub.bitmex import BitMEX
import json
import requests
import urllib
import time
import hashlib
import hmac
import configparser
import logging

class BitmexApi(object):
        
    def __init__(self, api_key, api_secret):
        self.bitmex_obj = BitMEX(base_url='https://www.bitmex.com/api/v1/', symbol='XBTUSD', apiKey=api_key, apiSecret=api_secret, RestOnly=True)

    # 获取账号余额，以BTC计价
    def walletBalanceBTC(self):
        resp_data = self.bitmex_obj._curl_bitmex(
            path='user/walletSummary',
            query={
                'currency':'XBt',
            },
            verb="GET"
        )
        length = len(resp_data)
        decimal = 8
        margin_bal = 0
        for i in range(length):
            item = resp_data[i]
            if item['transactType'] != 'Total':
                continue
            
            margin_bal = item['marginBalance']
            margin_bal = margin_bal/(pow(10,decimal))
        return margin_bal
    
    def depth(self,symbol,limit=5):
        resp_data = self.bitmex_obj._curl_bitmex(
            path='orderBook/L2',
            query={
                'symbol':symbol,
            },
            verb="GET"
        )

    
    def getAllPosition(self):
        resp_data = self.bitmex_obj._curl_bitmex(
            path='position',
            verb="GET"
        )
        all_bal = {}
        for item in resp_data:
            asset = item['underlying']
            all_bal[asset] = {
                'asset': asset,
                'total': item['openingQty']
            }
        return all_bal

