from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Position
from app.db.session import get_db
from app.services import alpaca

router = APIRouter()


class OpenPositionBody(BaseModel):
    ticker: str
    shares: float
    entry_price: float
    stop_loss: float
    take_profit: float
    pred_return_at_entry: float | None = None
    signal_strength_at_entry: str | None = None


class ClosePositionBody(BaseModel):
    close_price: float
    close_reason: str = "manual"


def _serialize(p: Position, current_price: float | None = None) -> dict:
    unrealized_pnl = None
    unrealized_pnl_pct = None
    if p.is_open and current_price:
        unrealized_pnl = round((current_price - p.entry_price) * p.shares, 4)
        unrealized_pnl_pct = round((current_price / p.entry_price - 1) * 100, 4)

    realized_pnl = None
    if not p.is_open and p.close_price:
        realized_pnl = round((p.close_price - p.entry_price) * p.shares, 4)

    return {
        "id": p.id,
        "ticker": p.ticker,
        "opened_at": p.opened_at.isoformat(),
        "closed_at": p.closed_at.isoformat() if p.closed_at else None,
        "shares": p.shares,
        "entry_price": p.entry_price,
        "stop_loss": p.stop_loss,
        "take_profit": p.take_profit,
        "close_price": p.close_price,
        "close_reason": p.close_reason,
        "pred_return_at_entry": p.pred_return_at_entry,
        "signal_strength_at_entry": p.signal_strength_at_entry,
        "is_open": p.is_open,
        "unrealized_pnl": unrealized_pnl,
        "unrealized_pnl_pct": unrealized_pnl_pct,
        "realized_pnl": realized_pnl,
    }


@router.get("")
def get_positions(db: Session = Depends(get_db)):
    open_pos = db.execute(
        select(Position).where(Position.is_open == True).order_by(Position.opened_at.desc())
    ).scalars().all()
    return [_serialize(p) for p in open_pos]


@router.get("/history")
def get_position_history(db: Session = Depends(get_db)):
    closed = db.execute(
        select(Position).where(Position.is_open == False).order_by(Position.closed_at.desc())
    ).scalars().all()
    return [_serialize(p) for p in closed]


@router.get("/summary")
def get_pnl_summary(db: Session = Depends(get_db)):
    all_closed = db.execute(
        select(Position).where(Position.is_open == False)
    ).scalars().all()

    realized_pnl = sum(
        (p.close_price - p.entry_price) * p.shares
        for p in all_closed if p.close_price
    )
    wins = [p for p in all_closed if p.close_price and p.close_price > p.entry_price]
    win_rate = (len(wins) / len(all_closed) * 100) if all_closed else 0

    open_pos = db.execute(select(Position).where(Position.is_open == True)).scalars().all()
    capital_in_positions = sum(p.entry_price * p.shares for p in open_pos)

    return {
        "capital": settings.paper_capital,
        "capital_deployed": round(capital_in_positions, 2),
        "capital_available": round(settings.paper_capital - capital_in_positions, 2),
        "realized_pnl": round(realized_pnl, 2),
        "total_trades": len(all_closed),
        "wins": len(wins),
        "losses": len(all_closed) - len(wins),
        "win_rate_pct": round(win_rate, 1),
        "open_positions": len(open_pos),
    }


@router.post("")
def open_position(body: OpenPositionBody, db: Session = Depends(get_db)):
    t = body.ticker.upper().strip()

    # Check capital availability
    open_pos = db.execute(select(Position).where(Position.is_open == True)).scalars().all()
    deployed = sum(p.entry_price * p.shares for p in open_pos)
    cost = body.entry_price * body.shares
    if deployed + cost > settings.paper_capital:
        raise HTTPException(status_code=400, detail=f"Insufficient paper capital. Available: ${settings.paper_capital - deployed:.2f}")

    pos = Position(
        ticker=t,
        opened_at=datetime.now(timezone.utc),
        shares=body.shares,
        entry_price=body.entry_price,
        stop_loss=body.stop_loss,
        take_profit=body.take_profit,
        pred_return_at_entry=body.pred_return_at_entry,
        signal_strength_at_entry=body.signal_strength_at_entry,
        is_open=True,
    )
    db.add(pos)
    db.commit()

    # Fire and forget to Alpaca — won't fail if not configured
    alpaca.place_order(t, body.shares, side="buy")

    return _serialize(pos)


@router.post("/{position_id}/close")
def close_position(position_id: int, body: ClosePositionBody, db: Session = Depends(get_db)):
    pos = db.execute(select(Position).where(Position.id == position_id)).scalar_one_or_none()
    if not pos:
        raise HTTPException(status_code=404, detail="Position not found")
    if not pos.is_open:
        raise HTTPException(status_code=400, detail="Position already closed")

    pos.close_price = body.close_price
    pos.close_reason = body.close_reason
    pos.closed_at = datetime.now(timezone.utc)
    pos.is_open = False
    db.commit()

    alpaca.close_position(pos.ticker)

    return _serialize(pos)
