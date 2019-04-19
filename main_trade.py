# -*- coding: utf-8 -*-

import asyncio
import os
import datetime 
import sys
import pprint
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ccxt.async_support as ccxt  # noqa: E402
from sqlalchemy.engine.url import URL
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.model import Base, SessionContextManager,IQuoteOrder
import traceback,time
import json
from market_maker.bitmex_mon_api import BitMexMon 
# from binanceApi.BinanceDataApi import BinanceDataAPI
from binance.websockets import BinanceSocketManager
from binance.depthcache import DepthCacheManager
from binance.client import Client
from datetime import timezone,timedelta
from multiprocessing import Process,Queue


exchange='bitmex'
symbol=['ETHM19','LTCM19','EOSM19','XRPM19','TRXM19','XBTUSD']
symbol_ch_dict={"bitmex":{"XBTUSD":"BTCUSD"}}
data_cache={}
sanity_data_cach={}
Current_ts = "000"
Last_ts = "000"
Last_last_ts = "000"
# DefaultUnAuthSubTables=["quote"]
DefaultUnAuthSubTables=["orderBook10"]
DefaultAuthSubTables=["order", "position"]

q,pingq,trade_q = Queue(), Queue(), Queue()

pingdict = {}

BINANCE_GSYMBOL={
    "ETHBTC":"ETH/BTC",
    "EOSBTC":"EOS/BTC",
    "LTCBTC":"LTC/BTC",
    "XRPBTC":"XRP/BTC"
}
GSYMBOL_BINANCE={
     "ETH/BTC":"ETHBTC",
    "EOS/BTC":"EOSBTC",
    "LTC/BTC":"LTCBTC",
    "XRP/BTC":"XRPBTC"
}

async def fetch_order_book(exchange_name,exchange_obj,symbols):

    # exchange = ccxt.okex({
    #     'enableRateLimit': True,  # required accoding to the Manual
    # })
    tzutc_0 = timezone(timedelta(hours=0))
    try:
        orderbooks = []
        for symbol in symbols:
            orderbook = await exchange_obj.fetch_order_book(symbol)
            orderbook['bids']=orderbook['bids'][0][0]
            orderbook['asks']=orderbook['asks'][0][0]
            orderbook['timestamp'] = datetime.datetime.now().astimezone(tzutc_0).strftime("%Y-%m-%dT%H:%M:%S")
            orderbook['exchange'] = exchange_name
            orderbook['symbol'] = symbol
            orderbook.pop('datetime')
            orderbook.pop('nonce')
            orderbooks.append(orderbook)
        #await exchange_obj.close()
        return orderbooks
    except ccxt.BaseError as e:
        print(type(e).__name__, str(e), str(e.args))
        raise e



      
def orderBookL2_data_format_func(data):

    sanity_data=[]
    
    for sdata in data:
        ts = sdata['timestamp'].split(".")[0]
        sanity_data.append(
            {
                'asks':sdata['asks'][0][0],
                'bids':sdata['bids'][0][0],
                'symbol':sdata['symbol'],
                'exchange':'bitmex',
                'timestamp':ts
            }
        )
        
    return sanity_data

def orderBookL2_callback(data):
  
    global q,pingq
   
    for sd in data:
        # print(sd)
        q.put(sd,False)
    pingq.put( ("bitmex",int(time.time())),False )
    return None


def save_binance_orderbook(dc):
    
    global q,pingq
    
    tzutc_0 = timezone(timedelta(hours=0))

    sd={
            'asks':dc.get_asks()[0][0],
            'bids':dc.get_bids()[0][0],
            'symbol':BINANCE_GSYMBOL[dc.symbol],
            'exchange':'binance',
            'timestamp':datetime.datetime.fromtimestamp(dc.update_time/1000).astimezone(tzutc_0).strftime("%Y-%m-%dT%H:%M:%S")
    }
   
    q.put(sd)
    pingq.put(("binance",int(time.time())))

def bitmexWsFun():
    global DefaultUnAuthSubTables,DefaultAuthSubTables

    bitmex_mon = BitMexMon(symbol,UnAuthSubTables=DefaultUnAuthSubTables,AuthSubTables=DefaultAuthSubTables)
    bitmex_mon.subscribe_data_callback('orderBook10',orderBookL2_callback,orderBookL2_data_format_func)
    while True:
        time.sleep(10)

def binanceWsFun():

    global GSYMBOL_BINANCE

    client = Client("api_key", "api_secret")
    bm = BinanceSocketManager(client)
    for isymbol in ['ETH/BTC','LTC/BTC','EOS/BTC','XRP/BTC']:
        dcm2 = DepthCacheManager(client, GSYMBOL_BINANCE[isymbol], callback=save_binance_orderbook, bm=bm)
    while True:
        time.sleep(10)

def save_to_db(q,trade_q):
    
    dburl = URL(**{
    "drivername": "postgresql+psycopg2",
    "host": "localhost",
    "port": 5432,
    "username": "ray",
    "password": "yqll",
    "database": "dashpoint"
    })
    engine = create_engine(dburl, echo=False)
    Session = sessionmaker(bind=engine, class_=SessionContextManager)
    Base.metadata.create_all(bind=engine)
    
    cache_list = [None]*3
    last_timestamp = None
    while True:
        sd = q.get()
        if sd['symbol']+"@"+sd['exchange'] == "XBTUSD@bitmex":
            
            if last_timestamp and  sd['timestamp']>= last_timestamp:
                
                if sd['timestamp']> last_timestamp:
                    cache_list.append(sd['asks'])
                    for i in range(len(cache_list)-1):
                        cache_list[i],cache_list[i+1] = cache_list[i+1],cache_list[i]
                    cache_list=cache_list[:-1]
                    with open("trade_q.log","a") as fp:
                        fp.write("{}\n".format(json.dumps(sd)))
                    last_timestamp = sd['timestamp']
                elif sd['timestamp']== last_timestamp:
                    cache_list.pop()
                    cache_list.append(sd['asks'])
                
                if all(cache_list):
                    put_msg = None
                    if all([ cache_list[i]<cache_list[i+1] for i in range(len(cache_list)-1)]):
                        put_msg = (sd['timestamp'],"buy",sd['asks'])
                    elif all([ cache_list[i]>cache_list[i+1] for i in range(len(cache_list)-1)]):
                        put_msg = (sd['timestamp'],"sell",sd['asks'])
                    if put_msg:    
                        trade_q.put(put_msg)
                        with open("trade_q.log","a") as fp:
                            fp.write("{}---{}---{}\n".format(*put_msg))
            elif not last_timestamp:
                last_timestamp = sd['timestamp']
                cache_list.pop()
                cache_list.append(sd['asks'])

            continue
    
        sd['timesymbol'] = "_".join([sd['timestamp'],sd['symbol'],sd['exchange']])
        with Session() as session:
            ex_id =  session.query(IQuoteOrder.id).filter_by(timesymbol=sd['timesymbol']).first()
            if ex_id:
                session.query(IQuoteOrder).filter(IQuoteOrder.id==ex_id[0]).update({"bids":sd['bids'],"asks":sd['asks']})
            else:
                session.add(IQuoteOrder(**sd))
                print(sd)
    
def start_back_process(flag):
    global q,trade_q
    if flag=="bitmex":
        p1 = Process(target=bitmexWsFun, args=())
        p1.start()
        return p1
    elif flag=="binance":
        p2 = Process(target=binanceWsFun, args=())
        p2.start()
        return p2
    elif flag=="savedb":
        p3 = Process(target=save_to_db, args=(q,trade_q))
        p3.start()
        return p3
        


def main():
    # bitmex_mon = BitMexMon(symbol,UnAuthSubTables=DefaultUnAuthSubTables,AuthSubTables=DefaultAuthSubTables)
    # bitmex_mon.subscribe_data_callback('orderBook10',orderBookL2_callback,orderBookL2_data_format_func)
    
    global q,pingq,pingdict
    
    p3 = start_back_process("savedb")
    for flag in ["bitmex","binance"]:
        pingdict[flag]={"ph":None,"lastping":int(time.time())}
        pingdict[flag]["ph"]=start_back_process(flag)

    # client = Client("api_key", "api_secret")
    # bm = BinanceSocketManager(client)
    # for isymbol in ['ETH/BTC','LTC/BTC','EOS/BTC','XRP/BTC']:
    #     dcm2 = DepthCacheManager(client, GSYMBOL_BINANCE[isymbol], callback=save_binance_orderbook, bm=bm)
    
    while True:
        try:
            exchangeSymbols = {
                # "bitmex":[ccxt.bitmex({}),['ETHM19','LTCM19','EOS19','XRPM19']],
                "gateio":[ccxt.gateio({}),['ETH/BTC','LTC/BTC','EOS/BTC','XRP/BTC']],
                # "binance":[ccxt.binance({'enableRateLimit': True}),['ETH/BTC','LTC/BTC','EOS/BTC','XRP/BTC']],
                "okex":[ccxt.okex(),['ETH/BTC','LTC/BTC','EOS/BTC','XRP/BTC']]
            }
            try:
                loop = asyncio.get_event_loop()
                while True:
                    orderbooks = loop.run_until_complete(asyncio.gather(*[fetch_order_book(en,es[0],es[1]) for en,es in exchangeSymbols.items()]))
                    
                    for r in orderbooks:
                        for orderbook in r:
                            q.put(orderbook)

                    while not pingq.empty():
                        pinginfo=pingq.get(block=False)
                        if pinginfo:
                            if pinginfo[1] - pingdict[pinginfo[0]]["lastping"] >90:
                                print("{} : long time no data,restart".format(pinginfo[0]))
                                try:
                                    pingdict[pinginfo[0]]["ph"].terminate()
                                except Exception :
                                    pass
                                finally:
                                    pingdict[pinginfo[0]]["ph"] = start_back_process(pinginfo[0])
                            else:
                                print("{} : update ping time {}".format(pinginfo[0],pinginfo[1]))
                                pingdict[pinginfo[0]]["lastping"] = pinginfo[1]
                    time.sleep(1)
            except Exception:
                print(traceback.format_exc())
                import sys
                sys.exit() 
                time.sleep(30)
            finally:
                for en,es in exchangeSymbols.items():
                    loop.run_until_complete(asyncio.gather(*[es[0].close() for en,es in exchangeSymbols.items()]))
                loop.close()
                for flag in pingdict.keys():
                    pingdict[flag]["ph"].terminate()
                p3.terminate()
                os._exit(1)
        except Exception:
            
            print("------------------------------------------------------------------")
            print(traceback.format_exc())
            print("------------------------------------------------------------------")
            time.sleep(30)

if __name__ == "__main__":

    main()

    
