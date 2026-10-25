import { useQuery } from '@tanstack/react-query'

import { fetchAccuracy, type AccuracyResponse } from '../api'
import { ChartPanel } from '../components/ChartPanel'
import {
  DailyMaeChart,
  ErrorByHourChart,
  HistogramChart,
  LeadTimeChart,
  ScatterForecastActual,
} from '../components/charts'
import { FigureRow } from '../components/FigureRow'
import { StatusMessage } from '../components/StatusMessage'
import { formatMw, formatSignedMw } from '../format'

export function AccuracyView({ cutoff }: { cutoff: string }) {
  const query = useQuery({ queryKey: ['accuracy', cutoff], queryFn: () => fetchAccuracy(cutoff) })

  if (query.isPending) return <StatusMessage kind="loading" />
  if (query.isError) return <StatusMessage kind="error" message={query.error.message} />
  return <AccuracyDetail data={query.data} />
}

function AccuracyDetail({ data }: { data: AccuracyResponse }) {
  const { metrics } = data
  const runsHigh = metrics.bias_mw > 0

  return (
    <div className="space-y-6">
      <section className="max-w-4xl">
        <p className="condensed text-3xl leading-tight font-semibold md:text-4xl">
          {data.headline}
        </p>
        <p className="mt-3 max-w-prose text-muted">
          {runsHigh
            ? `The forecast ran high: on average, wind came in ${formatMw(metrics.bias_mw)} below it. That under-delivery is the risk the buffer covers.`
            : `The forecast ran low: on average, wind came in ${formatMw(-metrics.bias_mw)} above it.`}{' '}
          Based on {metrics.hours_used} hours
          {metrics.hours_excluded > 0 &&
            `, with ${metrics.hours_excluded} hours left out for missing data`}
          .
        </p>
      </section>

      <FigureRow
        figures={[
          {
            label: 'Average miss',
            value: formatMw(metrics.mae_mw),
            note: `${metrics.mae_pct_of_mean_actual.toFixed(1)}% of average wind output; RMSE ${formatMw(metrics.rmse_mw)}`,
          },
          {
            label: 'Bias',
            value: formatSignedMw(metrics.bias_mw),
            note: 'Forecast minus actual; positive means wind fell short',
          },
          {
            label: 'Miss in 9 of 10 hours',
            value: `under ${formatMw(metrics.p90_abs_error_mw)}`,
            note: 'P90 of the absolute error, either direction',
          },
          {
            label: 'Buffer to hold',
            value: formatMw(metrics.buffer_mw),
            note: 'Covers wind shortfalls in 90% of hours',
            tone: 'shortfall',
          },
        ]}
      />

      <div className="grid gap-6 lg:grid-cols-2">
        <ChartPanel
          title="Error by hour of day (MW, UK time)"
          caption="Bars show the average miss; the line shows bias, how far the forecast ran above the actual."
        >
          <ErrorByHourChart data={data.by_hour} />
        </ChartPanel>
        <ChartPanel
          title="Average miss by forecast lead time (MW)"
          caption="Read with care: with a fixed cutoff, lead time tracks the hour of day. The shortest lead times cover the early-morning hours, which are hardest to forecast."
        >
          <LeadTimeChart data={data.by_lead_time} />
        </ChartPanel>
        <ChartPanel
          title="Average miss by delivery day (MW)"
          caption="The tallest bars are the days to look at first."
        >
          <DailyMaeChart data={data.by_day} />
        </ChartPanel>
        <ChartPanel
          title="How the hourly errors are spread (hours per 500 MW band)"
          caption="Orange bands are hours where wind fell short of the forecast; green bands are hours where it beat it."
        >
          <HistogramChart data={data.histogram} />
        </ChartPanel>
        <ChartPanel
          title="Forecast vs actual, every hour (MW)"
          caption="Points below the dashed line are hours where wind came in under the forecast."
          className="lg:col-span-2 [&>div]:h-96"
        >
          <ScatterForecastActual data={data.points} />
        </ChartPanel>
      </div>
    </div>
  )
}
