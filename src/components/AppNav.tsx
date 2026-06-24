import { NavLink } from "react-router";
import { HelpCircle } from "lucide-react";

const navItems = [
  { to: "/", label: "Sources" },
  { to: "/source/example.com", label: "Source Profile" },
  { to: "/cluster/abc123", label: "Cluster Report" },
  { to: "/timeline/abc123", label: "Timeline" },
  { to: "/pipeline", label: "Pipeline" },
  { to: "/investigate", label: "Investigate" },
  { to: "/panel", label: "Panel" },
  { to: "/settings", label: "Settings" },
] as const;

export default function AppNav() {
  return (
    <nav className="sticky top-0 z-50 flex items-center gap-4 border-b border-border bg-background px-6 py-3">
      <span className="font-semibold text-sm tracking-wide text-primary">
        Narrative Nexus
      </span>

      <div className="flex gap-1">
        {navItems.map(({ to, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              `rounded-md px-3 py-1.5 text-sm transition-colors ${
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted"
              }`
            }
          >
            {label}
          </NavLink>
        ))}
      </div>

      <div className="ml-auto">
        <button
          type="button"
          className="rounded-md p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
          aria-label="Open onboarding"
        >
          <HelpCircle size={18} />
        </button>
      </div>
    </nav>
  );
}
