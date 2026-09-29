from datetime import datetime, timezone
from typing import Any

import httpx
import pytest

from app.providers.binance import BinanceClient, BinanceClientError


START_TIME = datetime(2025, 1, 1, tzinfo=timezone.utc)
END_TIME = datetime(2025, 1, 1, 1, tzinfo=timezone.utc)
VALID_PAYLOAD = [
    [
        1735689600000,
        "100.00",
        "110.00",
        "90.00",
        "105.00",
        "42.00",
        1735693199999,
        "0",
        10,
        "0",
        "0",
        "0",
    ]
]


class FakeResponse:
    def __init__(self, payload: Any) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> Any:
        return self._payload


class FakeHttpClient:
    def __init__(
        self,
        *,
        response: FakeResponse | None = None,
        error: Exception | None = None,
    ) -> None:
        self.response = response
        self.error = error
        self.requests: list[tuple[str, dict[str, Any]]] = []
        self.closed = False

    def get(self, path: str, *, params: dict[str, Any]) -> FakeResponse:
        self.requests.append((path, params))

        if self.error is not None:
            raise self.error

        assert self.response is not None
        return self.response

    def close(self) -> None:
        self.closed = True


def build_client(fake_http_client: FakeHttpClient) -> BinanceClient:
    client = BinanceClient()
    client._client.close()
    client._client = fake_http_client  # type: ignore[assignment]
    return client


def test_fetch_klines_sends_expected_request_and_returns_valid_payload() -> None:
    fake_http_client = FakeHttpClient(response=FakeResponse(VALID_PAYLOAD))
    client = build_client(fake_http_client)

    try:
        payload = client.fetch_klines(
            symbol="btcusdt",
            interval="1h",
            start_time=START_TIME,
            end_time=END_TIME,
            limit=100,
        )
    finally:
        client.close()

    assert payload == VALID_PAYLOAD
    assert fake_http_client.closed is True
    assert fake_http_client.requests == [
        (
            BinanceClient.KLINES_PATH,
            {
                "symbol": "BTCUSDT",
                "interval": "1h",
                "startTime": 1735689600000,
                "endTime": 1735693200000,
                "limit": 100,
            },
        )
    ]


def test_fetch_klines_rejects_unexpected_response_payload() -> None:
    fake_http_client = FakeHttpClient(response=FakeResponse({"error": "invalid"}))
    client = build_client(fake_http_client)

    try:
        with pytest.raises(BinanceClientError, match="unexpected kline response format"):
            client.fetch_klines(
                symbol="BTCUSDT",
                interval="1h",
                start_time=START_TIME,
                end_time=END_TIME,
            )
    finally:
        client.close()


def test_fetch_klines_rejects_rows_with_invalid_shape() -> None:
    fake_http_client = FakeHttpClient(response=FakeResponse([["too", "short"]]))
    client = build_client(fake_http_client)

    try:
        with pytest.raises(BinanceClientError, match="unexpected kline row format"):
            client.fetch_klines(
                symbol="BTCUSDT",
                interval="1h",
                start_time=START_TIME,
                end_time=END_TIME,
            )
    finally:
        client.close()


def test_fetch_klines_wraps_http_errors() -> None:
    fake_http_client = FakeHttpClient(
        error=httpx.ConnectError("Binance is unavailable")
    )
    client = build_client(fake_http_client)

    try:
        with pytest.raises(
            BinanceClientError,
            match="Failed to retrieve kline data",
        ):
            client.fetch_klines(
                symbol="BTCUSDT",
                interval="1h",
                start_time=START_TIME,
                end_time=END_TIME,
            )
    finally:
        client.close()


@pytest.mark.parametrize(
    ("start_time", "end_time", "limit", "error_message"),
    [
        (
            datetime(2025, 1, 1),
            END_TIME,
            100,
            "start_time must be timezone-aware",
        ),
        (
            END_TIME,
            START_TIME,
            100,
            "start_time must be earlier than end_time",
        ),
        (
            START_TIME,
            END_TIME,
            BinanceClient.MAX_LIMIT + 1,
            "limit must be between",
        ),
    ],
)
def test_fetch_klines_rejects_invalid_requests(
    start_time: datetime,
    end_time: datetime,
    limit: int,
    error_message: str,
) -> None:
    fake_http_client = FakeHttpClient(response=FakeResponse(VALID_PAYLOAD))
    client = build_client(fake_http_client)

    try:
        with pytest.raises(ValueError, match=error_message):
            client.fetch_klines(
                symbol="BTCUSDT",
                interval="1h",
                start_time=start_time,
                end_time=end_time,
                limit=limit,
            )
    finally:
        client.close()

    assert fake_http_client.requests == []
