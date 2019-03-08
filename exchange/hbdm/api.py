from exchange.enums import Side, OrderType, OrderResultType
import configparser
from .service import HuobiDM
from exchange.iapi import IExchangeAPI
import sys
sys.path.append('../')
from db.redis_lib import RedisLib
import redis

class HuobiAPI(object):
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.access_key = self.config.get('huobi', 'access_key')
        self.secret_key = self.config.get('huobi', 'secret_key')
        self.url = "http://api.hbdm.com"
        self.dm = HuobiDM(self.url, self.access_key, self.secret_key)
        self.redis_lib = RedisLib()
        self.redis_conn = redis.Redis(host='localhost', port=6379)
        self.postion_info = {}



    def open_market_order(self, market_symbol, p_side, amount):
        # huobi 1张合约是100美金
        return self.open_order(market_symbol, p_side, '', amount, OrderType.Market)

    def open_limit_order(self, market_symbol, p_side, price, amount):
        return self.open_order(market_symbol, p_side, price, amount, OrderType.Limit)
    
    def get_position_amount(self, market_symbol):
        if market_symbol in self.postion_info:
            return self.postion_info[market_symbol]
        else:
            self.postion_info[market_symbol] = self.get_position(market_symbol)
            return self.postion_info[market_symbol]
    def set_position_amount(self,market_symbol,amount):
        self.postion_info[market_symbol] = amount
        return True

    def open_order(self, market_symbol, p_side, price, amount, p_order_type):
        amount = (int) (amount/100)
        position_amount = self.get_position_amount(market_symbol)
        need_open_amount = amount
        need_close_amount = 0

        # 仓位是空，需要开多仓
        if p_side == Side.Buy and position_amount < 0:
            #当前的空仓的数量
            down_amount = 0-position_amount

            #当前的多单数量
            up_amount = amount
            # 多单小于或等于空单
            if up_amount <= down_amount:
                need_close_amount = up_amount   #需要平空仓的数量
                need_open_amount = 0   #需要开多单的数量
            #多单大于空单
            else:
                need_close_amount = down_amount
                need_open_amount = up_amount-down_amount

        #仓位是多，需要开空仓
        elif p_side == Side.Sell and position_amount >0:

            #当前的空仓的数量
            down_amount = amount

            #当前的多单数量
            up_amount = position_amount

            # 多单小于或等于空单
            if up_amount <= down_amount:
                need_close_amount = up_amount   #需要平空仓的数量
                need_open_amount = down_amount-up_amount  #需要开多单的数量
            #多单大于空单
            else:
                need_close_amount = down_amount
                need_open_amount = 0

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

        if direction == 'buy' :
            new_position_amount = position_amount + amount
            if need_open_amount > 0 :
                ret = self.open_order_api(market_symbol=market_symbol, price=price, amount=need_open_amount, h_order_type=h_order_type,direction=direction)
                if ret == False:
                    return False
            if need_close_amount > 0:
                ret = self.close_market_order_api(market_symbol=market_symbol, amount=need_close_amount, direction='buy')

        else:
            new_position_amount = position_amount - amount
            if need_open_amount > 0 :
                ret = self.open_order_api(market_symbol=market_symbol, price=price, amount=need_open_amount, h_order_type=h_order_type,direction=direction)
                if ret == False:
                    return False
            if need_close_amount > 0:
                ret = self.close_market_order_api(market_symbol=market_symbol, amount=need_close_amount,direction='sell')
        self.set_position_amount(market_symbol,new_position_amount)
        return ret


    def open_order_api(self, market_symbol, price, amount, h_order_type,direction):
        amount = (int) (amount)
        ret = self.dm.send_contract_order(symbol=market_symbol, contract_type='this_week', contract_code='',
            client_order_id='', price=price, volume=amount, direction=direction,
            offset='open', lever_rate=5, order_price_type=h_order_type)
            
        if(ret['status'] == 'ok'):
            order_id = ret['data']['order_id']
            return order_id
        else:
            return False


    def close_market_order(self, market_symbol, amount, p_side):
        amount = (int)(amount/100)
        direction = ''
        if(p_side == Side.Buy):
            direction = 'buy'
        elif(p_side == Side.Sell):
            direction = 'sell'

        return self.close_market_order_api(market_symbol, amount, direction)


    def close_market_order_api(self, market_symbol, amount, direction):
        amount = (int) (amount)
        ret = self.dm.send_contract_order(symbol=market_symbol, contract_type='this_week', contract_code='',
                                        client_order_id='', price='', volume=amount, direction=direction,
                                        offset='close', lever_rate=5, order_price_type='opponent')
        print(ret)
        if(ret['status'] == 'ok'):
            return True
        else:
            return False

    # def ModifyOrder(self,MarketSymbol,OrderId,Price,Amount):
    #     pass

    # def CancelOrder(self,OrderId):
    #     pass



    def get_position(self,market_symbol):
        ret = self.dm.get_contract_position_info(market_symbol)
        # print(ret)
        if(len(ret['data'])>1):
            return False
        if(ret['data'] is not None):
            data = ret['data'][0]
            if data['direction'] == 'buy':
                return data['volume']
            else:
                return 0-data['volume']
        else:
            return 0
    