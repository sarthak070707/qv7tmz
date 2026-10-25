"""The committed data snapshot, so the deployed app never depends on Elexon being up."""

import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
# Compressed CSV rather than Parquet: Parquet needs pyarrow, which is too large
# for comfortable use in a serverless function, and the snapshot is small.
FORECASTS_FILE = "windfor.csv.gz"
ACTUALS_FILE = "fuelhh_wind.csv.gz"
_FILES = (FORECASTS_FILE, ACTUALS_FILE, "metadata.json")
TIME_COLUMNS = ["start_time", "publish_time"]


@dataclass(frozen=True)
class Snapshot:
    forecasts: pd.DataFrame
    actuals: pd.DataFrame
    ingested_at: datetime


class SnapshotMissing(RuntimeError):
    pass


def data_dir() -> Path:
    return Path(os.environ.get("DATA_DIR", DEFAULT_DATA_DIR))


def snapshot_exists(directory: Path | None = None) -> bool:
    directory = directory or data_dir()
    return all((directory / name).exists() for name in _FILES)


def save_snapshot(forecasts: pd.DataFrame, actuals: pd.DataFrame, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    forecasts.to_csv(directory / FORECASTS_FILE, index=False)
    actuals.to_csv(directory / ACTUALS_FILE, index=False)
    metadata = {"ingested_at": datetime.now(UTC).isoformat()}
    (directory / "metadata.json").write_text(json.dumps(metadata, indent=2))


def load_snapshot(directory: Path | None = None) -> Snapshot:
    directory = directory or data_dir()
    if not snapshot_exists(directory):
        raise SnapshotMissing(f"No data snapshot in {directory}. Run: python ingest.py")
    metadata = json.loads((directory / "metadata.json").read_text())
    return Snapshot(
        forecasts=_read_frame(directory / FORECASTS_FILE),
        actuals=_read_frame(directory / ACTUALS_FILE),
        ingested_at=datetime.fromisoformat(metadata["ingested_at"]),
    )


def _read_frame(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    for column in TIME_COLUMNS:
        frame[column] = pd.to_datetime(frame[column], utc=True)
    return frame
