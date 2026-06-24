/** Format a 0–1 decimal as percent (e.g. 0.65 → "65.0%"). */
export function formatDecimalAsPercent(value: number, decimals = 1): string {
  return `${(value * 100).toFixed(decimals)}%`
}

/** Format an integer as percent (e.g. 65 → "65%"). */
export function formatPercent(n: number): string {
  return `${n}%`
}

export function formatDays(value: number): string {
  return `${value.toFixed(1)}d`
}

export function formatRate(value: number, decimals = 2): string {
  return value.toFixed(decimals)
}