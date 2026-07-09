import { lazy, Suspense } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router";
import PageShell from "./components/PageShell";

// Code-split every page.  A single <Suspense> wraps all routes so
// navigating from one lazy page to another keeps the old content visible
// until the new chunk loads — no white flash.
const SourcesPage = lazy(() => import("./pages/Sources"));
const SourceProfilePage = lazy(() => import("./pages/SourceProfile"));
const ClusterReportPage = lazy(() => import("./pages/ClusterReport"));
const TimelinePage = lazy(() => import("./pages/Timeline"));
const PipelineFlowPage = lazy(() => import("./pages/PipelineFlow"));
const InvestigatePage = lazy(() => import("./pages/Investigate"));
const PanelPage = lazy(() => import("./pages/Panel"));
const SettingsPage = lazy(() => import("./pages/Settings"));
const StoriesPage = lazy(() => import("./pages/Stories"));
const NotFoundPage = lazy(() => import("./pages/NotFound"));

export function App() {
	return (
		<BrowserRouter>
			<Suspense
				fallback={
					<div className="flex min-h-[50vh] items-center justify-center text-[var(--nn-text-dim)]">
						Loading…
					</div>
				}
			>
				<Routes>
					<Route element={<PageShell />}>
						<Route index element={<SourcesPage />} />
						<Route path="source/:domain" element={<SourceProfilePage />} />
						<Route path="cluster/:clusterId" element={<ClusterReportPage />} />
						<Route path="timeline/:clusterId" element={<TimelinePage />} />
						<Route path="pipeline" element={<PipelineFlowPage />} />
						<Route path="investigate" element={<InvestigatePage />} />
						<Route path="panel" element={<PanelPage />} />
						<Route path="settings" element={<SettingsPage />} />
						<Route path="stories" element={<StoriesPage />} />
						{/* UX40: redirect bare /cluster and /timeline to /stories */}
						<Route path="cluster" element={<Navigate to="/stories" replace />} />
						<Route path="timeline" element={<Navigate to="/stories" replace />} />
						<Route path="*" element={<NotFoundPage />} />
					</Route>
				</Routes>
			</Suspense>
		</BrowserRouter>
	);
}
