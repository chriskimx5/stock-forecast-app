from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.db.models import PriceBar

router = APIRouter()

@router.get("/{ticker}")
def get_prices(
    ticker: str,
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    limit: int = Query(default=5000, ge=1, le=20000),
    db: Session = Depends(get_db),
):
    stmt = select(PriceBar).where(PriceBar.ticker == ticker.upper())
    if start is not None:
        stmt = stmt.where(PriceBar.ts >= start)
    if end is not None:
        stmt = stmt.where(PriceBar.ts <= end)

    if start is None and end is None:
        stmt = stmt.order_by(PriceBar.ts.desc()).limit(limit)
        rows = list(reversed(db.execute(stmt).scalars().all()))
    else:
        stmt = stmt.order_by(PriceBar.ts.asc()).limit(limit)
        rows = db.execute(stmt).scalars().all()
    return [
        {
            "ts": r.ts.isoformat(),
            "open": float(r.open) if r.open is not None else None,
            "high": float(r.high) if r.high is not None else None,
            "low": float(r.low) if r.low is not None else None,
            "close": float(r.close) if r.close is not None else None,
            "volume": int(r.volume) if r.volume is not None else None,
        }
        for r in rows
    ]
