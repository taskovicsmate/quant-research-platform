from datetime import datetime, timezone
from typing import Any, cast

import httpx


class BinanceClientError(RuntimeError):
    """Raised when Binance market-data retrieval fails."""


class BinanceClient:
    BASE_URL = "https://data-api.binance.vision"
    KLINES_PATH = "/api/v3/klines"
    MAX_LIMIT = 1_000

    def __init__(self, base_url: str = BASE_URL, timeout_seconds: float = 10.0,) -> None:
        self._client = httpx.Client(base_url=base_url,timeout=timeout_seconds,)

    def fetch_klines(self, * , symbol: str, interval: str, start_time: datetime, end_time: datetime, limit: int = MAX_LIMIT,) -> list[list[Any]]:
        self._validate_request(symbol=symbol,interval=interval,start_time=start_time,end_time=end_time,limit=limit,)

        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "startTime": self._to_unix_milliseconds(start_time),
            "endTime": self._to_unix_milliseconds(end_time),
            "limit": limit,
        }

        try:
            response = self._client.get(self.KLINES_PATH, params=params)
            response.raise_for_status()
        except httpx.HTTPError as error:
            raise BinanceClientError(
                "Failed to retrieve kline data from Binance."
            ) from error

        try:
            payload = response.json()
        except ValueError as error:
            raise BinanceClientError(
                "Binance returned an invalid JSON response."
            ) from error

        if not isinstance(payload, list):
            raise BinanceClientError(
                "Binance returned an unexpected kline response format."
            )

        if not all(isinstance(row, list) and len(row) == 12 for row in payload):
            raise BinanceClientError(
                "Binance returned an unexpected kline row format."
            )

        return cast(list[list[Any]], payload)

    def close(self) -> None:
        self._client.close()

    def _validate_request(self,*,symbol: str,interval: str,start_time: datetime, end_time: datetime,limit: int,) -> None:
        if not symbol.strip():
            raise ValueError("symbol must not be empty.")

        if not interval.strip():
            raise ValueError("interval must not be empty.")

        if not self._is_timezone_aware(start_time):
            raise ValueError("start_time must be timezone-aware.")

        if not self._is_timezone_aware(end_time):
            raise ValueError("end_time must be timezone-aware.")

        if start_time >= end_time:
            raise ValueError("start_time must be earlier than end_time.")

        if not 1 <= limit <= self.MAX_LIMIT:
            raise ValueError(
                f"limit must be between 1 and {self.MAX_LIMIT}."
            )

    @staticmethod
    def _is_timezone_aware(value: datetime) -> bool:
        return value.tzinfo is not None and value.utcoffset() is not None

    @staticmethod
    def _to_unix_milliseconds(value: datetime) -> int:
        return int(value.astimezone(timezone.utc).timestamp() * 1_000)