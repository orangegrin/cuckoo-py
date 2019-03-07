import sys,requests
from time import sleep
from .apihub import bitmex
from .settings import settings
from .apihub.utils import log, constants, errors, math
from ..enums import OrderType,Side

OrderSideMap = {Side.Buy.value:'Buy',Side.Sell.value:'Sell'}
OrderTypeMap = {OrderType.Limit.value:'Limit',OrderType.Market.value:'Market'}
logger = log.setup_custom_logger('root')

DefaultUnAuthSubTables=["orderBookL2"]
# DefaultUnAuthSubTables=["orderBookL2","quote"]
DefaultAuthSubTables=["order", "position"]

class BitMexMon(object):

    def __init__(self,symbol,AuthSubTables=DefaultAuthSubTables,UnAuthSubTables=DefaultUnAuthSubTables,RestOnly=False):
        """ Init bitmex api obj """
        # str(settings.get('bitmex','api_url'))
        self.symbol = symbol
        self.bitmex = bitmex.BitMEX(
            base_url=settings.get('bitmex','api_url'), symbol=self.symbol,
            apiKey=settings.get('bitmex','api_key'), apiSecret=settings.get('bitmex','api_secert'),
            orderIDPrefix=settings.get('bitmex','orde_id_prefix'), postOnly=settings.getboolean('bitmex','post_only'),
            timeout=settings.getint('bitmex','timeout'),AuthSubTables=AuthSubTables,UnAuthSubTables=UnAuthSubTables,
            RestOnly=RestOnly
        )
    
    def prepare_order(self,price,side,orderQty,ordType):
        """
        prepare order , may add some check
        """
        #if price > 0 and (
        # (orderQty >0 and side=='Buy') or (orderQty <0 and side=='Sell')
        # ) and (ordType=='Limit' or ordType=='Market')
        if ordType=='Limit':
            return {
                    "ordType": ordType,
                    "orderQty": orderQty,
                    "price": price,
                    "side": side
            }
        elif ordType=='Market':
            return {
                    "ordType": ordType,
                    "orderQty": orderQty,
                    "side": side
            }
        else:
            raise ValueError("[prepare_order] ordType error!!!")

    def open_limit_order(self,symbol, side, qty, price):
        self.open_orders([self.prepare_order(price,OrderSideMap[side.value],qty,OrderTypeMap[OrderType.Limit.value])])

    def open_market_order(self,symbol, side, qty):
        self.open_orders([self.prepare_order(None,OrderSideMap[side.value],qty,OrderTypeMap[OrderType.Limit.value])])
    
    def converge_orders(self, symbol,buy_orders, sell_orders):
        """Converge the orders we currently have in the book with what we want to be in the book.
           This involves amending any open orders and creating new ones if any have filled completely.
           We start from the closest orders outward."""

        tickLog = 1
        to_amend = []
        to_create = []
        to_cancel = []
        buys_matched = 0
        sells_matched = 0
        existing_orders = self.bitmex.http_open_orders()

        # Check all existing orders and match them up with what we want to place.
        # If there's an open one, we might be able to amend it to fit what we want.
        for order in existing_orders:
            try:
                if order['side'] == 'Buy':
                    desired_order = buy_orders[buys_matched]
                    buys_matched += 1
                else:
                    desired_order = sell_orders[sells_matched]
                    sells_matched += 1

                # Found an existing order. Do we need to amend it?
                if desired_order['orderQty'] != order['leavesQty'] or desired_order['price'] != order['price'] :
                    # If price has changed, and the change is more than our RELIST_INTERVAL, amend.
                    to_amend.append({'orderID': order['orderID'], 'orderQty': order['cumQty'] + desired_order['orderQty'],
                                     'price': desired_order['price'], 'side': order['side']})
            except IndexError:
                # Will throw if there isn't a desired order to match. In that case, cancel it.
                to_cancel.append(order)

        while buys_matched < len(buy_orders):
            to_create.append(buy_orders[buys_matched])
            buys_matched += 1

        while sells_matched < len(sell_orders):
            to_create.append(sell_orders[sells_matched])
            sells_matched += 1

        if len(to_amend) > 0:
            for amended_order in reversed(to_amend):
                reference_order = [o for o in existing_orders if o['orderID'] == amended_order['orderID']][0]
                logger.info("Amending %4s: %d @ %.*f to %d @ %.*f (%+.*f)" % (
                    amended_order['side'],
                    reference_order['leavesQty'], tickLog, reference_order['price'],
                    (amended_order['orderQty'] - reference_order['cumQty']), tickLog, amended_order['price'],
                    tickLog, (amended_order['price'] - reference_order['price'])
                ))
            # This can fail if an order has closed in the time we were processing.
            # The API will send us `invalid ordStatus`, which means that the order's status (Filled/Canceled)
            # made it not amendable.
            # If that happens, we need to catch it and re-tick.
            try:
                self.bitmex.amend_bulk_orders(to_amend)
            except requests.exceptions.HTTPError as e:
                errorObj = e.response.json()
                if errorObj['error']['message'] == 'Invalid ordStatus':
                    logger.warn("Amending failed. Waiting for order data to converge and retrying.")
                    sleep(0.5)
                    return self.converge_orders(symbol,[], [])
                else:
                    logger.error("Unknown error on amend: %s. Exiting" % errorObj)
                    sys.exit(1)

        if len(to_create) > 0:
            logger.info("Creating %d orders:" % (len(to_create)))
            for order in reversed(to_create):
                logger.info("%4s %d @ %.*f" % (order['side'], order['orderQty'], tickLog, order['price']))
            self.bitmex.create_bulk_orders(to_create)

        # Could happen if we exceed a delta limit
        if len(to_cancel) > 0:
            logger.info("Canceling %d orders:" % (len(to_cancel)))
            for order in reversed(to_cancel):
                logger.info("%4s %d @ %.*f" % (order['side'], order['leavesQty'], tickLog, order['price']))
            self.bitmex.cancel([order['orderID'] for order in to_cancel])

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
    
    def set_leverage(self,symbol,leverage):
        """
        set a symbol's leverage
        symbol: 'XBTUSD'
        leverage: 100,50,25,10,5,3,1
        """
        self.bitmex.isolate_margin(symbol,leverage)

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


    