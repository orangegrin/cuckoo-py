import asyncio
import shutil
import os
from datetime import datetime,timezone,timedelta
import sys
import pprint
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ccxt.async_support as ccxt  # noqa: E402
from sqlalchemy.engine.url import URL
from sqlalchemy import create_engine,and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from db.model import Base, SessionContextManager,BKQuoteOrder,IQuoteOrder,TradeHistory
import traceback,time
import mplcursors
import matplotlib.pyplot as plt
import matplotlib.dates as dates
from matplotlib.lines import Line2D
import pandas as pd
from pandas.plotting import register_matplotlib_converters
import numpy
import talib
import requests
import json
from binance.client import Client

from market_maker.bitmex_mon_api import BitMexMon

dburl = URL(**{
    "drivername": "postgresql+psycopg2",
    # "host": "150.109.52.225",
    # "host": "198.13.38.21",
    "host": "127.0.0.1",
    "port": 5432,
    "username": "ray",
    "password": "yqll",
    "database": "dashpoint"
    })
engine = create_engine(dburl, echo=False)
Session = sessionmaker(bind=engine, class_=SessionContextManager)
Base.metadata.create_all(bind=engine)

SYMBOL_MAP={
    "bitmex":{"ETH":"ETHU19","EOS":"EOSM19","XRP":"XRPM19","LTC":"LTCM19","BTCM":"XBTM19","BTCU":"XBTU19","BTCZ":"XBTZ19","BTCX":"XBTUSD","BTCH":"XBTH20"},
    "binance":{"ETH":"ETH/BTC","EOS":"EOS/BTC","XRP":"XRP/BTC","LTC":"LTC/BTC"},
    "gateio":{"ETH":"ETH/BTC","EOS":"EOS/BTC","XRP":"XRP/BTC","LTC":"LTC/BTC"},
    "okex":{"ETH":"ETH/BTC","EOS":"EOS/BTC","XRP":"XRP/BTC","LTC":"LTC/BTC"},
    "fcoin":{"ETH":"ETH/BTC","EOS":"EOS/BTC","XRP":"XRP/BTC","LTC":"LTC/BTC"}
}

SQL_DATA_CACHE = {}
tzutc_8 = timezone(timedelta(hours=8))

def self_reindex(bitmex_l,akey,binance_l,bkey):
    # dkey: 'asks'

    # bitmex_series = pd.Series([d[akey] for d in bitmex_l], index=pd.to_datetime([d['timestamp'].replace(microsecond=0) for d in bitmex_l]))
    # binance_series = pd.Series([d[bkey] for d in binance_l], index=pd.to_datetime([d['timestamp'].replace(microsecond=0) for d in binance_l]))
    bitmex_series = pd.Series([d[akey] for d in bitmex_l], index=pd.to_datetime([d['timestamp'].replace(microsecond=0).astimezone(tzutc_8) for d in bitmex_l]))
    binance_series = pd.Series([d[bkey] for d in binance_l], index=pd.to_datetime([d['timestamp'].replace(microsecond=0).astimezone(tzutc_8) for d in binance_l]))
    
    index_start = min(bitmex_series.index.min(),binance_series.index.min())
    index_end = max(bitmex_series.index.max(),binance_series.index.max())
    df_reindexed_bitmex = bitmex_series.reindex(pd.date_range(start=index_start,
                                                end=index_end,
                                                freq='1S'))   
    df_reindexed_binance = binance_series.reindex(pd.date_range(start=index_start,
                                                end=index_end,
                                                freq='1S'))   
    print(len(df_reindexed_bitmex))
    print(len(df_reindexed_binance))
    
    df_reindexed_bitmex = df_reindexed_bitmex.interpolate(method='nearest')
    df_reindexed_binance = df_reindexed_binance.interpolate(method='nearest')
    return df_reindexed_bitmex,df_reindexed_binance

def self_reindex_sig(bitmex_l,key,start_date,end_date):
    bitmex_series = pd.Series([d[key] for d in bitmex_l], index=pd.to_datetime([d['timestamp'].replace(microsecond=0).astimezone(tzutc_8) for d in bitmex_l]))
    # print(bitmex_series)
    df_reindexed_bitmex = bitmex_series.reindex(pd.date_range(start=start_date.astimezone(tzutc_8),end=end_date.astimezone(tzutc_8),freq='1S'),method='pad')  
    df_reindexed_bitmex = df_reindexed_bitmex.interpolate(method='nearest') 
    return df_reindexed_bitmex

def query_avg_cell(session,exchange,key,symbol,start_date_str,end_date_str):
    exchang_data_A = None
    
    if key == "bids":
        exchang_data_A = session.query(func.avg(BKQuoteOrder.bids).label("avg_bids")).filter_by(exchange=exchange,symbol=symbol).filter(and_(BKQuoteOrder.timesymbol > start_date_str,BKQuoteOrder.timesymbol<end_date_str)).all()[0][0]
        # exchang_data_A = session.query(BKQuoteOrder.bids).filter_by(exchange=exchange,symbol=symbol).filter(and_(BKQuoteOrder.timesymbol > start_date_str,BKQuoteOrder.timesymbol<end_date_str)).all()
        # print(exchang_data_A)
    elif key == "asks":
        exchang_data_A = session.query(func.avg(BKQuoteOrder.asks).label("avg_asks")).filter_by(exchange=exchange,symbol=symbol).filter(and_(BKQuoteOrder.timesymbol > start_date_str,BKQuoteOrder.timesymbol<end_date_str)).all()[0][0]

    # print(key,start_date_str,end_date_str,exchang_data_A)
    return exchang_data_A

def query_symbol_datafram(session,exchange,key,symbol,start_date_str,end_date_str):
    
    
    print("start get: ",symbol)
    end_date = datetime.strptime(end_date_str,'%Y-%m-%dT%H:%M:%S')+timedelta(minutes=1)
    end_date_str = end_date.strftime("%Y-%m-%dT%H:%M:%S")
    date_objs = pd.date_range(start=start_date_str, end=end_date_str, closed=None,freq='1min')
    dr = [ ts.strftime("%Y-%m-%dT%H:%M") for ts in date_objs]
    # .strftime("%Y-%m-%dT%H:%M:%S")
    prices = []
    start_date_str = dr[1]
    for idx in range(10):
        start_date_str_pre = (datetime.strptime(start_date_str,'%Y-%m-%dT%H:%M')+timedelta(minutes=-1)).strftime("%Y-%m-%dT%H:%M")
        # print(start_date_str_pre)
        exchang_data_A = query_avg_cell(session,exchange,key,symbol,start_date_str_pre,start_date_str)
        if exchang_data_A is not None:
            prices.append(exchang_data_A)
            break
        start_date_str = start_date_str_pre
    if prices == []:
        print("Can not find start Data at ",dr[0])
        return None
    start_ts = time.time()
    print(start_ts)
    print(prices)
    for idx in range(1,len(dr)-1):
        exchang_data_A = query_avg_cell(session,exchange,key,symbol,dr[idx],dr[idx+1])
        if exchang_data_A is not None:
            prices.append(exchang_data_A)
        else:
            prices.append(prices[idx-1])
        # print(exchang_data_A)
        # print(type(exchang_data_A))
    print(time.time() - start_ts)
    return pd.Series(prices, index=[d.tz_localize('utc').astimezone(tzutc_8) for d in date_objs[:-1]])

def gen_plot_datafram(session,exchangeA,akey,exchangeB,bkey,symbol,start_date_str="20190409T00:00:00",end_date_str=None,RAW_VALUE=False):
    # exchangeA,exchangeB "bitmex","binance"
    # akey,bkey "asks","bids"
    # exchangeA[akey],exchangeB[bkey] 
    # BTCXU --> BTCX/BTCU
    # BTCMU --> BTCM/BTCU  
    # binance/bitmex - 1    exchangeB/exchangeA - 1
    raw_symbol = symbol
    if end_date_str is None:
        end_date_str = datetime.fromtimestamp(time.time()).strftime("%Y-%m-%dT%H:%M:%S") 
    if raw_symbol.startswith('BTC'):
        symbol='BTC'+raw_symbol[4]
    f_bitmex = query_symbol_datafram(session,exchangeA,akey,SYMBOL_MAP[exchangeA][symbol],start_date_str=start_date_str,end_date_str=end_date_str)
    # bitmex = session.query(BKQuoteOrder).filter_by(exchange=exchangeA,symbol=SYMBOL_MAP[exchangeA][symbol]).filter(and_(BKQuoteOrder.timesymbol>start_date_str,BKQuoteOrder.timesymbol<end_date_str)).order_by(BKQuoteOrder.timesymbol.asc()).all()
    if raw_symbol.startswith('BTC'):
        symbol='BTC'+raw_symbol[3]
    if raw_symbol.startswith('BTC') and symbol=='BTC'+raw_symbol[4]:
        f_binance = f_bitmex
    else:
        f_binance = query_symbol_datafram(session,exchangeB,bkey,SYMBOL_MAP[exchangeB][symbol],start_date_str=start_date_str,end_date_str=end_date_str)
        # binance = session.query(BKQuoteOrder).filter_by(exchange=exchangeB,symbol=SYMBOL_MAP[exchangeB][symbol]).filter(and_(BKQuoteOrder.timesymbol>start_date_str,BKQuoteOrder.timesymbol<end_date_str)).order_by(BKQuoteOrder.timesymbol.asc()).all()
    
    # bitmex_l = [x.to_dict() for x in bitmex]
    # binance_l = [x.to_dict() for x in binance]

    # print(len(bitmex_l))
    # print(len(binance_l))
    # print("------------------")
    # if (binance_l == [] and bitmex_l == []):
    #     print('\nNo data found in selected time range!!!\n')
    #     return None

    # bitmex0=datetime.strptime(start_date_str,'%Y-%m-%dT%H:%M:%S')
    # binance0=datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M:%S')
    # if bitmex_l:
    #     bitmex0 = bitmex_l[0]['timestamp'].replace(microsecond=0)
    # if binance_l:
    #     binance0 = binance_l[0]['timestamp'].replace(microsecond=0)

    # if binance0>bitmex0 or binance_l == []:
    #     binance_tmp = session.query(BKQuoteOrder).filter_by(exchange=exchangeB,symbol=SYMBOL_MAP[exchangeB][symbol]).filter(and_(BKQuoteOrder.timesymbol<=start_date_str)).order_by(BKQuoteOrder.timesymbol.desc()).limit(1).all()
    #     tmp_item1,tmp_item2 = binance_tmp[0].to_dict(),binance_tmp[0].to_dict()
    #     tmp_item1['timestamp'] = bitmex0
    #     tmp_item2['timestamp'] = bitmex0 + timedelta(seconds=1)
    #     if binance_l == []:
    #         binance_l = [tmp_item2]
    #     binance_l = [tmp_item1]+binance_l

    # if binance0<bitmex0 or bitmex_l == []:
    #     bitmex_tmp = session.query(BKQuoteOrder).filter_by(exchange=exchangeA,symbol=SYMBOL_MAP[exchangeA][symbol]).filter(and_(BKQuoteOrder.timesymbol<=start_date_str)).order_by(BKQuoteOrder.timesymbol.desc()).limit(1).all()
    #     tmp_item1,tmp_item2 = bitmex_tmp[0].to_dict(),bitmex_tmp[0].to_dict()
    #     tmp_item1['timestamp'] = binance0
    #     tmp_item2['timestamp'] = binance0 + timedelta(seconds=1)
    #     if bitmex_l == []:
    #         bitmex_l = [tmp_item2]
    #     bitmex_l = [tmp_item1]+bitmex_l
    
    # print(len(bitmex_l))
    # print(len(binance_l))
    
    # df_reindexed_bitmex,df_reindexed_binance = self_reindex(bitmex_l,akey,binance_l,bkey)
    
    # df_reindexed_bitmex = df_reindexed_bitmex.fillna(method='pad')
    if RAW_VALUE:
        # return df_reindexed_bitmex/1
        return f_bitmex/1
    # df_reindexed_binance = df_reindexed_binance.fillna(method='pad')

    f = f_binance/f_bitmex-1
    
    return f

def get_MAs(data_list, timeperiods):
    MAs = []
    for timeperiod in timeperiods:
        MAs.append(talib.MA(data_list, timeperiod=timeperiod, matype=0))
    return MAs

def get_EMAs(data_list, timeperiods):
    EMAs = []
    for timeperiod in timeperiods:
        EMAs.append(talib.EMA(data_list, timeperiod=timeperiod))
    return EMAs

def merge_cut_df(df_raw,df_new,num=1440*12):
    tmp_d  = df_raw.to_dict()
    tmp_d.update(df_new.to_dict())
    tmp_keys = sorted(tmp_d.keys())[-num:]
    tmp_d = { key:tmp_d[key] for key in tmp_keys}
    return pd.Series(tmp_d)

def pre_get_f(session,exchangeA,akey,exchangeB,bkey,symbol,start_date_str,end_date_str):
    
    if end_date_str is None:
        end_date_str = datetime.fromtimestamp(time.time()).strftime("%Y-%m-%dT%H:%M:%S") 
    global SQL_DATA_CACHE
    data_cache_key = '_'.join([exchangeA,akey,exchangeB,bkey,symbol])
    print("Get df of {} start:".format(symbol))
    print(start_date_str,'-----',end_date_str)
    f = None
    if SQL_DATA_CACHE.get(data_cache_key,None) is None:
        print(start_date_str)
        if symbol == 'ETHUU':
            ethusd_f = query_symbol_datafram(session,exchangeA,"bids","ETHUSD",start_date_str=start_date_str,end_date_str=end_date_str)
            ethu19_f = query_symbol_datafram(session,exchangeA,"bids","ETHU19",start_date_str=start_date_str,end_date_str=end_date_str)
            btcz19_f = query_symbol_datafram(session,exchangeB,"asks","XBTUSD",start_date_str=start_date_str,end_date_str=end_date_str)

            if any([ethu19_f is None,ethusd_f is None,btcz19_f is None]):
                print("some symbol not find data,return!!")
                return None
            f = (ethusd_f/ethu19_f)/btcz19_f-1
        else:
            f = gen_plot_datafram(session,exchangeA,akey,exchangeB,bkey,symbol,start_date_str,end_date_str=end_date_str)
        if f is not None:
            f = f.resample('1min',closed='left',label='left').mean()
        SQL_DATA_CACHE[data_cache_key] = {'raw_data':f,'next_stat_ts':(datetime.now().astimezone(timezone(timedelta(hours=0)))-timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:00")}
    else:
        start_date_str = SQL_DATA_CACHE[data_cache_key]['next_stat_ts'] 
        print(start_date_str)
        if symbol == 'ETHUU':
            ethusd_f = query_symbol_datafram(session,exchangeA,"bids","ETHUSD",start_date_str=start_date_str,end_date_str=end_date_str)
            ethu19_f = query_symbol_datafram(session,exchangeA,"bids","ETHU19",start_date_str=start_date_str,end_date_str=end_date_str)
            btcz19_f = query_symbol_datafram(session,exchangeB,"asks","XBTUSD",start_date_str=start_date_str,end_date_str=end_date_str)
            if any([ethu19_f is None,ethusd_f is None,btcz19_f is None]):
                print("some symbol not find data,return!!")
                return None
            f = (ethusd_f/ethu19_f)/btcz19_f-1
        else:
            f = gen_plot_datafram(session,exchangeA,akey,exchangeB,bkey,symbol,start_date_str,end_date_str=end_date_str)
        if f is not None:
            f = f.resample('1min',closed='left',label='left').mean()
            SQL_DATA_CACHE[data_cache_key]['raw_data'] = merge_cut_df(SQL_DATA_CACHE[data_cache_key]['raw_data'],f)
        SQL_DATA_CACHE[data_cache_key]['next_stat_ts'] = (datetime.now().astimezone(timezone(timedelta(hours=0)))-timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:00")
    return SQL_DATA_CACHE[data_cache_key]['raw_data']

def plot_figure(session,f,exchangeA,akey,exchangeB,bkey,symbol,raw_f=None,offset=0,profit_range=0.002):
    
    print("########MA-CALC########")
    register_matplotlib_converters()
    

    # data_list = [i for i in list(f.to_dict().items()) if i[0].strftime("%Y-%m-%dT%H:%M:%S")[-2:]=="00"]
    # f =  f.resample('1min',closed='left',label='left').mean() 
    raw_f_vals, raw_f_index = [],[]
    if raw_f is not None:
        raw_f = raw_f.resample('1min',closed='left',label='left').mean() 
        raw_f_data = [i for i in list(f.to_dict().items())] 
        raw_f_vals = [i[1] for i in raw_f_data]
        raw_f_index = [i[0] for i in raw_f_data]

    data_list = [i for i in list(f.to_dict().items())] 
    vals = [i[1] for i in data_list]
    index = [i[0] for i in data_list]
    
    #calc MAs and MA_avg
    fig = None
    df_axes=None
    df2_axes=None
    if False and symbol=='BTCMU':
        fig = plt.figure(figsize=(48,27))
        df_axes=fig.add_subplot(211)
        df2_axes=fig.add_subplot(212)
    else :
        plt.figure(1)
    min_based_df=None
    if True:
        # MAs = get_MAs(numpy.array(vals),[1440, 1440,1440,1440*2,1440/2,  1440/6, 1440/4, 1440/8, 1440/12])
        # MAs = get_MAs(numpy.array(vals),[1440, 1440/2, 1440/3, 1440/4])
        MAs = get_EMAs(numpy.array(vals),[1440, 1440*2, 1440*3, 1440*4])
        MA_AVG=[]
        for i in zip(*MAs):
            if all(i):
                MA_AVG.append(sum(i)/len(i))
            else:
                MA_AVG.append(0)
        # MA_AVG = [sum(i)/len(i) for i in zip(*MAs) if any(i) else 0]
        # min_based_df=pd.DataFrame({'Diff':vals,'EMA1':MAs[0],'EMA2':MAs[1],'EMA3':MAs[2],'EMA4':MAs[3],'EMA_AVG':MA_AVG},index=index)
        plot_vals = [] 
        for idx in range(0,len(vals)) :
            v = vals[idx]
            # if symbol != 'ETHUU':
            if v > 0.02 or v < -0.04:
                if idx==0:
                    plot_vals.append(0)
                else:
                    plot_vals.append(plot_vals[idx-1])
            else:
                plot_vals.append(v)
            # plot_vals.append(v)
        # add offset
        MA_AVG = [av+offset for av in MA_AVG]
        # min_based_df=pd.DataFrame({'Diff':vals,'MA1':MAs[0],'MA2':MAs[1],'MA3':MAs[2],'MA4':MAs[3],'MA_AVG':MA_AVG},index=index)
        min_based_df=pd.DataFrame({'Diff':plot_vals,'MA_AVG':MA_AVG},index=index)
        # MA_AVG = MAs[3]
        # min_based_df=pd.DataFrame({'Diff':vals,'MA_AVG':MA_AVG},index=index)

    
        min_based_df.fillna(value=0)
        print(len(data_list))
        print([len(i) for i in MAs])
        # min_based_df.to_csv("./BTCUZ.csv")
        # print("save csv success!")
        if df_axes:
            df_axes = min_based_df.plot(figsize=(16, 9),ax=df_axes)
        elif raw_f is not None:
            df_axes = plt.subplot(211)
            df_axes = min_based_df.plot(figsize=(16, 9),ax=df_axes)
            # share x only
            ax2 = plt.subplot(212, sharex=df_axes)
            plt.plot(raw_f_index,raw_f_vals)
            # make these tick labels invisible
            # plt.setp(ax2.get_xticklabels(), visible=False)

            plt.show()
        else:
            df_axes = min_based_df.plot(figsize=(32, 9))
        
        locator = dates.HourLocator(interval=1)
        locator.MAXTICKS = 1000000
        df_axes.xaxis.set_minor_locator(locator)
        df_axes.xaxis.set_major_locator(dates.DayLocator())
        df_axes.xaxis.grid(True, which="major")
        df_axes.yaxis.grid()

    maxid = f.idxmax()
    minid = f.idxmin()
    print(index[0],index[-1])

    

    #plot 1min kline data
    if False:
        fig,ax1 = plt.subplots()
        ax1.plot([ datetime.fromtimestamp(i.value/1000000000) for i in index],vals,'b-')
        ax2 = ax1.twinx()
        ax2.set_ylabel("price")
        kline_bitmex_data = get_bitmex_kline_data("ETHM19",binSize="1m",start_time=datetime.fromtimestamp(index[0].value/1000000000))
        kline_binance_data = get_binance_kline_data('ETHBTC',start_time=int(index[0].value/1000000))
        x1,y1=[],[]
        for i in kline_bitmex_data:
            if i.get('close',0) is None or i.get('open',0) is None:
                continue
            x1.append(i['timestamp'])
            y1.append((i.get('close',0)+i.get('open',0))/2)
        ax2.plot(x1, y1, 'g-')
        x2,y2=[],[]
        for i in kline_binance_data:
            if i.get('close',0) is None or i.get('open',0) is None:
                continue
            x2.append(i['timestamp'])
            y2.append((float(i['close'])+float(i['open']))/2)
        ax2.plot(x2, y2, 'y-')
        
        ax1.set_xlabel("Timestamp")
        ax1.set_ylabel("Percent")
    #plot buy/sell chance point
    custom_legend_marks = []
    custom_legend_labels = []
    if True:
        up_marker,down_marker,hist_data = [],[],[]
        ##########################################
        # MA_AVG = MAs[3]
        ##########################################
        for idx in range(1,len(MA_AVG)):
            if MA_AVG[idx] and MA_AVG[idx-1]:
                if MA_AVG[idx-1]+profit_range < plot_vals[idx]:
                    up_marker.append([index[idx],plot_vals[idx]])
                elif MA_AVG[idx-1]-profit_range > plot_vals[idx]:
                    down_marker.append([index[idx],plot_vals[idx]])
                
                if idx >= 60*24*4:
                    if vals[idx] > MA_AVG[idx-1] or  vals[idx] < MA_AVG[idx-1] :
                        tmp_v = vals[idx] - (MA_AVG[idx-1]+0.0005)
                        hist_data.append(tmp_v)  
        if hist_data:
            plot_hist(hist_data,symbol,offset=offset)     
            plt.figure(2)       
        for i in up_marker:
            plt.scatter(i[0],i[1],s=40,c="red",marker="p")
        for i in down_marker:
            plt.scatter(i[0],i[1],s=40,c="green",marker="p")
        custom_legend_marks.append(Line2D([0], [0], marker='o', color='w',markerfacecolor='green', markersize=15))
        custom_legend_marks.append(Line2D([0], [0], marker='o', color='w',markerfacecolor='red', markersize=15))
        custom_legend_labels += ["Predict trade point"]*2


    #plot real trade point
    if False and symbol=='BTCMU':
        # ax = fig.add_subplot(212)
        # ax.plot(min_based_df.index,vals)
        df2_axes = pd.DataFrame({'Diff':vals},index=index).plot(figsize=(16, 9),ax=df2_axes)
        trade_points = get_trade_point_from_db(session,'XBTU19',index[0].strftime("%Y-%m-%dT%H:%M:%S"))
        # trade_points += get_trade_point_from_db(session,'XBTM19',index[0].strftime("%Y-%m-%dT%H:%M:%S"))
        # trade_points = get_trade_point_from_csv()
        for p in trade_points:
            color = 'black' if p['side'] == 'Buy' else 'orange'
            p['timestamp'] = p['timestamp'].strftime("%Y-%m-%dT%H:%M:00+08:00") 
            # print(min_based_df.ix[p['timestamp']])
            # yvalue = float(min_based_df[min_based_df.index[0]]['Diff'])
            yvalue = min_based_df.loc[p['timestamp']]['Diff']
            df2_axes.scatter(p['timestamp'],yvalue,s=40,c=color,marker="p")
       
        custom_legend_marks.append(Line2D([0], [0], marker='o', color='w',markerfacecolor='black', markersize=15))
        custom_legend_marks.append(Line2D([0], [0], marker='o', color='w',markerfacecolor='orange', markersize=15))
        custom_legend_labels += ["U19 Buy point","U19 Sell point"]


    #plot max/min point
    if False:
        # if not df_axes:
        #     df_axes=plt
        df_axes.annotate('max({t},{v})'.format(t = maxid,v='{:.8f}'.format(f[maxid])), xy=(maxid, f[maxid]),arrowprops=dict(facecolor='black', shrink=0.05))
        df_axes.axhline(y=f[maxid],linestyle="--",color="gray")
        # df_axes.text(maxid,f[maxid],'max({t},{v})'.format(t = maxid.strftime("%m%d#%H:%M:%S") ,v=f[maxid]))

        df_axes.annotate('min({t},{v})'.format(t = minid,v='{:.8f}'.format(f[minid])), xy=(minid, f[minid]),arrowprops=dict(facecolor='black', shrink=0.05))
        df_axes.axhline(y=f[minid],linestyle="--",color="gray")
        # df_axes.text(minid,f[minid],'min({t},{v})'.format(t = minid.strftime("%m%d#%H:%M:%S") ,v=f[minid]))
        # df_axes.axhline(y=0.0,linestyle="-",color="gray")
        if df2_axes:
            df2_axes.axhline(y=0.0,linestyle="-",color="gray")
    
    if False and custom_legend_marks and symbol == 'BTCMU' :
        legend1 = plt.legend(custom_legend_marks, custom_legend_labels)
        df2_axes.add_artist(legend1)
        # plt.legend(custom_legend_marks, custom_legend_labels)

    # add help line
    # for yval in [0.0,0.01,-0.01,0.02,-0.02,0.03,-0.03]:
    #     df_axes.axhline(y=yval,linestyle="--",color="black")

    plt.title("{symbol}---|{EB}[{BK}]/{EA}[{AK}]-1|---point +/-{PROFITRANGE}--offest[{OFFSET}]".format(symbol=symbol,EA=exchangeA,AK=akey,EB=exchangeB,BK=bkey,PROFITRANGE=str(profit_range),OFFSET=str(offset)))
    # mplcursors.cursor(fig)
    # plt.subplots_adjust(hspace=1)
    
    dst_file = "./figure/"+'-'.join([exchangeA,exchangeB,symbol,datetime.now().strftime("%Y-%m-%d %H%M%S")])+".png"
    upload_file = "./figure/"+symbol.upper()+".png"
    if offset != 0:
        dst_file = "./figure/"+'-'.join([exchangeA,exchangeB,symbol,"OFFSET",datetime.now().strftime("%Y-%m-%d %H%M%S")])+".png"
        upload_file = "./figure/"+(symbol+"_OFFSET").upper()+".png"
    
    plt.savefig(dst_file)
    shutil.copyfile(dst_file,upload_file)
    # plt.show()
    plt.close()

def plot_hist(data_list,symbol,offset=0):
    tmp_data_list = []
    for x in data_list:
        if abs(x)>0.01:
            continue
        if abs((x*1000 - int(x*1000))*10) >=5:
            if x > 0:
                tmp_data_list.append((int(x*1000)*10+5)/10000+0.00025)
            else:
                tmp_data_list.append((int(x*1000)*10+5)/10000-0.00025)
        else:
            if x > 0:
                tmp_data_list.append((int(x*1000)*10)/10000+0.00025)
            else:
                tmp_data_list.append((int(x*1000)*10)/10000-0.00025)

    data_list = tmp_data_list
    data_keys = set(data_list)
    data_dict = {k:0 for k in data_keys}
    
    for v in data_list:
        data_dict[v] = data_dict[v]+1
    above0,blow0 = len([ x for x in data_list if x>0]),len([ x for x in data_list if x<0])

    g = plt.figure(figsize=(16,9))
    plt.title("{symbol}--Offset={OFFSET}".format(symbol=symbol,OFFSET=str(offset)))
    ax = plt.gca()                                           
    ax.spines['right'].set_color('none') 
    ax.spines['top'].set_color('none')        
    ax.xaxis.set_ticks_position('bottom')   
    ax.yaxis.set_ticks_position('left')          
    ax.spines['bottom'].set_position(('data', 0))   
    ax.spines['left'].set_position(('data', 0))
    ax.set_yticks([])
    for px,y in data_dict.items():
        # px = x/1000+0.0005 if x > 0 else x/1000-0.0005
        color = "blue" if px > 0 else "orange"
        plt.bar(px, y, 0.0005, color=color)
        yp = (y/above0)*100 if px>0 else (y/blow0)*100
        plt.text(px, y+0.05, '{:.2f}%'.format(yp), ha='center', va= 'bottom',fontsize=6)
    
    dst_file = "./figure/"+symbol.upper()+"_HIST.png"
    if offset!=0:
        dst_file = "./figure/"+symbol.upper()+"_HIST_OFFSET.png"

    plt.savefig(dst_file)
    print("save: "+dst_file)
    plt.close()

def plot_exchangeAB(session,exchangeA,akey,exchangeB,bkey,symbol,start_date_str="2019-04-11T18:00:00",end_date_str=None,RAW_DATA=False,offset=0,profit_range=0.002):
    
    if symbol == 'BTCZH':
        start_date_str="2019-09-13T18:00:00"
    f = pre_get_f(session,exchangeA,akey,exchangeB,bkey,symbol,start_date_str=start_date_str,end_date_str=end_date_str)
    # f = gen_plot_datafram(session,exchangeA,akey,exchangeB,bkey,symbol,start_date_str=start_date_str,end_date_str=end_date_str)
    # RAW_DATAFRAM_CACHE = f
    # return None
    #want plot price value,so get raw price data,not diff data 
    raw_f = None
    if RAW_DATA:
        raw_symbol = symbol
        if symbol.startswith("XBT"):
            raw_symbol = "XBTXX"
        raw_f = gen_plot_datafram(session,exchangeA,akey,exchangeA,akey,raw_symbol,start_date_str=start_date_str,end_date_str=end_date_str,RAW_VALUE=True)
    #plot hist figure
    if False:
        plt.subplot(212)
        v = list(f.to_dict().values())
        import numpy as np
        nv = np.array(v)
        from scipy.stats import kstest
        print(kstest(nv, 'norm'))

        nmean = np.mean(nv)
        nsigma =np.std(nv,ddof=1)
        print(nmean,nsigma,int((nv.max()-nv.min())/nsigma))

        _count, bins, _ignored = plt.hist(nv, int((nv.max()-nv.min())/nsigma), density=True)
        fig = plt.plot(bins, 1/(nsigma * np.sqrt(2 * np.pi)) * np.exp( - (bins - nmean)**2 / (2 * nsigma**2) ),linewidth=3, color='y')
        my_x_ticks = np.arange(nv.min(), nv.max(), 0.001)
        plt.xticks(my_x_ticks)

        mplcursors.cursor(fig)

    plot_figure(session,f,exchangeA,akey,exchangeB,bkey,symbol,raw_f=raw_f,profit_range=profit_range)
    if offset!=0:
        plot_figure(session,f,exchangeA,akey,exchangeB,bkey,symbol,raw_f=raw_f,offset=offset,profit_range=profit_range)


def get_bitmex_kline_data(symbol,binSize="1m",start_time=None):

    bitmex_mon = BitMexMon(symbol,UnAuthSubTables=[],AuthSubTables=[],WebSocketOn=False)
    diff_mins = (datetime.now()-start_time).total_seconds()/60
    print(diff_mins)
    ret_n = []
    for loopnum in range(0,int(diff_mins/600+1)):
        if loopnum == 0:
            query_start_datetime = start_time 
        else:
            query_start_datetime = start_time + timedelta(minutes=(600*loopnum))
        print(query_start_datetime)
            
        ret = bitmex_mon.bitmex.http_get_kline(query={"binSize":"1m","partial":False,"symbol":symbol,"count":600,"reverse":"false","startTime":query_start_datetime.strftime("%Y-%m-%dT%H:%M")})
        for i in ret:
            i['timestamp'] = datetime.strptime(i['timestamp'].split('.')[0],"%Y-%m-%dT%H:%M:%S")
            ret_n.append(i)
    return ret_n

def get_binance_kline_data(symbol,binSize=Client.KLINE_INTERVAL_1MINUTE,start_time=""):
    
    client = Client("api_key", "api_secret")
    ret = client.get_historical_klines(symbol, binSize, start_time)
    ret_n = []
    for i in ret:
        t = {}
        t['timestamp'] = datetime.fromtimestamp(i[0]/1000)
        t['close'] = i[1]
        t['open'] = i[4]
        ret_n.append(t)
    return ret_n

def get_trade_point_from_db(session,symbol,start_time_str):
    # 'symbol': 'ETHM19',
    # {'orderID': '1fe51f92-7a48-5c81-0e41-2921483ccaf2', 'clOrdID': '', 'clOrdLinkID': '', 'account': 63450, 'symbol': 'ETHM19', 'side': 'Buy', 'simpleOrderQty': None, 'orderQty': 5, 'price': 0.02883, 'displayQty': None, 'stopPx': None, 'pegOffsetValue': None, 'pegPriceType': '', 'currency': 'XBT', 'settlCurrency': 'XBt', 'ordType': 'Limit', 'timeInForce': 'GoodTillCancel', 'execInst': 'ParticipateDoNotInitiate', 'contingencyType': '', 'exDestination': 'XBME', 'ordStatus': 'Filled', 'triggered': '', 'workingIndicator': False, 'ordRejReason': '', 'simpleLeavesQty': None, 'leavesQty': 0, 'simpleCumQty': None, 'cumQty': 5, 'avgPx': 0.02883, 'multiLegReportingType': 'SingleSecurity', 'text': 'Submission from www.bitmex.com', 'transactTime': '2019-05-09T02:42:00.904Z', 'timestamp': '2019-05-09T03:14:04.093Z'}
    ret = []
    trade_orders = session.query(TradeHistory).filter_by(symbol=symbol).filter(TradeHistory.timestamp>start_time_str).all()
    if trade_orders:
        for tod in trade_orders:
            try:
                ret.append({"timestamp":tod.timestamp,'value':tod.price,'side':tod.side})
            except Exception:
                print(traceback.format_exc())
                continue
    print(len(ret))
    return ret

# def get_kline_from_db(start_date_str):
    
#     bitmex = session.query(BKQuoteOrder).filter_by(exchange=exchangeA,symbol=SYMBOL_MAP[exchangeA][symbol]).filter(and_(BKQuoteOrder.timesymbol>=start_date_str,BKQuoteOrder.timesymbol<=end_date_str)).order_by(BKQuoteOrder.timesymbol.asc()).all()
#     pass

def get_trade_point_from_csv(csv = 'test\TradeHistory(symbol=EOSM19)2019-4-17.csv'):
    
    ret = []
    df = pd.read_csv(csv)
    for idx in range(len(df['transactTime'])):
        datetimes = datetime.strptime(df['transactTime'][idx], '%Y/%m/%d %p%I:%M:%S')
        ret.append({"timestamp":datetimes,'value':df['price'][idx],'side':df['side'][idx]})
    return ret

def scp_file_to_remote(upfiles,subdir="figure"):
    import paramiko
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # ssh.connect('198.13.38.21', 22, 'ray','yqll125321,.')
    ssh.connect('raylee.5166.info', 22, 'ray',key_filename='./figure/id_rsa')

    ftp_client=ssh.open_sftp()
    print("Open ssh sftp!")
    [ftp_client.put('./figure/{fig_name}.png'.format(fig_name=img_name),'/home/ray/web/{subdir}/{fig_name}.png'.format(subdir=subdir,fig_name=img_name)) for img_name in upfiles if os.path.exists('./figure/{fig_name}.png'.format(fig_name=img_name))]
    ftp_client.close()
    ssh.close()

def get_diff_offset_online(symbol_pair,api="http://raylee.5166.info:8001/diff_offset"):
    try:
        resp = requests.get(api,params={"symbol_pair":symbol_pair})
        # print(resp.content)
        return json.loads(resp.content)["value"] 
    except Exception:
        print(traceback.format_exc())
        return 0

def get_profit_range_online(symbol_pair,api="http://raylee.5166.info:8001/profit_range"):
    try:
        resp = requests.get(api,params={"symbol_pair":symbol_pair})
        # print(resp.content)
        return json.loads(resp.content)["value"] 
    except Exception:
        print(traceback.format_exc())
        return 0


def main():   
    # get_binance_kline_data('ETHBTC',start_time=1557569880000)
    # ret = get_bitmex_kline_data('ETHM19',start_time=datetime(2019,5,11,0,0))
    # print(len(ret))
    # get_trade_point_from_bitmex('ETHM19')
    last_profit_range = 0.002
    last_profit_dict={}
    last_offset_dict={}
    while True:
        try:
            with Session() as session:
                # Start_date_str = (datetime.now()-timedelta(days=12,hours=12)).strftime("%Y-%m-%dT%H:%M:00") 
                Start_date_str = (datetime.now().astimezone(timezone(timedelta(hours=0)))-timedelta(days=12,hours=12)).strftime("%Y-%m-%dT%H:%M:00") 
                for symbol_pair in [ "BTCZH", "BTCUZ","ETHUU" ]:
                    offset = get_diff_offset_online(symbol_pair)
                    profit_range = get_profit_range_online(symbol_pair)
                    print(offset,profit_range)
                    
                    if profit_range<=0:
                        profit_range = last_profit_range
                    else:
                        last_profit_range = profit_range
                    
                    last_offset_dict[symbol_pair]=offset
                    last_profit_dict[symbol_pair]=profit_range
                    plot_exchangeAB(session,"bitmex","bids","bitmex","bids",symbol_pair,start_date_str=Start_date_str,offset=offset,profit_range=profit_range)
                    # plot_exchangeAB(session,"bitmex","bids","bitmex","bids","ETHUU",start_date_str=Start_date_str,end_date_str="20190729T00:00:00",offset=offset,profit_range=profit_range)
                    # plot_exchangeAB(session,"bitmex","bids","bitmex","bids","BTCUZ",start_date_str=Start_date_str,offset=offset,profit_range=profit_range)
                # plot_exchangeAB(session,"bitmex","bids","bitmex","bids","BTCUZ",start_date_str="2019-06-20T00:00:00")
                # plot_exchangeAB(session,"bitmex","bids","bitmex","bids","BTCMU",start_date_str=Start_date_str)
                # plot_exchangeAB(session,"bitmex","asks","binance","bids","ETH",start_date_str=Start_date_str)
                # plot_exchangeAB(session,"bitmex","bids","bitmex","bids","BTCXM",start_date_str=Start_date_str)
                # plot_exchangeAB(session,"bitmex","bids","bitmex","bids","BTCXU",start_date_str=Start_date_str)
                # plot_exchangeAB(session,"bitmex","asks","binance","bids","EOS",start_date_str=Start_date_str)
                # plot_exchangeAB(session,"bitmex","asks","binance","bids","LTC",start_date_str=Start_date_str)
            scp_file_to_remote(['ETHUU','ETH','BTCMU','BTCXU','BTCUZ','BTCZH','BTCZH_OFFSET','BTCZH_HIST','BTCZH_HIST_OFFSET','BTCXM','EOS','LTC','ETHUU_HIST','ETH_HIST','BTCMU_HIST','BTCXU_HIST','BTCUZ_HIST','BTCXM_HIST','EOS_HIST','LTC_HIST','ETHUU_OFFSET','ETH_OFFSET','BTCMU_OFFSET','BTCXU_OFFSET','BTCUZ_OFFSET','BTCXM_OFFSET','EOS_OFFSET','LTC_OFFSET','ETHUU_HIST_OFFSET','ETH_HIST_OFFSET','BTCMU_HIST_OFFSET','BTCXU_HIST_OFFSET','BTCUZ_HIST_OFFSET','BTCXM_HIST_OFFSET','EOS_HIST_OFFSET','LTC_HIST_OFFSET'])
            print(datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
            sleep_sec=0
            out_while=False
            while sleep_sec < 60*60*0.1:
                time.sleep(10)
                sleep_sec += 1
                for symbol_pair in ["BTCUZ","ETHUU","BTCZH"]:
                    new_offset = get_diff_offset_online(symbol_pair)
                    new_profit = get_profit_range_online(symbol_pair)
                    if new_offset != last_offset_dict[symbol_pair]:
                        print(datetime.now().strftime("%Y-%m-%dT%H:%M:%S")+"-----[{SymbolPair}] offset change,from {LastOffset}-->{NewOffset},\nreplot!!!".format(SymbolPair=symbol_pair,LastOffset=last_offset_dict[symbol_pair],NewOffset=new_offset))
                        out_while=True
                    elif new_profit != last_profit_dict[symbol_pair]:
                        print(datetime.now().strftime("%Y-%m-%dT%H:%M:%S")+"-----[{SymbolPair}] offset change,from {LastProfit}-->{NewProfit},\nreplot!!!".format(SymbolPair=symbol_pair,LastProfit=last_profit_dict[symbol_pair],NewProfit=new_profit))
                        out_while=True
                if out_while:
                    break
            # time.sleep(10000)
        except Exception as e:
            print(traceback.format_exc())
            time.sleep(60*10)
            pass

if __name__ == "__main__":
    # main()

    with Session() as session:
        Start_date_str = (datetime.now().astimezone(timezone(timedelta(hours=0)))-timedelta(days=38,hours=12)).strftime("%Y-%m-%dT%H:%M:00") 
        for symbol_pair in ["BTCUZ"]:
            offset = get_diff_offset_online(symbol_pair)
            profit_range = get_profit_range_online(symbol_pair)
            print(offset,profit_range)
            
            plot_exchangeAB(session,"bitmex","bids","bitmex","bids",symbol_pair,start_date_str="2019-06-22T00:00:00",end_date_str="2019-09-16T00:00:00",offset=offset,profit_range=profit_range)
    # scp_file_to_remote(["BTCUZ","BTCUZ_OFFSET"],subdir="tt7")