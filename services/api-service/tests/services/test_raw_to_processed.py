from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.models.raw.candles import RawCandle
from app.services.raw_to_processed import RawToProcessedError, RawToProcessedService


def build_raw_candle(
    *,
    candle_id: int | None = 101,
    open_time: datetime | None = None,
    close_time: datetime | None = None,
    payload: list[object] | None = None,
) -> RawCandle:
    return RawCandle(
        id=candle_id,
        ingestion_run_id=10,
        source_row_number=0,
        exchange="binance",
        symbol="BTCUSDT",
        timeframe="1h",
        open_time=open_time or datetime(2025, 1, 1, tzinfo=timezone.utc),
        close_time=close_time
        or datetime(2025, 1, 1, 0, 59, 59, 999000, tzinfo=timezone.utc),
        source_payload=payload
        or [
            1735689600000,
            "100.10",
            "110.50",
            "90.00",
            "105.25",
            "42.75",
            1735693199999,
        ],
    )


@pytest.fixture
def service() -> RawToProcessedService:
    return RawToProcessedService()


def test_build_processed_candle_maps_valid_raw_candle(
    service: RawToProcessedService,
) -> None:
    raw_candle = build_raw_candle()

    processed_candle = service.build_processed_candle(raw_candle)

    assert processed_candle.source_raw_candle_id == raw_candle.id
    assert processed_candle.exchange == "binance"
    assert processed_candle.symbol == "BTCUSDT"
    assert processed_candle.timeframe == "1h"
    assert processed_candle.open_time == raw_candle.open_time
    assert processed_candle.close_time == raw_candle.close_time
    assert processed_candle.open == Decimal("100.10")
    assert processed_candle.high == Decimal("110.50")
    assert processed_candle.low == Decimal("90.00")
    assert processed_candle.close == Decimal("105.25")
    assert processed_candle.volume == Decimal("42.75")
    assert processed_candle.processed_at.tzinfo is not None
    assert processed_candle.processed_at >= raw_candle.close_time


@pytest.mark.parametrize(
    ("payload", "error_message"),
    [
        (
            [1735689600000, "100", "89", "90", "95", "1", 1735693199999],
            "high below low",
        ),
        (
            [1735689600000, "0", "110", "90", "95", "1", 1735693199999],
            "non-positive open or high price",
        ),
        (
            [1735689600000, "100", "110", "90", "105", "-1", 1735693199999],
            "negative volume",
        ),
        (
            [1735689600000, "100", "110", "90", "NaN", "1", 1735693199999],
            "non-finite close value",
        ),
    ],
)
def test_build_processed_candle_rejects_invalid_ohlcv_values(
    service: RawToProcessedService,
    payload: list[object],
    error_message: str,
) -> None:
    raw_candle = build_raw_candle(payload=payload)

    with pytest.raises(RawToProcessedError, match=error_message):
        service.build_processed_candle(raw_candle)


def test_build_processed_candle_rejects_timezone_naive_timestamp(
    service: RawToProcessedService,
) -> None:
    raw_candle = build_raw_candle(
        open_time=datetime(2025, 1, 1),
    )

    with pytest.raises(RawToProcessedError, match="timezone-naive open time"):
        service.build_processed_candle(raw_candle)


def test_build_processed_candle_rejects_invalid_time_range(
    service: RawToProcessedService,
) -> None:
    raw_candle = build_raw_candle(
        open_time=datetime(2025, 1, 1, 1, tzinfo=timezone.utc),
        close_time=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )

    with pytest.raises(RawToProcessedError, match="invalid time range"):
        service.build_processed_candle(raw_candle)


def test_build_processed_candle_rejects_unsaved_raw_candle(
    service: RawToProcessedService,
) -> None:
    raw_candle = build_raw_candle(candle_id=None)

    with pytest.raises(RawToProcessedError, match="must be stored"):
        service.build_processed_candle(raw_candle)


def test_build_processed_candle_rejects_invalid_payload_shape(
    service: RawToProcessedService,
) -> None:
    raw_candle = build_raw_candle(payload=["invalid"])

    with pytest.raises(RawToProcessedError, match="invalid Binance payload"):
        service.build_processed_candle(raw_candle)
