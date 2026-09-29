import argparse
import sys

from app.cli.ingestion_arguments import parse_ingestion_arguments
from app.db.database import SessionLocal, engine
from app.providers.binance import BinanceClient
from app.services.raw_ingestion import RawIngestionError, RawIngestionService
from app.services.raw_to_processed import (
    ProcessingResult,
    RawToProcessedError,
    RawToProcessedService,
)


def _ingest_raw_data(arguments: argparse.Namespace) -> int:
    session = SessionLocal()
    client = BinanceClient()
    service = RawIngestionService(client)

    try:
        return service.ingest_klines(
            session,
            symbol=arguments.symbol,
            timeframe=arguments.timeframe,
            start_time=arguments.start_time,
            end_time=arguments.end_time,
            limit=arguments.limit,
        )
    finally:
        client.close()
        session.close()


def _process_raw_run(ingestion_run_id: int) -> ProcessingResult:
    session = SessionLocal()
    service = RawToProcessedService()

    try:
        return service.process_completed_run(
            session,
            ingestion_run_id=ingestion_run_id,
        )
    finally:
        session.close()


def main() -> int:
    arguments = parse_ingestion_arguments(
        "Fetch Binance klines, store them as raw data, and process them."
    )

    try:
        ingestion_run_id = _ingest_raw_data(arguments)
        processing_result = _process_raw_run(ingestion_run_id)
    except RawIngestionError as error:
        print(f"Pipeline ingestion failed: {error}", file=sys.stderr)
        return 1
    except RawToProcessedError as error:
        print(f"Pipeline processing failed: {error}", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"Unexpected pipeline failure: {error}", file=sys.stderr)
        return 1
    finally:
        engine.dispose()

    print(f"Raw ingestion run completed: {ingestion_run_id}")
    print(f"Raw candle count: {processing_result.raw_candle_count}")
    print(
        "Inserted processed candle count: "
        f"{processing_result.inserted_candle_count}"
    )
    print(
        "Skipped processed candle count: "
        f"{processing_result.skipped_candle_count}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
