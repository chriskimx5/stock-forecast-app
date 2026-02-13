from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, Index, Numeric, String, UniqueConstraint
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
