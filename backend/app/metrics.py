"""Forecast accuracy metrics. Error is forecast minus actual, in MW.

Positive error means wind under-delivered, which leaves the buyer short.
Every function ignores hours that lack a forecast or an actual.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from app.config import (
    BUFFER_QUANTILE,
    LEAD_TIME_BUCKET_EDGES_H,
    LEAD_TIME_BUCKET_LABELS,
    UK_TIMEZONE,
)


@dataclass(frozen=True)
class ErrorMetrics:
    hours_used: int
    hours_excluded: int
    mae_mw: float
    rmse_mw: float
    bias_mw: float
    p50_abs_error_mw: float
    p90_abs_error_mw: float
    p95_abs_error_mw: float
    buffer_mw: float
    mae_pct_of_mean_actual: float


def complete_rows(aligned: pd.DataFrame) -> pd.DataFrame:
    return aligned[aligned["is_complete"]]


def compute_buffer_mw(errors: pd.Series, quantile: float = BUFFER_QUANTILE) -> float:
    """Extra MW to hold so wind shortfalls are covered in `quantile` of hours.

    Hours where wind beat the forecast count as zero shortfall, not as negative.
    """
    shortfall = errors.clip(lower=0)
    return float(np.quantile(shortfall, quantile))


def compute_error_metrics(aligned: pd.DataFrame) -> ErrorMetrics:
    rows = complete_rows(aligned)
    errors = rows["error_mw"]
    abs_errors = errors.abs()
    mae = float(abs_errors.mean())
    # Plain MAPE explodes when wind is near zero, so scale MAE by mean actual instead.
    mean_actual = float(rows["actual_mw"].mean())
    return ErrorMetrics(
        hours_used=len(rows),
        hours_excluded=len(aligned) - len(rows),
        mae_mw=mae,
        rmse_mw=float(np.sqrt((errors**2).mean())),
        bias_mw=float(errors.mean()),
        p50_abs_error_mw=float(np.quantile(abs_errors, 0.5)),
        p90_abs_error_mw=float(np.quantile(abs_errors, 0.9)),
        p95_abs_error_mw=float(np.quantile(abs_errors, 0.95)),
        buffer_mw=compute_buffer_mw(errors),
        mae_pct_of_mean_actual=100 * mae / mean_actual,
    )


def error_by_hour_of_day(aligned: pd.DataFrame) -> pd.DataFrame:
    rows = complete_rows(aligned)
    hour = rows["start_time"].dt.tz_convert(UK_TIMEZONE).dt.hour.rename("hour")
    return _summarise(rows.groupby(hour)["error_mw"])


def error_by_lead_time(aligned: pd.DataFrame) -> pd.DataFrame:
    rows = complete_rows(aligned)
    bucket = pd.cut(
        rows["lead_time_h"],
        bins=LEAD_TIME_BUCKET_EDGES_H,
        labels=LEAD_TIME_BUCKET_LABELS,
        right=False,
    ).rename("lead_time_bucket")
    return _summarise(rows.groupby(bucket, observed=True)["error_mw"])


def daily_mae(aligned: pd.DataFrame) -> pd.DataFrame:
    rows = complete_rows(aligned)
    day = rows["start_time"].dt.tz_convert(UK_TIMEZONE).dt.date.rename("delivery_day")
    return (
        rows.groupby(day)["error_mw"].apply(lambda e: e.abs().mean()).rename("mae_mw").reset_index()
    )


def error_histogram(aligned: pd.DataFrame, bin_width_mw: float = 500) -> pd.DataFrame:
    errors = complete_rows(aligned)["error_mw"]
    low = np.floor(errors.min() / bin_width_mw) * bin_width_mw
    high = np.ceil(errors.max() / bin_width_mw) * bin_width_mw
    edges = np.arange(low, high + bin_width_mw, bin_width_mw)
    counts, edges = np.histogram(errors, bins=edges)
    return pd.DataFrame({"bin_start_mw": edges[:-1], "bin_end_mw": edges[1:], "count": counts})


def _summarise(grouped_errors) -> pd.DataFrame:
    return grouped_errors.agg(
        mae_mw=lambda e: e.abs().mean(),
        bias_mw="mean",
        hours="count",
    ).reset_index()
