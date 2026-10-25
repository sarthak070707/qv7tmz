from datetime import date, time

ELEXON_BASE_URL = "https://data.elexon.co.uk/bmrs/api/v1"

# Decisions are made 1-31 January 2026, so delivery days run one day later.
FIRST_DELIVERY_DAY = date(2026, 1, 2)
LAST_DELIVERY_DAY = date(2026, 2, 1)

# Day-ahead auction gate closures, UK time on D-1.
CUTOFF_OPTIONS: dict[str, time] = {
    "epex_60": time(9, 20),
    "n2ex": time(9, 50),
    "epex_30": time(15, 30),
}
DEFAULT_CUTOFF = CUTOFF_OPTIONS["epex_60"]

UK_TIMEZONE = "Europe/London"

BUFFER_QUANTILE = 0.9
LEAD_TIME_BUCKET_EDGES_H = [0, 12, 18, 24, 30, float("inf")]
LEAD_TIME_BUCKET_LABELS = ["<12h", "12-18h", "18-24h", "24-30h", "30h+"]
