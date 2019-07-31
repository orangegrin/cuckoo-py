
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

class OGUser(Base):
    __tablename__ = 'oguser'

    id = Column(Integer, primary_key=True,unique=True, autoincrement='auto')
    username = Column(String(48), unique=True,nullable=False)
    passtoken = Column(String(128),nullable=False)
    extratext = Column(String(128))
    timestamp = Column(TIMESTAMP(timezone=False), nullable=False)

# {"id":"2","programID":60002,"deltaDiff":-0.001,"leverage":3.5,"openPositionBuyA":1,"openPositionSellA":1,"profitRange":{"s":0.001,"e":0.0035},"remark":"ETH正","createTime":"2019-07-01T04:00:00.000Z"}
class ArbitrageProcess(Base):
    __tablename__ = 'arbitrageprocess'

    id = Column(Integer, primary_key=True,unique=True, autoincrement='auto')
    programID = Column(String(48), unique=True)
    deltaDiff = Column(Float, nullable=False)
    leverage = Column(Float, nullable=False)
    openPositionBuyA = Column(Integer,nullable=False)
    openPositionSellA = Column(Integer, nullable=False)
    profitRangeS = Column(Float, nullable=False)
    profitRangeE = Column(Float, nullable=False)
    status = Column(Integer,nullable=False,default=1)
    remark = Column(String(128))
    createTime = Column(TIMESTAMP(timezone=True),nullable=False, server_default=func.now())
    
    def to_dict(self):
        properties = ["id","programID","deltaDiff","leverage","openPositionBuyA","openPositionSellA","profitRangeS","profitRangeE","remark","createTime"]
        pre_dict = {prop: getattr(self, prop, None) for prop in properties}
        pre_dict["profitRange"] = {"s":pre_dict["profitRangeS"],"e":pre_dict["profitRangeE"]}
        pre_dict["createTime"] = pre_dict["createTime"].strftime("%Y-%m-%dT%H:%M:%S")
        pre_dict.pop("profitRangeS")
        pre_dict.pop("profitRangeE")
        return pre_dict

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