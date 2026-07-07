import {
	CategoryScale,
	Chart as ChartJS,
	Filler,
	Legend,
	LinearScale,
	LineElement,
	PointElement,
	Tooltip,
} from "chart.js";
import { Line } from "react-chartjs-2";
import type { DailySnapshot } from "../data/scores";

ChartJS.register(
	CategoryScale,
	LinearScale,
	PointElement,
	LineElement,
	Filler,
	Tooltip,
	Legend,
);

interface Props {
	snapshots: DailySnapshot[];
	currentDay?: number;
}

/** Format ISO date "2026-03-03" → "Mar 3" */
function fmtDate(dateStr: string): string {
	const d = new Date(`${dateStr}T00:00:00`);
	return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export default function VfTrendChart({ snapshots, currentDay = 0 }: Props) {
	// ponytail: currentDay reserved for vertical reference line — not yet implemented
	void currentDay;

	if (snapshots.length === 0) {
		return (
			<div className="rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-5">
				<h2 className="mb-1 font-heading text-[1.15rem] font-bold text-[var(--nn-text)]">
					Validation over time
				</h2>
				<p className="mb-3 font-sans text-[0.78rem] text-[var(--nn-text-dim)]">
					How this source's validation score changed across the demo window (Mar–Jul 2026)
				</p>
				<p className="text-sm text-[var(--nn-text-dim)]">No trend data</p>
			</div>
		);
	}

	// F3b: Check if all R_val values are null or zero — show empty state
	const allNull = snapshots.every((s) => s.R_val == null || s.R_val === 0);
	if (allNull) {
		return (
			<div className="rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-5">
				<h2 className="mb-1 font-heading text-[1.15rem] font-bold text-[var(--nn-text)]">
					Validation over time
				</h2>
				<p className="mb-3 font-sans text-[0.78rem] text-[var(--nn-text-dim)]">
					How this source's validation score changed across the demo window (Mar–Jul 2026)
				</p>
				<div className="flex h-[200px] items-center justify-center">
					<p className="text-[0.85rem] text-[var(--nn-text-dim)]">
						No validation events recorded yet.
					</p>
				</div>
			</div>
		);
	}

	const labels = snapshots.map((s) => fmtDate(s.date));
	const values = snapshots.map((s) => s.R_val);

	const data = {
		labels,
		datasets: [
			{
				label: "Vf",
				data: values,
				borderColor: "var(--nn-teal)",
				backgroundColor: "rgba(94,189,142,0.22)",
				borderWidth: 2,
				pointRadius: 0,
				fill: true,
				tension: 0.2,
			},
		],
	};

	const options = {
		responsive: true,
		maintainAspectRatio: false,
		scales: {
			x: {
				ticks: { color: "var(--nn-text-dim)", font: { size: 9 } },
				grid: { color: "var(--nn-border)" },
			},
			y: {
				min: 0,
				max: 100,
				title: {
					display: true,
					text: "Validation score",
					color: "var(--nn-text-dim)",
					font: { size: 10 },
				},
				ticks: {
					color: "var(--nn-text-dim)",
					font: { size: 9 },
					stepSize: 25,
				},
				grid: { color: "var(--nn-border)" },
			},
		},
		plugins: {
			legend: { display: false },
			tooltip: {
				callbacks: {
					label: (ctx: { raw: unknown }) =>
						`Vf: ${Math.round(Number(ctx.raw) || 0)}`,
				},
			},
		},
	};

	return (
		<div className="rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-5">
			<h2 className="mb-1 font-heading text-[1.15rem] font-bold text-[var(--nn-text)]">
				Validation over time
			</h2>
			<p className="mb-3 font-sans text-[0.78rem] text-[var(--nn-text-dim)]">
				How this source's validation score changed across the demo window (Mar–Jul 2026)
			</p>
			<div className="h-[200px]">
				<Line
					data={data}
					options={options}
					aria-label="Validation trend chart"
				/>
			</div>
		</div>
	);
}
