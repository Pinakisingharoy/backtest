# from sqlalchemy.orm import declarative_base
# from sqlalchemy import Column
# from sqlalchemy import Integer
# from sqlalchemy import Float
# from sqlalchemy import String
# from sqlalchemy import DateTime
# from sqlalchemy.dialects.postgresql import JSONB

# Base = declarative_base()


# class MarketData(Base):

#     __tablename__ = "market_data"

#     id = Column(Integer, primary_key=True)

#     user_id = Column(String)

#     exchange = Column(String)

#     token = Column(String)

#     trading_symbol = Column(String)

#     instrument_type = Column(String)

#     ltp = Column(Float)

#     volume = Column(Integer)

#     open_interest = Column(Integer)

#     bid_price = Column(Float)

#     ask_price = Column(Float)

#     exchange_time = Column(DateTime)

#     received_at = Column(DateTime)

#     raw_data = Column(JSONB)

from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, Float, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()


class BacktestData(Base):
    __tablename__ = "backtest_data"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(String)
    exchange = Column(String)
    token = Column(String)
    trading_symbol = Column(String)
    instrument_type = Column(String)

    ltp = Column(Float)
    volume = Column(Integer)
    open_interest = Column(Integer)

    bid_price = Column(Float)
    ask_price = Column(Float)

    exchange_time = Column(DateTime)
    received_at = Column(DateTime)

    raw_data = Column(JSONB)