import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.core.config import DATABASE_URL


TEST_DATABASE_NAME = "quant_research_test"


def _assert_test_database() -> None:
    database_name = os.getenv("POSTGRES_DB")

    if database_name != TEST_DATABASE_NAME:
        raise pytest.UsageError(
            "Integration tests require POSTGRES_DB=quant_research_test. "
            "Refusing to use a different database."
        )


def _run_migrations() -> None:
    api_service_directory = Path(__file__).resolve().parents[2]
    alembic_config = Config(str(api_service_directory / "alembic.ini"))

    command.upgrade(alembic_config, "head")


def _truncate_test_data(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                "TRUNCATE TABLE processed.candles, raw.candles, "
                "raw.ingestion_runs RESTART IDENTITY"
            )
        )


@pytest.fixture
def integration_database() -> None:
    _assert_test_database()
    _run_migrations()

    engine = create_engine(DATABASE_URL)
    _truncate_test_data(engine)

    try:
        yield
    finally:
        _truncate_test_data(engine)
        engine.dispose()
