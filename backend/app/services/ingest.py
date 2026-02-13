from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
import yfinance as yf
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.db.models import PriceBar


def _normalize_yf_df(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df

    if isinstance(df.columns, pd.MultiIndex):
        flat = []
        for c in df.columns:
            parts = [str(x) for x in c if x not in (None, "", " ")]
            flat.append("_".join(parts) if parts else str(c[0]))
        df.columns = flat

    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated(keep="last")]

    if "Date" not in df.columns and "Datetime" not in df.columns:
        df = df.reset_index()

    ts_col = "Date" if "Date" in df.columns else ("Datetime" if "Datetime" in df.columns else df.columns[0])

    if ts_col != "ts":
        df = df.rename(columns={ts_col: "ts"})

    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    return df


def ingest_ticker(db: Session, ticker: str, period: str = "1y", interval: str = "1d") -> dict:
    t = ticker.upper().strip()

    df = yf.download(t, period=period, interval=interval, auto_adjust=False, progress=False)
    if df is None or df.empty:
        return {"ticker": t, "rows": 0, "affected": 0, "ts": datetime.now(timezone.utc).isoformat()}

    df = _normalize_yf_df(df)
    if df is None or df.empty:
        return {"ticker": t, "rows": 0, "affected": 0, "ts": datetime.now(timezone.utc).isoformat()}

    rename = {}
    for base in ["Open", "High", "Low", "Close", "Volume"]:
        if base in df.columns:
            continue
        matches = [c for c in df.columns if str(c).startswith(base + "_")]
        if matches:
            rename[matches[0]] = base
    if rename:
        df = df.rename(columns=rename)

    required = ["Open", "High", "Low", "Close", "Volume", "ts"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"missing column from market data: {col}")

    bad = [c for c in df.columns if str(c).startswith(("Open_", "High_", "Low_", "Close_", "Volume_"))]
    if bad:
        raise ValueError(f"unexpected multi-ticker columns for {t}: {bad[:10]}")


    close_series = pd.to_numeric(df["Close"], errors="coerce")
    if close_series.isna().any():
        raise ValueError(f"{t}: Close contains NaN after coercion")
    if (close_series <= 0).any():
        raise ValueError(f"{t}: non-positive Close encountered")

    ratio = (close_series / close_series.shift(1)).abs()
    if (ratio.dropna() > 2.0).any():
        raise ValueError(f"{t}: suspicious close jump detected")

    rows = []
    for rec in df[["ts", "Open", "High", "Low", "Close", "Volume"]].to_dict(orient="records"):
        ts = pd.Timestamp(rec["ts"])
        if ts.tzinfo is None:
            ts = ts.tz_localize("UTC")
        else:
            ts = ts.tz_convert("UTC")
        ts = ts.to_pydatetime()

        rows.append(
            {
                "ticker": t,
                "ts": ts,
                "open": float(rec["Open"]) if rec["Open"] is not None else None,
                "high": float(rec["High"]) if rec["High"] is not None else None,
                "low": float(rec["Low"]) if rec["Low"] is not None else None,
                "close": float(rec["Close"]) if rec["Close"] is not None else None,
                "volume": int(rec["Volume"]) if rec["Volume"] is not None else None,
            }
        )

    stmt = insert(PriceBar).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=[PriceBar.ticker, PriceBar.trade_date],
        set_={
            "ts": stmt.excluded.ts,
            "open": stmt.excluded.open,
            "high": stmt.excluded.high,
            "low": stmt.excluded.low,
            "close": stmt.excluded.close,
            "volume": stmt.excluded.volume,
        },
    )
    res = db.execute(stmt)
    db.commit()

    affected = getattr(res, "rowcount", -1)
    return {"ticker": t, "rows": len(rows), "affected": affected, "ts": datetime.now(timezone.utc).isoformat()}
