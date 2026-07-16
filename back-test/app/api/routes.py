from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
import pandas as pd
import io
from datetime import datetime
import logging

from app.database import get_db
from app import models, schemas
from app.crud import (
    bulk_create_market_data,
    get_unique_symbols,
    get_symbol_highs,
    get_daily_summary
)
from app.api import strategy_routes
from app.services.data_processor import DataProcessor
from app.services.backtest_service import BacktestService
from app.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

router.include_router(strategy_routes.router, prefix="/strategy", tags=["Strategy"])

@router.post("/upload")
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(400, "Only CSV files are allowed")
        content = await file.read()
        if len(content) > config.MAX_UPLOAD_SIZE:
            raise HTTPException(400, f"File too large. Max size: {config.MAX_UPLOAD_SIZE // (1024*1024)}MB")
        df = pd.read_csv(io.StringIO(content.decode('utf-8')))
        logger.info(f"Read {len(df)} rows from CSV")
        processor = DataProcessor()
        processed_data = processor.process_csv(df)
        data_list = processed_data.to_dict('records')
        rows_imported = bulk_create_market_data(db, data_list)
        return {
            "message": f"Successfully uploaded {rows_imported} records",
            "rows_imported": rows_imported,
            "filename": file.filename
        }
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/symbols")
def get_symbols(db: Session = Depends(get_db)):
    try:
        symbols = get_unique_symbols(db)
        return {"symbols": symbols, "count": len(symbols)}
    except Exception as e:
        logger.error(f"Error fetching symbols: {str(e)}")
        raise HTTPException(500, str(e))

@router.get("/top-highs/{limit}")
def get_top_highs(limit: int = 10, db: Session = Depends(get_db)):
    try:
        results = get_symbol_highs(db, limit)
        return {"top_highs": results, "count": len(results)}
    except Exception as e:
        logger.error(f"Error fetching top highs: {str(e)}")
        raise HTTPException(500, str(e))

@router.get("/export/csv")
def export_top_highs_csv(db: Session = Depends(get_db)):
    try:
        results = get_symbol_highs(db, 10)
        data = []
        for row in results:
            data.append({
                "Symbol": row["trading_symbol"],
                "High Price": row["high_price"],
                "Row ID": row.get("row_id", ""),
                "Rank": row["rank"]
            })
        df = pd.DataFrame(data)
        output_path = config.OUTPUT_DATA_DIR / "top_10_highs.csv"
        df.to_csv(output_path, index=False)
        return {
            "message": "Export successful",
            "file_path": str(output_path),
            "rows_exported": len(data)
        }
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        raise HTTPException(500, str(e))

@router.get("/analytics/daily-summary")
def get_daily_summary(
    date: Optional[datetime] = None,
    db: Session = Depends(get_db)
):
    try:
        summary = get_daily_summary(db, date)
        return summary
    except Exception as e:
        logger.error(f"Analytics error: {str(e)}")
        raise HTTPException(500, str(e))

# --- Debug endpoints ---
@router.get("/debug/symbols")
def debug_symbols(db: Session = Depends(get_db)):
    symbols = db.query(models.MarketData.trading_symbol).distinct().all()
    raw = [s[0] for s in symbols if s[0]]
    return {
        "count": len(raw),
        "symbols": raw,
        "first_10": raw[:10]
    }

@router.get("/debug/data")
def debug_data(db: Session = Depends(get_db)):
    symbols = db.query(models.MarketData.trading_symbol).distinct().all()
    symbols_list = [s[0] for s in symbols if s[0]]
    result = {}
    for sym in symbols_list[:5]:
        candles = db.query(models.MarketData).filter(
            models.MarketData.trading_symbol == sym
        ).order_by(models.MarketData.id).limit(20).all()
        ltp_values = [c.ltp for c in candles if c.ltp is not None]
        result[sym] = {
            "count": len(candles),
            "ltp_sample": ltp_values[:10] if ltp_values else [],
            "min_ltp": min(ltp_values) if ltp_values else None,
            "max_ltp": max(ltp_values) if ltp_values else None,
            "has_null_ltp": any(c.ltp is None for c in candles),
        }
    return {
        "total_symbols": len(symbols_list),
        "symbols_shown": symbols_list[:10],
        "sample_data": result
    }