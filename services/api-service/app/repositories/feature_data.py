from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.features.indicator_values import IndicatorValue
from app.models.processed.candles import ProcessedCandle


class FeatureDataRepository:
    """Contains database operations for calculated research features."""

    def get_processed_candles(
        self,
        session: Session,
        *,
        exchange: str,
        symbol: str,
        timeframe: str,
    ) -> Sequence[ProcessedCandle]:
        statement = (
            select(ProcessedCandle)
            .where(
                ProcessedCandle.exchange == exchange,
                ProcessedCandle.symbol == symbol,
                ProcessedCandle.timeframe == timeframe,
            )
            .order_by(ProcessedCandle.open_time)
        )

        return session.scalars(statement).all()

    def insert_indicator_values_ignore_conflicts(
        self,
        session: Session,
        indicator_values: Sequence[IndicatorValue],
    ) -> int:
        if not indicator_values:
            return 0

        values = [
            {
                "source_processed_candle_id": value.source_processed_candle_id,
                "indicator_name": value.indicator_name,
                "parameter_signature": value.parameter_signature,
                "parameters": value.parameters,
                "calculation_version": value.calculation_version,
                "value": value.value,
            }
            for value in indicator_values
        ]

        statement = (
            insert(IndicatorValue)
            .values(values)
            .on_conflict_do_nothing()
            .returning(IndicatorValue.id)
        )

        return len(session.scalars(statement).all())
