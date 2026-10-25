from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from app.models.features.indicator_values import IndicatorValue
from app.models.processed.candles import ProcessedCandle
from app.repositories.feature_data import FeatureDataRepository


class SimpleMovingAverageError(ValueError):
    """Raised when a simple moving average cannot be calculated safely."""


@dataclass(frozen=True)
class SmaCalculationResult:
    exchange: str
    symbol: str
    timeframe: str
    window: int
    processed_candle_count: int
    calculated_value_count: int
    inserted_value_count: int
    skipped_value_count: int


class SimpleMovingAverageService:
    INDICATOR_NAME = "sma"
    CALCULATION_VERSION = "v1"
    VALUE_PRECISION = Decimal("0.000000000001")

    def __init__(
        self,
        repository: FeatureDataRepository | None = None,
    ) -> None:
        self._repository = repository or FeatureDataRepository()

    def calculate_for_market(
        self,
        session: Session,
        *,
        exchange: str,
        symbol: str,
        timeframe: str,
        window: int,
    ) -> SmaCalculationResult:
        normalized_exchange = self._normalize_required_text(
            exchange,
            "exchange",
        ).lower()
        normalized_symbol = self._normalize_required_text(symbol, "symbol").upper()
        normalized_timeframe = self._normalize_required_text(timeframe, "timeframe")
        self._validate_window(window)

        try:
            candles = self._repository.get_processed_candles(
                session,
                exchange=normalized_exchange,
                symbol=normalized_symbol,
                timeframe=normalized_timeframe,
            )
            indicator_values = self.build_indicator_values(candles, window=window)
            inserted_value_count = (
                self._repository.insert_indicator_values_ignore_conflicts(
                    session,
                    indicator_values,
                )
            )
            session.commit()
        except Exception:
            session.rollback()
            raise

        return SmaCalculationResult(
            exchange=normalized_exchange,
            symbol=normalized_symbol,
            timeframe=normalized_timeframe,
            window=window,
            processed_candle_count=len(candles),
            calculated_value_count=len(indicator_values),
            inserted_value_count=inserted_value_count,
            skipped_value_count=len(indicator_values) - inserted_value_count,
        )

    def build_indicator_values(
        self,
        candles: Sequence[ProcessedCandle],
        *,
        window: int,
    ) -> list[IndicatorValue]:
        self._validate_window(window)

        if len(candles) < window:
            return []

        parameter_signature = f"window={window}"
        parameters = {"window": window}
        rolling_sum = Decimal("0")
        indicator_values: list[IndicatorValue] = []

        for index, candle in enumerate(candles):
            if candle.id is None:
                raise SimpleMovingAverageError(
                    "A processed candle must be stored before calculating features."
                )

            rolling_sum += candle.close

            if index >= window:
                rolling_sum -= candles[index - window].close

            if index < window - 1:
                continue

            average = (rolling_sum / Decimal(window)).quantize(
                self.VALUE_PRECISION,
                rounding=ROUND_HALF_UP,
            )
            indicator_values.append(
                IndicatorValue(
                    source_processed_candle_id=candle.id,
                    indicator_name=self.INDICATOR_NAME,
                    parameter_signature=parameter_signature,
                    parameters=parameters,
                    calculation_version=self.CALCULATION_VERSION,
                    value=average,
                )
            )

        return indicator_values

    @staticmethod
    def _normalize_required_text(value: str, field_name: str) -> str:
        normalized_value = value.strip()

        if not normalized_value:
            raise SimpleMovingAverageError(f"{field_name} must not be empty.")

        return normalized_value

    @staticmethod
    def _validate_window(window: int) -> None:
        if isinstance(window, bool) or not isinstance(window, int) or window <= 0:
            raise SimpleMovingAverageError("window must be a positive integer.")
