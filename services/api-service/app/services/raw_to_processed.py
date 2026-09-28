from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy.orm import Session

from app.models.processed.candles import ProcessedCandle
from app.models.raw.candles import RawCandle
from app.repositories.processed_market_data import ProcessedMarketDataRepository
from app.repositories.raw_market_data import RawMarketDataRepository


class RawToProcessedError(ValueError):
    """Raised when raw market data cannot be processed safely."""


@dataclass(frozen=True)
class ProcessingResult:
    ingestion_run_id: int
    raw_candle_count: int
    inserted_candle_count: int
    skipped_candle_count: int


class RawToProcessedService:
    def __init__(
        self,
        raw_repository: RawMarketDataRepository | None = None,
        processed_repository: ProcessedMarketDataRepository | None = None,
    ) -> None:
        self._raw_repository = raw_repository or RawMarketDataRepository()
        self._processed_repository = (
            processed_repository or ProcessedMarketDataRepository()
        )

    def process_completed_run(self,session: Session,*,ingestion_run_id: int,) -> ProcessingResult:
        try:
            run = self._raw_repository.get_ingestion_run(
                session,
                run_id=ingestion_run_id,
            )

            if run is None:
                raise RawToProcessedError(
                    f"Ingestion run {ingestion_run_id} was not found."
                )

            if run.status != "completed":
                raise RawToProcessedError(
                    f"Ingestion run {ingestion_run_id} is not completed."
                )

            raw_candles = self._raw_repository.get_candles_for_run(
                session,
                ingestion_run_id=ingestion_run_id,
            )

            if len(raw_candles) != run.record_count:
                raise RawToProcessedError(
                    f"Ingestion run {ingestion_run_id} expected "
                    f"{run.record_count} raw candles but loaded "
                    f"{len(raw_candles)}."
                )

            processed_candles = [
                self.build_processed_candle(raw_candle)
                for raw_candle in raw_candles
            ]

            inserted_candle_count = (
                self._processed_repository.insert_candles_ignore_conflicts(
                    session,
                    processed_candles,
                )
            )

            session.commit()

        except Exception:
            session.rollback()
            raise

        return ProcessingResult(
            ingestion_run_id=ingestion_run_id,
            raw_candle_count=len(raw_candles),
            inserted_candle_count=inserted_candle_count,
            skipped_candle_count=len(raw_candles) - inserted_candle_count,
        )

    def build_processed_candle(self,raw_candle: RawCandle, ) -> ProcessedCandle:
        if raw_candle.id is None:
            raise RawToProcessedError(
                "A raw candle must be stored before it can be processed."
            )

        self._validate_timestamps(raw_candle)

        payload = raw_candle.source_payload

        if not isinstance(payload, list) or len(payload) < 7:
            raise RawToProcessedError(
                f"Raw candle {raw_candle.id} has an invalid Binance payload."
            )

        open_price = self._to_decimal(
            payload[1],
            field_name="open",
            raw_candle_id=raw_candle.id,
        )
        high_price = self._to_decimal(
            payload[2],
            field_name="high",
            raw_candle_id=raw_candle.id,
        )
        low_price = self._to_decimal(
            payload[3],
            field_name="low",
            raw_candle_id=raw_candle.id,
        )
        close_price = self._to_decimal(
            payload[4],
            field_name="close",
            raw_candle_id=raw_candle.id,
        )
        volume = self._to_decimal(
            payload[5],
            field_name="volume",
            raw_candle_id=raw_candle.id,
        )

        self._validate_ohlcv(
            raw_candle_id=raw_candle.id,
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            close_price=close_price,
            volume=volume,
        )

        processed_at = datetime.now(timezone.utc)

        if processed_at < raw_candle.close_time:
            raise RawToProcessedError(
                f"Raw candle {raw_candle.id} closes in the future."
            )

        return ProcessedCandle(
            source_raw_candle_id=raw_candle.id,
            exchange=raw_candle.exchange,
            symbol=raw_candle.symbol,
            timeframe=raw_candle.timeframe,
            open_time=raw_candle.open_time,
            close_time=raw_candle.close_time,
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            volume=volume,
            processed_at=processed_at,
        )

    @staticmethod
    def _to_decimal(value: Any,*,field_name: str,raw_candle_id: int,) -> Decimal:
        try:
            decimal_value = Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError) as error:
            raise RawToProcessedError(
                f"Raw candle {raw_candle_id} has an invalid "
                f"{field_name} value."
            ) from error

        if not decimal_value.is_finite():
            raise RawToProcessedError(
                f"Raw candle {raw_candle_id} has a non-finite "
                f"{field_name} value."
            )

        return decimal_value

    @staticmethod
    def _validate_timestamps(raw_candle: RawCandle) -> None:
        if raw_candle.open_time.tzinfo is None:
            raise RawToProcessedError(
                f"Raw candle {raw_candle.id} has a timezone-naive open time."
            )

        if raw_candle.close_time.tzinfo is None:
            raise RawToProcessedError(
                f"Raw candle {raw_candle.id} has a timezone-naive close time."
            )

        if raw_candle.open_time >= raw_candle.close_time:
            raise RawToProcessedError(
                f"Raw candle {raw_candle.id} has an invalid time range."
            )

    @staticmethod
    def _validate_ohlcv(
        *,
        raw_candle_id: int,
        open_price: Decimal,
        high_price: Decimal,
        low_price: Decimal,
        close_price: Decimal,
        volume: Decimal,
    ) -> None:
        if open_price <= 0 or high_price <= 0:
            raise RawToProcessedError(
                f"Raw candle {raw_candle_id} has a non-positive open or high price."
            )

        if low_price <= 0 or close_price <= 0:
            raise RawToProcessedError(
                f"Raw candle {raw_candle_id} has a non-positive low or close price."
            )

        if volume < 0:
            raise RawToProcessedError(
                f"Raw candle {raw_candle_id} has a negative volume."
            )

        if high_price < low_price:
            raise RawToProcessedError(
                f"Raw candle {raw_candle_id} has high below low."
            )

        if high_price < open_price or high_price < close_price:
            raise RawToProcessedError(
                f"Raw candle {raw_candle_id} has high below open or close."
            )

        if low_price > open_price or low_price > close_price:
            raise RawToProcessedError(
                f"Raw candle {raw_candle_id} has low above open or close."
            )
