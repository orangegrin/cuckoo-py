import asyncio
import os
import datetime 
from datetime import datetime,timezone,timedelta
import sys
import pprint
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ccxt.async_support as ccxt  # noqa: E402
from sqlalchemy.engine.url import URL
from sqlalchemy import create_engine,and_
from sqlalchemy.orm import sessionmaker
from db.model import Base, SessionContextManager,BKQuoteOrder
import traceback,time
import mplcursors
import matplotlib.pyplot as plt
import pandas as pd
import numpy
from matplotlib import pyplot
import talib
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
    "bitmex":{"ETH":"ETHM19","EOS":"EOSM19","XRP":"XRPM19","LTC":"LTCM19"},
    "binance":{"ETH":"ETH/BTC","EOS":"EOS/BTC","XRP":"XRP/BTC","LTC":"LTC/BTC"},
    "gateio":{"ETH":"ETH/BTC","EOS":"EOS/BTC","XRP":"XRP/BTC","LTC":"LTC/BTC"},
    "okex":{"ETH":"ETH/BTC","EOS":"EOS/BTC","XRP":"XRP/BTC","LTC":"LTC/BTC"},
    "fcoin":{"ETH":"ETH/BTC","EOS":"EOS/BTC","XRP":"XRP/BTC","LTC":"LTC/BTC"}
}

def self_reindex(bitmex_l,akey,binance_l,bkey):
    # dkey: 'asks'
    tzutc_8 = timezone(timedelta(hours=8))
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

def gen_plot_datafram(session,exchangeA,akey,exchangeB,bkey,symbol,start_date_str="20190409 00:00:00",end_data_str=None):
    # exchangeA,exchangeB "bitmex","binance"
    # akey,bkey "asks","bids"
    # exchangeA[akey],exchangeB[bkey] 
    # 
    if not end_data_str:
        end_data_str = datetime.fromtimestamp(time.time()).strftime("%Y%m%d %H:%M:%S") 
    bitmex = session.query(BKQuoteOrder).filter_by(exchange=exchangeA,symbol=SYMBOL_MAP[exchangeA][symbol]).filter(and_(BKQuoteOrder.timestamp>=start_date_str,BKQuoteOrder.timestamp<=end_data_str)).order_by(BKQuoteOrder.timestamp.asc()).all()
    binance = session.query(BKQuoteOrder).filter_by(exchange=exchangeB,symbol=SYMBOL_MAP[exchangeB][symbol]).filter(and_(BKQuoteOrder.timestamp>=start_date_str,BKQuoteOrder.timestamp<=end_data_str)).order_by(BKQuoteOrder.timestamp.asc()).all()
    
    bitmex_l = [x.to_dict() for x in bitmex]
    binance_l = [x.to_dict() for x in binance]

    print(len(bitmex_l))
    print(len(binance_l))
    print("------------------")
    if (binance_l == [] and bitmex_l == []):
        print('\nNo data found in selected time range!!!\n')
        return None

    bitmex0=datetime.strptime(start_date_str,'%Y%m%d %H:%M:%S')
    binance0=datetime.strptime(start_date_str, '%Y%m%d %H:%M:%S')
    if bitmex_l:
        bitmex0 = bitmex_l[0]['timestamp'].replace(microsecond=0)
    if binance_l:
        binance0 = binance_l[0]['timestamp'].replace(microsecond=0)

    if binance0>bitmex0 or binance_l == []:
        binance_tmp = session.query(BKQuoteOrder).filter_by(exchange=exchangeB,symbol=SYMBOL_MAP[exchangeB][symbol]).filter(and_(BKQuoteOrder.timestamp<=start_date_str)).order_by(BKQuoteOrder.timestamp.desc()).limit(1).all()
        tmp_item1,tmp_item2 = binance_tmp[0].to_dict(),binance_tmp[0].to_dict()
        tmp_item1['timestamp'] = bitmex0
        tmp_item2['timestamp'] = bitmex0 + timedelta(seconds=1)
        if binance_l == []:
            binance_l = [tmp_item2]
        binance_l = [tmp_item1]+binance_l

    if binance0<bitmex0 or bitmex_l == []:
        bitmex_tmp = session.query(BKQuoteOrder).filter_by(exchange=exchangeA,symbol=SYMBOL_MAP[exchangeA][symbol]).filter(and_(BKQuoteOrder.timestamp<=start_date_str)).order_by(BKQuoteOrder.timestamp.desc()).limit(1).all()
        tmp_item1,tmp_item2 = bitmex_tmp[0].to_dict(),bitmex_tmp[0].to_dict()
        tmp_item1['timestamp'] = binance0
        tmp_item2['timestamp'] = binance0 + timedelta(seconds=1)
        if bitmex_l == []:
            bitmex_l = [tmp_item2]
        bitmex_l = [tmp_item1]+bitmex_l
    
    print(len(bitmex_l))
    print(len(binance_l))
    
    df_reindexed_bitmex,df_reindexed_binance = self_reindex(bitmex_l,'asks',binance_l,'bids')
    
    df_reindexed_bitmex = df_reindexed_bitmex.fillna(method='pad')
    df_reindexed_binance = df_reindexed_binance.fillna(method='pad')
    # print(df_reindexed_binance)
    # print(df_reindexed_bitmex)
    f = df_reindexed_binance/df_reindexed_bitmex-1
    
    return f

def get_MAs(data_list, timeperiods):
    MAs = []
    for timeperiod in timeperiods:
        MAs.append(talib.MA(data_list, timeperiod=timeperiod, matype=0))
    return MAs

def plot_figure(f,exchangeA,akey,exchangeB,bkey,symbol):
    
    print("########MA-CALC########")
    
    data_list = [i for i in list(f.to_dict().items()) if i[0].strftime("%Y%m%d#%H:%M:%S")[-2:]=="00"]
    vals = [i[1] for i in data_list]
    index = [i[0] for i in data_list]
    MAs = get_MAs(numpy.array(vals),[1440, 1440*2, 1440*3, 1440*4])
    MA_AVG=[]
    for i in zip(*MAs):
        if all(i):
            MA_AVG.append(sum(i)/len(i))
        else:
            MA_AVG.append(0)
    # MA_AVG = [sum(i)/len(i) for i in zip(*MAs) if any(i) else 0]
    min_based_df=pd.DataFrame({'Diff':vals,'MA1':MAs[0],'MA2':MAs[1],'MA3':MAs[2],'MA4':MAs[3],'MA_AVG':MA_AVG},index=index)
    min_based_df.fillna(value=0)
    print(len(data_list))
    print([len(i) for i in MAs])
    # min_based_df.plot()
    raw_df = pd.DataFrame(f)
    print(raw_df)
    final_df = raw_df.join(min_based_df)
    

    plt.subplot(211)
    print(index[50],MA_AVG[50])
    maxid = f.idxmax()
    minid = f.idxmin()
    print(maxid,minid)
    
    
    fig = min_based_df.plot()
    up_marker,down_marker = [],[]
    for idx in range(1,len(MA_AVG)):
        if MA_AVG[idx] and MA_AVG[idx-1]:
            if MA_AVG[idx-1]+0.004 < vals[idx]:
                up_marker.append([index[idx],vals[idx]])
            elif MA_AVG[idx-1]-0.004 > vals[idx]:
                down_marker.append([index[idx],vals[idx]])
    for i in up_marker:
        plt.scatter(i[0],i[1],s=40,c="red",marker="p")
    for i in down_marker:
        plt.scatter(i[0],i[1],s=40,c="green",marker="p")
    # plt.annotate('max({t},{v})'.format(t = maxid,v=f[maxid]), xy=(maxid, f[maxid]),arrowprops=dict(facecolor='black', shrink=0.05))
    plt.axhline(y=f[maxid],linestyle="--",color="gray")
    plt.text(maxid,f[maxid],'max({t},{v})'.format(t = maxid.strftime("%Y%m%d#%H:%M:%S") ,v=f[maxid]))
    # plt.annotate('min({t},{v})'.format(t = minid,v=f[minid]), xy=(minid, f[minid]),arrowprops=dict(facecolor='black', shrink=0.05))
    plt.axhline(y=f[minid],linestyle="--",color="gray")
    plt.text(minid,f[minid],'min({t},{v})'.format(t = minid.strftime("%Y%m%d#%H:%M:%S") ,v=f[minid]))
    
    plt.xlabel("Timestamp")
    plt.ylabel("Percent")
    plt.title("{symbol}---{EB}[{BK}]/{EA}[{AK}]-1".format(symbol=symbol,EA=exchangeA,AK=akey,EB=exchangeB,BK=bkey))
    mplcursors.cursor(fig)
    plt.subplots_adjust(hspace=1)
    pyplot.show()

def plot_exchangeAB(session,exchangeA,akey,exchangeB,bkey,symbol,start_date_str="20190411 18:00:00",end_data_str=None):
    f = gen_plot_datafram(session,exchangeA,akey,exchangeB,bkey,symbol,start_date_str=start_date_str,end_data_str=end_data_str)
    
    
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
    plot_figure(f,exchangeA,akey,exchangeB,bkey,symbol)

if __name__ == "__main__":

    with Session() as session:
        
        plot_exchangeAB(session,"bitmex","asks","binance","bids","XRP",start_date_str="20190429 00:00:00")
        plot_exchangeAB(session,"bitmex","asks","binance","bids","ETH",start_date_str="20190429 00:00:00")
        plot_exchangeAB(session,"bitmex","asks","binance","bids","EOS",start_date_str="20190429 00:00:00")
        plot_exchangeAB(session,"bitmex","asks","binance","bids","LTC",start_date_str="20190429 00:00:00")