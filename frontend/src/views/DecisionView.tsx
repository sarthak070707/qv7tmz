import { useQuery } from '@tanstack/react-query'

import { fetchDay } from '../api'
import { ChartPanel } from '../components/ChartPanel'
import { DayChart } from '../components/charts'
import { FigureRow } from '../components/FigureRow'
import { StatusMessage } from '../components/StatusMessage'
import {
  formatDay,
  formatHours,
  formatMw,
  formatMwh,
  formatUkDateTime,
  formatUkTime,
} from '../format'

type Props = {
  days: string[]
  day: string
  onDayChange: (day: string) => void
  cutoff: string
}

export function DecisionView({ days, day, onDayChange, cutoff }: Props) {
  const query = useQuery({ queryKey: ['day', day, cutoff], queryFn: () => fetchDay(day, cutoff) })
  const index = days.indexOf(day)

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="condensed text-3xl font-semibold">{formatDay(day)}</h2>
          <p className="mt-1 text-muted">
            What you would have known when deciding at {cutoff} the day before, and what the wind
            actually did.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => onDayChange(days[index - 1]!)}
            disabled={index <= 0}
            className="rounded-md border border-line bg-surface px-3 py-1.5 text-sm disabled:opacity-40"
          >
            Previous day
          </button>
          <label className="sr-only" htmlFor="delivery-day">
            Delivery day
          </label>
          <select
            id="delivery-day"
            value={day}
            onChange={(event) => onDayChange(event.target.value)}
            className="rounded-md border border-line bg-surface px-2 py-1.5 text-sm"
          >
            {days.map((option) => (
              <option key={option} value={option}>
                {formatDay(option, 'short')}
              </option>
            ))}
          </select>
          <button
            type="button"
            onClick={() => onDayChange(days[index + 1]!)}
            disabled={index >= days.length - 1}
            className="rounded-md border border-line bg-surface px-3 py-1.5 text-sm disabled:opacity-40"
          >
            Next day
          </button>
        </div>
      </div>

      {query.isPending && <StatusMessage kind="loading" />}
      {query.isError && <StatusMessage kind="error" message={query.error.message} />}
      {query.data && <DayDetail data={query.data} />}
    </div>
  )
}

function DayDetail({ data }: { data: NonNullable<Awaited<ReturnType<typeof fetchDay>>> }) {
  const { summary, hours } = data
  const firstLead = hours.find((hour) => hour.lead_time_h !== null)?.lead_time_h ?? null
  const missing = summary.hours_excluded

  return (
    <>
      <p className="rounded-md border-l-4 border-forecast bg-surface px-4 py-3 text-sm">
        {summary.forecast_published_at && firstLead !== null ? (
          <>
            Forecast published {formatUkDateTime(summary.forecast_published_at)},{' '}
            {formatHours(firstLead)} before the first hour of the day.
          </>
        ) : (
          <>No forecast had been published before this cutoff.</>
        )}
        {missing > 0 && (
          <span className="text-shortfall">
            {' '}
            {missing} of 24 hours are missing a forecast or an actual and are left out of the
            figures.
          </span>
        )}
      </p>

      <ChartPanel
        title="Forecast at decision time vs actual wind (MW, UK time)"
        caption="Each step is the hour's average. Shaded gaps show where wind came in below or above the forecast."
        className="[&>div]:h-80"
      >
        <DayChart hours={hours} />
      </ChartPanel>

      <FigureRow
        figures={[
          { label: 'Forecast total', value: formatMwh(summary.forecast_mwh) },
          { label: 'Actual total', value: formatMwh(summary.actual_mwh) },
          {
            label: 'Average miss',
            value: formatMw(summary.mae_mw),
            note: 'Mean absolute error per hour',
          },
          {
            label: 'Largest shortfall',
            value: formatMw(summary.largest_shortfall_mw),
            note: summary.largest_shortfall_at
              ? `At ${formatUkTime(summary.largest_shortfall_at)}`
              : 'Wind never fell short of the forecast',
            tone: 'shortfall',
          },
        ]}
      />
    </>
  )
}
