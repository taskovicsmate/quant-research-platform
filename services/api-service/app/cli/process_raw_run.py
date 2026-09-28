import argparse
import sys

from app.db.database import SessionLocal, engine
from app.services.raw_to_processed import RawToProcessedError, RawToProcessedService


def _positive_int(value: str) -> int:
    try:
        integer_value = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "must be a positive integer"
        ) from error

    if integer_value <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")

    return integer_value


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transform one completed raw ingestion run into processed candles."
    )
    parser.add_argument(
        "--run-id",
        required=True,
        type=_positive_int,
        help="ID of the completed raw ingestion run to process.",
    )

    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    session = SessionLocal()
    service = RawToProcessedService()

    try:
        result = service.process_completed_run(
            session,
            ingestion_run_id=arguments.run_id,
        )
    except RawToProcessedError as error:
        print(f"Processing failed: {error}", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"Unexpected processing failure: {error}", file=sys.stderr)
        return 1
    finally:
        session.close()
        engine.dispose()

    print(f"Ingestion run id: {result.ingestion_run_id}")
    print(f"Raw candle count: {result.raw_candle_count}")
    print(f"Inserted processed candle count: {result.inserted_candle_count}")
    print(f"Skipped candle count: {result.skipped_candle_count}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
