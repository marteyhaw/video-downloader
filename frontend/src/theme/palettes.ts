import type { PaletteGroup, ThemePalette } from "./types";

export interface PaletteOption {
  id: ThemePalette;
  label: string;
  group: PaletteGroup;
}

export const PALETTE_OPTIONS: PaletteOption[] = [
  { id: "neutral", label: "Neutral", group: "neutral" },
  { id: "ocean", label: "Ocean", group: "cool" },
  { id: "frost", label: "Frost", group: "cool" },
  { id: "sunset", label: "Sunset", group: "warm" },
  { id: "ember", label: "Ember", group: "warm" },
];

export const PALETTE_GROUP_LABELS: Record<PaletteGroup, string> = {
  neutral: "Default",
  cool: "Cool",
  warm: "Warm",
};
