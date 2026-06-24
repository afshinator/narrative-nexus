import { Outlet } from "react-router";
import AppNav from "./AppNav";
import { ErrorBoundary } from "./ErrorBoundary";

export default function PageShell() {
  return (
    <div className="flex min-h-screen flex-col">
      <AppNav />
      <main className="flex-1 p-6">
        <ErrorBoundary>
          <Outlet />
        </ErrorBoundary>
      </main>
      <footer className="border-t border-border px-6 py-4 text-center text-sm text-muted-foreground">
        Narrative Nexus tracks consensus reality, not truth
      </footer>
    </div>
  );
}
