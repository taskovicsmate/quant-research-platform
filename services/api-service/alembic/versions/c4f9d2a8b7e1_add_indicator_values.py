"""Add indicator value storage.

Revision ID: c4f9d2a8b7e1
Revises: f15a560fccb0
Create Date: 2026-10-25 20:16:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "c4f9d2a8b7e1"
down_revision = "f15a560fccb0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA features")

    op.create_table(
        "indicator_values",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_processed_candle_id", sa.Integer(), nullable=False),
        sa.Column("indicator_name", sa.String(length=50), nullable=False),
        sa.Column("parameter_signature", sa.String(length=200), nullable=False),
        sa.Column("parameters", postgresql.JSONB(), nullable=False),
        sa.Column("calculation_version", sa.String(length=50), nullable=False),
        sa.Column("value", sa.Numeric(precision=24, scale=12), nullable=False),
        sa.Column(
            "calculated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "char_length(trim(indicator_name)) > 0",
            name="ck_indicator_values_indicator_name_not_empty",
        ),
        sa.CheckConstraint(
            "char_length(trim(parameter_signature)) > 0",
            name="ck_indicator_values_parameter_signature_not_empty",
        ),
        sa.CheckConstraint(
            "char_length(trim(calculation_version)) > 0",
            name="ck_indicator_values_calculation_version_not_empty",
        ),
        sa.ForeignKeyConstraint(
            ["source_processed_candle_id"],
            ["processed.candles.id"],
            name="fk_indicator_values_source_processed_candle",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source_processed_candle_id",
            "indicator_name",
            "parameter_signature",
            "calculation_version",
            name="uq_indicator_values_source_configuration",
        ),
        schema="features",
    )
    op.create_index(
        "ix_indicator_values_configuration_source",
        "indicator_values",
        [
            "indicator_name",
            "parameter_signature",
            "calculation_version",
            "source_processed_candle_id",
        ],
        schema="features",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_indicator_values_configuration_source",
        table_name="indicator_values",
        schema="features",
    )
    op.drop_table("indicator_values", schema="features")
    op.execute("DROP SCHEMA features")
