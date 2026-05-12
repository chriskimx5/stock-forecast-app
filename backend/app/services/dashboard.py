from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import PriceBar

ARTIFACT_DIR = Path(__file__).resolve().parents[1] / "ml_artifacts"


def _get_closes(db: Session, ticker: str, limit: int = 60) -> pd.Series:
    stmt = (
        select(PriceBar.ts, PriceBar.close)
        .where(PriceBar.ticker == ticker)
        .order_by(PriceBar.ts.desc())
        .limit(limit)
    )
    rows = list(reversed(db.execute(stmt).all()))
    if not rows:
        return pd.Series(dtype=float)
    return pd.Series(
        [float(r[1]) for r in rows],
        index=pd.to_datetime([r[0] for r in rows], utc=True),
    ).dropna()


def _signal_strength(pred_return: float, rmse: float) -> str:
    abs_pred = abs(pred_return)
    if abs_pred < rmse:
        return "Weak"
    elif abs_pred < 2 * rmse:
        return "Medium"
    return "Strong"


def compute_dashboard_row(db: Session, ticker: str) -> dict:
    t = ticker.upper()
    closes = _get_closes(db, t, limit=60)

    if len(closes) < 2:
        return {"ticker": t, "status": "no_data"}

    price = float(closes.iloc[-1])

    def pct_return(n: int) -> float | None:
        if len(closes) < n + 1:
            return None
        return float((closes.iloc[-1] / closes.iloc[-(n + 1)] - 1) * 100)

    ret_1d = pct_return(1)
    ret_5d = pct_return(5)
    ret_20d = pct_return(20)

    volatility = float(closes.pct_change().std() * 100) if len(closes) >= 5 else None

    ma20 = float(closes.iloc[-20:].mean()) if len(closes) >= 20 else None
    ma50 = float(closes.iloc[-50:].mean()) if len(closes) >= 50 else None

    dist_ma20 = float((price / ma20 - 1) * 100) if ma20 else None
    dist_ma50 = float((price / ma50 - 1) * 100) if ma50 else None

    pred_return = pred_close = rmse = signal = trained_at = None

    path = ARTIFACT_DIR / f"{t}.joblib"
    if path.exists():
        try:
            artifact = joblib.load(path)
            rmse = float(artifact.get("rmse_return", 0))
            trained_at = artifact.get("trained_at")
            from app.services.ml import predict_next_close
            pred = predict_next_close(db, t)
            pred_return = float(pred["pred_log_return"] * 100)
            pred_close = float(pred["pred_close"])
            signal = _signal_strength(pred_return, rmse * 100)
        except Exception:
            pass

    return {
        "ticker": t,
        "status": "ok",
        "price": price,
        "ret_1d": ret_1d,
        "ret_5d": ret_5d,
        "ret_20d": ret_20d,
        "volatility": volatility,
        "ma20": ma20,
        "ma50": ma50,
        "dist_ma20": dist_ma20,
        "dist_ma50": dist_ma50,
        "pred_return": pred_return,
        "pred_close": pred_close,
        "rmse_return": rmse,
        "signal_strength": signal,
        "trained_at": trained_at,
    }
