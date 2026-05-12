from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import WatchlistItem
from app.db.session import get_db

router = APIRouter()


class AddTickerBody(BaseModel):
    ticker: str


@router.get("")
def get_watchlist(db: Session = Depends(get_db)):
    rows = db.execute(select(WatchlistItem).order_by(WatchlistItem.added_at)).scalars().all()
    return [{"id": r.id, "ticker": r.ticker, "added_at": r.added_at.isoformat()} for r in rows]


@router.post("")
def add_ticker(body: AddTickerBody, db: Session = Depends(get_db)):
    t = body.ticker.upper().strip()
    existing = db.execute(select(WatchlistItem).where(WatchlistItem.ticker == t)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail=f"{t} already in watchlist")
    item = WatchlistItem(ticker=t, added_at=datetime.now(timezone.utc))
    db.add(item)
    db.commit()
    return {"ticker": t, "added_at": item.added_at.isoformat()}


@router.delete("/{ticker}")
def remove_ticker(ticker: str, db: Session = Depends(get_db)):
    t = ticker.upper().strip()
    item = db.execute(select(WatchlistItem).where(WatchlistItem.ticker == t)).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail=f"{t} not in watchlist")
    db.delete(item)
    db.commit()
    return {"removed": t}
