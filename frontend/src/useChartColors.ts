import { useEffect, useState } from 'react'

// Recharts writes colours as SVG attributes, which can't resolve CSS variables,
// so read the theme tokens in JS and re-read them when the system theme flips.
const TOKENS = ['ink', 'muted', 'line', 'surface', 'forecast', 'actual', 'shortfall'] as const

export type ChartColors = Record<(typeof TOKENS)[number], string>

function readColors(): ChartColors {
  const style = getComputedStyle(document.documentElement)
  return Object.fromEntries(
    TOKENS.map((token) => [token, style.getPropertyValue(`--${token}`).trim()]),
  ) as ChartColors
}

export function useChartColors(): ChartColors {
  const [colors, setColors] = useState(readColors)
  useEffect(() => {
    const query = window.matchMedia('(prefers-color-scheme: dark)')
    const update = () => setColors(readColors())
    query.addEventListener('change', update)
    return () => query.removeEventListener('change', update)
  }, [])
  return colors
}
