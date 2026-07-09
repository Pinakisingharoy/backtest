from sqlalchemy import Column, Integer, String, Float, DateTime, BigInteger, Index, Text, Enum
from sqlalchemy.sql import func
from app.database import Base
import enum

class TradeStatus(enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"

class MarketData(Base):
    __tablename__ = "backtest_data"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50))
    exchange = Column(String(20))
    token = Column(String(50))
    trading_symbol = Column(String(50), index=True)
    instrument_type = Column(String(30))
    ltp = Column(Float)
    volume = Column(BigInteger)
    open_interest = Column(BigInteger)
    bid_ask = Column(BigInteger)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    date = Column(DateTime(timezone=True))
    
    __table_args__ = (Index('idx_symbol_date', 'trading_symbol', 'date'),)

class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(String(50), unique=True, index=True)
    symbol = Column(String(50), index=True)
    entry_time = Column(DateTime(timezone=True), nullable=False)
    entry_price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    strategy_name = Column(String(50), nullable=False)
    status = Column(Enum(TradeStatus), default=TradeStatus.OPEN)
    exit_time = Column(DateTime(timezone=True), nullable=True)
    exit_price = Column(Float, nullable=True)
    profit_loss = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())