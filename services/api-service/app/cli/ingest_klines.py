import sys

from app.cli.ingestion_arguments import parse_ingestion_arguments
from app.db.database import SessionLocal, engine
from app.providers.binance import BinanceClient
from app.services.raw_ingestion import RawIngestionError, RawIngestionService


def main() -> int:
    arguments = parse_ingestion_arguments(
        "Fetch Binance klines and store them as an immutable raw run."
    )
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
