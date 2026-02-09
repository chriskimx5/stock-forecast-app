import logging
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.ingest import ingest_ticker

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/{ticker}")
def ingest(
    ticker: str,
    period: str = Query(default="1y"),
    interval: str = Query(default="1d"),
    db: Session = Depends(get_db),
):
    try:
        return ingest_ticker(db, ticker=ticker, period=period, interval=interval)
    except Exception as e:
        logger.exception("Ingest failed for %s", ticker)
        # Return the actual error message so we can fix it quickly
        raise HTTPException(status_code=500, detail=str(e))
