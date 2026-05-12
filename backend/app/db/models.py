from datetime import date, datetime

from sqlalchemy import BigInteger, Boolean, Date, DateTime, Float, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PriceBar(Base):
    __tablename__ = "prices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(16), nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)

    open: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    high: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    low: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    close: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    volume: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    __table_args__ = (
        UniqueConstraint("ticker", "trade_date", name="uq_prices_ticker_trade_date"),
        Index("ix_prices_ticker_ts", "ticker", "ts"),
    )


class WatchlistItem(Base):
    __tablename__ = "watchlist"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class JournalEntry(Base):
    __tablename__ = "journal"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ticker: Mapped[str] = mapped_column(String(16), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    entry_price: Mapped[float | None] = mapped_column(Float, nullable=True)

    pred_return: Mapped[float | None] = mapped_column(Float, nullable=True)
    pred_close: Mapped[float | None] = mapped_column(Float, nullable=True)
    signal_strength: Mapped[str | None] = mapped_column(String(16), nullable=True)

    outcome_1d: Mapped[float | None] = mapped_column(Float, nullable=True)
    outcome_1w: Mapped[float | None] = mapped_column(Float, nullable=True)
    outcome_1m: Mapped[float | None] = mapped_column(Float, nullable=True)
    outcome_filled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Position(Base):
    """Paper trading positions."""
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(16), nullable=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    shares: Mapped[float] = mapped_column(Float, nullable=False)
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    stop_loss: Mapped[float] = mapped_column(Float, nullable=False)
    take_profit: Mapped[float] = mapped_column(Float, nullable=False)

    close_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    close_reason: Mapped[str | None] = mapped_column(String(32), nullable=True)  # "stop_loss", "take_profit", "manual"

    pred_return_at_entry: Mapped[float | None] = mapped_column(Float, nullable=True)
    signal_strength_at_entry: Mapped[str | None] = mapped_column(String(16), nullable=True)

    is_open: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class TradeSignal(Base):
    """Daily computed signals per ticker."""
    __tablename__ = "trade_signals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ticker: Mapped[str] = mapped_column(String(16), nullable=False)

    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    pred_return: Mapped[float | None] = mapped_column(Float, nullable=True)
    rmse: Mapped[float | None] = mapped_column(Float, nullable=True)
    signal_strength: Mapped[str | None] = mapped_column(String(16), nullable=True)

    above_ma20: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    criteria_met: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    suggested_shares: Mapped[float | None] = mapped_column(Float, nullable=True)
    suggested_stop_loss: Mapped[float | None] = mapped_column(Float, nullable=True)
    suggested_take_profit: Mapped[float | None] = mapped_column(Float, nullable=True)

    __table_args__ = (Index("ix_trade_signals_ticker_computed", "ticker", "computed_at"),)
