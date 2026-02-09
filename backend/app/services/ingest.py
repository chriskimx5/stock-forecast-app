from __future__ import annotations

from datetime import datetime, timezone
import pandas as pd
import yfinance as yf
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.db.models import PriceBar

def _normalize_yf_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize yfinance output into columns:
    ts (UTC), Open, High, Low, Close, Volume
    Handles index-based timestamps and occasional MultiIndex columns.
    """
    if df is None or df.empty:
        return df

    # If columns are MultiIndex, flatten them into unique names
    if isinstance(df.columns, pd.MultiIndex):
        flat = []
        for c in df.columns:
            # keep non-empty parts, join with "_"
            parts = [str(x) for x in c if x not in (None, "", " ")]
            flat.append("_".join(parts) if parts else str(c[0]))
        df.columns = flat

    # If columns are still duplicated, keep the last occurrence
    if df.columns.duplicated().any():
        df = df.loc[:, ~df.columns.duplicated(keep="last")]


    # Move index -> column if needed
    if "Date" not in df.columns and "Datetime" not in df.columns:
        df = df.reset_index()

    # Identify timestamp column
    ts_col = "Date" if "Date" in df.columns else ("Datetime" if "Datetime" in df.columns else df.columns[0])

    # Rename to a common name
    if ts_col != "ts":
        df = df.rename(columns={ts_col: "ts"})

    # Force UTC timestamps
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
    
    # Normalize column names to expected OHLCV keys
    rename = {}
    for base in ["Open", "High", "Low", "Close", "Volume"]:
        if base in df.columns:
            continue
        # try to find a column that starts with base (e.g., Open_TSLA)
        matches = [c for c in df.columns if str(c).startswith(base + "_")]
        if matches:
            rename[matches[0]] = base
    if rename:
        df = df.rename(columns=rename)


    required = ["Open", "High", "Low", "Close", "Volume", "ts"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"missing column from market data: {col}")

    rows = []
    for rec in df[["ts", "Open", "High", "Low", "Close", "Volume"]].to_dict(orient="records"):
        ts = pd.Timestamp(rec["ts"]).to_pydatetime()
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
        index_elements=[PriceBar.ticker, PriceBar.ts],
        set_={
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
