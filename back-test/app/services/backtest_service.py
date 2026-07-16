import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import List, Dict, Optional
import uuid
import logging

from app import models
from app.schemas import TradeCreate

logger = logging.getLogger(__name__)

class BacktestService:
    def __init__(self, db: Session):
        self.db = db

    def run_backtest(self, request) -> Dict:
        symbol = request.symbol
        if symbol:
            cleaned = symbol.strip().upper()
            exists = self.db.query(models.MarketData).filter(
                func.lower(func.trim(models.MarketData.trading_symbol)) == cleaned.lower()
            ).first()
            if not exists:
                available = self.db.query(models.MarketData.trading_symbol).distinct().limit(10).all()
                available_list = [s[0] for s in available if s[0]]
                raise ValueError(
                    f"Symbol '{symbol}' not found. Available symbols (first 10): {available_list}"
                )
            symbols_to_test = [cleaned]
        else:
            symbols = self.db.query(models.MarketData.trading_symbol).distinct().all()
            symbols_to_test = [s[0].strip() for s in symbols if s[0]]

        if not symbols_to_test:
            logger.warning("No symbols found in database.")
            return {'trades': [], 'stats': self._empty_stats()}

        all_trades = []
        for sym in symbols_to_test:
            logger.info(f"Running backtest for symbol: {sym}")
            trades = self._backtest_symbol(sym, request.lookback, request.quantity, request.strategy_name)
            all_trades.extend(trades)

        saved_trades = self._save_trades(all_trades)
        stats = self._calculate_stats(saved_trades)
        logger.info(f"Backtest completed. Generated {len(saved_trades)} trades.")
        return {
            'trades': saved_trades,
            'stats': stats
        }

    def _backtest_symbol(self, symbol: str, lookback: int, quantity: int, strategy_name: str) -> List[TradeCreate]:
        candles = self.db.query(models.MarketData).filter(
            func.lower(func.trim(models.MarketData.trading_symbol)) == symbol.lower()
        ).order_by(models.MarketData.id).all()

        logger.info(f"Symbol {symbol}: Retrieved {len(candles)} candles.")

        if len(candles) < lookback + 1:
            logger.warning(f"Symbol {symbol}: Not enough candles. Need {lookback+1}, got {len(candles)}.")
            return []

        ltp_values = [c.ltp for c in candles if c.ltp is not None]
        if not ltp_values:
            logger.warning(f"Symbol {symbol}: All ltp values are NULL.")
            return []

        logger.info(f"Symbol {symbol}: ltp range: min={min(ltp_values):.2f}, max={max(ltp_values):.2f}")
        logger.info(f"Symbol {symbol}: first 20 ltp values: {ltp_values[:20]}")

        trades = []
        position = None
        entry_count = 0

        for i in range(lookback, len(candles)):
            current = candles[i]
            prev_candles = candles[i - lookback:i]
            highest_prev = max(c.ltp for c in prev_candles)
            current_ltp = current.ltp

            if i % 200 == 0 or current_ltp > highest_prev:
                logger.info(f"Idx {i}: current={current_ltp:.2f}, highest_prev={highest_prev:.2f}, diff={current_ltp - highest_prev:.2f}")

            if position is None and current_ltp > highest_prev:
                entry_price = current_ltp
                entry_time = datetime.now()
                trade_id = f"{strategy_name}_{symbol}_{i}_{uuid.uuid4().hex[:6]}"
                sl = candles[i-1].ltp
                position = {
                    'entry_price': entry_price,
                    'sl': sl,
                    'entry_time': entry_time,
                    'entry_idx': i,
                    'trade_id': trade_id,
                    'symbol': symbol,
                    'quantity': quantity,
                    'strategy_name': strategy_name
                }
                entry_count += 1
                logger.info(f"BUY #{entry_count} for {symbol} at {entry_price:.2f}, SL={sl:.2f} (idx={i})")

            elif position is not None:
                current_low = current_ltp
                if current_low > position['sl']:
                    position['sl'] = current_low
                if current_low <= position['sl'] or current_ltp <= position['sl']:
                    exit_price = position['sl']
                    exit_time = datetime.now()
                    gross_pnl = (exit_price - position['entry_price']) * quantity
                    net_pnl = gross_pnl
                    trade = TradeCreate(
                        symbol=symbol,
                        entry_price=position['entry_price'],
                        quantity=quantity,
                        strategy_name=strategy_name,
                        entry_time=position['entry_time'],
                        trade_id=position['trade_id']
                    )
                    trade.exit_price = exit_price
                    trade.exit_time = exit_time
                    trade.profit_loss = net_pnl
                    trade.exit_reason = "SL_HIT"
                    trade.status = models.TradeStatus.CLOSED
                    trades.append(trade)
                    position = None
                    logger.info(f"EXIT for {symbol} at {exit_price:.2f}, PnL={net_pnl:.2f}")

        if position is not None:
            last_candle = candles[-1]
            exit_price = last_candle.ltp
            exit_time = datetime.now()
            gross_pnl = (exit_price - position['entry_price']) * quantity
            net_pnl = gross_pnl
            trade = TradeCreate(
                symbol=symbol,
                entry_price=position['entry_price'],
                quantity=quantity,
                strategy_name=strategy_name,
                entry_time=position['entry_time'],
                trade_id=position['trade_id']
            )
            trade.exit_price = exit_price
            trade.exit_time = exit_time
            trade.profit_loss = net_pnl
            trade.exit_reason = "END_OF_DATA"
            trade.status = models.TradeStatus.CLOSED
            trades.append(trade)
            logger.info(f"Position closed at end for {symbol} at {exit_price:.2f}")

        logger.info(f"Symbol {symbol}: Generated {len(trades)} trades. Entry signals: {entry_count}")
        return trades

    def _save_trades(self, trade_creates: List) -> List[models.Trade]:
        saved = []
        for tc in trade_creates:
            trade = models.Trade(
                trade_id=tc.trade_id,
                symbol=tc.symbol,
                entry_time=tc.entry_time,
                entry_price=tc.entry_price,
                quantity=tc.quantity,
                strategy_name=tc.strategy_name,
                status=getattr(tc, 'status', models.TradeStatus.OPEN),
                exit_time=getattr(tc, 'exit_time', None),
                exit_price=getattr(tc, 'exit_price', None),
                profit_loss=getattr(tc, 'profit_loss', None),
                exit_reason=getattr(tc, 'exit_reason', None)
            )
            self.db.add(trade)
            saved.append(trade)
        self.db.commit()
        for t in saved:
            self.db.refresh(t)
        return saved

    def _calculate_stats(self, trades: List[models.Trade]) -> Dict:
        closed = [t for t in trades if t.status == models.TradeStatus.CLOSED]
        if not closed:
            return self._empty_stats()
        df = pd.DataFrame([{'pnl': t.profit_loss or 0} for t in closed])
        total = len(df)
        winning = len(df[df['pnl'] > 0])
        losing = len(df[df['pnl'] < 0])
        win_rate = winning / total if total > 0 else 0
        net_profit = df['pnl'].sum()
        avg_profit = df['pnl'].mean() if total > 0 else 0
        cumsum = df['pnl'].cumsum()
        max_drawdown = (cumsum - cumsum.expanding().max()).min()
        gross_profit = df[df['pnl'] > 0]['pnl'].sum()
        gross_loss = abs(df[df['pnl'] < 0]['pnl'].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        return {
            'total_trades': total,
            'winning_trades': winning,
            'losing_trades': losing,
            'win_rate': round(win_rate, 4),
            'net_profit': round(net_profit, 2),
            'avg_profit': round(avg_profit, 2),
            'max_drawdown': round(max_drawdown, 2),
            'profit_factor': round(profit_factor, 4)
        }

    def _empty_stats(self):
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0.0,
            'net_profit': 0.0,
            'avg_profit': 0.0,
            'max_drawdown': 0.0,
            'profit_factor': 0.0
        }