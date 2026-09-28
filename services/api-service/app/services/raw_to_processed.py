from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from app.models.processed.candles import ProcessedCandle
from app.models.raw.candles import RawCandle


class RawToProcessedError(ValueError):
    """Raised when a raw candle cannot be transformed safely."""


class RawToProcessedService:
    def build_processed_candle(self, raw_candle: RawCandle, ) -> ProcessedCandle:
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
    def _to_decimal( value: Any, *,field_name: str, raw_candle_id: int, ) -> Decimal:
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
    def _validate_ohlcv(*,raw_candle_id: int,open_price: Decimal, high_price: Decimal,low_price: Decimal, close_price: Decimal, volume: Decimal, ) -> None:
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