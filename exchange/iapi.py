from Exchange.Enum import Side,OrderType,OrderResultType

class ExchangeAPI(object):
    def __init__(self):
        pass
        
    def open_market_order(self,market_symbal,side,price,amount):
        pass

    def open_limit_order(self,market_symbal,side,price,amount):
        pass

    def modify_order(self,order_id,price,amount):
        pass

    def cancel_order(self,order_id):
        pass

