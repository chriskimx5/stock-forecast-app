"""
Evaluates buy criteria for each watchlist ticker and persists TradeSignal rows.

Buy criteria (ALL must be true):
  1. pred_return > 1x rmse  (signal stronger than noise)
  2. price above 20-day MA
  3. signal_strength in ("Medium", "Strong")

Position sizing:
  - Risk per trade = capital * max_risk_per_trade_pct / 100
  - Stop loss distance = entry_price * stop_loss_pct / 100
  - Shares = risk_amount / stop_loss_distance  (risk-based sizing)
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import TradeSignal, WatchlistItem
from app.services.dashboard import compute_dashboard_row

logger = logging.getLogger(__name__)


def _position_sizing(price: float) -> tuple[float, float, float]:
    """Returns (shares, stop_loss_price, take_profit_price)."""
    risk_amount = settings.paper_capital * settings.max_risk_per_trade_pct / 100
    stop_dist = price * settings.stop_loss_pct / 100
    shares = round(risk_amount / stop_dist, 4) if stop_dist > 0 else 0
    stop_loss = round(price * (1 - settings.stop_loss_pct / 100), 4)
    take_profit = round(price * (1 + settings.take_profit_pct / 100), 4)
    return shares, stop_loss, take_profit


def compute_signals(db: Session) -> list[dict]:
    tickers = db.execute(select(WatchlistItem.ticker)).scalars().all()
    now = datetime.now(timezone.utc)
    results = []

    for ticker in tickers:
        try:
            row = compute_dashboard_row(db, ticker)
            if row.get("status") == "no_data":
                continue

            price = row.get("price") or 0
            pred_return = row.get("pred_return")   # already in % terms
            rmse = row.get("rmse_return")          # in decimal (e.g. 0.012)
            signal_strength = row.get("signal_strength")
            ma20 = row.get("ma20")

            above_ma20 = bool(price > ma20) if ma20 else None

            # Evaluate buy criteria (relaxed: pred_return > 0 and above MA20)
            rmse_pct = (rmse * 100) if rmse else None
            criteria_met = bool(
                pred_return is not None
                and pred_return > 0
                and above_ma20
            )

            shares, stop_loss, take_profit = _position_sizing(price) if price > 0 else (None, None, None)

            signal = TradeSignal(
                computed_at=now,
                ticker=ticker,
                price=price,
                pred_return=pred_return,
                rmse=rmse_pct,
                signal_strength=signal_strength,
                above_ma20=above_ma20,
                criteria_met=criteria_met,
                suggested_shares=shares if criteria_met else None,
                suggested_stop_loss=stop_loss if criteria_met else None,
                suggested_take_profit=take_profit if criteria_met else None,
            )
            db.add(signal)
            results.append({
                "ticker": ticker,
                "price": price,
                "pred_return": pred_return,
                "rmse": rmse_pct,
                "signal_strength": signal_strength,
                "above_ma20": above_ma20,
                "criteria_met": criteria_met,
                "suggested_shares": shares if criteria_met else None,
                "suggested_stop_loss": stop_loss if criteria_met else None,
                "suggested_take_profit": take_profit if criteria_met else None,
            })
        except Exception:
            logger.exception("Signal computation failed for %s", ticker)

    db.commit()
    results.sort(key=lambda r: (r.get("criteria_met", False), abs(r.get("pred_return") or 0)), reverse=True)
    return results


def get_latest_signals(db: Session) -> list[dict]:
    """Return the most recent signal row per ticker."""
    tickers = db.execute(select(WatchlistItem.ticker)).scalars().all()
    out = []
    for ticker in tickers:
        row = db.execute(
            select(TradeSignal)
            .where(TradeSignal.ticker == ticker)
            .order_by(TradeSignal.computed_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        if row:
            out.append({
                "ticker": row.ticker,
                "computed_at": row.computed_at.isoformat(),
                "price": row.price,
                "pred_return": row.pred_return,
                "rmse": row.rmse,
                "signal_strength": row.signal_strength,
                "above_ma20": row.above_ma20,
                "criteria_met": row.criteria_met,
                "suggested_shares": row.suggested_shares,
                "suggested_stop_loss": row.suggested_stop_loss,
                "suggested_take_profit": row.suggested_take_profit,
            })
    out.sort(key=lambda r: (r.get("criteria_met", False), abs(r.get("pred_return") or 0)), reverse=True)
    return out
