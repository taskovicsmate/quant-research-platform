from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class RawCandle(Base):
    __tablename__ = "candles"
    __table_args__ = (
        UniqueConstraint("ingestion_run_id","source_row_number",name="uq_raw_candles_ingestion_row",),
        Index("ix_raw_candles_market_open_time","exchange","symbol","timeframe","open_time",),
        {
            "schema": "raw"
        },
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    ingestion_run_id: Mapped[int] = mapped_column(ForeignKey("raw.ingestion_runs.id", ondelete="RESTRICT"))
    source_row_number: Mapped[int] = mapped_column(Integer)
    exchange: Mapped[str] = mapped_column(String(20))
    symbol: Mapped[str] = mapped_column(String(20))
    timeframe: Mapped[str] = mapped_column(String(20))
    open_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    close_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    source_payload: Mapped[list[Any]] = mapped_column(JSONB)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
