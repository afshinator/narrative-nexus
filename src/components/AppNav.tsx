import { useState } from "react";
import { NavLink } from "react-router";
import { HelpCircle } from "lucide-react";
import { useStore } from "../store";
import { OnboardingDialog } from "./OnboardingDialog";

const navItems = [
  { to: "/", label: "Sources" },
  { to: "/source/example.com", label: "Source Profile" },
  { to: "/cluster/abc123", label: "Cluster Report" },
  { to: "/timeline/abc123", label: "Timeline" },
  { to: "/pipeline", label: "Pipeline" },
  { to: "/investigate", label: "Investigate" },
  { to: "/panel", label: "Panel" },
] as const;

export default function AppNav() {
  const onboardingComplete = useStore((s) => s.onboardingComplete);
  const [dialogOpen, setDialogOpen] = useState(!onboardingComplete);

  return (
    <nav className="sticky top-0 z-50 flex h-[52px] items-stretch gap-0.5 border-b border-[var(--nn-border)] bg-[var(--nn-nav-bg)] px-7">
      {/* Brand */}
      <span className="flex items-center gap-2.5 pr-6 font-heading text-[1rem] font-bold tracking-[-0.01em] text-[var(--nn-text)]">
        <svg width="20" height="20" viewBox="0 0 26 26" className="shrink-0">
          <circle cx="13" cy="13" r="11" fill="none" stroke="var(--nn-navy)" strokeWidth="1.4" strokeDasharray="2,2.8" />
          <circle cx="13" cy="13" r="6.5" fill="none" stroke="var(--nn-navy)" strokeWidth="1.4" />
          <circle cx="13" cy="13" r="2.2" fill="var(--nn-navy)" />
        </svg>
        Narrative Nexus
      </span>

      {/* Nav links */}
      {navItems.map(({ to, label }) => (
        <NavLink
          key={to}
          to={to}
          end={to === "/"}
          className={({ isActive }) =>
            `flex items-center px-3.5 font-sans text-[0.84rem] border-b-2 transition-[color,border-color] duration-150 ${
              isActive
                ? "border-[var(--nn-navy)] font-semibold text-[var(--nn-navy)]"
                : "border-transparent text-[var(--nn-text-dim)] hover:text-[var(--nn-text)]"
            }`
          }
        >
          {label}
        </NavLink>
      ))}

      {/* Spacer + Settings */}
      <span className="flex-1" />
      <span className="my-[13px] w-px bg-[var(--nn-border)]" />
      <NavLink
        to="/settings"
        className={({ isActive }) =>
          `flex items-center px-3.5 font-sans text-[0.84rem] border-b-2 transition-[color,border-color] duration-150 ${
            isActive
              ? "border-[var(--nn-navy)] font-semibold text-[var(--nn-navy)]"
              : "border-transparent text-[var(--nn-text-dim)] hover:text-[var(--nn-text)]"
          }`
        }
      >
        Settings
      </NavLink>

      {/* ? icon */}
      <button
        type="button"
        className="flex items-center px-2 text-[var(--nn-text-dim)] hover:text-[var(--nn-text)] transition-colors duration-150"
        aria-label="Open onboarding"
        onClick={() => setDialogOpen(true)}
      >
        <HelpCircle size={18} />
      </button>

      <OnboardingDialog open={dialogOpen} onOpenChange={setDialogOpen} />
    </nav>
  );
}
