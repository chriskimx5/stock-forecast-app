from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, distinct

from app.db.session import get_db
from app.db.models import PriceBar

router = APIRouter()

@router.get("/search")
def search_tickers(q: str = Query(min_length=1, max_length=10), limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    q = q.upper()
    stmt = (
        select(distinct(PriceBar.ticker))
        .where(PriceBar.ticker.like(f"{q}%"))
        .limit(limit)
    )
    tickers = [r[0] for r in db.execute(stmt).all()]
    return {"tickers": tickers}
