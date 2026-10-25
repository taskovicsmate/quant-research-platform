import argparse
import sys

from app.db.database import SessionLocal, engine
from app.services.simple_moving_average import (
    SimpleMovingAverageError,
    SimpleMovingAverageService,
)


def _non_empty_string(value: str) -> str:
    if not value.strip():
        raise argparse.ArgumentTypeError("must not be empty")

    return value


def _positive_integer(value: str) -> int:
    try:
        parsed_value = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be a positive integer") from error

    if parsed_value <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")

    return parsed_value


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calculate and store simple moving average indicator values."
    )
    parser.add_argument(
        "--exchange",
        default="binance",
        type=_non_empty_string,
        help="Exchange name. Defaults to binance.",
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
        help="Candle timeframe, for example 1h.",
    )
    parser.add_argument(
        "--window",
        required=True,
        type=_positive_integer,
        help="Number of candles in the moving-average window.",
    )

    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    session = SessionLocal()
    service = SimpleMovingAverageService()

    try:
        result = service.calculate_for_market(
            session,
            exchange=arguments.exchange,
            symbol=arguments.symbol,
            timeframe=arguments.timeframe,
            window=arguments.window,
        )
    except SimpleMovingAverageError as error:
        print(f"SMA calculation failed: {error}", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"Unexpected SMA calculation failure: {error}", file=sys.stderr)
        return 1
    finally:
        session.close()
        engine.dispose()

    print(f"Market: {result.exchange} {result.symbol} {result.timeframe}")
    print(f"SMA window: {result.window}")
    print(f"Processed candle count: {result.processed_candle_count}")
    print(f"Calculated SMA value count: {result.calculated_value_count}")
    print(f"Inserted SMA value count: {result.inserted_value_count}")
    print(f"Skipped SMA value count: {result.skipped_value_count}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
