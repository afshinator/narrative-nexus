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

export default function SettingsPage() {
  const thresholds = useStore((s) => s.consensusThresholds);
  const fontScale = useStore((s) => s.fontScale);
  const theme = useStore((s) => s.theme);
  const setConsensusThreshold = useStore((s) => s.setConsensusThreshold);
  const resetThresholds = useStore((s) => s.resetThresholds);
  const setFontScale = useStore((s) => s.setFontScale);
  const setTheme = useStore((s) => s.setTheme);

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <h1 className="font-heading text-2xl font-semibold tracking-tight text-foreground">
        Settings
      </h1>

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
            <RotateCcw size={14} className="mr-1" />
            Reset
          </Button>
        </div>
        <div className="space-y-4">
          {(Object.keys(VERTICAL_LABELS) as VerticalThresholdKey[]).map(
            (key) => (
              <div key={key} className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-sm text-muted-foreground">
                    {VERTICAL_LABELS[key]}
                  </label>
                  <span className="font-mono text-sm tabular-nums text-foreground">
                    {formatPercent(thresholds[key])}
                  </span>
                </div>
                <Slider
                  value={[thresholds[key]]}
                  onValueChange={([v]) => setConsensusThreshold(key, v)}
                  min={0}
                  max={100}
                  step={1}
                />
              </div>
            ),
          )}
        </div>
      </Card>

      {/* Font Scale */}
      <Card className="p-6">
        <h2 className="mb-4 text-base font-medium text-foreground">
          Font Scale
        </h2>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-sm text-muted-foreground">Scale</label>
            <span className="font-mono text-sm tabular-nums text-foreground">
              {fontScale.toFixed(1)}×
            </span>
          </div>
          <Slider
            value={[fontScale]}
            onValueChange={([v]) => setFontScale(v)}
            min={0.8}
            max={1.5}
            step={0.05}
          />
        </div>
        <p className="mt-3 text-xs text-muted-foreground">
          This text resizes live as you drag.
        </p>
      </Card>

      {/* Theme */}
      <Card className="p-6">
        <h2 className="mb-4 text-base font-medium text-foreground">Theme</h2>
        <div className="flex items-center justify-between">
          <label className="text-sm text-muted-foreground">Dark mode</label>
          <Switch
            checked={theme === "dark"}
            onCheckedChange={(on) => setTheme(on ? "dark" : "light")}
          />
        </div>
      </Card>
    </div>
  );
}
