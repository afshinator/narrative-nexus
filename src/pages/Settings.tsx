import { useStore } from "../store";
import type { VerticalThresholdKey } from "../data/thresholds";
import { formatPercent } from "../utils/format";
import { Card } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { RotateCcw } from "lucide-react";

const VERTICAL_LABELS: Record<VerticalThresholdKey, string> = {
  geopolitics: "Geopolitics",
  economics: "Economics",
  technology: "Technology",
};

const VERTICAL_ORDER: VerticalThresholdKey[] = [
  "geopolitics",
  "economics",
  "technology",
];

export default function SettingsPage() {
  const theme = useStore((s) => s.theme);
  const setTheme = useStore((s) => s.setTheme);
  const thresholds = useStore((s) => s.consensusThresholds);
  const setConsensusThreshold = useStore((s) => s.setConsensusThreshold);
  const resetThresholds = useStore((s) => s.resetThresholds);
  const fontScale = useStore((s) => s.fontScale);
  const setFontScale = useStore((s) => s.setFontScale);

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      {/* Page header — mock style */}
      <div className="pagehead">
        <h1 className="font-heading text-[2rem] font-bold leading-none tracking-[-0.02em] text-[var(--nn-text)]">
          Settings
        </h1>
      </div>
      <p className="-mt-2 font-sans text-[0.9rem] text-[var(--nn-text-dim)]">
        Configure thresholds, appearance, and preferences
      </p>

      {/* Consensus Thresholds */}
      <Card className="p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-medium text-foreground">
            Consensus Thresholds
          </h2>
          <Button
            variant="ghost"
            size="sm"
            onClick={resetThresholds}
            aria-label="Reset thresholds to defaults"
          >
            <RotateCcw size={14} />
            Reset
          </Button>
        </div>
        <div className="space-y-4">
          {VERTICAL_ORDER.map((key) => (
            <div key={key} className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">
                  {VERTICAL_LABELS[key]}
                </span>
                <span className="font-mono text-sm tabular-nums text-foreground">
                  {formatPercent(thresholds[key])}
                </span>
              </div>
              <Slider
                value={[thresholds[key]]}
                onValueChange={([v]) => setConsensusThreshold(key, v)}
                max={100}
                step={1}
                aria-label={VERTICAL_LABELS[key]}
              />
            </div>
          ))}
        </div>
      </Card>

      {/* Font Scale */}
      <Card className="p-6">
        <h2 className="mb-4 text-base font-medium text-foreground">Font Scale</h2>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Scale</span>
            <span className="font-mono text-sm tabular-nums text-foreground">
              {fontScale.toFixed(1)}×
            </span>
          </div>
          <Slider
            value={[fontScale]}
            onValueChange={([v]) => setFontScale(Math.round(v * 10) / 10)}
            min={0.8}
            max={1.4}
            step={0.1}
            aria-label="Font scale"
          />
        </div>
      </Card>

      {/* Theme */}
      <Card className="p-6">
        <h2 className="mb-4 text-base font-medium text-foreground">Theme</h2>
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Dark mode</span>
          <Switch
            checked={theme === "dark"}
            onCheckedChange={(v) => setTheme(v ? "dark" : "light")}
            aria-label="Toggle dark mode"
          />
        </div>
      </Card>
    </div>
  );
}
