"""add positions and trade_signals tables

Revision ID: 0003_add_positions_signals
Revises: 0002_add_watchlist_journal
Create Date: 2026-01-01 00:00:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0003_add_positions_signals"
down_revision: Union[str, Sequence[str], None] = "0002_add_watchlist_journal"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "positions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ticker", sa.String(16), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("shares", sa.Float(), nullable=False),
        sa.Column("entry_price", sa.Float(), nullable=False),
        sa.Column("stop_loss", sa.Float(), nullable=False),
        sa.Column("take_profit", sa.Float(), nullable=False),
        sa.Column("close_price", sa.Float(), nullable=True),
        sa.Column("close_reason", sa.String(32), nullable=True),
        sa.Column("pred_return_at_entry", sa.Float(), nullable=True),
        sa.Column("signal_strength_at_entry", sa.String(16), nullable=True),
        sa.Column("is_open", sa.Boolean(), nullable=False, server_default="true"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "trade_signals",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ticker", sa.String(16), nullable=False),
        sa.Column("price", sa.Float(), nullable=True),
        sa.Column("pred_return", sa.Float(), nullable=True),
        sa.Column("rmse", sa.Float(), nullable=True),
        sa.Column("signal_strength", sa.String(16), nullable=True),
        sa.Column("above_ma20", sa.Boolean(), nullable=True),
        sa.Column("criteria_met", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("suggested_shares", sa.Float(), nullable=True),
        sa.Column("suggested_stop_loss", sa.Float(), nullable=True),
        sa.Column("suggested_take_profit", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trade_signals_ticker_computed", "trade_signals", ["ticker", "computed_at"])


def downgrade() -> None:
    op.drop_index("ix_trade_signals_ticker_computed", table_name="trade_signals")
    op.drop_table("trade_signals")
    op.drop_table("positions")
