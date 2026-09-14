from collections.abc import Sequence
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.raw.candles import RawCandle
from app.models.raw.ingestion_runs import IngestionRun


class RawMarketDataRepository:
    """Contains only database persistence operations for raw market data."""

    def create_ingestion_run(self,session: Session,*,exchange: str,symbol: str,timeframe: str,start_time: datetime,end_time: datetime,) -> IngestionRun:
        run = IngestionRun(
            exchange=exchange,
            symbol=symbol,
            timeframe=timeframe,
            status="running",
            start_time=start_time,
            end_time=end_time,
            started_at=datetime.now(timezone.utc),
            record_count=0,
        )

        session.add(run)
        session.flush()

        return run

    def add_candles(self,session: Session,candles: Sequence[RawCandle],) -> None:
        session.add_all(candles)

    def mark_run_completed(self,run: IngestionRun,*,record_count: int,) -> None:
        run.status = "completed"
        run.record_count = record_count
        run.completed_at = datetime.now(timezone.utc)
        run.error_message = None

    def mark_run_failed(self,run: IngestionRun,*,error_message: str,) -> None:
        run.status = "failed"
        run.completed_at = datetime.now(timezone.utc)
        run.error_message = error_message