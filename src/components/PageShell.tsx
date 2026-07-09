import { Outlet } from "react-router";
import { useEffect, useState } from "react";
import AppNav from "./AppNav";
import { ErrorBoundary } from "./ErrorBoundary";

interface Stats {
	articles: number;
	sources: number;
	claims: number;
	clusters: number;
	dateStart: string;
	dateEnd: string;
}

const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

function fmtMonth(iso: string): string {
	const m = parseInt(iso.slice(5,7),10);
	const y = iso.slice(0,4);
	return `${MONTHS[m-1] || ""} ${y}`;
}

export default function PageShell() {
	const [stats, setStats] = useState<Stats | null>(null);

	useEffect(() => {
		fetch("/api/stats")
			.then((r) => (r.ok ? r.json() : Promise.reject(new Error("bad response"))))
			.then((s: Stats) => setStats(s))
			.catch((err: unknown) => {
				console.warn("Footer stats fetch failed — endpoint may be unreachable", err);
				setStats(null);
			});
	}, []);

	return (
		<div className="flex min-h-screen flex-col">
			<AppNav />
			<main className="mx-auto w-full max-w-[1340px] flex-1 px-8 py-7">
				<ErrorBoundary>
					<Outlet />
				</ErrorBoundary>
			</main>
			<footer className="py-9 text-center font-mono text-[1.1rem] tracking-[0.04em] text-[var(--nn-text)]">
				Narrative Nexus tracks consensus reality, not truth
				{stats && (
					<>
						<br />
						<span className="text-[0.75rem] text-[var(--nn-text-dim)]">
							{stats.articles} articles · {stats.sources} sources · {fmtMonth(stats.dateStart)}–{fmtMonth(stats.dateEnd)}
						</span>
					</>
				)}
			</footer>
		</div>
	);
}
