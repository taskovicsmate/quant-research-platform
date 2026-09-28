from collections.abc import Sequence

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.processed.candles import ProcessedCandle


class ProcessedMarketDataRepository:
    """Contains only database persistence operations for processed market data."""

    def insert_candles_ignore_conflicts(
        self,
        session: Session,
        candles: Sequence[ProcessedCandle],
    ) -> int:
        if not candles:
            return 0

        values = [
            {
                "source_raw_candle_id": candle.source_raw_candle_id,
                "exchange": candle.exchange,
                "symbol": candle.symbol,
                "timeframe": candle.timeframe,
                "open_time": candle.open_time,
                "close_time": candle.close_time,
                "open": candle.open,
                "high": candle.high,
                "low": candle.low,
                "close": candle.close,
                "volume": candle.volume,
                "processed_at": candle.processed_at,
            }
            for candle in candles
        ]

        statement = (
            insert(ProcessedCandle)
            .values(values)
            .on_conflict_do_nothing()
            .returning(ProcessedCandle.id)
        )

        return len(session.scalars(statement).all())
