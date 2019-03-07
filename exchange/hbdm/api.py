import sys
sys.path.append('../')
from exchange.iapi import IExchangeAPI
from exchange.enums import Side,OrderType,OrderResultType
from service import HuobiDM

import configparser

class HuobiAPI(object):                                        
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.access_key = self.config.get('huobi', 'access_key')
        self.secret_key = self.config.get('huobi', 'secret_key')
        self.url = "https://api.huobi.pro/"
        self.dm = HuobiDM(self.url, self.access_key, self.secret_key)

    def open_market_order(self,market_symbol,p_side,amount):
        return self.open_order(market_symbol,p_side,'',amount,OrderType.Market)

    def open_limit_order(self,market_symbol,p_side,price,amount):
        return self.open_order(market_symbol,p_side,price,amount,OrderType.Limit)

    
    def open_order(self,market_symbol,p_side,price,amount,p_order_type):
        direction = ''
        if(p_side == Side.Buy):
            direction = 'buy'
        elif(p_side == Side.Sell):
            direction = 'sell'
        
        h_order_type = ''
        if(p_order_type == OrderType.Limit):
            h_order_type = 'limit'
        elif(p_order_type == OrderType.Market):
            h_order_type = 'opponent'
 
        ret = self.dm.send_contract_order(symbol='BTC', contract_type='this_week', contract_code='', 
                        client_order_id='', price=price, volume=amount, direction=direction,
                        offset='open', lever_rate=5, order_price_type=h_order_type)

        if(ret['status'] == 'ok'):
            order_id = ret['order_id']
            return order_id
        else:
            return False

    # def ModifyOrder(self,MarketSymbol,OrderId,Price,Amount):
    #     pass

    # def CancelOrder(self,OrderId):
    #     pass

