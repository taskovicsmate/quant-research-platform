import argparse
import sys
from datetime import datetime, timezone

from app.db.database import SessionLocal, engine
from app.providers.binance import BinanceClient
from app.services.raw_ingestion import RawIngestionError, RawIngestionService


def _non_empty_string(value: str) -> str:
    if not value.strip():
        raise argparse.ArgumentTypeError("must not be empty")

    return value


def _parse_datetime(value: str) -> datetime:
    try:
        parsed_value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "must be an ISO 8601 datetime, for example "
            "2025-01-01T00:00:00+00:00"
        ) from error

    if parsed_value.tzinfo is None or parsed_value.utcoffset() is None:
        raise argparse.ArgumentTypeError("must include a timezone offset")

    return parsed_value.astimezone(timezone.utc)


def _limit(value: str) -> int:
    try:
        parsed_value = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be an integer") from error

    if not 1 <= parsed_value <= BinanceClient.MAX_LIMIT:
        raise argparse.ArgumentTypeError(
            f"must be between 1 and {BinanceClient.MAX_LIMIT}"
        )

    return parsed_value


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch Binance klines and store them as an immutable raw run."
    )
    parser.add_argument(
        "--symbol",
        required=True,
        type=_non_empty_string,
        help="Market symbol, for example BTCUSDT.",
    )
    parser.add_argument(
        "--timeframe",
        required=True,
        type=_non_empty_string,
        help="Binance kline interval, for example 1h.",
    )
    parser.add_argument(
        "--start-time",
        required=True,
        type=_parse_datetime,
        help="ISO 8601 start time with timezone, for example 2025-01-01T00:00:00+00:00.",
    )
    parser.add_argument(
        "--end-time",
        required=True,
        type=_parse_datetime,
        help="ISO 8601 end time with timezone, for example 2025-01-02T00:00:00+00:00.",
    )
    parser.add_argument(
        "--limit",
        type=_limit,
        default=BinanceClient.MAX_LIMIT,
        help=f"Maximum number of candles to request, from 1 to {BinanceClient.MAX_LIMIT}.",
    )

    arguments = parser.parse_args()

    if arguments.start_time >= arguments.end_time:
        parser.error("--start-time must be earlier than --end-time")

    return arguments


def main() -> int:
    arguments = parse_arguments()
    session = SessionLocal()
    client = BinanceClient()
    service = RawIngestionService(client)

    try:
        run_id = service.ingest_klines(
            session,
            symbol=arguments.symbol,
            timeframe=arguments.timeframe,
            start_time=arguments.start_time,
            end_time=arguments.end_time,
            limit=arguments.limit,
        )
    except RawIngestionError as error:
        print(f"Ingestion failed: {error}", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"Unexpected ingestion failure: {error}", file=sys.stderr)
        return 1
    finally:
        client.close()
        session.close()
        engine.dispose()

    print(f"Raw ingestion run completed: {run_id}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
