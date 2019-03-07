from abc import ABCMeta, abstractmethod

class IExchangeAPI(metaclass=ABCMeta):
    @abstractmethod
    def open_market_order(self, market_symbol, side, amount):
        pass
    @abstractmethod
    def open_limit_order(self, market_symbol, side, price, amount):
        pass
    @abstractmethod
    def modify_order(self, market_symbol, order_id, price, amount):
        pass

    # buy_orders = []
    # sell_orders = []
    # populate buy and sell orders, e.g.
    # buy_orders.append({'price': 999.0, 'orderQty': 100, 'side': "Buy"})
    # sell_orders.append({'price': 1001.0, 'orderQty': 100, 'side': "Sell"})
    @abstractmethod
    def converge_orders(self, buy_orders, sell_orders):
        pass
    @abstractmethod
    def cancel_order(self, order_id):
        pass

    @abstractmethod
    def close_market_order(self,market_symbol,order_id,amount,p_side):
        pass
