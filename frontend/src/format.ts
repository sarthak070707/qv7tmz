const UK = 'Europe/London'

const mw = new Intl.NumberFormat('en-GB', { maximumFractionDigits: 0 })

export const formatMw = (value: number | null) => (value === null ? '–' : `${mw.format(value)} MW`)

export const formatMwh = (value: number | null) =>
  value === null ? '–' : `${mw.format(value)} MWh`

export const formatSignedMw = (value: number) => `${value > 0 ? '+' : ''}${mw.format(value)} MW`

export const formatAxisMw = (value: number) => mw.format(value)

// Histogram bins sit on 500 MW steps, so short labels like 1.5k stay exact.
export const formatBinMw = (value: number) => `${(value / 1000).toLocaleString('en-GB')}k`

export const formatUkTime = (iso: string) =>
  new Intl.DateTimeFormat('en-GB', { timeZone: UK, hour: '2-digit', minute: '2-digit' }).format(
    new Date(iso),
  )

export const formatUkDateTime = (iso: string) =>
  new Intl.DateTimeFormat('en-GB', {
    timeZone: UK,
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(iso))

export const formatDay = (isoDate: string, style: 'short' | 'long' = 'long') =>
  new Intl.DateTimeFormat('en-GB', {
    timeZone: 'UTC',
    weekday: style === 'long' ? 'long' : undefined,
    day: 'numeric',
    month: style === 'long' ? 'long' : 'short',
  }).format(new Date(`${isoDate}T00:00:00Z`))

export const formatHours = (hours: number) => `${hours.toLocaleString('en-GB')} h`
