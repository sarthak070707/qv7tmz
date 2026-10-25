from datetime import date, time

import pandas as pd
import pytest

from app.config import CUTOFF_OPTIONS
from app.forecasting import (
    build_aligned_day,
    decision_cutoff,
    hourly_actuals,
    select_decision_forecast,
)

DELIVERY_DAY = date(2026, 1, 14)


def utc(text: str) -> pd.Timestamp:
    return pd.Timestamp(text, tz="UTC")


def forecast_rows(rows: list[tuple[str, str, float]]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "start_time": [utc(start) for start, _, _ in rows],
            "publish_time": [utc(published) for _, published, _ in rows],
            "generation": [mw for _, _, mw in rows],
        }
    )


@pytest.mark.parametrize(
    "cutoff",
    [*CUTOFF_OPTIONS.values(), time(0, 0), time(7, 30), time(12, 0), time(23, 59)],
)
def test_never_uses_forecast_published_at_or_after_cutoff(windfor, cutoff):
    selected = select_decision_forecast(windfor, DELIVERY_DAY, cutoff)
    published = selected["forecast_published_at"].dropna()

    assert (published < decision_cutoff(DELIVERY_DAY, cutoff)).all()


@pytest.mark.parametrize(
    ("cutoff", "expected_publish"),
    [
        (time(9, 20), "2026-01-13T07:30Z"),
        (time(9, 50), "2026-01-13T09:30Z"),
        (time(15, 30), "2026-01-13T11:30Z"),
    ],
)
def test_each_auction_uses_latest_forecast_before_its_gate_closure(
    windfor, cutoff, expected_publish
):
    selected = select_decision_forecast(windfor, DELIVERY_DAY, cutoff)

    assert (selected["forecast_published_at"] == utc(expected_publish)).all()


def test_forecast_published_exactly_at_cutoff_is_not_used(windfor):
    # WINDFOR publishes at 15:30, the same minute the EPEX 30-min auction closes.
    selected = select_decision_forecast(windfor, DELIVERY_DAY, time(15, 30))

    assert (selected["forecast_published_at"] != utc("2026-01-13T15:30Z")).all()


@pytest.mark.parametrize("cutoff", [*CUTOFF_OPTIONS.values(), time(23, 59)])
def test_lead_time_is_always_positive(windfor, cutoff):
    # Each publish also forecasts hours already past; none of those may slip in.
    selected = select_decision_forecast(windfor, DELIVERY_DAY, cutoff)

    assert (selected["lead_time_h"].dropna() > 0).all()


def test_latest_qualifying_forecast_wins():
    forecasts = forecast_rows(
        [
            ("2026-01-14T00:00Z", "2026-01-13T02:30Z", 100.0),
            ("2026-01-14T00:00Z", "2026-01-13T07:30Z", 200.0),
            ("2026-01-14T00:00Z", "2026-01-13T09:30Z", 999.0),
        ]
    )

    selected = select_decision_forecast(forecasts, DELIVERY_DAY, time(9, 20))
    first_hour = selected.iloc[0]

    assert first_hour["forecast_mw"] == 200.0
    assert first_hour["forecast_published_at"] == utc("2026-01-13T07:30Z")
    assert first_hour["lead_time_h"] == 16.5


def test_hours_without_a_forecast_stay_visible_as_gaps():
    forecasts = forecast_rows([("2026-01-14T05:00Z", "2026-01-13T07:30Z", 300.0)])

    selected = select_decision_forecast(forecasts, DELIVERY_DAY, time(9, 20))

    assert len(selected) == 24
    assert selected["forecast_mw"].notna().sum() == 1


def test_half_hours_are_averaged_into_hours(fuelhh):
    hourly = hourly_actuals(fuelhh)

    assert len(hourly) == 24
    first_hour = hourly.iloc[0]
    assert first_hour["start_time"] == utc("2026-01-14T00:00Z")
    assert first_hour["actual_mw"] == (9462 + 9060) / 2


def test_hour_missing_a_half_hour_counts_as_missing(fuelhh):
    without_0030 = fuelhh[fuelhh["start_time"] != utc("2026-01-14T00:30Z")]

    hourly = hourly_actuals(without_0030)

    assert pd.isna(hourly.iloc[0]["actual_mw"])


def test_latest_revision_of_actuals_wins():
    actuals = forecast_rows(
        [
            ("2026-01-14T00:00Z", "2026-01-14T00:30Z", 1000.0),
            ("2026-01-14T00:00Z", "2026-01-14T02:00Z", 1100.0),
            ("2026-01-14T00:30Z", "2026-01-14T01:00Z", 1300.0),
        ]
    )

    hourly = hourly_actuals(actuals)

    assert hourly.iloc[0]["actual_mw"] == 1200.0


def test_real_day_aligns_completely(windfor, fuelhh):
    aligned = build_aligned_day(windfor, fuelhh, DELIVERY_DAY, time(9, 20))

    assert len(aligned) == 24
    assert aligned["is_complete"].all()
    assert (aligned["error_mw"] == aligned["forecast_mw"] - aligned["actual_mw"]).all()
