"""Pick the forecast a buyer actually had at decision time and line it up with actuals.

All frames use UTC timestamps. Forecasts have columns start_time, publish_time,
generation; actuals have the same plus one row per half-hour settlement period.
"""

from datetime import date, datetime, time, timedelta

import pandas as pd

from app.config import FIRST_DELIVERY_DAY, LAST_DELIVERY_DAY, UK_TIMEZONE


def records_to_frame(records: list[dict]) -> pd.DataFrame:
    frame = pd.DataFrame.from_records(records)
    frame = frame.rename(columns={"startTime": "start_time", "publishTime": "publish_time"})
    frame["start_time"] = pd.to_datetime(frame["start_time"], utc=True)
    frame["publish_time"] = pd.to_datetime(frame["publish_time"], utc=True)
    return frame[["start_time", "publish_time", "generation"]]


def delivery_days() -> list[date]:
    span = (LAST_DELIVERY_DAY - FIRST_DELIVERY_DAY).days
    return [FIRST_DELIVERY_DAY + timedelta(days=offset) for offset in range(span + 1)]


def decision_cutoff(delivery_day: date, cutoff: time) -> pd.Timestamp:
    # Gate closures are quoted in UK local time, so convert to UTC explicitly.
    local = datetime.combine(delivery_day - timedelta(days=1), cutoff)
    return pd.Timestamp(local).tz_localize(UK_TIMEZONE).tz_convert("UTC")


def delivery_day_hours(delivery_day: date) -> pd.DatetimeIndex:
    start = pd.Timestamp(delivery_day).tz_localize(UK_TIMEZONE)
    end = start + pd.Timedelta(days=1)
    return pd.date_range(start, end, freq="h", inclusive="left").tz_convert("UTC")


def latest_revision_of_actuals(actuals: pd.DataFrame) -> pd.DataFrame:
    latest = actuals.sort_values("publish_time").drop_duplicates("start_time", keep="last")
    return latest.sort_values("start_time").reset_index(drop=True)


def hourly_actuals(actuals: pd.DataFrame) -> pd.DataFrame:
    """Average FUELHH half-hours into hours to match WINDFOR's hourly resolution."""
    actuals = latest_revision_of_actuals(actuals)
    hours = actuals.assign(start_time=actuals["start_time"].dt.floor("h"))
    grouped = hours.groupby("start_time")["generation"].agg(["mean", "count"])
    # An hour missing one of its half-hours would be a biased average, so treat it as missing.
    grouped.loc[grouped["count"] < 2, "mean"] = float("nan")
    return grouped["mean"].rename("actual_mw").reset_index()


def select_decision_forecast(
    forecasts: pd.DataFrame, delivery_day: date, cutoff: time
) -> pd.DataFrame:
    """One row per hour of the delivery day, with the forecast available at the cutoff.

    Hours with no qualifying forecast are kept with empty values so the gap stays visible.
    """
    cutoff_utc = decision_cutoff(delivery_day, cutoff)
    hours = delivery_day_hours(delivery_day)

    # Strictly before: a forecast published at the gate closure minute can't be acted on.
    available = forecasts[
        forecasts["start_time"].isin(hours) & (forecasts["publish_time"] < cutoff_utc)
    ].drop_duplicates(["start_time", "publish_time"])

    latest = available.sort_values("publish_time").drop_duplicates("start_time", keep="last")
    selected = (
        latest.set_index("start_time")
        .reindex(hours)
        .rename_axis("start_time")
        .reset_index()
        .rename(columns={"generation": "forecast_mw", "publish_time": "forecast_published_at"})
    )
    lead = selected["start_time"] - selected["forecast_published_at"]
    selected["lead_time_h"] = lead.dt.total_seconds() / 3600
    return selected[["start_time", "forecast_mw", "forecast_published_at", "lead_time_h"]]


def align_with_actuals(decision_forecast: pd.DataFrame, hourly: pd.DataFrame) -> pd.DataFrame:
    aligned = decision_forecast.merge(hourly, on="start_time", how="left")
    aligned["error_mw"] = aligned["forecast_mw"] - aligned["actual_mw"]
    aligned["is_complete"] = aligned["forecast_mw"].notna() & aligned["actual_mw"].notna()
    return aligned


def build_aligned_day(
    forecasts: pd.DataFrame, actuals: pd.DataFrame, delivery_day: date, cutoff: time
) -> pd.DataFrame:
    decision_forecast = select_decision_forecast(forecasts, delivery_day, cutoff)
    return align_with_actuals(decision_forecast, hourly_actuals(actuals))


def build_aligned_range(
    forecasts: pd.DataFrame, actuals: pd.DataFrame, days: list[date], cutoff: time
) -> pd.DataFrame:
    hourly = hourly_actuals(actuals)
    frames = [
        align_with_actuals(select_decision_forecast(forecasts, day, cutoff), hourly) for day in days
    ]
    return pd.concat(frames, ignore_index=True)
