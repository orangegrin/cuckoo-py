
from sqlalchemy import (
    ARRAY,
    BigInteger,
    BOOLEAN,
    Column,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    TIMESTAMP,
    cast,
    func,
    literal,
    null,
    text,
    tuple_
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Query, relationship, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData
from sqlalchemy.ext.hybrid import hybrid_property
import sys,time
from multiprocessing import Lock

SCHEMA = 'datastore'
meta = MetaData(schema=SCHEMA)
Base = declarative_base(metadata=meta)

class IQuoteOrder(Base):
    __tablename__ = 'iquoteorder'

    id = Column(Integer, primary_key=True,unique=True, autoincrement='auto')
    timesymbol = Column(String(40),unique=True)
    asks = Column(Float,nullable=False)
    bids = Column(Float,nullable=False)
    exchange = Column(String(16),nullable=False)
    symbol = Column(String(16),nullable=False)
    timestamp = Column(TIMESTAMP(timezone=False), nullable=False)
    

    def to_dict(self):
        properties = ['timesymbol','exchange', 'symbol', 'asks', 'bids','timestamp']
        return {prop: getattr(self, prop, None) for prop in properties}


class LPriceDiff(Base):
    __tablename__ = 'lpricediff'

    id = Column(Integer, primary_key=True,unique=True, autoincrement='auto')
    symbol = Column(String(16),nullable=False)
    exchangepair = Column(String(40), nullable=False)
    value = Column(Float, nullable=False)
    timestamp = Column(TIMESTAMP(timezone=False), nullable=False)
    
    def to_dict(self):
        properties = ['exchangepair', 'symbol','timestamp','value']
        dict_t = {prop: getattr(self, prop, None) for prop in properties}
        dict_t['timestamp'] = int(time.mktime(dict_t['timestamp'].timetuple()))
        return dict_t

class BKQuoteOrder(Base):
    __tablename__ = 'bkquoteorder'

    id = Column(Integer, primary_key=True,unique=True, autoincrement='auto')
    timesymbol = Column(String(40),unique=True)
    asks = Column(Float,nullable=False)
    bids = Column(Float,nullable=False)
    exchange = Column(String(16),nullable=False)
    symbol = Column(String(16),nullable=False)
    timestamp = Column(TIMESTAMP(timezone=False), nullable=False)
    

    def to_dict(self):
        properties = ['timesymbol','exchange', 'symbol', 'asks', 'bids','timestamp']
        return {prop: getattr(self, prop, None) for prop in properties}

class PreDiff(Base):
    __tablename__ = 'prediff'

    id = Column(Integer, primary_key=True,unique=True, autoincrement='auto')
    timepairsymbol = Column(String(40),unique=True)
    diff = Column(Float,nullable=False)
    timestamp = Column(TIMESTAMP(timezone=False), nullable=False)

    def to_dict(self):
        properties = ['timepairsymbol','diff','timestamp']
        return {prop: getattr(self, prop, None) for prop in properties}

class TradeHistory(Base):
    __tablename__ = 'tradehistory'

    id = Column(Integer, primary_key=True,unique=True, autoincrement='auto')
    orderid = Column(String(48), unique=True)
    accountid = Column(Integer, nullable=False)
    symbol = Column(String(16),nullable=False)
    side = Column(String(8),nullable=False)
    price = Column(Float, nullable=False)
    orderqty = Column(Integer, nullable=False)
    extratext = Column(String(128))
    transactTime = Column(TIMESTAMP(timezone=False), nullable=False)
    timestamp = Column(TIMESTAMP(timezone=False), nullable=False)
    
#     def to_dict(self):
#         properties = ['exchangepair', 'symbol','timestamp','value']
#         dict_t = {prop: getattr(self, prop, None) for prop in properties}
#         dict_t['timestamp'] = int(time.mktime(dict_t['timestamp'].timetuple()))
#         return dict_t

class SessionContextManager(Session):

    def __init__(self, *args, raise_commit=True, **kwargs):
        self.raise_commit = raise_commit
        # self.lock = Lock()
        super().__init__(*args, **kwargs)

    def __enter__(self):
        # self.lock.acquire()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not exc_type:
            try:
                self.commit()
            except Exception as e:
                if self.raise_commit:
                    raise e
                else:
                    print(sys.exc_info()[0])
        else:
            self.rollback()
        self.close()
        # self.lock.release() 