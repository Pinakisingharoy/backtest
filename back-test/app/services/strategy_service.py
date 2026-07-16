import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional, Dict
import uuid
import logging

from app import models
from app.schemas import TradeCreate

logger = logging.getLogger(__name__)

class StrategyService:
    def __init__(self, db: Session):
        self.db = db

    def run_strategy_for_symbol(self, symbol: str, lookback: int, quantity: int, strategy_name: str,
                                start_date: Optional[datetime] = None,
                                end_date: Optional[datetime] = None) -> List[TradeCreate]:
        trades = []
        query = self.db.query(models.MarketData).filter(
            models.MarketData.trading_symbol == symbol
        )
        # NOTE: Since there is no date column, we cannot filter by date.
        # We'll ignore start_date and end_date for now.
        # Instead, we order by id (assuming chronological insertion).
        candles = query.order_by(models.MarketData.id).all()   # <-- order by id

        if len(candles) < lookback + 1:
            logger.info(f"Not enough candles for {symbol} (need {lookback+1}, got {len(candles)})")
            return trades

        for i in range(lookback, len(candles)):
            current = candles[i]
            prev_candles = candles[i - lookback:i]
            highest_prev = max(c.ltp for c in prev_candles)
            if current.ltp > highest_prev:
                trade_id = f"{strategy_name}_{symbol}_{i}_{uuid.uuid4().hex[:6]}"
                trade = TradeCreate(
                    symbol=symbol,
                    entry_price=current.ltp,
                    quantity=quantity,
                    strategy_name=strategy_name,
                    entry_time=datetime.now(),   # no entry_time from data, use current time
                    trade_id=trade_id
                )
                trades.append(trade)
        return trades

    def save_trades(self, trade_creates: List[TradeCreate]) -> List[models.Trade]:
        saved = []
        for tc in trade_creates:
            trade = models.Trade(
                trade_id=tc.trade_id,
                symbol=tc.symbol,
                entry_time=tc.entry_time,
                entry_price=tc.entry_price,
                quantity=tc.quantity,
                strategy_name=tc.strategy_name,
                status=models.TradeStatus.OPEN
            )
            self.db.add(trade)
            saved.append(trade)
        self.db.commit()
        for t in saved:
            self.db.refresh(t)
        return saved

    def run_strategy(self, request) -> Dict:
        symbols_to_run = []
        if request.symbol:
            symbols_to_run = [request.symbol]
        else:
            symbols = self.db.query(models.MarketData.trading_symbol).distinct().all()
            symbols_to_run = [s[0] for s in symbols if s[0]]

        if not symbols_to_run:
            return {'trades_generated': 0, 'trades': []}

        all_trades = []
        for sym in symbols_to_run:
            trades = self.run_strategy_for_symbol(
                sym,
                lookback=request.lookback,
                quantity=request.quantity,
                strategy_name=request.strategy_name,
                start_date=request.start_date,
                end_date=request.end_date
            )
            all_trades.extend(trades)

        saved_trades = self.save_trades(all_trades)
        return {
            'trades_generated': len(saved_trades),
            'trades': saved_trades
        }