import sys
from time import sleep
from .apihub import bitmex
from .settings import settings
from .apihub.utils import log, constants, errors, math


OrderSide = {'buy':'Buy','sell':'Sell'}
OrderType = {'limit':'Limit','market':'Market'}
logger = log.setup_custom_logger('root')



class BitMexMon(object):

    def __init__(self,symbol,AuthSubTables=None,UnAuthSubTables=None):
        """ Init bitmex api obj """
        # str(settings.get('bitmex','api_url'))
        self.symbol = symbol
        self.bitmex = bitmex.BitMEX(
            base_url=settings.get('bitmex','api_url'), symbol=self.symbol,
            apiKey=settings.get('bitmex','api_key'), apiSecret=settings.get('bitmex','api_secert'),
            orderIDPrefix=settings.get('bitmex','orde_id_prefix'), postOnly=settings.getboolean('bitmex','post_only'),
            timeout=settings.getint('bitmex','timeout'),AuthSubTables=AuthSubTables,UnAuthSubTables=UnAuthSubTables,
            RestOnly=False
        )

    
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
        return self.bitmex.create_bulk_orders(orders)
    
    def amend_orders(self,orders):
        """
        place multi orders also can place signal one
        orders : [{}...] array type
        """
        return self.bitmex.amend_bulk_orders(orders)
    
    def cancel_orders(self,orderIDs,cancel_all=False):
        """
        cancel orders by id array or cancel all activate orders 
        
        """
        while True:
            try:
                self.bitmex.cancel(orderIDs,cancel_all=cancel_all)
                sleep(settings.getfloat('bitmex','api_rest_interval'))
            except ValueError as e:
                logger.info(e)
                sleep(settings.getfloat('bitmex','api_error_interval'))
            else:
                break
        

    def get_position(self):
        """
        get account current position with self.symbol
        """
        return self.bitmex.position(self.symbol)
        

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


    