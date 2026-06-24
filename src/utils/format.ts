export function formatPercent(value: number, decimals = 1): string {
  return `${(value * 100).toFixed(decimals)}%`
}

export function formatDays(value: number): string {
  return `${value.toFixed(1)}d`
}

export function formatRate(value: number, decimals = 2): string {
  return value.toFixed(decimals)
}