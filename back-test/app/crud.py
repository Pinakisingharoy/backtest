from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models import MarketData
from datetime import datetime
from typing import List, Optional, Dict, Any
import pandas as pd

def bulk_create_market_data(db: Session, data_list: List[Dict[str, Any]]) -> int:
    db_data_list = [MarketData(**data) for data in data_list]
    db.bulk_save_objects(db_data_list)
    db.commit()
    return len(db_data_list)

def get_unique_symbols(db: Session) -> List[str]:
    symbols = db.query(MarketData.trading_symbol).distinct().all()
    return [s[0] for s in symbols if s[0]]

def get_symbol_highs(db: Session, limit: int = 10):
    # Since there's no date, we use id as order (or you can remove date from output)
    query = text("""
        WITH ranked_prices AS (
            SELECT 
                trading_symbol,
                ltp as high_price,
                id as row_id,
                ROW_NUMBER() OVER (PARTITION BY trading_symbol ORDER BY ltp DESC) as rank
            FROM backtest_data
            WHERE ltp IS NOT NULL 
            AND trading_symbol IS NOT NULL
            AND trading_symbol != ''
        )
        SELECT trading_symbol, high_price, row_id, rank
        FROM ranked_prices 
        WHERE rank <= :limit
        ORDER BY trading_symbol, rank
    """)
    result = db.execute(query, {"limit": limit})
    rows = result.fetchall()
    return [
        {
            "trading_symbol": row[0],
            "high_price": row[1],
            "row_id": row[2],
            "rank": row[3]
        }
        for row in rows
    ]

def get_daily_summary(db: Session, date: Optional[datetime] = None) -> Dict[str, Any]:
    # Without a date column, return a simple summary of all data
    data = db.query(MarketData).all()
    if not data:
        return {"message": "No data available"}
    df = pd.DataFrame([{
        'symbol': d.trading_symbol,
        'ltp': d.ltp or 0,
        'volume': d.volume or 0
    } for d in data])
    return {
        "total_symbols": len(df['symbol'].unique()),
        "total_volume": int(df['volume'].sum()),
        "avg_price": float(df['ltp'].mean()) if not df.empty else 0,
        "max_price": float(df['ltp'].max()) if not df.empty else 0,
        "min_price": float(df['ltp'].min()) if not df.empty else 0
    }