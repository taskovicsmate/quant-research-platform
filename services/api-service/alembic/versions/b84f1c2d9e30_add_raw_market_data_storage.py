"""add raw market data storage

Revision ID: b84f1c2d9e30
Revises: 754d690fb877
Create Date: 2026-08-16 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "b84f1c2d9e30"
down_revision: Union[str, Sequence[str], None] = "754d690fb877"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create immutable raw ingestion metadata and candle storage."""
    op.execute("CREATE SCHEMA raw")

    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("exchange", sa.String(length=20), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("timeframe", sa.String(length=20), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "record_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "completed_at IS NULL OR completed_at >= started_at",
            name="ck_raw_ingestion_runs_completion_time",
        ),
        sa.CheckConstraint(
            "record_count >= 0",
            name="ck_raw_ingestion_runs_non_negative_count",
        ),
        sa.CheckConstraint(
            "status IN ('running', 'completed', 'failed')",
            name="ck_raw_ingestion_runs_status",
        ),
        sa.CheckConstraint(
            "start_time < end_time", name="ck_raw_ingestion_runs_time_range"
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="raw",
    )

    op.create_table(
        "candles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("ingestion_run_id", sa.Integer(), nullable=False),
        sa.Column("source_row_number", sa.Integer(), nullable=False),
        sa.Column("exchange", sa.String(length=20), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("timeframe", sa.String(length=20), nullable=False),
        sa.Column("open_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("close_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "ingested_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["ingestion_run_id"], ["raw.ingestion_runs.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "ingestion_run_id",
            "source_row_number",
            name="uq_raw_candles_ingestion_row",
        ),
        schema="raw",
    )
    op.create_index(
        "ix_raw_candles_market_open_time",
        "candles",
        ["exchange", "symbol", "timeframe", "open_time"],
        unique=False,
        schema="raw",
    )


def downgrade() -> None:
    """Remove raw storage in dependency order."""
    op.drop_index(
        "ix_raw_candles_market_open_time", table_name="candles", schema="raw"
    )
    op.drop_table("candles", schema="raw")
    op.drop_table("ingestion_runs", schema="raw")
    op.execute("DROP SCHEMA raw")
