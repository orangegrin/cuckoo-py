
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
import sys
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