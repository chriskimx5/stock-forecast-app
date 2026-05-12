from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.ingest import ingest_ticker
from app.services.ml import train_ticker_model

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler(timezone="UTC")


def _with_db(fn, *args, **kwargs):
    db: Session = SessionLocal()
    try:
        return fn(db, *args, **kwargs)
    finally:
        db.close()


def _run_daily_pipeline():
    """Ingest + retrain all watchlist tickers, then compute signals and send summary."""
    from app.db.models import WatchlistItem
    from sqlalchemy import select

    db: Session = SessionLocal()
    try:
        tickers = db.execute(select(WatchlistItem.ticker)).scalars().all()
        if not tickers:
            logger.info("Daily pipeline: no watchlist tickers, skipping")
            return

        for t in tickers:
            try:
                ingest_ticker(db, t, period=settings.ingest_period, interval=settings.ingest_interval)
                logger.info("Ingested %s", t)
            except Exception:
                logger.exception("Ingest failed for %s", t)

            try:
                train_ticker_model(db, t, window=settings.model_window)
                logger.info("Trained %s", t)
            except Exception:
                logger.exception("Train failed for %s", t)

        # Compute signals after all tickers are fresh
        from app.services.signals import compute_signals
        signals = compute_signals(db)
        logger.info("Computed %d signals, %d meet criteria",
                    len(signals), sum(1 for s in signals if s.get("criteria_met")))

        # Build P&L summary for email
        from app.db.models import Position
        open_pos = db.execute(select(Position).where(Position.is_open == True)).scalars().all()
        closed_pos = db.execute(select(Position).where(Position.is_open == False)).scalars().all()
        realized_pnl = sum(
            (p.close_price - p.entry_price) * p.shares
            for p in closed_pos if p.close_price
        )
        wins = [p for p in closed_pos if p.close_price and p.close_price > p.entry_price]
        pnl = {
            "capital": settings.paper_capital,
            "realized_pnl": round(realized_pnl, 2),
            "win_rate_pct": round(len(wins) / len(closed_pos) * 100, 1) if closed_pos else 0,
            "unrealized_pnl": 0,
        }

        open_pos_dicts = [
            {
                "ticker": p.ticker,
                "shares": p.shares,
                "entry_price": p.entry_price,
                "unrealized_pnl_pct": 0,  # would need current price to compute
            }
            for p in open_pos
        ]

        from app.services.notify import send_daily_summary
        send_daily_summary(signals, open_pos_dicts, pnl)

    finally:
        db.close()


def start_scheduler():
    if scheduler.running:
        return

    tickers = [t.strip().upper() for t in settings.scheduler_tickers.split(",") if t.strip()]
    if not tickers:
        tickers = ["AAPL"]

    if settings.scheduler_mode == "interval":
        # Dev mode: run pipeline every N minutes for fast feedback
        scheduler.add_job(
            _run_daily_pipeline,
            "interval",
            minutes=settings.scheduler_every_minutes,
            id="daily_pipeline",
            replace_existing=True,
        )
    else:
        # Production: run after market close on weekdays (default 22:00 UTC = 5pm ET + buffer)
        scheduler.add_job(
            _run_daily_pipeline,
            "cron",
            day_of_week="mon-fri",
            hour=settings.scheduler_hour_utc,
            minute=settings.scheduler_minute_utc,
            id="daily_pipeline",
            replace_existing=True,
        )

    scheduler.start()
    logger.info("Scheduler started in %s mode", settings.scheduler_mode)


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
