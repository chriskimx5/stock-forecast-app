from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.signals import compute_signals, get_latest_signals

router = APIRouter()


@router.get("")
def get_signals(db: Session = Depends(get_db)):
    """Return latest cached signal per watchlist ticker."""
    return get_latest_signals(db)


@router.post("/compute")
def run_compute_signals(db: Session = Depends(get_db)):
    """Recompute signals now for all watchlist tickers."""
    return compute_signals(db)
