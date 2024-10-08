import json
import requests
import urllib
import time
import hashlib
import hmac
import configparser
import logging

class BinanceApi(object):
    def __init__(self, api_key, api_secret):
        self.api_key =  api_key
        self.api_secret = api_secret
        self.url = 'https://api.binance.com'

    def walletBalanceBTC(self):
        all_bal = self.getAllBalance()
        all_bal = all_bal.values()
        return self._caculateBtcBal(all_bal)

    def _caculateBtcBal(self,all_bal):
        length = len(all_bal)
        total_btc = 0
        for bal in all_bal:
            asset = bal['asset']
            amount = bal['total']
            if asset == 'BTC':
                total_btc += amount
                continue

            if asset == 'USDT':
                symbol = 'BTC'+asset
                price = self.price(symbol)
                total_btc += amount/price
                continue

            symbol = asset+'BTC'
            price = self.price(symbol)
            if price == False:
                continue
            total_btc += price * amount

        return total_btc

    def depth(self,symbol,limit=5):
        path = '/api/v1/depth'
        params = {
            'symbol': symbol,
            'limit': limit
        }
        info = self._query('GET',path,params)
        return info
    

    def price(self,symbol):
        path = '/api/v3/ticker/price'
        params = {
            'symbol': symbol
        }
        info = self._query('GET',path,params)
        if info == False:
            return False
        price = float(info['price'])
        return price

    def getAllBalance(self,need_asset=None):
        path = '/api/v3/account'
        params = {}
        params['timestamp'] = int(round(time.time() * 1000))
        info = self._query(method='GET',path=path,params=params,auth=True)
        balances = info['balances']
        none_zero_bal = {}
        for item in balances:
            new_item = {}
            asset = item['asset']
            
            free_amount = float(item['free'])
            locked_amount = float(item['locked'])
            total_amount = free_amount + locked_amount
            if total_amount != 0:
                new_item['asset'] = item['asset']
                new_item['total'] = total_amount
                new_item['free'] = free_amount
                new_item['locked'] = locked_amount
                none_zero_bal[asset] = new_item 
        return none_zero_bal

    def _makeSignature(self,query_str):
        secret_bytes = bytes(self.api_secret, encoding = "utf8")
        query_bytes = bytes(query_str, encoding = "utf8")
        m = hmac.new(secret_bytes, query_bytes, hashlib.sha256)
        signature = m.hexdigest()
        return signature
    

    def _query(self,method,path,params,auth=False):
        query_url = self.url+path
        # params['timestamp'] = int(round(time.time() * 1000))
        query_str = urllib.parse.urlencode(params)

        if auth == False:
            if method == 'GET':
                query_url = query_url + '?'+query_str
                res = requests.get(query_url)
        else:
            signature = self._makeSignature(query_str)
            query_str = query_str + '&signature='+signature

            headers = {'X-MBX-APIKEY': self.api_key}

            if method == 'POST':
                reqbody = query_str
                res = requests.post(
                    query_url,
                    data=reqbody,
                    headers=headers)

            elif method== 'GET':
                query_url = query_url + '?'+query_str
                res = requests.get(query_url,headers=headers)


        if res.status_code != 200:
            return False

        info = json.loads(res._content.decode())
        return info
    