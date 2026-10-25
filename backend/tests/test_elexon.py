from datetime import date

import httpx
import pytest

from app.elexon import ElexonError, fetch_fuelhh_wind, get_records, make_client


def client_returning(responses: list[httpx.Response], seen: list[httpx.Request]) -> httpx.Client:
    queue = iter(responses)

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return next(queue)

    return make_client(transport=httpx.MockTransport(handler))


def test_retries_after_server_error_then_succeeds():
    seen = []
    client = client_returning(
        [httpx.Response(503), httpx.Response(200, json=[{"generation": 1}])], seen
    )

    assert get_records(client, "/datasets/WINDFOR/stream", {}, backoff_s=0) == [{"generation": 1}]
    assert len(seen) == 2


def test_accepts_wrapped_response_shape():
    client = client_returning([httpx.Response(200, json={"data": [{"generation": 2}]})], [])

    assert get_records(client, "/datasets/WINDFOR/stream", {}, backoff_s=0) == [{"generation": 2}]


def test_gives_up_after_repeated_failures():
    client = client_returning([httpx.Response(429)] * 5, [])

    with pytest.raises(ElexonError, match="after 5 attempts"):
        get_records(client, "/datasets/WINDFOR/stream", {}, backoff_s=0)


def test_fuelhh_chunks_do_not_overlap():
    seen = []
    client = client_returning([httpx.Response(200, json=[])] * 2, seen)

    fetch_fuelhh_wind(client, date(2026, 1, 1), date(2026, 1, 10))

    windows = [(r.url.params["settlementDateFrom"], r.url.params["settlementDateTo"]) for r in seen]
    assert windows == [("2026-01-01", "2026-01-07"), ("2026-01-08", "2026-01-10")]
    assert all(r.url.params["fuelType"] == "WIND" for r in seen)
