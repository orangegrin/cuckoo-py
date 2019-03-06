from ExchangeAPI import ExchangeAPI
from Exchange.Enum import Side,OrderType,OrderResultType
from HuobiDMService import HuobiDM
import configparser

class HuobiAPI(ExchangeAPI):
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.access_key = self.config.get('huobi', 'access_key')
        self.secret_key = self.config.get('huobi', 'secret_key')
        self.url = "https://api.huobi.pro/"
        self.dm = HuobiDM(self.url, self.access_key, self.secret_key)

    def OpenMarketOrder(self,MarketSymbol,pSide,Price,Amount):
        return self.OpenOrder(MarketSymbol,pSide,Price,Amount,OrderType.Market)

    def OpenLimitOrder(self,MarketSymbol,pSide,Price,Amount):
        return self.OpenOrder(MarketSymbol,pSide,Price,Amount,OrderType.Limit)

    def OpenOrder(self,MarketSymbol,pSide,Price,Amount,pOrderType):
        direction = ''
        if(pSide == Side.Buy):
            direction = 'buy'
        elif(pSide == Side.Sell):
            direction = 'sell'
        
        hOrderType = ''
        if(pOrderType == OrderType.Limit):
            hOrderType = 'limit'
        elif(pOrderType == OrderType.Market):
            hOrderType = 'opponent'
 
        ret = self.dm.send_contract_order(symbol='BTC', contract_type='this_week', contract_code='', 
                        client_order_id='', price=Price, volume=Amount, direction=direction,
                        offset='open', lever_rate=5, order_price_type=hOrderType)

        if(ret['status'] == 'ok'):
            OrderId = ret['order_id']
        else:
            return False

    # def ModifyOrder(self,MarketSymbol,OrderId,Price,Amount):
    #     pass

    # def CancelOrder(self,OrderId):
    #     pass

