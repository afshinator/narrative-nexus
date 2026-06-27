/** Format an integer as percent (e.g. 65 → "65%"). */
export function formatPercent(n: number): string {
	return `${n}%`;
}

export function formatDays(value: number): string {
	return `${value.toFixed(1)}d`;
}

export function formatRate(value: number, decimals = 2): string {
	return value.toFixed(decimals);
}
