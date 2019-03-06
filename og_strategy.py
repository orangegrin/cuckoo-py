
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

def order_callback(data):
    print("In order handle!!")
    #[[price,qty]...]
    
    tar_symbol = symbol_ch_dict[exchange][symbol]
    channel = rsLib.setChannelName("OrderChange."+exchange+"."+tar_symbol)
    
    pub_data=[]
    for idata in data:
        pub_data.append( {
            "Exchange": exchange,
            "MarketSymbol":tar_symbol,
            "Amount":idata.get('leavesQty',None),
            "Price":idata.get('price',None),
            "StopPrice":None,
            "IsBuy":None,
            "IsMargin":None,
            "ShouldRoundAmount":None,
            "OrderType":idata.get('ordType',None),
            "ExtraParameters":None
        })
    redis_pub(channel,pub_data)
    pprint.pprint(pub_data)

def position_callback(data):
    print("In position handle!!")
    # pprint.pprint(data)
    #[[price,qty]...]
    current_position={
        'avgCostPrice': data[0].get('avgCostPrice',None), 
        'avgEntryPrice': data[0].get('avgEntryPrice',None), 
        'currentQty': data[0].get('currentQty',None), 
        'symbol': symbol
    }
    if data_cache.get('position',{})!=current_position:
        data_cache['position']=current_position
        tar_symbol = symbol_ch_dict[exchange][symbol]
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
            # {'avgCostPrice': 0, 'avgEntryPrice': 0, 'currentQty': 0, 'symbol': symbol}
            redis_pub(channel,pub_data)
            pprint.pprint(data_cache)
        except Exception as e:
            pprint.pprint(traceback.format_exc())
            pprint.pprint(data)

def redis_pub(channel,pub_data):
    return True
    pprint.pprint(pub_data)
    redis_conn.publish(channel, json.dumps(pub_data))



def run() -> None:
    bitmex_mon = BitMexMon(symbol)
    bitmex_mon.cancel_orders([],cancel_all=True)
    position_callback([bitmex_mon.get_position()])
    
    pprint.pprint(data_cache)
    # return None
    # Try/except just keeps ctrl-c from printing an ugly stacktrace
    # bitmex_mon.subscribe_data_callback('orderBookL2',orderBookL2_callback,orderBookL2_data_format_func)
    bitmex_mon.subscribe_data_callback('order',order_callback,lambda x:x)
    bitmex_mon.subscribe_data_callback('position',position_callback,lambda x:x)

    try:
        while True:
            time.sleep(3)
    except (KeyboardInterrupt, SystemExit):
        sys.exit()

if __name__ == "__main__":

    run()

    