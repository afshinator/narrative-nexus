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
	currentDay: number;
}

export default function VfTrendChart({ snapshots, currentDay }: Props) {
	// ponytail: currentDay reserved for vertical reference line — not yet implemented
	void currentDay;

	if (snapshots.length === 0) {
		return (
			<div className="rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-5">
				<h2 className="mb-1 font-heading text-[1.15rem] font-bold text-[var(--nn-text)]">
					Verifiability Trend
				</h2>
				<p className="text-sm text-[var(--nn-text-dim)]">No trend data</p>
			</div>
		);
	}

	const labels = snapshots.map((s) => String(s.day));
	const values = snapshots.map((s) => s.R_val);

	const data = {
		labels,
		datasets: [
			{
				label: "Vf",
				data: values,
				borderColor: "var(--nn-teal)",
				backgroundColor: "rgba(94,189,142,0.08)",
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
				Verifiability Trend
			</h2>
			<div className="h-[200px]">
				<Line
					data={data}
					options={options}
					aria-label="Verifiability trend chart"
				/>
			</div>
		</div>
	);
}
