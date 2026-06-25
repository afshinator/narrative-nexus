import { useCallback, useMemo, useState } from "react";
import { useNavigate } from "react-router";
import ArchetypePills from "../components/ArchetypePills";
import ScatterPlot from "../components/ScatterPlot";
import { DEFAULT_SOURCES } from "../data/sources";
import { useStore } from "../store";
import { getArchetype } from "../utils/archetype";

/** Reputation score for one source in one vertical.
 *  Extracted to a shared location when backend exists. */
export interface ReputationScore {
	sourceId: string;
	vertical: string;
	R_orig: number;
	R_val: number;
	R_speed: number;
	R_frame: number;
	R_edit: number;
	R_correct: number;
}

interface Props {
	scores?: ReputationScore[];
}

const SCORE_COLUMNS = [
	{ key: "R_orig", label: "Origination" },
	{ key: "R_val", label: "Validation" },
	{ key: "R_speed", label: "Speed" },
	{ key: "R_frame", label: "Framing" },
	{ key: "R_edit", label: "Silent Edits" },
	{ key: "R_correct", label: "Corrections" },
] as const;

type SortKey = "name" | (typeof SCORE_COLUMNS)[number]["key"];

export default function SourcesPage({ scores = [] }: Props) {
	const navigate = useNavigate();
	const [hoveredSource, setHoveredSource] = useState<string | null>(null);
	const [sortKey, setSortKey] = useState<SortKey>("name");
	const [sortDir, setSortDir] = useState<1 | -1>(1);

	const filter = useStore((s) => s.archetypeFilter);

	const scoreMap = useMemo(
		() => new Map(scores.map((s) => [s.sourceId, s])),
		[scores],
	);

	// Compute panel median for archetype assignment
	const panelMedian = useMemo(() => {
		if (scores.length === 0) return { orig: 50, val: 50 };
		const sorted = {
			orig: [...scores].sort((a, b) => a.R_orig - b.R_orig),
			val: [...scores].sort((a, b) => a.R_val - b.R_val),
		};
		const mid = Math.floor(scores.length / 2);
		return {
			orig:
				scores.length % 2
					? sorted.orig[mid].R_orig
					: (sorted.orig[mid - 1].R_orig + sorted.orig[mid].R_orig) / 2,
			val:
				scores.length % 2
					? sorted.val[mid].R_val
					: (sorted.val[mid - 1].R_val + sorted.val[mid].R_val) / 2,
		};
	}, [scores]);

	// Enrich sources with scores + archetype, then filter + sort
	const rows = useMemo(() => {
		const enriched = DEFAULT_SOURCES.map((source) => {
			const score = scoreMap.get(source.id);
			const archetype = score
				? getArchetype(
						score.R_orig,
						score.R_val,
						panelMedian.orig,
						panelMedian.val,
					)
				: null;
			return { source, score, archetype };
		});

		// Filter by archetype — dim-mode: keep all rows, dim non-matching
		const allRows = enriched.map((r) => ({
			...r,
			dimmed: filter !== null && r.archetype !== filter,
		}));

		// Sort
		allRows.sort((a, b) => {
			let va: number | string, vb: number | string;
			if (sortKey === "name") {
				va = a.source.name.toLowerCase();
				vb = b.source.name.toLowerCase();
			} else {
				va = a.score?.[sortKey] ?? 0;
				vb = b.score?.[sortKey] ?? 0;
			}
			if (va < vb) return -1 * sortDir;
			if (va > vb) return 1 * sortDir;
			return 0;
		});

		return allRows;
	}, [scoreMap, panelMedian, filter, sortKey, sortDir]);

	function handleSort(key: SortKey) {
		if (sortKey === key) {
			setSortDir((d) => (d === 1 ? -1 : 1));
		} else {
			setSortKey(key);
			setSortDir(1);
		}
	}

	function sortArrow(key: SortKey) {
		if (sortKey !== key) return "";
		return sortDir === 1 ? " ↑" : " ↓";
	}

	const handleSelect = useCallback(
		(id: string) => {
			const source = DEFAULT_SOURCES.find((s) => s.id === id);
			if (source) navigate(`/source/${source.domain}`);
		},
		[navigate],
	);

	return (
		<div className="mx-auto max-w-[1340px] space-y-6">
			{/* Page header */}
			<div className="pagehead">
				<h1 className="font-heading text-[2rem] font-bold leading-none tracking-[-0.02em] text-[var(--nn-text)]">
					Sources
				</h1>
			</div>
			<p className="-mt-2 font-sans text-[0.9rem] text-[var(--nn-text-dim)]">
				Behavioral reputation across 20 monitored outlets — GEOPOLITICS vertical
			</p>

			{/* Archetype filter pills */}
			<ArchetypePills />

			{/* Scatter plot card */}
			<div className="rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-6">
				<div className="mb-2 flex items-baseline justify-between gap-2">
					<h2 className="font-heading text-[1.15rem] font-bold text-[var(--nn-text)]">
						The Reputation Map
					</h2>
				</div>
				<ScatterPlot
					data={[]}
					hoveredId={hoveredSource}
					onHover={setHoveredSource}
					onSelect={handleSelect}
				/>
			</div>

			{/* Ledger card */}
			<div className="rounded-[14px] border border-[var(--nn-border)] bg-[var(--nn-surface)] p-6">
				<div className="mb-3 flex items-baseline justify-between gap-2">
					<h2 className="font-heading text-[1.15rem] font-bold text-[var(--nn-text)]">
						Full Ledger
					</h2>
				</div>
				<div className="overflow-x-auto">
					<table className="w-full border-collapse text-[0.88rem]">
						<thead>
							<tr>
								<th
									className="px-2.5 py-2 text-left font-mono text-[0.7rem] font-bold uppercase tracking-[0.05em] text-[var(--nn-text-dim)] border-b-2 border-[var(--nn-border)] cursor-pointer select-none hover:text-[var(--nn-text)]"
									onClick={() => handleSort("name")}
								>
									Source{sortArrow("name")}
								</th>
								{SCORE_COLUMNS.map((col) => (
									<th
										key={col.key}
										className="px-2.5 py-2 text-left font-mono text-[0.7rem] font-bold uppercase tracking-[0.05em] text-[var(--nn-text-dim)] border-b-2 border-[var(--nn-border)] cursor-pointer select-none hover:text-[var(--nn-text)]"
										onClick={() => handleSort(col.key)}
									>
										{col.label}
										{sortArrow(col.key)}
									</th>
								))}
							</tr>
						</thead>
						<tbody>
							{rows.map(({ source, score, dimmed }) => (
								<tr
									key={source.id}
									data-source-id={source.id}
									className={`border-b border-[var(--nn-border)] hover:bg-[var(--nn-surface2)] transition-colors cursor-pointer${
										dimmed ? " opacity-15" : ""
									}`}
									onMouseEnter={() => setHoveredSource(source.id)}
									onMouseLeave={() => setHoveredSource(null)}
									onClick={() => navigate(`/source/${source.domain}`)}
								>
									<td className="px-2.5 py-2.5 font-semibold text-[0.9rem] text-[var(--nn-text)]">
										{source.name}
										<span className="ml-2 font-mono text-[0.78rem] font-normal text-[var(--nn-text-dim)]">
											{source.domain}
										</span>
									</td>
									{SCORE_COLUMNS.map((col) => (
										<td
											key={col.key}
											className="px-2.5 py-2.5 font-mono text-[0.8rem] tabular-nums text-[var(--nn-text-dim)]"
										>
											{score != null
												? score[col.key as keyof ReputationScore]
												: "—"}
										</td>
									))}
								</tr>
							))}
						</tbody>
					</table>
				</div>
			</div>
		</div>
	);
}
