from Exchange.Enum import Side,OrderType,OrderResultType

class ExchangeAPI(object):
    def __init__(self):
        pass
        
    def OpenMarketOrder(self,MarketSymbol,Side,Price,Amount):
        pass

    def OpenLimitOrder(self,MarketSymbol,Side,Price,Amount):
        pass

    def ModifyOrder(self,MarketSymbol,OrderId,Price,Amount):
        pass

    def CancelOrder(self,OrderId):
        pass

