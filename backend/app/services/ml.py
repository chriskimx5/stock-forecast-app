from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import joblib
from sklearn.linear_model import Ridge
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import PriceBar

ARTIFACT_DIR = Path(__file__).resolve().parents[1] / "ml_artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class TrainResult:
    ticker: str
    n_rows: int
    n_train: int
    window: int
    rmse_return: float
    artifact_path: str
    trained_at: str


def _load_close_series(db: Session, ticker: str, limit: int) -> pd.Series:
    t = ticker.upper()
    stmt = (
        select(PriceBar.ts, PriceBar.close)
        .where(PriceBar.ticker == t)
        .order_by(PriceBar.ts.desc())
        .limit(limit)
    )
    rows = db.execute(stmt).all()
    rows = list(reversed(rows))  # back to ascending time

    if not rows:
        return pd.Series(dtype=float)

    ts = [r[0] for r in rows]
    close = [float(r[1]) if r[1] is not None else np.nan for r in rows]
    s = pd.Series(close, index=pd.to_datetime(ts, utc=True)).dropna()
    return s


def _make_features(logrets: np.ndarray, window: int) -> tuple[np.ndarray, np.ndarray]:
    n = len(logrets)
    if n <= window:
        return np.empty((0, window)), np.empty((0,))

    X = np.zeros((n - window, window), dtype=np.float64)
    y = np.zeros((n - window,), dtype=np.float64)
    for i in range(window, n):
        X[i - window] = logrets[i - window : i]
        y[i - window] = logrets[i]
    return X, y


def train_ticker_model(db: Session, ticker: str, window: int = 20, max_rows: int = 5000) -> TrainResult:
    t = ticker.upper().strip()
    close = _load_close_series(db, t, limit=max_rows)

    if len(close) < (window + 50):
        raise ValueError(f"Not enough data to train. Need at least {window+50} closes; got {len(close)}")

    logp = np.log(close.values)
    logrets = np.diff(logp)

    X, y = _make_features(logrets, window=window)
    if len(y) < 50:
        raise ValueError("Not enough samples after featurization.")

    split = int(len(y) * 0.8)
    Xtr, ytr = X[:split], y[:split]
    Xva, yva = X[split:], y[split:]

    model = Ridge(alpha=1.0, random_state=0)
    model.fit(Xtr, ytr)

    pred_va = model.predict(Xva)
    rmse = float(np.sqrt(np.mean((pred_va - yva) ** 2)))

    resid_std = float(np.std(ytr - model.predict(Xtr)))

    artifact = {
        "ticker": t,
        "window": window,
        "model": model,
        "resid_std": resid_std,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "rmse_return": rmse,
        "last_ts": close.index[-1].isoformat(),
        "last_close": float(close.values[-1]),
    }

    path = ARTIFACT_DIR / f"{t}.joblib"
    joblib.dump(artifact, path)

    return TrainResult(
        ticker=t,
        n_rows=int(len(close)),
        n_train=int(len(ytr)),
        window=window,
        rmse_return=rmse,
        artifact_path=str(path),
        trained_at=artifact["trained_at"],
    )


def predict_next_close(db: Session, ticker: str) -> dict:
    t = ticker.upper().strip()
    path = ARTIFACT_DIR / f"{t}.joblib"
    if not path.exists():
        raise ValueError(f"No trained model found for {t}. Train first.")

    artifact = joblib.load(path)
    window = int(artifact["window"])
    model = artifact["model"]
    resid_std = float(artifact["resid_std"])

    close = _load_close_series(db, t, limit=window + 60)
    if len(close) < (window + 2):
        raise ValueError("Not enough data to compute features for prediction.")

    logp = np.log(close.values)
    logrets = np.diff(logp)
    if len(logrets) < window:
        raise ValueError("Not enough returns for prediction window.")

    x = logrets[-window:].astype(np.float64).reshape(1, -1)
    pred_logret = float(model.predict(x)[0])

    last_close = float(close.values[-1])
    pred_close = float(last_close * np.exp(pred_logret))

    lo_close = float(last_close * np.exp(pred_logret - resid_std))
    hi_close = float(last_close * np.exp(pred_logret + resid_std))

    return {
        "ticker": t,
        "asof_ts": close.index[-1].isoformat(),
        "last_close": last_close,
        "pred_log_return": pred_logret,
        "pred_close": pred_close,
        "pred_close_1sigma_low": lo_close,
        "pred_close_1sigma_high": hi_close,
        "model_window": window,
        "trained_at": artifact.get("trained_at"),
        "rmse_return": artifact.get("rmse_return"),
    }
