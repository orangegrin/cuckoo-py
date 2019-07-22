import asyncio
import os
from datetime import datetime,timezone,timedelta
import sys
import pprint
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ccxt.async_support as ccxt  # noqa: E402
from psycopg2.errors import UniqueViolation
from sqlalchemy.exc import IntegrityError
from sqlalchemy.engine.url import URL
from sqlalchemy import create_engine,and_
from sqlalchemy.orm import sessionmaker
from db.model import Base, SessionContextManager,IQuoteOrder,BKQuoteOrder
import traceback,time
import mplcursors
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import pyplot

remo_dburl = URL(**{
    "drivername": "postgresql+psycopg2",
    "host": "150.109.52.225",
    # "host": "198.13.38.21",
    "port": 5432,
    "username": "ray",
    "password": "yqll",
    "database": "dashpoint"
    })
remo_engine = create_engine(remo_dburl, echo=False)
Remo_Session = sessionmaker(bind=remo_engine, class_=SessionContextManager)
Base.metadata.create_all(bind=remo_engine)


local_dburl = URL(**{
    "drivername": "postgresql+psycopg2",
    # "host": "150.109.52.225",
    "host": "localhost",
    "port": 5432,
    "username": "ray",
    "password": "yqll",
    "database": "dashpoint"
    })
local_engine = create_engine(local_dburl, echo=False)
Local_Session = sessionmaker(bind=local_engine, class_=SessionContextManager)
Base.metadata.create_all(bind=local_engine)

def main():
    while True:
        last_timesymbol = None
        with Local_Session() as local_session:
            last_timesymbol = local_session.query(BKQuoteOrder.timesymbol).order_by(BKQuoteOrder.id.desc()).first()

        if last_timesymbol:
            with Remo_Session() as remo_session:
                remo_start = remo_session.query(IQuoteOrder.id).filter_by(timesymbol=last_timesymbol[0]).first()
                if remo_start:
                    start_id = remo_start[0]
                else:
                    time.sleep(10)
                    continue
        else:
            start_id = 0
        print(start_id)
        last_id = start_id
        with Remo_Session() as remo_session:
            raw_data_bucket = remo_session.query(IQuoteOrder).filter(IQuoteOrder.id > last_id).order_by(IQuoteOrder.id.asc()).limit(1000).all()
            if raw_data_bucket:
                data_bucket = [BKQuoteOrder(**i.to_dict()) for i in raw_data_bucket]
                try:
                    with Local_Session() as local_session:
                        local_session.add_all(data_bucket)
                except :
                    print("add_all error!!")
                    for i in data_bucket:
                        try:
                            with Local_Session() as local_session:
                                local_session.add(i)
                        except Exception as e:
                            print(type(e))
                            
            if len(raw_data_bucket) < 1000:
                time.sleep(10)

def fill_binance(symbol='ethbtc',dbsymbol='ETH/BTC',after=1557889200):
    # import ccxt.async_support as ccxt
    # kraken = ccxt.kraken()
    # loop = asyncio.get_event_loop()
    # resp =  loop.run_until_complete( asyncio.gather(kraken.fetchOHLCV('ethbtc', timeframe = '1m', since = 1557889200)))
    import requests
    from datetime import timezone,timedelta
    
    tzutc_0 = timezone(timedelta(hours=0))

    resp = requests.get("https://api.cryptowat.ch/markets/kraken/{symbol}/ohlc?after=1557889200&periods=60".format(symbol=symbol))
    kraken = { i[0]:i[1] for i in resp.json()['result']['60'] }
    resp = requests.get("https://api.cryptowat.ch/markets/bitfinex/{symbol}/ohlc?after=1557889200&periods=60".format(symbol=symbol))
    bitfinex = { i[0]:i[1] for i in resp.json()['result']['60'] }
    resp = requests.get("https://api.cryptowat.ch/markets/huobi/{symbol}/ohlc?after=1557889200&periods=60".format(symbol=symbol))
    huobi = { i[0]:i[1] for i in resp.json()['result']['60'] }
    
    avg_price = {}
    for i in range(max(len(kraken),len(bitfinex),len(huobi))):
        start_key = 1557889200
        key = start_key + i*60
        sum_p = 0
        count = 0
        if kraken.get(key,None) is not None:
            sum_p += kraken[key]
            count += 1
        if bitfinex.get(key,None) is not None:
            sum_p += bitfinex[key]
            count += 1
        if huobi.get(key,None) is not None:
            sum_p += huobi[key]
            count += 1
        if count>0:
            avg_price[key] = sum_p/count
        if count==0:
            if key != start_key:
                tmp_key=key
                while True:
                    tmp_key=tmp_key - 60
                    if tmp_key < start_key:
                        break
                    if avg_price.get(tmp_key,None):
                        avg_price[key] = avg_price[tmp_key]
                        break
    fill_items = []
    for key in avg_price:
        sd = {
                'asks':avg_price[key],
                'bids':avg_price[key],
                'symbol':dbsymbol,
                'exchange':'binance',
                'timestamp':datetime.fromtimestamp(key).astimezone(tzutc_0).strftime("%Y-%m-%dT%H:%M:%S")
        }
        fill_items.append(sd)
    
    for sd in fill_items:
        sd['timesymbol'] = "_".join([sd['timestamp'],sd['symbol'],sd['exchange']])
        with Local_Session() as local_session:
            ex_id =  local_session.query(IQuoteOrder.id).filter_by(timesymbol=sd['timesymbol']).first()
            if ex_id:
                local_session.query(IQuoteOrder).filter(IQuoteOrder.id==ex_id[0]).update({"bids":sd['bids'],"asks":sd['asks']})
            else:
                local_session.add(IQuoteOrder(**sd))
                print(sd)

    print(len(avg_price))

def fill_lost_data_to_db(exchange,lost_data):
    # [{'timestamp': datetime.datetime(2019, 5, 20, 8, 30), 'symbol': 'XBTUSD', 'open': 7920, 'high': 7920, 'low': 7903.5, 'close': 7903.5, 'trades': 673, 'volume': 2005070, 'vwap': 7910.7666, 'lastSize': 2500, 'turnover': 25348031427, 'homeNotional': 253.48031427, 'foreignNotional': 2005070}...]
    fill_items = []
    for item in lost_data:
        avg_price = int((item['open']+item['close'])/2*100)/100
        sd = {
                'asks':avg_price,
                'bids':avg_price,
                'symbol':item['symbol'],
                'exchange':exchange,
                'timestamp':item['timestamp'].strftime("%Y-%m-%dT%H:%M:%S")
        }
        fill_items.append(sd)
    
    for sd in fill_items:
        sd['timesymbol'] = "_".join([sd['timestamp'],sd['symbol'],sd['exchange']])
        with Local_Session() as local_session:
            ex_id =  local_session.query(IQuoteOrder.id).filter_by(timesymbol=sd['timesymbol']).first()
            if ex_id:
                local_session.query(IQuoteOrder).filter(IQuoteOrder.id==ex_id[0]).update({"bids":sd['bids'],"asks":sd['asks']})
            else:
                local_session.add(IQuoteOrder(**sd))
                print(sd)
    
if __name__ == "__main__":
    from plot_figure import get_bitmex_kline_data
    start_date = datetime.now()-timedelta(days=5)
    lost_data = get_bitmex_kline_data('XBTUSD',start_time=start_date)+get_bitmex_kline_data('XBTM19',start_time=start_date)+get_bitmex_kline_data('XBTU19',start_time=start_date)
    fill_lost_data_to_db('bitmex',lost_data)
    # fill_binance()
    # fill_binance(symbol='ethbtc',dbsymbol='ETH/BTC',after=1557889200)
    # fill_binance(symbol='eosbtc',dbsymbol='EOS/BTC',after=1557889200)
    # fill_binance(symbol='ltcbtc',dbsymbol='LTC/BTC',after=1557889200)
    # fill_binance(symbol='xrpbtc',dbsymbol='XRP/BTC',after=1557889200)
    # main()
                        
                
    

