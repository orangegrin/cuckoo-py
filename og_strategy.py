
import time
import sys
import redis
import pprint
import json
from RedisLib import RedisLib
from market_maker.bitmex_mon_api import BitMexMon 

redis_conn = redis.Redis(host='localhost', port=6379)
rsLib = RedisLib()
exchange='bitmex'
symbol='XBTUSD'

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
    tar_data= {
        'symbol':symbol,
        'bids':bids,
        'asks':asks
    }
    channel = rsLib.setChannelName("OrderBookChange."+exchange+"."+symbol)
    bids = rsLib.ResampleOrderbooks(bids,0.5,False)
    asks = rsLib.ResampleOrderbooks(asks,0.5,True)
    
    updateUtc = int(time.time()*1000)
    pubData = {
        "Exchange": exchange,
        "SequenceId":  str(updateUtc),
        "MarketSymbol": symbol,
        "LastUpdatedUtc": updateUtc,
        "Asks": asks,
        "Bids": bids
    }
    pubdata_json = json.dumps(pubData)
    pprint.pprint(pubData)
    res = redis_conn.publish(channel, pubdata_json)


def run() -> None:
    bitmex_mon = BitMexMon('XBTUSD')

    # Try/except just keeps ctrl-c from printing an ugly stacktrace
    bitmex_mon.subscribe_data_callback('orderBookL2',orderBookL2_callback,orderBookL2_data_format_func)
    try:
        while True:
            time.sleep(3)
    except (KeyboardInterrupt, SystemExit):
        sys.exit()

if __name__ == "__main__":

    run()