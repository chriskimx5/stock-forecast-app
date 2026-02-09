from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.ml import train_ticker_model, predict_next_close
from app.services.cache import cache_get_json, cache_set_json

router = APIRouter()

@router.post("/train/{ticker}")
def train(ticker: str, window: int = Query(default=20, ge=5, le=200), db: Session = Depends(get_db)):
    try:
        res = train_ticker_model(db, ticker=ticker, window=window)
        return {
            "ticker": res.ticker,
            "n_rows": res.n_rows,
            "n_train": res.n_train,
            "window": res.window,
            "rmse_return": res.rmse_return,
            "artifact_path": res.artifact_path,
            "trained_at": res.trained_at,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/predict/{ticker}")
def predict(ticker: str, ttl: int = Query(default=60, ge=0, le=3600), db: Session = Depends(get_db)):
    key = f"pred:{ticker.upper()}:nextclose"
    if ttl > 0:
        cached = cache_get_json(key)
        if cached is not None:
            cached["cached"] = True
            return cached

    try:
        out = predict_next_close(db, ticker=ticker)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    out["cached"] = False
    if ttl > 0:
        cache_set_json(key, out, ttl_seconds=ttl)
    return out
