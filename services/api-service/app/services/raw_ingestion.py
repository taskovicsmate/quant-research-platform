from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.raw.candles import RawCandle
from app.models.raw.ingestion_runs import IngestionRun
from app.providers.binance import BinanceClient
from app.repositories.raw_market_data import RawMarketDataRepository


class RawIngestionError(RuntimeError):
    """Raised when a raw market-data ingestion cannot complete."""


class RawIngestionService:
    EXCHANGE = "binance"

    def __init__(self,client: BinanceClient,repository: RawMarketDataRepository | None = None,) -> None:
        self._client = client
        self._repository = repository or RawMarketDataRepository()

    def ingest_klines(self,session: Session,*,symbol: str,timeframe: str,start_time: datetime,end_time: datetime,limit: int = BinanceClient.MAX_LIMIT,) -> int:
        normalized_symbol = symbol.strip().upper()
        normalized_timeframe = timeframe.strip()

        run_id = self._start_ingestion_run(session,symbol=normalized_symbol,timeframe=normalized_timeframe,start_time=start_time,end_time=end_time,)

        try:
            payloads = self._client.fetch_klines(
                symbol=normalized_symbol,
                interval=normalized_timeframe,
                start_time=start_time,
                end_time=end_time,
                limit=limit,
            )

            candles = self._build_raw_candles(
                ingestion_run_id=run_id,
                symbol=normalized_symbol,
                timeframe=normalized_timeframe,
                payloads=payloads,
            )

            self._repository.add_candles(session, candles)

            run = session.get(IngestionRun, run_id)
            if run is None:
                raise RawIngestionError(
                    f"Ingestion run {run_id} could not be found."
                )

            self._repository.mark_run_completed(run,record_count=len(candles))

            session.commit()

        except Exception as error:
            session.rollback()
            self._record_failure(
                session,
                run_id=run_id,
                error=error,
            )

            raise RawIngestionError(
                f"Raw ingestion run {run_id} failed."
            ) from error

        return run_id

    def _start_ingestion_run(self,session: Session,*,symbol: str,timeframe: str,start_time: datetime,end_time: datetime,) -> int:
        try:
            run = self._repository.create_ingestion_run(
                session,
                exchange=self.EXCHANGE,
                symbol=symbol,
                timeframe=timeframe,
                start_time=start_time,
                end_time=end_time,
            )

            run_id = run.id
            session.commit()

        except Exception:
            session.rollback()
            raise

        return run_id

    def _record_failure(self,session: Session,*,run_id: int,error: Exception,) -> None:
        try:
            run = session.get(IngestionRun, run_id)

            if run is None:
                return

            self._repository.mark_run_failed(
                run,
                error_message=str(error) or type(error).__name__,
            )

            session.commit()

        except Exception:
            session.rollback()

    def _build_raw_candles(self,*,ingestion_run_id: int,symbol: str,timeframe: str,payloads: list[list[Any]],) -> list[RawCandle]:
        return [
            RawCandle(
                ingestion_run_id=ingestion_run_id,
                source_row_number=source_row_number,
                exchange=self.EXCHANGE,
                symbol=symbol,
                timeframe=timeframe,
                open_time=self._from_unix_milliseconds(payload[0]),
                close_time=self._from_unix_milliseconds(payload[6]),
                source_payload=list(payload),
            )
            for source_row_number, payload in enumerate(payloads)
        ]

    @staticmethod
    def _from_unix_milliseconds(value: Any) -> datetime:
        try:
            timestamp_milliseconds = int(value)
        except (TypeError, ValueError) as error:
            raise ValueError(
                "Binance returned an invalid candle timestamp."
            ) from error

        return datetime.fromtimestamp(
            timestamp_milliseconds / 1_000,
            tz=timezone.utc,
        )