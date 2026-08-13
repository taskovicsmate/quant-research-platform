from sqlalchemy import String
from sqlalchemy import Numeric
from decimal import Decimal

from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from sqlalchemy import DateTime
from sqlalchemy import CheckConstraint, UniqueConstraint
from app.db.database import Base

class ProcessedCandle(Base):
    __tablename__ = "candles"
    __table_args__ = (
        CheckConstraint("open_time < close_time", name="check_open_close_time"),
        CheckConstraint("high >= low", name="check_high_low"),
        CheckConstraint("high >= open", name="check_high_open"),
        CheckConstraint("high >= close", name="check_high_close"),
        CheckConstraint("low <= open", name="check_low_open"),
        CheckConstraint("low <= close", name="check_low_close"),
        CheckConstraint("volume >= 0", name="check_volume_non_negative"),
        CheckConstraint("processed_at >= open_time", name="check_processed_at_open_time"),
        CheckConstraint("processed_at >= close_time", name="check_processed_at_close_time"),
        UniqueConstraint("exchange", "symbol", "timeframe", "open_time", name="unique_candle_constraint"),
        {
            "schema": "processed"
        }
    )
    


    id: Mapped[int] = mapped_column(primary_key=True)

    exchange: Mapped[str] = mapped_column(String(20))

    symbol: Mapped[str] = mapped_column(String(20))

    timeframe: Mapped[str] = mapped_column(String(20))

    open_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    close_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    open: Mapped[Decimal] = mapped_column(Numeric(20, 10))

    high: Mapped[Decimal] = mapped_column(Numeric(20, 10))
 
    low: Mapped[Decimal] = mapped_column(Numeric(20, 10))

    close: Mapped[Decimal] = mapped_column(Numeric(20, 10))

    volume: Mapped[Decimal] = mapped_column(Numeric(20, 10))

    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))