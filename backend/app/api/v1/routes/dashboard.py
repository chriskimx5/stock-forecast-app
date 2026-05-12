from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import WatchlistItem
from app.db.session import get_db
from app.services.dashboard import compute_dashboard_row

router = APIRouter()


@router.get("")
def get_dashboard(db: Session = Depends(get_db)):
    tickers = db.execute(select(WatchlistItem.ticker).order_by(WatchlistItem.added_at)).scalars().all()
    rows = [compute_dashboard_row(db, t) for t in tickers]
    rows.sort(
        key=lambda r: (r.get("volatility") or 0, abs(r.get("pred_return") or 0)),
        reverse=True,
    )
    return rows
