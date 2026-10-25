"""Download FUELHH wind actuals and WINDFOR forecasts from Elexon's Insights API."""

import time
from collections.abc import Iterator
from datetime import date, datetime, timedelta

import httpx

from app.config import ELEXON_BASE_URL

RETRY_STATUSES = {429, 500, 502, 503, 504}
MAX_ATTEMPTS = 5
CHUNK_DAYS = 7


class ElexonError(RuntimeError):
    pass


def make_client(transport: httpx.BaseTransport | None = None) -> httpx.Client:
    return httpx.Client(base_url=ELEXON_BASE_URL, timeout=30.0, transport=transport)


def get_records(
    client: httpx.Client, path: str, params: dict[str, str], backoff_s: float = 1.0
) -> list[dict]:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = client.get(path, params=params)
        except httpx.TransportError as error:
            failure = str(error)
        else:
            if response.status_code not in RETRY_STATUSES:
                response.raise_for_status()
                return _unwrap(response.json())
            failure = f"HTTP {response.status_code}"
        if attempt < MAX_ATTEMPTS:
            time.sleep(backoff_s * 2 ** (attempt - 1))
    raise ElexonError(f"{path} failed after {MAX_ATTEMPTS} attempts: {failure}")


def fetch_windfor(client: httpx.Client, published_from: date, published_to: date) -> list[dict]:
    records = []
    for start, end in _date_chunks(published_from, published_to):
        params = {
            "publishDateTimeFrom": _iso_midnight(start),
            "publishDateTimeTo": _iso_midnight(end),
        }
        records.extend(get_records(client, "/datasets/WINDFOR/stream", params))
    return records


def fetch_fuelhh_wind(
    client: httpx.Client, settlement_from: date, settlement_to: date
) -> list[dict]:
    records = []
    for start, end in _date_chunks(settlement_from, settlement_to):
        # settlementDateTo is inclusive, so stop the chunk the day before the next one starts.
        params = {
            "settlementDateFrom": start.isoformat(),
            "settlementDateTo": (end - timedelta(days=1)).isoformat(),
            "fuelType": "WIND",
        }
        records.extend(get_records(client, "/datasets/FUELHH/stream", params))
    return records


def _unwrap(payload: list | dict) -> list[dict]:
    # Stream endpoints return a bare array; the non-stream ones wrap it in "data".
    if isinstance(payload, dict):
        return payload["data"]
    return payload


def _date_chunks(first: date, last: date) -> Iterator[tuple[date, date]]:
    """Half-open [start, end) windows covering first..last inclusive."""
    start = first
    stop = last + timedelta(days=1)
    while start < stop:
        end = min(start + timedelta(days=CHUNK_DAYS), stop)
        yield start, end
        start = end


def _iso_midnight(day: date) -> str:
    return datetime.combine(day, datetime.min.time()).strftime("%Y-%m-%dT%H:%MZ")
