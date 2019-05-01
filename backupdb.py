import asyncio
import os
import datetime 
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
                        
                
    
