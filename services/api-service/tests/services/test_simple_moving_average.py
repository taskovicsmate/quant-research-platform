from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.models.processed.candles import ProcessedCandle
from app.services.simple_moving_average import (
    SimpleMovingAverageError,
    SimpleMovingAverageService,
)


def build_processed_candle(
    *,
    candle_id: int | None,
    close: str,
    hour_offset: int,
) -> ProcessedCandle:
    open_time = datetime(2025, 1, 1, tzinfo=timezone.utc) + timedelta(
        hours=hour_offset
    )
    close_time = open_time + timedelta(hours=1) - timedelta(milliseconds=1)
    close_value = Decimal(close)

    return ProcessedCandle(
        id=candle_id,
        source_raw_candle_id=(candle_id or 1) + 1_000,
        exchange="binance",
        symbol="BTCUSDT",
        timeframe="1h",
        open_time=open_time,
        close_time=close_time,
        open=close_value,
        high=close_value,
        low=close_value,
        close=close_value,
        volume=Decimal("1"),
        processed_at=close_time,
    )


def test_build_indicator_values_calculates_sma_without_future_data() -> None:
    service = SimpleMovingAverageService()
    candles = [
        build_processed_candle(candle_id=1, close="1", hour_offset=0),
        build_processed_candle(candle_id=2, close="2", hour_offset=1),
        build_processed_candle(candle_id=3, close="3", hour_offset=2),
        build_processed_candle(candle_id=4, close="4", hour_offset=3),
    ]

    indicator_values = service.build_indicator_values(candles, window=3)

    assert [
        value.source_processed_candle_id for value in indicator_values
    ] == [3, 4]
    assert [value.value for value in indicator_values] == [
        Decimal("2.000000000000"),
        Decimal("3.000000000000"),
    ]
    assert all(value.indicator_name == "sma" for value in indicator_values)
    assert all(value.parameter_signature == "window=3" for value in indicator_values)
    assert all(value.parameters == {"window": 3} for value in indicator_values)
    assert all(value.calculation_version == "v1" for value in indicator_values)


def test_build_indicator_values_returns_nothing_before_window_is_complete() -> None:
    service = SimpleMovingAverageService()
    candles = [
        build_processed_candle(candle_id=1, close="1", hour_offset=0),
        build_processed_candle(candle_id=2, close="2", hour_offset=1),
    ]

    assert service.build_indicator_values(candles, window=3) == []


@pytest.mark.parametrize("window", [0, -1, True, "3"])
def test_build_indicator_values_rejects_invalid_windows(window: object) -> None:
    service = SimpleMovingAverageService()

    with pytest.raises(SimpleMovingAverageError, match="positive integer"):
        service.build_indicator_values([], window=window)  # type: ignore[arg-type]


def test_build_indicator_values_rejects_unsaved_processed_candle() -> None:
    service = SimpleMovingAverageService()
    unsaved_candle = build_processed_candle(
        candle_id=None,
        close="1",
        hour_offset=0,
    )

    with pytest.raises(SimpleMovingAverageError, match="must be stored"):
        service.build_indicator_values([unsaved_candle], window=1)
