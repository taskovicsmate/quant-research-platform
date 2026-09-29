import argparse
from datetime import datetime, timezone

from app.providers.binance import BinanceClient


def parse_ingestion_arguments(description: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=description)
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
        help=(
            "ISO 8601 start time with timezone, for example "
            "2025-01-01T00:00:00+00:00."
        ),
    )
    parser.add_argument(
        "--end-time",
        required=True,
        type=_parse_datetime,
        help=(
            "ISO 8601 end time with timezone, for example "
            "2025-01-02T00:00:00+00:00."
        ),
    )
    parser.add_argument(
        "--limit",
        type=_limit,
        default=BinanceClient.MAX_LIMIT,
        help=(
            "Maximum number of candles to request, from 1 to "
            f"{BinanceClient.MAX_LIMIT}."
        ),
    )

    arguments = parser.parse_args()

    if arguments.start_time >= arguments.end_time:
        parser.error("--start-time must be earlier than --end-time")

    return arguments


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
