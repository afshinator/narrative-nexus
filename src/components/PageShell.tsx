import { Outlet } from "react-router";
import AppNav from "./AppNav";
import { ErrorBoundary } from "./ErrorBoundary";

export default function PageShell() {
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
			</footer>
		</div>
	);
}
