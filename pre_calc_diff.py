
import time
import pandas as pd

from db.model import PreDiff
from plot_figure import Session,gen_plot_datafram,get_MAs

def get_pre_diff(session,exchangeA,akey,exchangeB,bkey,symbol,start_date_str):
    # exchangeB/exchangeA - 1

    # start_date_str = (datetime.now().astimezone(timezone(timedelta(hours=0)))-timedelta(days=latest_days,hours=12)).strftime("%Y-%m-%dT%H:%M:00") 
    print(start_date_str)
    f = gen_plot_datafram(session,exchangeA,akey,exchangeB,bkey,symbol,start_date_str)
    # f = f.resample('1min',closed='left',label='left').mean()

def save_prediff_to_db(session,df):
    for i in range(len(df.index)):
        ts = df.index[i]
        diff = df.at[ts]