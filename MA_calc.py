
import datetime 
import time
from decimal import Decimal
from db.model import Base, SessionContextManager,BKQuoteOrder,LPriceDiff
import pandas as pd
import numpy as np
from plot_figure import gen_plot_datafram,get_MAs
SYMBOL_MAP={
    "bitmex":{"ETH":"ETHM19","EOS":"EOSM19","XRP":"XRPM19","LTC":"LTCM19"},
    "binance":{"ETH":"ETH/BTC","EOS":"EOS/BTC","XRP":"XRP/BTC","LTC":"LTC/BTC"},
    "gateio":{"ETH":"ETH/BTC","EOS":"EOS/BTC","XRP":"XRP/BTC","LTC":"LTC/BTC"},
    "okex":{"ETH":"ETH/BTC","EOS":"EOS/BTC","XRP":"XRP/BTC","LTC":"LTC/BTC"},
    "fcoin":{"ETH":"ETH/BTC","EOS":"EOS/BTC","XRP":"XRP/BTC","LTC":"LTC/BTC"}
}

def tv_data_fetch(session,exchangeA,akey,exchangeB,bkey,symbol,resolution,start_timestamp,end_timestamp):
    data_begin_timestamp = 1555372800 #20190416T00:00:00
    start_timestamp,end_timestamp = int(start_timestamp),int(end_timestamp)
    if end_timestamp < data_begin_timestamp:
        return None
    start_date_str = (datetime.datetime.fromtimestamp(start_timestamp)).strftime("%Y%m%d %H:%M:00") 
    end_date_str = (datetime.datetime.fromtimestamp(end_timestamp)).strftime("%Y%m%d %H:%M:00") 
    f = gen_plot_datafram(session,exchangeA,akey,exchangeB,bkey,symbol,start_date_str,end_date_str)
    if resolution in ['1','3','5','15','30']:
        f = f.resample(resolution+'min',closed='left',label='left').mean()
    elif resolution in ['1H','2H','3H','4H','6H','12H','1D','3D','1W','2W','1M']:
        f = f.resample(resolution,closed='left',label='left').mean()
    elif resolution in ['1s','2s','3s','4s','5s','10s']:
        f = f.resample(resolution,closed='left',label='left').mean()
    
    ret_body = {"t":[int(t.timestamp()) for t in f.index],"o":[(float(Decimal('%.5f' % val).quantize(Decimal('0.00000')))) for val in list(f.values)]}
    return ret_body

def calc_latest_diff_data(session,exchangeA,akey,exchangeB,bkey,symbol,latest_days=4):
    
    start_date_str = (datetime.datetime.now()-datetime.timedelta(days=latest_days,hours=12)).strftime("%Y%m%d %H:%M:00") 
    f = gen_plot_datafram(session,exchangeA,akey,exchangeB,bkey,symbol,start_date_str)
    print(start_date_str)
    
    # data_list = [i for i in list(f.to_dict().items()) if i[0].strftime("%Y%m%d#%H:%M:%S")[-2:]=="00"]
    data_list = f.resample('1min',closed='left',label='left').mean()
    vals = data_list.values
    index = data_list.index
    print(len(vals),index[:10])
    MAs = get_MAs(np.array(vals),[1440, 1440*2, 1440*3, 1440*4])
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
    res = list(min_based_df.tail(1).to_dict()["MA_AVG"].items())
    print(res)
    timestamp,ma_avg_value = res[0][0],res[0][1]
    if not np.isnan(ma_avg_value):
        print('save:',datetime.datetime.fromtimestamp(timestamp.timestamp()).strftime("%Y%m%d %H:%M:%S"))
        session.add(LPriceDiff(symbol=symbol,exchangepair='/'.join([exchangeA,exchangeB]),value=ma_avg_value,timestamp=datetime.datetime.fromtimestamp(timestamp.timestamp()).strftime("%Y%m%d %H:%M:%S")))
    else:
        print("None")
  
def fetch_latest_diff_data(session,exchangeA,exchangeB,symbol):

    ret = session.query(LPriceDiff).filter_by(symbol=symbol).filter_by(exchangepair='/'.join([exchangeA,exchangeB])).order_by(LPriceDiff.timestamp.desc()).first()
    print(ret)
    if ret:
        return ret.to_dict()
    else:
        return None

def get_rnn_sample_data():
    from sqlalchemy.engine.url import URL
    from sqlalchemy import create_engine,and_
    from sqlalchemy.orm import sessionmaker
    import traceback,time
    from db.model import Base, SessionContextManager,BKQuoteOrder
    if True:
        print("Calc start......")
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
        
        start_tick = time.time()
        with Session() as session:
            # calc_latest_diff_data(session,'bitmex','asks','binance','bids','ETH',latest_days=4)
            # calc_latest_diff_data(session,'bitmex','asks','binance','bids','EOS',latest_days=4)
            # calc_latest_diff_data(session,'bitmex','asks','binance','bids','LTC',latest_days=4)
            # calc_latest_diff_data(session,'bitmex','asks','binance','bids','XRP',latest_days=4)
            f = tv_data_fetch(session,'bitmex','asks','binance','bids','ETH','1s',1555372800,1555459200)
            return f['o']

if __name__ == "__main__":

    from sqlalchemy.engine.url import URL
    from sqlalchemy import create_engine,and_
    from sqlalchemy.orm import sessionmaker
    import traceback,time
    from db.model import Base, SessionContextManager,BKQuoteOrder
    while True:
        print("Calc start......")
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
        
        start_tick = time.time()
        with Session() as session:
            # calc_latest_diff_data(session,'bitmex','asks','binance','bids','ETH',latest_days=4)
            # calc_latest_diff_data(session,'bitmex','asks','binance','bids','EOS',latest_days=4)
            # calc_latest_diff_data(session,'bitmex','asks','binance','bids','LTC',latest_days=4)
            # calc_latest_diff_data(session,'bitmex','asks','binance','bids','XRP',latest_days=4)
            f = tv_data_fetch(session,'bitmex','asks','binance','bids','ETH','1s',1555372800,1555459200)
            print(len(f['o']))
            
        # time.sleep(1)
        # with Session() as session:
        #     fetch_latest_diff_data(session,'bitmex','binance','ETH')
        print("Calc spend: ",time.time() - start_tick)
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("---------------------------------------------------------")
        print("sleep 40 mins......")
        time.sleep(40*60)
    