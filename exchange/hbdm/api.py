from exchange.enums import Side, OrderType, OrderResultType
import configparser
from .service import HuobiDM
from exchange.iapi import IExchangeAPI
import sys
sys.path.append('../')


class HuobiAPI(object):
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.access_key = self.config.get('huobi', 'access_key')
        self.secret_key = self.config.get('huobi', 'secret_key')
        self.url = "http://api.hbdm.com"
        self.dm = HuobiDM(self.url, self.access_key, self.secret_key)
        self.amount = 0

    def open_market_order(self, market_symbol, p_side, amount):
        # huobi 1张合约是100美金
        return self.open_order(market_symbol, p_side, '', amount, OrderType.Market)

    def open_limit_order(self, market_symbol, p_side, price, amount):
        return self.open_order(market_symbol, p_side, price, amount, OrderType.Limit)

    def open_order(self, market_symbol, p_side, price, amount, p_order_type):
        amount = (int) (amount/100)
        # 仓位是空，需要开多仓
        if p_side == Side.Buy and self.amount < 0:
            #当前的空仓的数量
            down_amount = 0-self.amount

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
        elif p_side == Side.Sell and self.amount >0:

            #当前的空仓的数量
            down_amount = amount

            #当前的多单数量
            up_amount = self.amount

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

        ret = self.dm.send_contract_order(symbol='BTC', contract_type='this_week', contract_code='',
                                          client_order_id='', price=price, volume=amount, direction=direction,
                                          offset='open', lever_rate=5, order_price_type=h_order_type)
        print(ret)
        if(ret['status'] == 'ok'):
            order_id = ret['data']['order_id']
            if(p_side == Side.Buy):
                self.amount += amount
            else:
                self.amount -= amount

            return order_id
        else:
            return False

    # def close_market_order(self, market_symbol, order_id, amount, direction):
    #     amount = (int)(amount/100)
    #     direction = ''
    #     if(p_side == Side.Buy):
    #         direction = 'buy'
    #     elif(p_side == Side.Sell):
    #         direction = 'sell'

    #     ret = self.dm.send_contract_order(symbol='BTC', contract_type='this_week', contract_code='',
    #                                       client_order_id='', price='', volume=amount, direction=direction,
    #                                       offset='close', lever_rate=5, order_price_type='opponent')
    #     print(ret)
    #     if(ret['status'] == 'ok'):
    #         return True
    #     else:
    #         return False

    # def ModifyOrder(self,MarketSymbol,OrderId,Price,Amount):
    #     pass

    # def CancelOrder(self,OrderId):
    #     pass
