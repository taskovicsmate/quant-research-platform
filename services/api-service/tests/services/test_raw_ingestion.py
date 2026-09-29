from datetime import datetime, timezone
from typing import Any

import pytest

from app.models.raw.ingestion_runs import IngestionRun
from app.services.raw_ingestion import RawIngestionError, RawIngestionService


START_TIME = datetime(2025, 1, 1, tzinfo=timezone.utc)
END_TIME = datetime(2025, 1, 1, 2, tzinfo=timezone.utc)
VALID_PAYLOADS = [
    [
        1735689600000,
        "100.00",
        "110.00",
        "90.00",
        "105.00",
        "42.00",
        1735693199999,
        "0",
        10,
        "0",
        "0",
        "0",
    ],
    [
        1735693200000,
        "105.00",
        "115.00",
        "100.00",
        "110.00",
        "30.00",
        1735696799999,
        "0",
        12,
        "0",
        "0",
        "0",
    ],
]


class FakeBinanceClient:
    def __init__(
        self,
        *,
        payloads: list[list[Any]] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.payloads = payloads or []
        self.error = error
        self.requests: list[dict[str, Any]] = []

    def fetch_klines(self, **kwargs: Any) -> list[list[Any]]:
        self.requests.append(kwargs)

        if self.error is not None:
            raise self.error

        return self.payloads


class FakeSession:
    def __init__(self, run: IngestionRun) -> None:
        self.run = run
        self.commit_count = 0
        self.rollback_count = 0
        self.get_calls: list[tuple[type[Any], int]] = []

    def commit(self) -> None:
        self.commit_count += 1

    def rollback(self) -> None:
        self.rollback_count += 1

    def get(self, model: type[Any], run_id: int) -> IngestionRun | None:
        self.get_calls.append((model, run_id))

        if model is IngestionRun and run_id == self.run.id:
            return self.run

        return None


class FakeRawMarketDataRepository:
    def __init__(self, run: IngestionRun) -> None:
        self.run = run
        self.create_arguments: dict[str, Any] | None = None
        self.candles: list[Any] = []

    def create_ingestion_run(self, session: FakeSession, **kwargs: Any) -> IngestionRun:
        self.create_arguments = kwargs
        return self.run

    def add_candles(self, session: FakeSession, candles: list[Any]) -> None:
        self.candles.extend(candles)

    def mark_run_completed(self, run: IngestionRun, *, record_count: int) -> None:
        run.status = "completed"
        run.record_count = record_count

    def mark_run_failed(self, run: IngestionRun, *, error_message: str) -> None:
        run.status = "failed"
        run.error_message = error_message


def build_run() -> IngestionRun:
    return IngestionRun(
        id=42,
        exchange="binance",
        symbol="BTCUSDT",
        timeframe="1h",
        status="running",
        start_time=START_TIME,
        end_time=END_TIME,
        record_count=0,
    )


def test_ingest_klines_creates_completed_raw_run_and_candles() -> None:
    run = build_run()
    client = FakeBinanceClient(payloads=VALID_PAYLOADS)
    repository = FakeRawMarketDataRepository(run)
    session = FakeSession(run)
    service = RawIngestionService(client, repository)  # type: ignore[arg-type]

    run_id = service.ingest_klines(
        session,  # type: ignore[arg-type]
        symbol=" btcusdt ",
        timeframe=" 1h ",
        start_time=START_TIME,
        end_time=END_TIME,
        limit=100,
    )

    assert run_id == 42
    assert repository.create_arguments == {
        "exchange": "binance",
        "symbol": "BTCUSDT",
        "timeframe": "1h",
        "start_time": START_TIME,
        "end_time": END_TIME,
    }
    assert client.requests == [
        {
            "symbol": "BTCUSDT",
            "interval": "1h",
            "start_time": START_TIME,
            "end_time": END_TIME,
            "limit": 100,
        }
    ]
    assert run.status == "completed"
    assert run.record_count == 2
    assert session.commit_count == 2
    assert session.rollback_count == 0
    assert [candle.source_row_number for candle in repository.candles] == [0, 1]
    assert [candle.ingestion_run_id for candle in repository.candles] == [42, 42]
    assert repository.candles[0].open_time == START_TIME
    assert repository.candles[0].close_time == datetime(
        2025,
        1,
        1,
        0,
        59,
        59,
        999000,
        tzinfo=timezone.utc,
    )
    assert repository.candles[0].source_payload == VALID_PAYLOADS[0]


def test_ingest_klines_marks_run_failed_when_client_fails() -> None:
    run = build_run()
    client = FakeBinanceClient(error=RuntimeError("network unavailable"))
    repository = FakeRawMarketDataRepository(run)
    session = FakeSession(run)
    service = RawIngestionService(client, repository)  # type: ignore[arg-type]

    with pytest.raises(RawIngestionError, match="Raw ingestion run 42 failed"):
        service.ingest_klines(
            session,  # type: ignore[arg-type]
            symbol="BTCUSDT",
            timeframe="1h",
            start_time=START_TIME,
            end_time=END_TIME,
        )

    assert repository.candles == []
    assert run.status == "failed"
    assert run.error_message == "network unavailable"
    assert session.commit_count == 2
    assert session.rollback_count == 1
