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
from db.model import Base, SessionContextManager,BKQuoteOrder,IQuoteOrder,TradeHistory
import traceback,time
import mplcursors
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import pandas as pd
from pandas.plotting import register_matplotlib_converters
import numpy
from matplotlib import pyplot
from matplotlib.pyplot import figure
figure(num=None, figsize=(80, 60), dpi=100, facecolor='w', edgecolor='k')
import talib
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
    "bitmex":{"ETH":"ETHM19","EOS":"EOSM19","XRP":"XRPM19","LTC":"LTCM19","BTCM":"XBTM19","BTCU":"XBTU19","BTCX":"XBTUSD"},
    "binance":{"ETH":"ETH/BTC","EOS":"EOS/BTC","XRP":"XRP/BTC","LTC":"LTC/BTC"},
    "gateio":{"ETH":"ETH/BTC","EOS":"EOS/BTC","XRP":"XRP/BTC","LTC":"LTC/BTC"},
    "okex":{"ETH":"ETH/BTC","EOS":"EOS/BTC","XRP":"XRP/BTC","LTC":"LTC/BTC"},
    "fcoin":{"ETH":"ETH/BTC","EOS":"EOS/BTC","XRP":"XRP/BTC","LTC":"LTC/BTC"}
}

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

def gen_plot_datafram(session,exchangeA,akey,exchangeB,bkey,symbol,start_date_str="20190409T00:00:00",end_data_str=None):
    # exchangeA,exchangeB "bitmex","binance"
    # akey,bkey "asks","bids"
    # exchangeA[akey],exchangeB[bkey] 
    # BTCXU --> BTCX/BTCU
    # BTCMU --> BTCM/BTCU 
    raw_symbol = symbol
    if not end_data_str:
        end_data_str = datetime.fromtimestamp(time.time()).strftime("%Y-%m-%dT%H:%M:%S") 
    if raw_symbol.startswith('BTC'):
        symbol='BTC'+raw_symbol[4]
    
    bitmex = session.query(BKQuoteOrder).filter_by(exchange=exchangeA,symbol=SYMBOL_MAP[exchangeA][symbol]).filter(and_(BKQuoteOrder.timesymbol>=start_date_str,BKQuoteOrder.timesymbol<=end_data_str)).order_by(BKQuoteOrder.timesymbol.asc()).all()
    if raw_symbol.startswith('BTC'):
        symbol='BTC'+raw_symbol[3]
    binance = session.query(BKQuoteOrder).filter_by(exchange=exchangeB,symbol=SYMBOL_MAP[exchangeB][symbol]).filter(and_(BKQuoteOrder.timesymbol>=start_date_str,BKQuoteOrder.timesymbol<=end_data_str)).order_by(BKQuoteOrder.timesymbol.asc()).all()
    
    bitmex_l = [x.to_dict() for x in bitmex]
    binance_l = [x.to_dict() for x in binance]

    print(len(bitmex_l))
    print(len(binance_l))
    print("------------------")
    if (binance_l == [] and bitmex_l == []):
        print('\nNo data found in selected time range!!!\n')
        return None

    bitmex0=datetime.strptime(start_date_str,'%Y-%m-%dT%H:%M:%S')
    binance0=datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M:%S')
    if bitmex_l:
        bitmex0 = bitmex_l[0]['timestamp'].replace(microsecond=0)
    if binance_l:
        binance0 = binance_l[0]['timestamp'].replace(microsecond=0)

    if binance0>bitmex0 or binance_l == []:
        binance_tmp = session.query(BKQuoteOrder).filter_by(exchange=exchangeB,symbol=SYMBOL_MAP[exchangeB][symbol]).filter(and_(BKQuoteOrder.timesymbol<=start_date_str)).order_by(BKQuoteOrder.timesymbol.desc()).limit(1).all()
        tmp_item1,tmp_item2 = binance_tmp[0].to_dict(),binance_tmp[0].to_dict()
        tmp_item1['timestamp'] = bitmex0
        tmp_item2['timestamp'] = bitmex0 + timedelta(seconds=1)
        if binance_l == []:
            binance_l = [tmp_item2]
        binance_l = [tmp_item1]+binance_l

    if binance0<bitmex0 or bitmex_l == []:
        bitmex_tmp = session.query(BKQuoteOrder).filter_by(exchange=exchangeA,symbol=SYMBOL_MAP[exchangeA][symbol]).filter(and_(BKQuoteOrder.timesymbol<=start_date_str)).order_by(BKQuoteOrder.timesymbol.desc()).limit(1).all()
        tmp_item1,tmp_item2 = bitmex_tmp[0].to_dict(),bitmex_tmp[0].to_dict()
        tmp_item1['timestamp'] = binance0
        tmp_item2['timestamp'] = binance0 + timedelta(seconds=1)
        if bitmex_l == []:
            bitmex_l = [tmp_item2]
        bitmex_l = [tmp_item1]+bitmex_l
    
    print(len(bitmex_l))
    print(len(binance_l))
    
    df_reindexed_bitmex,df_reindexed_binance = self_reindex(bitmex_l,akey,binance_l,bkey)
    
    df_reindexed_bitmex = df_reindexed_bitmex.fillna(method='pad')
    df_reindexed_binance = df_reindexed_binance.fillna(method='pad')
  
    f = df_reindexed_binance/df_reindexed_bitmex-1
    
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

def plot_figure(session,f,exchangeA,akey,exchangeB,bkey,symbol):
    
    print("########MA-CALC########")
    register_matplotlib_converters()
    
    # data_list = [i for i in list(f.to_dict().items()) if i[0].strftime("%Y-%m-%dT%H:%M:%S")[-2:]=="00"]
    f =  f.resample('1min',closed='left',label='left').mean() 
    data_list = [i for i in list(f.to_dict().items())] 
    vals = [i[1] for i in data_list]
    index = [i[0] for i in data_list]
    
    #calc MAs and MA_avg
    fig = plt.figure(figsize=(48,27))
    df_axes=fig.add_subplot(211)
    df2_axes=fig.add_subplot(212)
    min_based_df=None
    if True:
        MAs = get_MAs(numpy.array(vals),[1440, 1440*2, 1440*3, 1440*4])
        # MAs = get_EMAs(numpy.array(vals),[1440, 1440*2, 1440*3, 1440*4])
        MA_AVG=[]
        for i in zip(*MAs):
            if all(i):
                MA_AVG.append(sum(i)/len(i))
            else:
                MA_AVG.append(0)
        # MA_AVG = [sum(i)/len(i) for i in zip(*MAs) if any(i) else 0]
        # min_based_df=pd.DataFrame({'Diff':vals,'EMA1':MAs[0],'EMA2':MAs[1],'EMA3':MAs[2],'EMA4':MAs[3],'EMA_AVG':MA_AVG},index=index)
        min_based_df=pd.DataFrame({'Diff':vals,'MA1':MAs[0],'MA2':MAs[1],'MA3':MAs[2],'MA4':MAs[3],'MA_AVG':MA_AVG},index=index)

    
        min_based_df.fillna(value=0)
        print(len(data_list))
        print([len(i) for i in MAs])
        df_axes = min_based_df.plot(figsize=(16, 9),ax=df_axes)
        
 
    maxid = f.idxmax()
    minid = f.idxmin()
    print(maxid,minid)

    

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
        up_marker,down_marker = [],[]
        for idx in range(1,len(MA_AVG)):
            if MA_AVG[idx] and MA_AVG[idx-1]:
                if MA_AVG[idx-1]+0.002 < vals[idx]:
                    up_marker.append([index[idx],vals[idx]])
                elif MA_AVG[idx-1]-0.002 > vals[idx]:
                    down_marker.append([index[idx],vals[idx]])
        for i in up_marker:
            df_axes.scatter(i[0],i[1],s=40,c="red",marker="p")
        for i in down_marker:
            df_axes.scatter(i[0],i[1],s=40,c="green",marker="p")
        custom_legend_marks.append(Line2D([0], [0], marker='o', color='w',markerfacecolor='green', markersize=15))
        custom_legend_marks.append(Line2D([0], [0], marker='o', color='w',markerfacecolor='red', markersize=15))
        custom_legend_labels += ["Predict trade point"]*2


    #plot real trade point
    if symbol=='BTCMU':
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
    if True:
        df_axes.annotate('max({t},{v})'.format(t = maxid,v='{:.8f}'.format(f[maxid])), xy=(maxid, f[maxid]),arrowprops=dict(facecolor='black', shrink=0.05))
        df_axes.axhline(y=f[maxid],linestyle="--",color="gray")
        # df_axes.text(maxid,f[maxid],'max({t},{v})'.format(t = maxid.strftime("%m%d#%H:%M:%S") ,v=f[maxid]))

        df_axes.annotate('min({t},{v})'.format(t = minid,v='{:.8f}'.format(f[minid])), xy=(minid, f[minid]),arrowprops=dict(facecolor='black', shrink=0.05))
        df_axes.axhline(y=f[minid],linestyle="--",color="gray")
        # df_axes.text(minid,f[minid],'min({t},{v})'.format(t = minid.strftime("%m%d#%H:%M:%S") ,v=f[minid]))
    
    if custom_legend_marks:
        legend1 = pyplot.legend(custom_legend_marks, custom_legend_labels)
        df2_axes.add_artist(legend1)
        # plt.legend(custom_legend_marks, custom_legend_labels)
    plt.title("{symbol}---{EB}[{BK}]/{EA}[{AK}]-1".format(symbol=symbol,EA=exchangeA,AK=akey,EB=exchangeB,BK=bkey))
    # mplcursors.cursor(fig)
    plt.subplots_adjust(hspace=1)
    
    dst_file = "./figure/"+'-'.join([exchangeA,exchangeB,symbol,datetime.now().strftime("%Y-%m-%dT%H%M%S")])+".png"
    plt.savefig(dst_file)
    shutil.copyfile(dst_file,"./figure/"+symbol.upper()+".png")
    # fig.show()

def plot_exchangeAB(session,exchangeA,akey,exchangeB,bkey,symbol,start_date_str="20190411 18:00:00",end_data_str=None):
    
    f = gen_plot_datafram(session,exchangeA,akey,exchangeB,bkey,symbol,start_date_str=start_date_str,end_data_str=end_data_str)
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

    plot_figure(session,f,exchangeA,akey,exchangeB,bkey,symbol)

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

def get_trade_point_from_csv(csv = 'test\TradeHistory(symbol=EOSM19)2019-4-17.csv'):
    
    ret = []
    df = pd.read_csv(csv)
    for idx in range(len(df['transactTime'])):
        datetimes = datetime.strptime(df['transactTime'][idx], '%Y/%m/%d %p%I:%M:%S')
        ret.append({"timestamp":datetimes,'value':df['price'][idx],'side':df['side'][idx]})
    return ret

def scp_file_to_remote(upfiles):
    import paramiko
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # ssh.connect('198.13.38.21', 22, 'ray','yqll125321,.')
    ssh.connect('150.109.52.225', 22, 'ray',key_filename='./figure/id_rsa')

    ftp_client=ssh.open_sftp()
    [ftp_client.put('./figure/{fig_name}.png'.format(fig_name=img_name),'/home/ray/web/figure/{fig_name}.png'.format(fig_name=img_name)) for img_name in upfiles]
    ftp_client.close()
    ssh.close()

if __name__ == "__main__":
    
    # get_binance_kline_data('ETHBTC',start_time=1557569880000)
    # ret = get_bitmex_kline_data('ETHM19',start_time=datetime(2019,5,11,0,0))
    # print(len(ret))
    # get_trade_point_from_bitmex('ETHM19')
    
    while True:
        try:
            with Session() as session:
                Start_date_str = (datetime.now().astimezone(timezone(timedelta(hours=0)))-timedelta(days=11,hours=12)).strftime("%Y-%m-%dT%H:%M:00") 
                plot_exchangeAB(session,"bitmex","asks","binance","bids","ETH",start_date_str=Start_date_str)
                plot_exchangeAB(session,"bitmex","bids","bitmex","bids","BTCXM",start_date_str=Start_date_str)
                plot_exchangeAB(session,"bitmex","bids","bitmex","bids","BTCMU",start_date_str=Start_date_str)
                plot_exchangeAB(session,"bitmex","bids","bitmex","bids","BTCXU",start_date_str=Start_date_str)
                plot_exchangeAB(session,"bitmex","asks","binance","bids","EOS",start_date_str=Start_date_str)
                plot_exchangeAB(session,"bitmex","asks","binance","bids","LTC",start_date_str=Start_date_str)

            scp_file_to_remote(['ETH','BTCMU','BTCXU','BTCXM','EOS','LTC'])
            print(datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
            time.sleep(60*60*2)
        except Exception:
            
            time.sleep(60*10)
            pass
    