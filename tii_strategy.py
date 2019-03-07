
import time
import sys
import traceback
import redis
import pprint
import json
from RedisLib import RedisLib
from market_maker.bitmex_mon_api import BitMexMon 

redis_conn = redis.Redis(host='localhost', port=6379)
rsLib = RedisLib()
exchange='bitmex'
symbol='XBTUSD'
symbol_ch_dict={"bitmex":{"XBTUSD":"BTCUSD"}}
data_cache={}

DefaultUnAuthSubTables=["quote"]
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
    channel = rsLib.setChannelName("OrderBookChange."+exchange+"."+tar_symbol)
    bids = rsLib.ResampleOrderbooks(bids,0.5,False)
    asks = rsLib.ResampleOrderbooks(asks,0.5,True)
    updateUtc = int(time.time()*1000)
    pub_data = {
        "Exchange": exchange,
        "SequenceId":  str(updateUtc),
        "MarketSymbol": tar_symbol,
        "LastUpdatedUtc": updateUtc,
        "Asks": asks,
        "Bids": bids
    }
    redis_pub(channel,pub_data)
    pprint.pprint(pub_data)

def order_callback(data):
    print("In order handle!!")
    #[[price,qty]...]
    
    tar_symbol = symbol_ch_dict[exchange][symbol]
    channel = rsLib.setChannelName("OrderChange."+exchange+"."+tar_symbol)
    
    pub_data=[]
    for idata in data:
        pub_data.append( {
            "Exchange": exchange,
            "OrderId":idata['orderID'],
            "MarketSymbol":tar_symbol,
            "Amount":idata.get('leavesQty',0),
            "Price":idata.get('price',None),
            "StopPrice":None,
            "side":idata.get('side',None),
            "IsMargin":None,
            "ShouldRoundAmount":None,
            "OrderType":idata.get('ordType',None),
            "ExtraParameters":None
        })
    data_cache['order']=pub_data
    redis_pub(channel,pub_data)
    pprint.pprint(pub_data)

def position_callback(data):
    print("In position handle!!")
    tar_symbol = symbol_ch_dict[exchange][symbol]
    
    current_position={
        "Exchange":exchange,
        "MarketSymbol":tar_symbol,
        "Amount":data[0].get('currentQty',None),
        "Total":0,
        "ProfitLoss":data[0].get('unrealisedPnl',None),
        "LendingFees":0,
        "Type":0,
        "BasePrice":data[0].get('avgEntryPrice',None),
        "LiquidationPrice":data[0].get('liquidationPrice',None),
        "Leverage":data[0].get('leverage',None)
    }
    if data_cache.get('position',{})!=current_position:
        data_cache['position']=current_position
        channel = rsLib.setChannelName("PositionChange."+exchange+"."+tar_symbol)
        try:
            pub_data ={
                "Exchange":exchange,
                "MarketSymbol":tar_symbol,
                "Amount":data[0].get('currentQty',None),
                "Total":0,
                "ProfitLoss":data[0].get('unrealisedPnl',None),
                "LendingFees":0,
                "Type":0,
                "BasePrice":data[0].get('avgEntryPrice',None),
                "LiquidationPrice":data[0].get('liquidationPrice',None),
                "Leverage":data[0].get('leverage',None)
            }
            
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
    return True
    pprint.pprint(pub_data)
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
            print("$$$$$$$$$$$$$$$$$$")
            if len(data_cache.get('order',[]))>0:
                for o in orders:
                    order_cate = 2
                    for hold_order in data_cache['order']:
                        if o['price']==hold_order['Price'] and o['orderQty']==hold_order['Amount'] and o['side'] == hold_order['side']:
                            order_cate=1
                            break
                        elif o['side'] == hold_order['side']:
                            o['orderID']= hold_order['OrderId']
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

if __name__ == "__main__":

    run()

    