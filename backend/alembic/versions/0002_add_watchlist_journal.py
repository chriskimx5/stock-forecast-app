"""add watchlist and journal tables

Revision ID: 0002_add_watchlist_journal
Revises: 3daaa2358410
Create Date: 2026-01-01 00:00:00
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0002_add_watchlist_journal"
down_revision: Union[str, Sequence[str], None] = "3daaa2358410"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "watchlist",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ticker", sa.String(16), nullable=False),
        sa.Column("added_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticker", name="uq_watchlist_ticker"),
    )
    op.create_table(
        "journal",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ticker", sa.String(16), nullable=False),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=False),
        sa.Column("entry_price", sa.Float(), nullable=True),
        sa.Column("pred_return", sa.Float(), nullable=True),
        sa.Column("pred_close", sa.Float(), nullable=True),
        sa.Column("signal_strength", sa.String(16), nullable=True),
        sa.Column("outcome_1d", sa.Float(), nullable=True),
        sa.Column("outcome_1w", sa.Float(), nullable=True),
        sa.Column("outcome_1m", sa.Float(), nullable=True),
        sa.Column("outcome_filled_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("journal")
    op.drop_table("watchlist")
