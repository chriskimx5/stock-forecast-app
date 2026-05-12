from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import JournalEntry, PriceBar
from app.db.session import get_db

router = APIRouter()


class JournalEntryBody(BaseModel):
    ticker: str
    action: str
    reasoning: str
    entry_price: float | None = None
    pred_return: float | None = None
    pred_close: float | None = None
    signal_strength: str | None = None


def _get_close_after(db: Session, ticker: str, after: datetime, days: int) -> float | None:
    target = after + timedelta(days=days)
    stmt = (
        select(PriceBar.close)
        .where(PriceBar.ticker == ticker)
        .where(PriceBar.ts >= target)
        .order_by(PriceBar.ts.asc())
        .limit(1)
    )
    row = db.execute(stmt).scalar_one_or_none()
    return float(row) if row is not None else None


def _fill_outcomes(db: Session, entry: JournalEntry) -> bool:
    now = datetime.now(timezone.utc)
    changed = False
    age = (now - entry.created_at).days

    if entry.outcome_1d is None and age >= 1:
        close = _get_close_after(db, entry.ticker, entry.created_at, 1)
        if close and entry.entry_price:
            entry.outcome_1d = (close / entry.entry_price - 1) * 100
            changed = True

    if entry.outcome_1w is None and age >= 7:
        close = _get_close_after(db, entry.ticker, entry.created_at, 7)
        if close and entry.entry_price:
            entry.outcome_1w = (close / entry.entry_price - 1) * 100
            changed = True

    if entry.outcome_1m is None and age >= 30:
        close = _get_close_after(db, entry.ticker, entry.created_at, 30)
        if close and entry.entry_price:
            entry.outcome_1m = (close / entry.entry_price - 1) * 100
            changed = True

    if changed:
        entry.outcome_filled_at = now

    return changed


@router.get("")
def get_journal(db: Session = Depends(get_db)):
    entries = db.execute(
        select(JournalEntry).order_by(JournalEntry.created_at.desc())
    ).scalars().all()

    updated = any(_fill_outcomes(db, e) for e in entries)
    if updated:
        db.commit()

    return [
        {
            "id": e.id,
            "created_at": e.created_at.isoformat(),
            "ticker": e.ticker,
            "action": e.action,
            "reasoning": e.reasoning,
            "entry_price": e.entry_price,
            "pred_return": e.pred_return,
            "pred_close": e.pred_close,
            "signal_strength": e.signal_strength,
            "outcome_1d": e.outcome_1d,
            "outcome_1w": e.outcome_1w,
            "outcome_1m": e.outcome_1m,
            "outcome_filled_at": e.outcome_filled_at.isoformat() if e.outcome_filled_at else None,
        }
        for e in entries
    ]


@router.post("")
def add_journal_entry(body: JournalEntryBody, db: Session = Depends(get_db)):
    entry = JournalEntry(
        created_at=datetime.now(timezone.utc),
        ticker=body.ticker.upper().strip(),
        action=body.action,
        reasoning=body.reasoning,
        entry_price=body.entry_price,
        pred_return=body.pred_return,
        pred_close=body.pred_close,
        signal_strength=body.signal_strength,
    )
    db.add(entry)
    db.commit()
    return {"id": entry.id, "created_at": entry.created_at.isoformat()}


@router.delete("/{entry_id}")
def delete_journal_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.execute(select(JournalEntry).where(JournalEntry.id == entry_id)).scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    db.delete(entry)
    db.commit()
    return {"deleted": entry_id}
