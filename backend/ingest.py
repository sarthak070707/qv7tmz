"""Build the data snapshot from Elexon.

python ingest.py            # download only if no snapshot exists yet
python ingest.py --refresh  # download again and overwrite the snapshot
"""

import argparse
import sys
from datetime import timedelta

import pandas as pd

from app.config import CUTOFF_OPTIONS, FIRST_DELIVERY_DAY, LAST_DELIVERY_DAY
from app.elexon import ElexonError, fetch_fuelhh_wind, fetch_windfor, make_client
from app.forecasting import delivery_days, records_to_frame, select_decision_forecast
from app.snapshot import data_dir, save_snapshot, snapshot_exists

# Pull a little wider than the scope, then let the selection logic trim it.
FORECASTS_PUBLISHED_FROM = FIRST_DELIVERY_DAY - timedelta(days=3)
FORECASTS_PUBLISHED_TO = LAST_DELIVERY_DAY
ACTUALS_FROM = FIRST_DELIVERY_DAY - timedelta(days=1)
ACTUALS_TO = LAST_DELIVERY_DAY + timedelta(days=1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="re-download even if data exists")
    args = parser.parse_args()

    directory = data_dir()
    if snapshot_exists(directory) and not args.refresh:
        print(f"Snapshot already in {directory}. Use --refresh to download again.")
        return 0

    try:
        forecasts, actuals = download()
    except ElexonError as error:
        # The existing snapshot is left untouched, so the app keeps working.
        print(f"Download failed, snapshot not changed: {error}", file=sys.stderr)
        return 1

    save_snapshot(forecasts, actuals, directory)
    print(f"Saved {len(forecasts):,} forecast rows and {len(actuals):,} actual rows to {directory}")
    report_coverage(forecasts, actuals)
    return 0


def download() -> tuple[pd.DataFrame, pd.DataFrame]:
    with make_client() as client:
        print(f"WINDFOR: publishes {FORECASTS_PUBLISHED_FROM} to {FORECASTS_PUBLISHED_TO}")
        windfor = fetch_windfor(client, FORECASTS_PUBLISHED_FROM, FORECASTS_PUBLISHED_TO)
        print(f"FUELHH wind: settlement dates {ACTUALS_FROM} to {ACTUALS_TO}")
        fuelhh = fetch_fuelhh_wind(client, ACTUALS_FROM, ACTUALS_TO)
    return clean(records_to_frame(windfor)), clean(records_to_frame(fuelhh))


def clean(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.dropna(subset=["generation"]).drop_duplicates()
    return frame.sort_values(["start_time", "publish_time"]).reset_index(drop=True)


def report_coverage(forecasts: pd.DataFrame, actuals: pd.DataFrame) -> None:
    actual_days = set(actuals["start_time"].dt.date)
    for day in delivery_days():
        problems = []
        for name, cutoff in CUTOFF_OPTIONS.items():
            selected = select_decision_forecast(forecasts, day, cutoff)
            missing = int(selected["forecast_mw"].isna().sum())
            if missing:
                problems.append(f"{missing} hours without a forecast at {name}")
        if day not in actual_days:
            problems.append("no actuals")
        if problems:
            print(f"  {day}: " + "; ".join(problems))


if __name__ == "__main__":
    sys.exit(main())
