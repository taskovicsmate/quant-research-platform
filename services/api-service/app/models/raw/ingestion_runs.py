from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Integer, String, Text, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"
    __table_args__ = (
        CheckConstraint("start_time < end_time", name="ck_raw_ingestion_runs_time_range"),
        CheckConstraint("record_count >= 0", name="ck_raw_ingestion_runs_non_negative_count"),
        CheckConstraint("status IN ('running', 'completed', 'failed')",name="ck_raw_ingestion_runs_status"), 
        CheckConstraint("completed_at IS NULL OR completed_at >= started_at",name="ck_raw_ingestion_runs_completion_time"),
        {

            "schema": "raw"

        },
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    exchange: Mapped[str] = mapped_column(String(20))
    symbol: Mapped[str] = mapped_column(String(20))
    timeframe: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20))
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    record_count: Mapped[int] = mapped_column( Integer, server_default=text("0"))
    error_message: Mapped[str | None] = mapped_column(Text)
