import {
  Area,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import type { AccuracyResponse, HourRow } from '../api'
import { formatAxisMw, formatBinMw, formatDay, formatMw, formatUkTime } from '../format'
import { useChartColors, type ChartColors } from '../useChartColors'

function axisProps(colors: ChartColors) {
  return {
    stroke: colors.line,
    tick: { fill: colors.muted, fontSize: 12 },
    tickLine: false,
  }
}

function tooltipProps(colors: ChartColors) {
  return {
    contentStyle: {
      background: colors.surface,
      border: `1px solid ${colors.line}`,
      borderRadius: 6,
      color: colors.ink,
      fontSize: 13,
    },
    labelStyle: { color: colors.ink, fontWeight: 600 },
  }
}

const mwFormatter = (value: unknown) => (typeof value === 'number' ? formatMw(value) : '–')

export function DayChart({ hours }: { hours: HourRow[] }) {
  const colors = useChartColors()
  const rows = hours.map((hour) => {
    const { forecast_mw: forecast, actual_mw: actual } = hour
    const both = forecast !== null && actual !== null
    return {
      time: formatUkTime(hour.start_time),
      forecast,
      actual,
      shortfall: both && forecast > actual ? [actual, forecast] : null,
      surplus: both && actual > forecast ? [forecast, actual] : null,
    }
  })
  // Each value is the hour's average, so draw steps and repeat the last hour to close 24:00.
  const last = rows.at(-1)
  const data = last ? [...rows, { ...last, time: '24:00' }] : rows

  return (
    <ResponsiveContainer width="100%" height="100%">
      <ComposedChart data={data} margin={{ top: 8, right: 20, left: 0, bottom: 0 }}>
        <CartesianGrid stroke={colors.line} vertical={false} />
        <XAxis dataKey="time" {...axisProps(colors)} minTickGap={24} />
        <YAxis {...axisProps(colors)} tickFormatter={formatAxisMw} width={56} />
        <Tooltip {...tooltipProps(colors)} formatter={mwFormatter} />
        <Legend wrapperStyle={{ fontSize: 13, color: colors.muted }} />
        <Area
          type="stepAfter"
          dataKey="shortfall"
          name="Shortfall (wind below forecast)"
          stroke="none"
          fill={colors.shortfall}
          fillOpacity={0.28}
          isAnimationActive={false}
          tooltipType="none"
        />
        <Area
          type="stepAfter"
          dataKey="surplus"
          name="Surplus (wind above forecast)"
          stroke="none"
          fill={colors.actual}
          fillOpacity={0.14}
          isAnimationActive={false}
          tooltipType="none"
        />
        <Line
          type="stepAfter"
          dataKey="forecast"
          name="Forecast at decision time"
          stroke={colors.forecast}
          strokeWidth={2}
          strokeDasharray="6 4"
          dot={false}
          isAnimationActive={false}
        />
        <Line
          type="stepAfter"
          dataKey="actual"
          name="Actual wind"
          stroke={colors.actual}
          strokeWidth={2}
          dot={false}
          isAnimationActive={false}
        />
      </ComposedChart>
    </ResponsiveContainer>
  )
}

export function ErrorByHourChart({ data }: { data: AccuracyResponse['by_hour'] }) {
  const colors = useChartColors()
  const rows = data.map((row) => ({ ...row, label: `${String(row.hour).padStart(2, '0')}:00` }))
  return (
    <ResponsiveContainer width="100%" height="100%">
      <ComposedChart data={rows} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid stroke={colors.line} vertical={false} />
        <XAxis dataKey="label" {...axisProps(colors)} minTickGap={16} />
        <YAxis {...axisProps(colors)} tickFormatter={formatAxisMw} width={56} />
        <Tooltip {...tooltipProps(colors)} formatter={mwFormatter} />
        <Legend wrapperStyle={{ fontSize: 13 }} />
        <Bar
          dataKey="mae_mw"
          name="Average miss"
          fill={colors.forecast}
          isAnimationActive={false}
        />
        <Line
          dataKey="bias_mw"
          name="Bias (forecast minus actual)"
          stroke={colors.shortfall}
          strokeWidth={2}
          dot={false}
          isAnimationActive={false}
        />
      </ComposedChart>
    </ResponsiveContainer>
  )
}

export function LeadTimeChart({ data }: { data: AccuracyResponse['by_lead_time'] }) {
  const colors = useChartColors()
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid stroke={colors.line} vertical={false} />
        <XAxis dataKey="lead_time_bucket" {...axisProps(colors)} />
        <YAxis {...axisProps(colors)} tickFormatter={formatAxisMw} width={56} />
        <Tooltip
          {...tooltipProps(colors)}
          formatter={(value, name) => (name === 'Hours' ? String(value) : mwFormatter(value))}
        />
        <Bar
          dataKey="mae_mw"
          name="Average miss"
          fill={colors.forecast}
          isAnimationActive={false}
        />
        <Bar dataKey="hours" name="Hours" hide />
      </BarChart>
    </ResponsiveContainer>
  )
}

export function DailyMaeChart({ data }: { data: AccuracyResponse['by_day'] }) {
  const colors = useChartColors()
  const rows = data.map((row) => ({ ...row, label: formatDay(row.delivery_day, 'short') }))
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={rows} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid stroke={colors.line} vertical={false} />
        <XAxis dataKey="label" {...axisProps(colors)} minTickGap={16} />
        <YAxis {...axisProps(colors)} tickFormatter={formatAxisMw} width={56} />
        <Tooltip {...tooltipProps(colors)} formatter={mwFormatter} />
        <Bar
          dataKey="mae_mw"
          name="Average miss"
          fill={colors.forecast}
          isAnimationActive={false}
        />
      </BarChart>
    </ResponsiveContainer>
  )
}

export function HistogramChart({ data }: { data: AccuracyResponse['histogram'] }) {
  const colors = useChartColors()
  const rows = data.map((bin) => ({
    ...bin,
    label: formatBinMw(bin.bin_start_mw),
    range: `${formatMw(bin.bin_start_mw)} to ${formatMw(bin.bin_end_mw)}`,
  }))
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={rows} margin={{ top: 8, right: 8, left: 0, bottom: 0 }} barCategoryGap={1}>
        <CartesianGrid stroke={colors.line} vertical={false} />
        <XAxis dataKey="label" {...axisProps(colors)} interval={1} />
        <YAxis {...axisProps(colors)} width={56} allowDecimals={false} />
        <Tooltip
          {...tooltipProps(colors)}
          labelFormatter={(_, payload) => payload[0]?.payload.range ?? ''}
        />
        <ReferenceLine x="0k" stroke={colors.ink} strokeDasharray="3 3" />
        <Bar dataKey="count" name="Hours" isAnimationActive={false}>
          {rows.map((bin) => (
            <Cell
              key={bin.bin_start_mw}
              fill={bin.bin_start_mw >= 0 ? colors.shortfall : colors.actual}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

export function ScatterForecastActual({ data }: { data: AccuracyResponse['points'] }) {
  const colors = useChartColors()
  const values = data.flatMap((point) => [point.forecast_mw, point.actual_mw])
  const top = Math.ceil(Math.max(0, ...values) / 2000) * 2000
  return (
    <ResponsiveContainer width="100%" height="100%">
      <ScatterChart margin={{ top: 8, right: 8, left: 0, bottom: 8 }}>
        <CartesianGrid stroke={colors.line} />
        <XAxis
          type="number"
          dataKey="forecast_mw"
          name="Forecast"
          domain={[0, top]}
          {...axisProps(colors)}
          tickFormatter={formatAxisMw}
          label={{
            value: 'Forecast (MW)',
            position: 'insideBottom',
            offset: -4,
            fill: colors.muted,
            fontSize: 12,
          }}
        />
        <YAxis
          type="number"
          dataKey="actual_mw"
          name="Actual"
          domain={[0, top]}
          {...axisProps(colors)}
          tickFormatter={formatAxisMw}
          width={72}
          label={{
            value: 'Actual (MW)',
            angle: -90,
            position: 'insideLeft',
            fill: colors.muted,
            fontSize: 12,
          }}
        />
        <Tooltip {...tooltipProps(colors)} formatter={mwFormatter} />
        <ReferenceLine
          segment={[
            { x: 0, y: 0 },
            { x: top, y: top },
          ]}
          stroke={colors.ink}
          strokeDasharray="4 4"
          ifOverflow="hidden"
        />
        <Scatter data={data} fill={colors.forecast} fillOpacity={0.35} isAnimationActive={false} />
      </ScatterChart>
    </ResponsiveContainer>
  )
}
