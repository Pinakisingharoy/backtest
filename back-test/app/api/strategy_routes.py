from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app import schemas, models
from app.services.backtest_service import BacktestService

router = APIRouter()

@router.post("/run", response_model=schemas.StrategyRunResponse)
def run_strategy(
    request: schemas.StrategyRunRequest,
    db: Session = Depends(get_db)
):
    try:
        backtest_req = schemas.BacktestRequest(
            symbol=request.symbol,
            lookback=request.lookback,
            quantity=request.quantity,
            strategy_name=request.strategy_name
        )
        service = BacktestService(db)
        result = service.run_backtest(backtest_req)
        trades_response = [schemas.TradeResponse.model_validate(t) for t in result['trades']]
        return schemas.StrategyRunResponse(
            message=f"Strategy executed. Generated {len(trades_response)} trades.",
            trades_generated=len(trades_response),
            trades=trades_response
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/backtest", response_model=schemas.BacktestResponse)
def run_backtest(
    request: schemas.BacktestRequest,
    db: Session = Depends(get_db)
):
    try:
        service = BacktestService(db)
        result = service.run_backtest(request)
        trades_response = [schemas.TradeResponse.model_validate(t) for t in result['trades']]
        stats = schemas.BacktestStats(**result['stats'])
        return schemas.BacktestResponse(
            message="Backtest completed",
            trades=trades_response,
            stats=stats
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trades", response_model=list[schemas.TradeResponse])
def get_trades(
    symbol: Optional[str] = None,
    status: Optional[schemas.TradeStatus] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Trade)
    if symbol:
        query = query.filter(models.Trade.symbol == symbol)
    if status:
        query = query.filter(models.Trade.status == status)
    trades = query.order_by(models.Trade.entry_time.desc()).all()
    return [schemas.TradeResponse.model_validate(t) for t in trades]