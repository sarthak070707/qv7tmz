from datetime import date, datetime, time
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app import service
from app.config import CUTOFF_OPTIONS, DEFAULT_CUTOFF, FIRST_DELIVERY_DAY, LAST_DELIVERY_DAY
from app.schemas import AccuracyResponse, DayResponse, DeliveryDays, Health
from app.snapshot import SnapshotMissing

CUTOFF_LABELS = {
    "epex_60": "EPEX Day-Ahead 60 min (09:20)",
    "n2ex": "N2EX Day-Ahead Hourly (09:50)",
    "epex_30": "EPEX Day-Ahead 30 min (15:30)",
}

app = FastAPI(title="UK Wind Forecast Decision Portal API")
# Read-only public data, so any origin may call it.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"])

CutoffParam = Annotated[
    str,
    Query(
        pattern=r"^([01]\d|2[0-3]):[0-5]\d$",
        description="Decision cutoff on D-1, UK time, as HH:MM",
    ),
]


@app.get("/api/health", response_model=Health)
def health() -> Health:
    try:
        ingested_at = service.snapshot().ingested_at
    except SnapshotMissing:
        return Health(status="no_data", data_as_of=None)
    return Health(status="ok", data_as_of=ingested_at)


@app.get("/api/delivery-days", response_model=DeliveryDays)
def delivery_days() -> DeliveryDays:
    return DeliveryDays(
        delivery_days=service.delivery_days(),
        cutoff_options=[
            {"key": key, "label": CUTOFF_LABELS[key], "time": cutoff.strftime("%H:%M")}
            for key, cutoff in CUTOFF_OPTIONS.items()
        ],
        default_cutoff=DEFAULT_CUTOFF.strftime("%H:%M"),
    )


@app.get("/api/day/{delivery_day}", response_model=DayResponse)
def day(delivery_day: date, cutoff: CutoffParam = "09:20") -> dict:
    if not FIRST_DELIVERY_DAY <= delivery_day <= LAST_DELIVERY_DAY:
        raise HTTPException(
            status_code=422,
            detail=f"delivery_day must be between {FIRST_DELIVERY_DAY} and {LAST_DELIVERY_DAY}",
        )
    return _with_snapshot(service.day_view, delivery_day, _parse_cutoff(cutoff))


@app.get("/api/accuracy", response_model=AccuracyResponse)
def accuracy(cutoff: CutoffParam = "09:20") -> dict:
    return _with_snapshot(service.accuracy_view, _parse_cutoff(cutoff))


def _parse_cutoff(cutoff: str) -> time:
    return datetime.strptime(cutoff, "%H:%M").time()


def _with_snapshot(view, *args) -> dict:
    try:
        return view(*args)
    except SnapshotMissing as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except service.NoCompleteHours as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
