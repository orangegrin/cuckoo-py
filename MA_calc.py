
import datetime 
import time
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

 

def calc_latest_diff_data(session,exchangeA,akey,exchangeB,bkey,symbol,latest_days=4):
    
    start_date_str = (datetime.datetime.now()-datetime.timedelta(days=latest_days,hours=12)).strftime("%Y%m%d %H:%M:00") 
    f = gen_plot_datafram(session,exchangeA,akey,exchangeB,bkey,symbol,start_date_str)
    print(start_date_str)

    data_list = [i for i in list(f.to_dict().items()) if i[0].strftime("%Y%m%d#%H:%M:%S")[-2:]=="00"]
    vals = [i[1] for i in data_list]
    index = [i[0] for i in data_list]
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

if __name__ == "__main__":

    from sqlalchemy.engine.url import URL
    from sqlalchemy import create_engine,and_
    from sqlalchemy.orm import sessionmaker
    import traceback,time
    from db.model import Base, SessionContextManager,BKQuoteOrder
    while True:
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
            calc_latest_diff_data(session,'bitmex','asks','binance','bids','ETH',latest_days=4)
            calc_latest_diff_data(session,'bitmex','asks','binance','bids','EOS',latest_days=4)
            calc_latest_diff_data(session,'bitmex','asks','binance','bids','LTC',latest_days=4)
            calc_latest_diff_data(session,'bitmex','asks','binance','bids','XRP',latest_days=4)
        # time.sleep(1)
        # with Session() as session:
        #     fetch_latest_diff_data(session,'bitmex','binance','ETH')
        print("Calc spend: {} s"%time.time() - start_tick)
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        print("---------------------------------------------------------")
        print("sleep 40 mins......")
        time.sleep(40*60)
    