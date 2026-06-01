import { Monitor, Moon, Sun } from "lucide-react";
import { PALETTE_GROUP_LABELS, PALETTE_OPTIONS } from "../theme/palettes";
import { useTheme } from "../theme/useTheme";
import type { ThemeMode, ThemePalette } from "../theme/types";
import { Tooltip } from "./Tooltip";
import { SelectField } from "./SelectField";

const MODE_OPTIONS: {
  id: ThemeMode;
  label: string;
  icon: typeof Sun;
}[] = [
  { id: "light", label: "Light", icon: Sun },
  { id: "dark", label: "Dark", icon: Moon },
  { id: "system", label: "System", icon: Monitor },
];

const modeBtnBase =
  "inline-flex size-8 items-center justify-center rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-accent/30";

export function ThemeSwitcher() {
  const { mode, palette, setMode, setPalette } = useTheme();

  const groups = ["neutral", "cool", "warm"] as const;

  return (
    <div
      className="flex shrink-0 flex-col items-end gap-2 sm:flex-row sm:items-center"
      aria-label="Theme settings"
    >
      <div
        className="flex rounded-lg border border-border bg-surface p-0.5"
        role="group"
        aria-label="Color mode"
      >
        {MODE_OPTIONS.map((opt) => {
          const Icon = opt.icon;
          const active = mode === opt.id;
          return (
            <Tooltip key={opt.id} text={opt.label} variant="floating">
              <button
                type="button"
                className={`${modeBtnBase} ${
                  active
                    ? "bg-accent text-white"
                    : "text-muted hover:bg-surface-hover hover:text-foreground"
                }`}
                aria-pressed={active}
                aria-label={opt.label}
                onClick={() => setMode(opt.id)}
              >
                <Icon size={16} aria-hidden />
              </button>
            </Tooltip>
          );
        })}
      </div>

      <label className="flex items-center gap-1.5 text-xs text-muted">
        <span className="sr-only">Color palette</span>
        <SelectField
          compact
          value={palette}
          onChange={(e) => setPalette(e.target.value as ThemePalette)}
          aria-label="Color palette"
        >
          {groups.map((group) => (
            <optgroup key={group} label={PALETTE_GROUP_LABELS[group]}>
              {PALETTE_OPTIONS.filter((p) => p.group === group).map((p) => (
                <option key={p.id} value={p.id}>
                  {p.label}
                </option>
              ))}
            </optgroup>
          ))}
        </SelectField>
      </label>
    </div>
  );
}
