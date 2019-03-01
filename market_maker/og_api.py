import sys

from market_maker.market_maker import OrderManager

orderSide = {'buy':'Buy','sell':'Sell'}
orderType = {'limit':'Limit','market':'Market'}

class CustomOrderManager(OrderManager):
    """A sample order manager for implementing your own custom strategy"""

    def place_orders(self) -> None:
        # implement your custom strategy here

        buy_orders = []
        sell_orders = []

        # populate buy and sell orders, e.g.
        # buy_orders.append({'price': 999.0, 'orderQty': 100, 'side': "Buy"})
        # sell_orders.append({'price': 1001.0, 'orderQty': 100, 'side': "Sell"})

        self.converge_orders(buy_orders, sell_orders)


def run() -> None:
    order_manager = CustomOrderManager()

    # Try/except just keeps ctrl-c from printing an ugly stacktrace
    try:
        order_manager.run_loop()
    except (KeyboardInterrupt, SystemExit):
        sys.exit()

class BitMexMon(object):

    def __init__(self,symbol):
        """ Init bitmex api obj """
        self.symbol = symbol
        pass
    
    def prepare_order(self,price,side,orderQty,ordType):
        """
        prepare order , may add some check
        """
        #if price > 0 and (
        # (orderQty >0 and side=='Buy') or (orderQty <0 and side=='Sell')
        # ) and (ordType=='Limit' or ordType=='Market')
        return {
                "ordType": ordType,
                "orderQty": orderQty,
                "price": price,
                "side": side
        }

    def open_orders(self,orders):
        """
        place multi orders also can place signal one
        orders : [{}...] array type

        """
        pass
    
    def cancel_orders(self,orderIDs,cancel_all=False):
        """
        cancel orders by id array or cancel all activate orders 
        
        """
        pass

    def get_position(self):
        """
        get account current position with self.symbol
        """
        pass

    def close_position(self,price,ordType):
        """
        close out account current position with self.symbol
        {
            execInst: "Close"
            ordType: "Limit"/"Market"
            price: 3803 if "Limit" else ''
            symbol: "XBTUSD"
        }
        """
        pass

    def push_data(self):
        pass
    
