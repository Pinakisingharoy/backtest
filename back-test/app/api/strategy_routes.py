from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app import schemas, models
from app.services.strategy_service import StrategyService

router = APIRouter()

@router.post("/run", response_model=schemas.StrategyRunResponse)
def run_strategy(
    request: schemas.StrategyRunRequest,
    db: Session = Depends(get_db)
):
    try:
        service = StrategyService(db)
        result = service.run_strategy(request)
        trades_response = [schemas.TradeResponse.model_validate(t) for t in result['trades']]
        return schemas.StrategyRunResponse(
            message="Strategy executed successfully",
            trades_generated=result['trades_generated'],
            trades=trades_response
        )
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