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
from db.model import Base, SessionContextManager,IQuoteOrder,TradeHistory
import traceback,time
import json
from market_maker.bitmex_mon_api import BitMexMon 
from binance.websockets import BinanceSocketManager
from binance.depthcache import DepthCacheManager
from binance.client import Client
from datetime import timezone,timedelta
from queue import Queue
# from multiprocessing import Process,Queue

import fcoin
from fcoin.WebsocketClient import WebsocketClient as FcoinWebsocketClient
from bitfinex.websocket import WebsocketClient as BitfinexWebsocketClient
from kraken.websocket import WebsocketClient as KrakenWebsocketClient

exchange='bitmex'
symbol=['ETHM19','LTCM19','EOSM19','XRPM19','TRXM19']
symbol_ch_dict={"bitmex":{"XBTUSD":"BTCUSD"}}
data_cache={}
sanity_data_cach={}
Current_ts = "000"
Last_ts = "000"
Last_last_ts = "000"
# DefaultUnAuthSubTables=["quote"]
DefaultUnAuthSubTables=["orderBook10"]
DefaultAuthSubTables=[]
# DefaultAuthSubTables=["order", "position"]

DATA_QUEUE,PING_QUEUE = Queue(), Queue()

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

KRAKEN_GSYMBOL={
    "ETH/XBT":"ETH/BTC",
    "EOS/XBT":"EOS/BTC",
    "LTC/XBT":"LTC/BTC",
    "XRP/XBT":"XRP/BTC"
}
FCOIN_TOPICS = ["depth.L20.ethbtc", "depth.L20.eosbtc", "depth.L20.xrpbtc", "depth.L20.ltcbtc"]
BITFINEX_PAIR = ["ETHBTC","EOSBTC","LTCBTC","XRPBTC"]
KRAKEN_PAIR = ["ETH/XBT","EOS/XBT","LTC/XBT","XRP/XBT"]

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
  
    global DATA_QUEUE,PING_QUEUE
   
    for sd in data:
        # print(sd)
        DATA_QUEUE.put(sd,False)
    PING_QUEUE.put( ("bitmex",int(time.time())),False )
    return None


def save_binance_orderbook(dc):
    
    global DATA_QUEUE,PING_QUEUE
    
    tzutc_0 = timezone(timedelta(hours=0))

    sd={
            'asks':dc.get_asks()[0][0],
            'bids':dc.get_bids()[0][0],
            'symbol':BINANCE_GSYMBOL[dc.symbol],
            'exchange':'binance',
            'timestamp':datetime.datetime.fromtimestamp(dc.update_time/1000).astimezone(tzutc_0).strftime("%Y-%m-%dT%H:%M:%S")
    }
   
    DATA_QUEUE.put(sd,False)
    PING_QUEUE.put(("binance",int(time.time())),False)

def save_fcoin_orderbook(dc):
    
    # {
    # "type": "depth.L20.ethbtc",
    # "ts": 1523619211000,
    # "seq": 120,
    # "bids": [0.000100000, 1.000000000, 0.000010000, 1.000000000],
    # "asks": [1.000000000, 1.000000000]
    # }

    global DATA_QUEUE,PING_QUEUE
    
    tzutc_0 = timezone(timedelta(hours=0))
    
    if dc["type"] in FCOIN_TOPICS:
        sd={
                'asks':dc['asks'][0],
                'bids':dc['bids'][0],
                'symbol':BINANCE_GSYMBOL[dc['type'].split('.')[-1].upper()],
                'exchange':'fcoin',
                'timestamp':datetime.datetime.fromtimestamp(dc["ts"]/1000).astimezone(tzutc_0).strftime("%Y-%m-%dT%H:%M:%S")
        }
    
        DATA_QUEUE.put(sd,False)
        PING_QUEUE.put(("fcoin",int(time.time())),False)
    else:
        pprint.pprint(dc)

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
        try:
            _dcm2 = DepthCacheManager(client, GSYMBOL_BINANCE[isymbol], callback=save_binance_orderbook, bm=bm)
        except :
            print(traceback.format_exc())
            time.sleep(10)
    while True:
        time.sleep(10)

def fcoinWsFun():
    
    ws = FcoinWebsocketClient()
    ws.handle_fun = save_fcoin_orderbook
    ws.sub(FCOIN_TOPICS)


def bitfinexcallback(data_body):

    global DATA_QUEUE,PING_QUEUE
    tzutc_0 = timezone(timedelta(hours=0))

    for key in data_body:
        if data_body[key]['asks'] and data_body[key]['bids']:
            ask1 = sorted(data_body[key]['asks'].keys())[0]
            bid1 = sorted(data_body[key]['bids'].keys())[-1]

            sd = {}
            if data_body[key]['pair'] in BITFINEX_PAIR:
                sd={
                        'asks':ask1,
                        'bids':bid1,
                        'symbol':BINANCE_GSYMBOL[data_body[key]['pair'].upper()],
                        'exchange':'bitfinex',
                        'timestamp':datetime.datetime.fromtimestamp(time.time()).astimezone(tzutc_0).strftime("%Y-%m-%dT%H:%M:%S")
                }
                DATA_QUEUE.put(sd,False)
                PING_QUEUE.put(("bitfinex",int(time.time())),False)
            else:
                pprint.pprint(data_body)

def bitfinexWsFun():
    
    ws = BitfinexWebsocketClient()
    ws.handle_fun = bitfinexcallback
    ws.sub([['book','tEOSBTC'],['book','tETHBTC']])

def krakencallback(data_body):
    global DATA_QUEUE,PING_QUEUE
    tzutc_0 = timezone(timedelta(hours=0))

    for key in data_body:
        if data_body[key]['asks'] and data_body[key]['bids']:
            ask1 = sorted(data_body[key]['asks'].keys())[0]
            bid1 = sorted(data_body[key]['bids'].keys())[-1]

            sd = {}
            if data_body[key]['pair'] in KRAKEN_PAIR:
                sd={
                        'asks':ask1,
                        'bids':bid1,
                        'symbol':KRAKEN_GSYMBOL[data_body[key]['pair'].upper()],
                        'exchange':'kraken',
                        'timestamp':datetime.datetime.fromtimestamp(time.time()).astimezone(tzutc_0).strftime("%Y-%m-%dT%H:%M:%S")
                }
                DATA_QUEUE.put(sd,False)
                PING_QUEUE.put(("kraken",int(time.time())),False)
            else:
                pprint.pprint(data_body)

def krakenWsFun(channel="book",symbol_pair=["ETH/XBT","EOS/XBT","LTC/XBT","XRP/XBT"]):
    
    ws = KrakenWebsocketClient()
    ws.handle_fun = krakencallback
    ws.sub(channel=channel,symbol_pair=symbol_pair)

def log_trade_history_from_bitmex(session):
    #
    # {'orderID': '1fe51f92-7a48-5c81-0e41-2921483ccaf2', 'clOrdID': '', 'clOrdLinkID': '', 'account': 63450, 'symbol': 'ETHM19', 'side': 'Buy', 'simpleOrderQty': None, 'orderQty': 5, 'price': 0.02883, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'XBT', 'settlCurrency': 'XBt', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': 'ParticipateDoNotInitiate', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'Filled', 'triggered': '', 'workingIndicator': False, 'ordRejReason': '', 'simpleLeavesQty': None, 'leavesQty': 0, 'simpleCumQty': None, 'cumQty': 5, 'avgPx': 0.02883, 'multiLegReportingType': 'SingleSecurity', 'text': 'Submission from www.bitmex.com', 'transactTime': '2019-05-09T02:42:00.904Z', 'timestamp': '2019-05-09T03:14:04.093Z'}
    
    try:
        bitmex_mon = BitMexMon(symbol,UnAuthSubTables=[],AuthSubTables=[],WebSocketOn=False)
        orders = bitmex_mon.bitmex.http_get_orders({},all_order=True)
        for od in orders:
            if od.get('ordStatus',None) == 'Filled':
                try:
                    tmp_od = {'symbol': od['symbol'], 'side': od['side'],'price': od['price'], 'orderid': od['orderID'], 'accountid': od['account'], 'orderqty': od['orderQty'], 'extratext': od['text'],'timestamp': datetime.datetime.strptime(od['timestamp'].split('.')[0],"%Y-%m-%dT%H:%M:%S"),'transactTime': datetime.datetime.strptime(od['transactTime'].split('.')[0],"%Y-%m-%dT%H:%M:%S")}
                    ex_id =  session.query(TradeHistory.id).filter_by(orderid=tmp_od['orderid']).first()
                    if ex_id:
                        continue
                    else:
                        print(tmp_od)
                        session.add(TradeHistory(**tmp_od))
                except Exception:
                    print(traceback.format_exc())
                    continue
    except Exception:
        print(traceback.format_exc())            

def save_to_db(q):

    try:
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
        
        log_trade_ts = None
        while True:
            sd = q.get()
            sd['timesymbol'] = "_".join([sd['timestamp'],sd['symbol'],sd['exchange']])
            with Session() as session:
                ex_id =  session.query(IQuoteOrder.id).filter_by(timesymbol=sd['timesymbol']).first()
                # print(ex_id)
                if ex_id:
                    session.query(IQuoteOrder).filter(IQuoteOrder.id==ex_id[0]).update({"bids":sd['bids'],"asks":sd['asks']})
                else:
                    session.add(IQuoteOrder(**sd))
                    print(sd)
            if log_trade_ts == None or (time.time() - log_trade_ts) > 60*60*12:
                  log_trade_ts  = time.time()
                  log_trade_history_from_bitmex(session)

    except Exception :
        print(traceback.format_exc())
        os._exit(1)
        sys.exit() 
    
    
def start_back_process(flag):
    global DATA_QUEUE
    from threading import Thread
    if flag=="bitmex":
        p1 = Thread(target=bitmexWsFun, args=())
        p1.start()
        return p1
    elif flag=="binance":
        p2 = Thread(target=binanceWsFun, args=())
        p2.start()
        return p2
    elif flag=="fcoin":
        p2 = Thread(target=fcoinWsFun, args=())
        p2.start()
        return p2
    elif flag=="bitfinex":
        p2 = Thread(target=bitfinexWsFun, args=())
        p2.start()
        return p2
    elif flag=="kraken":
        p2 = Thread(target=krakenWsFun, args=())
        p2.start()
        return p2
    elif flag=="savedb":
        p3 = Thread(target=save_to_db, args=(DATA_QUEUE,))
        p3.start()
        return p3
        


def main():
    
    global DATA_QUEUE,PING_QUEUE,pingdict
    
    start_back_process("savedb")
    for flag in ["kraken"]:#"bitfinex","bitmex","binance","fcoin"]:
        pingdict[flag]={"ph":None,"lastping":int(time.time())}
        pingdict[flag]["ph"]=start_back_process(flag)

    while True:
        try:
            exchangeSymbols = {
                # "bitmex":[ccxt.bitmex({}),['ETHM19','LTCM19','EOS19','XRPM19']],
                "gateio":[ccxt.gateio({}),['ETH/BTC','LTC/BTC','EOS/BTC','XRP/BTC']],
                # "binance":[ccxt.binance({'enableRateLimit': True}),['ETH/BTC','LTC/BTC','EOS/BTC','XRP/BTC']],
                "okex":[ccxt.okex(),['ETH/BTC','LTC/BTC','EOS/BTC','XRP/BTC']],
                # "fcoin":[ccxt.fcoin(),['ETH/BTC','LTC/BTC','EOS/BTC','XRP/BTC']]
            }
            try:
                loop =None
                loop = asyncio.get_event_loop()
                while True:
                   
                    orderbooks = loop.run_until_complete(asyncio.gather(*[fetch_order_book(en,es[0],es[1]) for en,es in exchangeSymbols.items()]))
                    
                    for r in orderbooks:
                        for orderbook in r:
                            DATA_QUEUE.put(orderbook,False)
                    
                    while not PING_QUEUE.empty():
                        pinginfo=PING_QUEUE.get(block=False)
                        #pinginfo----('bitmex',155284612231)
                        if pinginfo:
                            # print("{} : update ping time {}".format(pinginfo[0],pinginfo[1]))
                            pingdict[pinginfo[0]]["lastping"] = pinginfo[1]

                    for exchangename in pingdict.keys():
                        if (int(time.time()) - pingdict[exchangename]["lastping"]) >30:
                            print("{} : long time no data,restart script!!!".format(exchangename))
                            sys.exit()
                    
                    time.sleep(1)
            except Exception:
                print(traceback.format_exc())
                sys.exit() 
                # time.sleep(30)
            finally:
                if loop:
                    for _en,es in exchangeSymbols.items():
                        loop.run_until_complete(asyncio.gather(*[es[0].close() for en,es in exchangeSymbols.items()]))
                    loop.close()
                # for flag in pingdict.keys():
                #     pingdict[flag]["ph"].close()
                # p3.close()
                os._exit(1)
                sys.exit() 
        except Exception:
            
            print("------------------------------------------------------------------")
            print(traceback.format_exc())
            print("------------------------------------------------------------------")
            time.sleep(30)

if __name__ == "__main__":

    main()
    # bitmex_mon = BitMexMon(symbol,UnAuthSubTables=DefaultUnAuthSubTables,AuthSubTables=DefaultAuthSubTables,WebSocketOn=False)
    # filter_dict = {}
    # filled_orders = bitmex_mon.bitmex.http_get_orders(filter_dict,all_order=True)
    # tar_info = [{'symbol': i['symbol'], 'side': i['side'],'price': i['price'],'timestamp': i['timestamp']} for i in filled_orders]
    # print(tar_info)

    
