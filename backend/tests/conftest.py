import json
from pathlib import Path

import pandas as pd
import pytest

from app.forecasting import records_to_frame

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> pd.DataFrame:
    return records_to_frame(json.loads((FIXTURES / name).read_text()))


@pytest.fixture
def windfor() -> pd.DataFrame:
    # Every WINDFOR publish from 13 Jan 2026; together they cover all of 14 Jan.
    return load_fixture("windfor_sample.json")


@pytest.fixture
def fuelhh() -> pd.DataFrame:
    # FUELHH wind actuals for all 48 settlement periods of 14 Jan 2026.
    return load_fixture("fuelhh_sample.json")
