from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from enum import Enum

class TradeStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"

class TradeBase(BaseModel):
    symbol: str
    entry_price: float
    quantity: int
    strategy_name: str

class TradeCreate(TradeBase):
    entry_time: datetime
    trade_id: str

class TradeResponse(TradeBase):
    id: int
    trade_id: str
    entry_time: datetime
    status: TradeStatus
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    profit_loss: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True

class StrategyRunRequest(BaseModel):
    symbol: Optional[str] = None
    lookback: int = 10
    quantity: int = 1
    strategy_name: str = "LongBreakout"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class StrategyRunResponse(BaseModel):
    message: str
    trades_generated: int
    trades: List[TradeResponse]
    trades: List[TradeResponse]