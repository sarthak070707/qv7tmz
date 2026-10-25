from datetime import date, datetime

from pydantic import BaseModel


class Health(BaseModel):
    status: str
    data_as_of: datetime | None


class CutoffOption(BaseModel):
    key: str
    label: str
    time: str


class DeliveryDays(BaseModel):
    delivery_days: list[date]
    cutoff_options: list[CutoffOption]
    default_cutoff: str


class HourRow(BaseModel):
    start_time: datetime
    forecast_mw: float | None
    actual_mw: float | None
    error_mw: float | None
    forecast_published_at: datetime | None
    lead_time_h: float | None
    is_complete: bool


class DaySummary(BaseModel):
    forecast_published_at: datetime | None
    forecast_mwh: float | None
    actual_mwh: float | None
    mae_mw: float | None
    largest_shortfall_mw: float | None
    largest_shortfall_at: datetime | None
    hours_excluded: int


class DayResponse(BaseModel):
    delivery_day: date
    cutoff: str
    decision_cutoff_utc: datetime
    hours: list[HourRow]
    summary: DaySummary


class Metrics(BaseModel):
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


class HourOfDayError(BaseModel):
    hour: int
    mae_mw: float
    bias_mw: float
    hours: int


class LeadTimeError(BaseModel):
    lead_time_bucket: str
    mae_mw: float
    bias_mw: float
    hours: int


class DailyError(BaseModel):
    delivery_day: date
    mae_mw: float


class HistogramBin(BaseModel):
    bin_start_mw: float
    bin_end_mw: float
    count: int


class ScatterPoint(BaseModel):
    forecast_mw: float
    actual_mw: float


class AccuracyResponse(BaseModel):
    cutoff: str
    headline: str
    metrics: Metrics
    by_hour: list[HourOfDayError]
    by_lead_time: list[LeadTimeError]
    by_day: list[DailyError]
    histogram: list[HistogramBin]
    points: list[ScatterPoint]
