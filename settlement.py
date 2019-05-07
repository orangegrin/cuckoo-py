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

class BinanceApi(object):
    def __init__(self, api_key, api_secret):
        self.api_key =  api_key
        self.api_secret = api_secret
        self.url = 'https://api.binance.com'

    def walletBalanceBTC(self):
        all_bal = self.getAllBalance()
        return self._caculateBtcBal(all_bal)

    def _caculateBtcBal(self,all_bal):
        length = len(all_bal)
        total_btc = 0
        for i in range(length):
            asset = all_bal[i]['asset']
            amount = all_bal[i]['total']
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
        length = len(balances)
        none_zero_bal = []
        for i in range(length):
            item = balances[i]
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
                none_zero_bal.append(new_item)
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

            # data = {"sign":"xxxx","data":[{"uid":110,"remark":"just4test"}]}


            if method == 'POST':
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



 
# logging.basicConfig(level=logging.DEBUG,
#                     filename='balance.log',
#                     datefmt='%Y-%m-%d %H:%M:%S',
#                     format='%(asctime)s  %(message)s')

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

    win_rate = (latest_bal-origin_bal)/origin_bal

    log_data = {
        'binance_bal':binance_bal,
        'bitmex_bal':bitmex_bal,
        'latest_bal':latest_bal,
        'origin_bal':origin_bal,
        'win_rate':win_rate
    }

    log_str = json.dumps(log_data)
    logger.info(log_str)
    time.sleep(sleep_time)

