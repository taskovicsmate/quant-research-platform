from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class IndicatorValue(Base):
    __tablename__ = "indicator_values"
    __table_args__ = (
        CheckConstraint(
            "char_length(trim(indicator_name)) > 0",
            name="ck_indicator_values_indicator_name_not_empty",
        ),
        CheckConstraint(
            "char_length(trim(parameter_signature)) > 0",
            name="ck_indicator_values_parameter_signature_not_empty",
        ),
        CheckConstraint(
            "char_length(trim(calculation_version)) > 0",
            name="ck_indicator_values_calculation_version_not_empty",
        ),
        UniqueConstraint(
            "source_processed_candle_id",
            "indicator_name",
            "parameter_signature",
            "calculation_version",
            name="uq_indicator_values_source_configuration",
        ),
        Index(
            "ix_indicator_values_configuration_source",
            "indicator_name",
            "parameter_signature",
            "calculation_version",
            "source_processed_candle_id",
        ),
        {"schema": "features"},
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    source_processed_candle_id: Mapped[int] = mapped_column(
        ForeignKey(
            "processed.candles.id",
            name="fk_indicator_values_source_processed_candle",
            ondelete="RESTRICT",
        )
    )

    indicator_name: Mapped[str] = mapped_column(String(50))
    parameter_signature: Mapped[str] = mapped_column(String(200))
    parameters: Mapped[dict[str, Any]] = mapped_column(JSONB)
    calculation_version: Mapped[str] = mapped_column(String(50))
    value: Mapped[Decimal] = mapped_column(Numeric(24, 12))
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
