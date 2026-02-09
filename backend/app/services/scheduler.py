from __future__ import annotations

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.ingest import ingest_ticker
from app.services.ml import train_ticker_model

scheduler = BackgroundScheduler(timezone="UTC")

def _with_db(fn, *args, **kwargs):
    db: Session = SessionLocal()
    try:
        return fn(db, *args, **kwargs)
    finally:
        db.close()

def start_scheduler():
    if scheduler.running:
        return

    tickers = [t.strip().upper() for t in settings.scheduler_tickers.split(",") if t.strip()]
    if not tickers:
        tickers = ["AAPL"]

    # Dev mode: every N minutes (fast feedback)
    if settings.scheduler_mode == "interval":
        for t in tickers:
            scheduler.add_job(
                _with_db,
                "interval",
                minutes=settings.scheduler_every_minutes,
                args=(ingest_ticker, t),
                kwargs={"period": settings.ingest_period, "interval": settings.ingest_interval},
                id=f"ingest_{t}",
                replace_existing=True,
            )
            scheduler.add_job(
                _with_db,
                "interval",
                minutes=settings.scheduler_every_minutes,
                args=(train_ticker_model, t),
                kwargs={"window": settings.model_window},
                id=f"train_{t}",
                replace_existing=True,
            )
    else:
        # Realistic: weekdays once per day (UTC)
        for t in tickers:
            scheduler.add_job(
                _with_db,
                "cron",
                day_of_week="mon-fri",
                hour=settings.scheduler_hour_utc,
                minute=settings.scheduler_minute_utc,
                args=(ingest_ticker, t),
                kwargs={"period": settings.ingest_period, "interval": settings.ingest_interval},
                id=f"ingest_{t}",
                replace_existing=True,
            )
            scheduler.add_job(
                _with_db,
                "cron",
                day_of_week="mon-fri",
                hour=settings.scheduler_hour_utc,
                minute=(settings.scheduler_minute_utc + 10) % 60,
                args=(train_ticker_model, t),
                kwargs={"window": settings.model_window},
                id=f"train_{t}",
                replace_existing=True,
            )

    scheduler.start()

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
