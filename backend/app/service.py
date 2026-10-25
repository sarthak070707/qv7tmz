"""Turn the snapshot into API payloads, cached per cutoff since the data never changes."""

from dataclasses import asdict
from datetime import date, time
from functools import lru_cache

import pandas as pd

from app.config import BUFFER_QUANTILE
from app.forecasting import build_aligned_range, decision_cutoff, delivery_days
from app.metrics import (
    complete_rows,
    compute_error_metrics,
    daily_mae,
    error_by_hour_of_day,
    error_by_lead_time,
    error_histogram,
)
from app.snapshot import Snapshot, load_snapshot


class NoCompleteHours(RuntimeError):
    pass


@lru_cache(maxsize=1)
def snapshot() -> Snapshot:
    return load_snapshot()


@lru_cache(maxsize=32)
def aligned_scope(cutoff: time) -> pd.DataFrame:
    data = snapshot()
    return build_aligned_range(data.forecasts, data.actuals, delivery_days(), cutoff)


def day_view(delivery_day: date, cutoff: time) -> dict:
    aligned = aligned_scope(cutoff)
    local_day = aligned["start_time"].dt.tz_convert("Europe/London").dt.date
    day = aligned[local_day == delivery_day]
    return {
        "delivery_day": delivery_day,
        "cutoff": cutoff.strftime("%H:%M"),
        "decision_cutoff_utc": decision_cutoff(delivery_day, cutoff),
        "hours": records(day),
        "summary": day_summary(day),
    }


def day_summary(day: pd.DataFrame) -> dict:
    complete = day[day["is_complete"]]
    shortfalls = complete[complete["error_mw"] > 0]
    worst = shortfalls.loc[shortfalls["error_mw"].idxmax()] if len(shortfalls) else None
    published = day["forecast_published_at"].dropna()
    return {
        "forecast_published_at": published.max() if len(published) else None,
        # Totals cover complete hours only, so forecast and actual are comparable.
        # Each value is an hourly average MW, so MWh = MW x 1 h.
        "forecast_mwh": _or_none(complete["forecast_mw"].sum(), len(complete)),
        "actual_mwh": _or_none(complete["actual_mw"].sum(), len(complete)),
        "mae_mw": _or_none(complete["error_mw"].abs().mean(), len(complete)),
        "largest_shortfall_mw": None if worst is None else float(worst["error_mw"]),
        "largest_shortfall_at": None if worst is None else worst["start_time"],
        "hours_excluded": int((~day["is_complete"]).sum()),
    }


@lru_cache(maxsize=32)
def accuracy_view(cutoff: time) -> dict:
    aligned = aligned_scope(cutoff)
    if not aligned["is_complete"].any():
        raise NoCompleteHours("No hours have both a forecast and an actual for this cutoff.")
    metrics = compute_error_metrics(aligned)
    cutoff_label = cutoff.strftime("%H:%M")
    return {
        "cutoff": cutoff_label,
        "headline": headline(cutoff_label, metrics.mae_mw, metrics.buffer_mw),
        "metrics": asdict(metrics),
        "by_hour": records(error_by_hour_of_day(aligned)),
        "by_lead_time": records(error_by_lead_time(aligned).astype({"lead_time_bucket": str})),
        "by_day": records(daily_mae(aligned)),
        "histogram": records(error_histogram(aligned)),
        "points": records(complete_rows(aligned)[["forecast_mw", "actual_mw"]]),
    }


def headline(cutoff_label: str, mae_mw: float, buffer_mw: float) -> str:
    coverage = round(BUFFER_QUANTILE * 100)
    return (
        f"Across January, the {cutoff_label} forecast missed by {mae_mw:,.0f} MW on average, "
        f"and holding a {buffer_mw:,.0f} MW buffer would have covered wind shortfalls "
        f"in {coverage}% of hours."
    )


def records(frame: pd.DataFrame) -> list[dict]:
    # NaN and NaT become None so missing hours serialise as null, not as invalid JSON.
    cleaned = frame.astype(object).where(frame.notna(), None)
    return cleaned.to_dict(orient="records")


def _or_none(value: float, count: int) -> float | None:
    return float(value) if count else None
