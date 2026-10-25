const API_BASE = import.meta.env.VITE_API_URL ?? ''

export type CutoffOption = { key: string; label: string; time: string }

export type DeliveryDays = {
  delivery_days: string[]
  cutoff_options: CutoffOption[]
  default_cutoff: string
}

export type HourRow = {
  start_time: string
  forecast_mw: number | null
  actual_mw: number | null
  error_mw: number | null
  forecast_published_at: string | null
  lead_time_h: number | null
  is_complete: boolean
}

export type DaySummary = {
  forecast_published_at: string | null
  forecast_mwh: number | null
  actual_mwh: number | null
  mae_mw: number | null
  largest_shortfall_mw: number | null
  largest_shortfall_at: string | null
  hours_excluded: number
}

export type DayResponse = {
  delivery_day: string
  cutoff: string
  decision_cutoff_utc: string
  hours: HourRow[]
  summary: DaySummary
}

export type Metrics = {
  hours_used: number
  hours_excluded: number
  mae_mw: number
  rmse_mw: number
  bias_mw: number
  p50_abs_error_mw: number
  p90_abs_error_mw: number
  p95_abs_error_mw: number
  buffer_mw: number
  mae_pct_of_mean_actual: number
}

export type GroupedError = { mae_mw: number; bias_mw: number; hours: number }

export type AccuracyResponse = {
  cutoff: string
  headline: string
  metrics: Metrics
  by_hour: (GroupedError & { hour: number })[]
  by_lead_time: (GroupedError & { lead_time_bucket: string })[]
  by_day: { delivery_day: string; mae_mw: number }[]
  histogram: { bin_start_mw: number; bin_end_mw: number; count: number }[]
  points: { forecast_mw: number; actual_mw: number }[]
}

export class ApiError extends Error {}

const UNREACHABLE = 'Could not reach the API. Check that the backend is running.'

// A proxy in front of the API answers 502 or 504 when the API itself is down.
const GATEWAY_STATUSES = new Set([502, 504])

async function getJson<T>(path: string): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_BASE}${path}`)
  } catch {
    throw new ApiError(UNREACHABLE)
  }
  if (GATEWAY_STATUSES.has(response.status)) {
    throw new ApiError(UNREACHABLE)
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const detail = typeof body?.detail === 'string' ? body.detail : `HTTP ${response.status}`
    throw new ApiError(detail)
  }
  return response.json() as Promise<T>
}

export const fetchDeliveryDays = () => getJson<DeliveryDays>('/api/delivery-days')

export const fetchDay = (day: string, cutoff: string) =>
  getJson<DayResponse>(`/api/day/${day}?cutoff=${encodeURIComponent(cutoff)}`)

export const fetchAccuracy = (cutoff: string) =>
  getJson<AccuracyResponse>(`/api/accuracy?cutoff=${encodeURIComponent(cutoff)}`)
