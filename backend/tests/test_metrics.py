import math
from datetime import time

import pandas as pd
import pytest

from app.forecasting import build_aligned_day
from app.metrics import (
    compute_buffer_mw,
    compute_error_metrics,
    daily_mae,
    error_by_hour_of_day,
    error_by_lead_time,
    error_histogram,
)


def aligned_frame(forecast: list[float], actual: list[float]) -> pd.DataFrame:
    hours = pd.date_range("2026-01-14", periods=len(forecast), freq="h", tz="UTC")
    frame = pd.DataFrame(
        {
            "start_time": hours,
            "forecast_mw": forecast,
            "actual_mw": actual,
            "lead_time_h": 16.5 + pd.Series(range(len(forecast)), dtype=float),
        }
    )
    frame["error_mw"] = frame["forecast_mw"] - frame["actual_mw"]
    frame["is_complete"] = frame["forecast_mw"].notna() & frame["actual_mw"].notna()
    return frame


def test_buffer_matches_hand_computed_example():
    # Shortfalls 0, 100, ..., 900 MW. P90 by linear interpolation:
    # position 0.9 * 9 = 8.1, so 800 + 0.1 * (900 - 800) = 810.
    errors = pd.Series([100.0 * i for i in range(10)])

    assert compute_buffer_mw(errors) == pytest.approx(810.0)


def test_buffer_treats_over_delivery_as_zero_shortfall():
    # Wind beat the forecast in every hour, so no buffer is needed.
    errors = pd.Series([-500.0, -200.0, -50.0])

    assert compute_buffer_mw(errors) == 0.0


def test_core_metrics_match_hand_computed_values():
    aligned = aligned_frame(forecast=[1100, 900, 1300, 1000], actual=[1000, 1000, 1000, 1000])
    # Errors: +100, -100, +300, 0

    metrics = compute_error_metrics(aligned)

    assert metrics.hours_used == 4
    assert metrics.mae_mw == pytest.approx(125.0)
    assert metrics.bias_mw == pytest.approx(75.0)
    assert metrics.rmse_mw == pytest.approx(math.sqrt((100**2 + 100**2 + 300**2) / 4))
    assert metrics.mae_pct_of_mean_actual == pytest.approx(12.5)


def test_missing_hours_are_excluded_from_metrics():
    aligned = aligned_frame(forecast=[1100, None, 1000], actual=[1000, 1000, None])

    metrics = compute_error_metrics(aligned)

    assert metrics.hours_used == 1
    assert metrics.hours_excluded == 2
    assert metrics.mae_mw == pytest.approx(100.0)


def test_breakdowns_on_real_day(windfor, fuelhh):
    aligned = build_aligned_day(windfor, fuelhh, pd.Timestamp("2026-01-14").date(), time(9, 20))

    by_hour = error_by_hour_of_day(aligned)
    by_lead = error_by_lead_time(aligned)
    histogram = error_histogram(aligned)

    assert list(by_hour["hour"]) == list(range(24))
    assert by_lead["hours"].sum() == 24
    assert histogram["count"].sum() == 24
    assert len(daily_mae(aligned)) == 1
