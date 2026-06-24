import { BrowserRouter, Routes, Route } from "react-router";
import PageShell from "./components/PageShell";
import SourcesPage from "./pages/Sources";
import SourceProfilePage from "./pages/SourceProfile";
import ClusterReportPage from "./pages/ClusterReport";
import TimelinePage from "./pages/Timeline";
import PipelineFlowPage from "./pages/PipelineFlow";
import InvestigatePage from "./pages/Investigate";
import PanelPage from "./pages/Panel";
import SettingsPage from "./pages/Settings";
import NotFoundPage from "./pages/NotFound";

export function App() {
  return (
    <BrowserRouter>
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
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
