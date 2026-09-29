from datetime import datetime, timezone
from typing import Any

import pytest
from sqlalchemy import select

from app.db.database import SessionLocal
from app.models.processed.candles import ProcessedCandle
from app.models.raw.candles import RawCandle
from app.models.raw.ingestion_runs import IngestionRun
from app.services.raw_ingestion import RawIngestionService
from app.services.raw_to_processed import RawToProcessedService


START_TIME = datetime(2025, 1, 1, tzinfo=timezone.utc)
END_TIME = datetime(2025, 1, 1, 2, tzinfo=timezone.utc)
BINANCE_PAYLOADS = [
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
    def fetch_klines(self, **_: Any) -> list[list[Any]]:
        return BINANCE_PAYLOADS


@pytest.mark.integration
def test_raw_to_processed_pipeline_persists_and_is_idempotent(
    integration_database: None,
) -> None:
    ingestion_session = SessionLocal()

    try:
        ingestion_run_id = RawIngestionService(
            FakeBinanceClient(),  # type: ignore[arg-type]
        ).ingest_klines(
            ingestion_session,
            symbol="BTCUSDT",
            timeframe="1h",
            start_time=START_TIME,
            end_time=END_TIME,
            limit=100,
        )
    finally:
        ingestion_session.close()

    processing_session = SessionLocal()

    try:
        first_result = RawToProcessedService().process_completed_run(
            processing_session,
            ingestion_run_id=ingestion_run_id,
        )
    finally:
        processing_session.close()

    assert first_result.raw_candle_count == 2
    assert first_result.inserted_candle_count == 2
    assert first_result.skipped_candle_count == 0

    verification_session = SessionLocal()

    try:
        run = verification_session.get(IngestionRun, ingestion_run_id)
        raw_candles = verification_session.scalars(
            select(RawCandle)
            .where(RawCandle.ingestion_run_id == ingestion_run_id)
            .order_by(RawCandle.source_row_number)
        ).all()
        processed_candles = verification_session.scalars(
            select(ProcessedCandle).order_by(ProcessedCandle.open_time)
        ).all()
    finally:
        verification_session.close()

    assert run is not None
    assert run.status == "completed"
    assert run.record_count == 2
    assert [candle.source_row_number for candle in raw_candles] == [0, 1]
    assert [candle.source_payload for candle in raw_candles] == BINANCE_PAYLOADS
    assert len(processed_candles) == 2
    assert {
        candle.source_raw_candle_id for candle in processed_candles
    } == {candle.id for candle in raw_candles}

    retry_session = SessionLocal()

    try:
        retry_result = RawToProcessedService().process_completed_run(
            retry_session,
            ingestion_run_id=ingestion_run_id,
        )
    finally:
        retry_session.close()

    assert retry_result.raw_candle_count == 2
    assert retry_result.inserted_candle_count == 0
    assert retry_result.skipped_candle_count == 2
