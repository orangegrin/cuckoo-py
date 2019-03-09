

import time
import sys
import traceback
import redis
import pprint
import json
from db.redis_lib import RedisLib
from exchange.bitmex.bitmex_mon_api import BitMexMon 
from exchange import enums

redis_conn = redis.Redis(host='localhost', port=6379)
rsLib = RedisLib()
exchange='bitmex'
symbol='XBTUSD'
symbol_ch_dict={"bitmex":{"XBTUSD":"XBTUSD"}}
data_cache={}

DefaultUnAuthSubTables=["orderBookL2","quote"]
# DefaultUnAuthSubTables=["orderBookL2"]
DefaultAuthSubTables=["order", "position"]

def orderBookL2_data_format_func(data):
    print("In orderbookL2 data_format_func handle!!")
    return data

def orderBookL2_callback(data):
    print("In orderbookL2 handle!!")
    #[[price,qty]...]
    bids=[]
    asks=[]
    for iorder in data:
        if iorder['side']=='Sell':
            bids.append([iorder['price'],iorder['size']])
        elif iorder['side']=='Buy':
            asks.append([iorder['price'],iorder['size']])
    
    tar_symbol = symbol_ch_dict[exchange][symbol]
    channel = rsLib.set_channel_name("OrderBookChange."+exchange+"."+tar_symbol)
    bids = rsLib.resample_orderbooks(bids,0.5,False)
    asks = rsLib.resample_orderbooks(asks,0.5,True)
    updateUtc = int(time.time()*1000)
    pub_data = {
        "exchange": exchange,
        "sequenceId":  str(updateUtc),
        "marketSymbol": tar_symbol,
        "lastUpdatedUtc": updateUtc,
        "asks": asks,
        "bids": bids
    }
    redis_pub(channel,pub_data)
    # pprint.pprint(pub_data)

def order_callback(data):
    print("In order handle!!")
    #[[price,qty]...]
    
    tar_symbol = symbol_ch_dict[exchange][symbol]
    channel = rsLib.set_channel_name("OrderChange."+exchange+"."+tar_symbol)
    
    pub_data=[]
    for idata in data:
        pub_data.append({
            "exchange": exchange,
            "orderId":idata['orderID'],
            "marketSymbol":tar_symbol,
            "qty":idata.get('leavesQty',0),
            "price":idata.get('price',0),
            "side":enums.Side.Buy.value if idata['side']=="Buy" else enums.Side.Sell.value,
            "orderType": enums.OrderType.Limit.value if idata['ordType'] == 'Limit' else enums.OrderType.Market.value,
            "extraParameters":""
        })
    data_cache['order']=pub_data
    redis_pub(channel,pub_data)
    # pprint.pprint(pub_data)

def position_callback(data):
    print("In position handle!!")
    tar_symbol = symbol_ch_dict[exchange][symbol]
    print(data[0])
    if data[0]:
        pub_data ={
                    "exchange":exchange,
                    "marketSymbol":tar_symbol,
                    "qty":data[0]['currentQty'],
                    "total":0,
                    "profitLoss":data[0]['unrealisedPnl'],
                    "lendingFees":0,
                    "basePrice":data[0]['avgEntryPrice'],
                    "liquidationPrice":data[0]['liquidationPrice'],
                }
        if data_cache.get('position',{})!=pub_data:
            data_cache['position']=pub_data
            channel = rsLib.set_channel_name("PositionChange."+exchange+"."+tar_symbol)
            try:
                redis_pub(channel,pub_data)
                pprint.pprint(data_cache)
            except Exception as e:
                pprint.pprint(traceback.format_exc())
                pprint.pprint(data)
            

def quote_callback(data):
    print("In quote handle!!")
    current_quote={
        'askPrice': data[-1].get('askPrice',0),
        'askSize': data[-1].get('askSize',0),
        'bidPrice': data[-1].get('bidPrice',0),
        'bidSize': data[-1].get('bidSize',0),
        'symbol': symbol
    }
    # cache_quote=data_cache.get('quote',{})
    data_cache['quote']=current_quote
    # if current_quote.get('askPrice',0)!=cache_quote.get('askPrice',0) or current_quote.get('bidPrice',0)!=cache_quote.get('bidPrice',0):
    #     pass
    pprint.pprint(data[-1])

def redis_pub(channel,pub_data):
    #return True
    # pprint.pprint(pub_data)
    redis_conn.publish(channel, json.dumps(pub_data))



def run() -> None:
    bitmex_mon = BitMexMon(symbol,UnAuthSubTables=DefaultUnAuthSubTables,AuthSubTables=DefaultAuthSubTables)
    bitmex_mon.cancel_orders([],cancel_all=True)
    position_callback([bitmex_mon.get_position()])
    
    pprint.pprint(data_cache)
    # return None
    # Try/except just keeps ctrl-c from printing an ugly stacktrace
    # bitmex_mon.subscribe_data_callback('orderBookL2',orderBookL2_callback,orderBookL2_data_format_func)
    bitmex_mon.subscribe_data_callback('order',order_callback,lambda x:x)
    bitmex_mon.subscribe_data_callback('quote',quote_callback,lambda x:x)
    bitmex_mon.subscribe_data_callback('position',position_callback,lambda x:x)
    MAX_POSITION=100
    try:
        while True:
            if not data_cache.get('quote',None):
                time.sleep(1)
                continue
            orders=[]
            current_position_amount = data_cache['position']['Amount']
            if current_position_amount==0: 
                orders.append(bitmex_mon.prepare_order(data_cache['quote']['askPrice'],'Sell',MAX_POSITION,'Limit'))
                orders.append(bitmex_mon.prepare_order(data_cache['quote']['bidPrice'],'Buy',MAX_POSITION,'Limit'))
            elif current_position_amount>0:
                if current_position_amount<MAX_POSITION:
                    orders.append(bitmex_mon.prepare_order(data_cache['quote']['bidPrice'],'Buy',MAX_POSITION-current_position_amount,'Limit'))
                orders.append(bitmex_mon.prepare_order(data_cache['quote']['askPrice'],'Sell',MAX_POSITION,'Limit'))
            elif current_position_amount<0:
                if current_position_amount>(MAX_POSITION*-1):
                    orders.append(bitmex_mon.prepare_order(data_cache['quote']['askPrice'],'Sell',MAX_POSITION+current_position_amount,'Limit'))
                orders.append(bitmex_mon.prepare_order(data_cache['quote']['bidPrice'],'Buy',MAX_POSITION,'Limit'))

            tar_orders = []
            amd_orders=[]
            print("$$$$$$$$$$$$$$$$$$")
            print(orders)
            print(data_cache.get('order',[]))
            print("$$$$$$$$$$$$$$$$$$")
            if len(data_cache.get('order',[]))>0:
                for o in orders:
                    order_cate = 2
                    for hold_order in data_cache['order']:
                        if o['price']==hold_order['Price'] and o['orderQty']==hold_order['Amount'] and o['side'] == "Buy" if hold_order['IsBuy'] else "Sell":
                            order_cate=1
                            break
                        elif o['side'] == "Buy" if hold_order['IsBuy'] else "Sell":
                            o['orderID']= hold_order['orderId']
                            order_cate=0
                            break

                    if order_cate ==0:
                        amd_orders.append(o)
                    elif order_cate==2:
                        tar_orders.append(o)
            else:
                tar_orders=orders
            
            print("!!!!!!!!!!!!!!!!!!")
            print(tar_orders)
            print("##################")
            print("!!!!!!!!!!!!!!!!!!")
            print(amd_orders)
            print("##################")
            if tar_orders:
                bitmex_mon.open_orders(tar_orders)
            if amd_orders:
                bitmex_mon.amend_orders(amd_orders)
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        sys.exit()

def main() -> None:
    bitmex_mon = BitMexMon(symbol,UnAuthSubTables=DefaultUnAuthSubTables,AuthSubTables=DefaultAuthSubTables)
    bitmex_mon.cancel_orders([],cancel_all=True)
    # position_callback([bitmex_mon.get_position()])
    
    pprint.pprint(data_cache)
    # return None
    # Try/except just keeps ctrl-c from printing an ugly stacktrace
    bitmex_mon.subscribe_data_callback('orderBookL2',orderBookL2_callback,orderBookL2_data_format_func)
    bitmex_mon.subscribe_data_callback('order',order_callback,lambda x:x)
    # bitmex_mon.subscribe_data_callback('quote',quote_callback,lambda x:x)
    bitmex_mon.subscribe_data_callback('position',position_callback,lambda x:x)
    try:
        while True:
            time.sleep(3)
    except (KeyboardInterrupt, SystemExit):
        sys.exit()

#if __name__ == "__main__":

#    # run()
#    main()

    