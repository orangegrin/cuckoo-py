import sys
from time import sleep
from market_maker import bitmex
from market_maker.settings import settings
from market_maker.utils import log, constants, errors, math

OrderSide = {'buy':'Buy','sell':'Sell'}
OrderType = {'limit':'Limit','market':'Market'}
logger = log.setup_custom_logger('root')



class BitMexMon(object):

    def __init__(self,symbol):
        """ Init bitmex api obj """
        self.symbol = symbol
        self.bitmex = bitmex.BitMEX(
            base_url=settings.BASE_URL, symbol=self.symbol,
            apiKey=settings.API_KEY, apiSecret=settings.API_SECRET,
            orderIDPrefix=settings.ORDERID_PREFIX, postOnly=settings.POST_ONLY,
            timeout=settings.TIMEOUT
        )

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
        self.bitmex.create_bulk_orders(orders)
    
    def cancel_orders(self,orderIDs,cancel_all=False):
        """
        cancel orders by id array or cancel all activate orders 
        
        """
        while True:
            try:
                self.bitmex.cancel(orderIDs)
                sleep(settings.API_REST_INTERVAL)
            except ValueError as e:
                logger.info(e)
                sleep(settings.API_ERROR_INTERVAL)
            else:
                break
        

    def get_position(self):
        """
        get account current position with self.symbol
        """
        self.bitmex.position(self.symbol)
        

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
        order={
            "execInst": "Close",
            "ordType": ordType
        }
        if ordType==OrderType['limit']:
            order["price"]= price
        self.open_orders([order])
    
    def subscribe_data_callback(self,table_name,push_callback,format_func,args=[]):
        """
        table_name:'orderBookL2','order','position'...
        args: orderbook particle_size 0.5,1,4....
        """
        sub_callback_dic={table_name:
            {
                'callback_fun':push_callback,
                'dataformat_fun':format_func,
                'args':args # for future use
            }
        }
        self.bitmex.set_websocket_callback(sub_callback_dic)
        pass




def orderBookL2_data_format_func(data):
    print("In orderbookL2 data_format_func handle!!")
    return data[:6]+data[-6:]

def orderBookL2_callback(data):
    print("In orderbookL2 handle!!")
    print(data)

def run() -> None:
    bitmex_mon = BitMexMon('XBTUSD')

    # Try/except just keeps ctrl-c from printing an ugly stacktrace
    bitmex_mon.subscribe_data_callback('orderBookL2',orderBookL2_callback,orderBookL2_data_format_func)
    try:
        while True:
            sleep(3)
    except (KeyboardInterrupt, SystemExit):
        sys.exit()
    