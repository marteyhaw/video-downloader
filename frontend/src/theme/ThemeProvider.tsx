import { createContext, useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import type { ResolvedMode, ThemeMode, ThemePalette } from "./types";

const STORAGE_MODE = "vd-theme-mode";
const STORAGE_PALETTE = "vd-theme-palette";

function readStoredMode(): ThemeMode {
  const v = localStorage.getItem(STORAGE_MODE);
  if (v === "light" || v === "dark" || v === "system") return v;
  return "system";
}

function readStoredPalette(): ThemePalette {
  const v = localStorage.getItem(STORAGE_PALETTE);
  if (v === "neutral" || v === "ocean" || v === "frost" || v === "sunset" || v === "ember") {
    return v;
  }
  return "neutral";
}

function systemPrefersDark(): boolean {
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

function resolveMode(mode: ThemeMode): ResolvedMode {
  if (mode === "system") {
    return systemPrefersDark() ? "dark" : "light";
  }
  return mode;
}

export interface ThemeContextValue {
  mode: ThemeMode;
  palette: ThemePalette;
  resolvedMode: ResolvedMode;
  setMode: (mode: ThemeMode) => void;
  setPalette: (palette: ThemePalette) => void;
}

export const ThemeContext = createContext<ThemeContextValue | null>(null);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [mode, setModeState] = useState<ThemeMode>(() => readStoredMode());
  const [palette, setPaletteState] = useState<ThemePalette>(() => readStoredPalette());
  const [resolvedMode, setResolvedMode] = useState<ResolvedMode>(() =>
    resolveMode(readStoredMode()),
  );

  const applyToDocument = useCallback((nextMode: ThemeMode, nextPalette: ThemePalette) => {
    const resolved = resolveMode(nextMode);
    setResolvedMode(resolved);
    document.documentElement.setAttribute("data-palette", nextPalette);
    document.documentElement.setAttribute("data-mode", resolved);
    document.documentElement.style.colorScheme = resolved;
  }, []);

  useEffect(() => {
    applyToDocument(mode, palette);
  }, [mode, palette, applyToDocument]);

  useEffect(() => {
    if (mode !== "system") return;
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => applyToDocument("system", palette);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, [mode, palette, applyToDocument]);

  const setMode = useCallback((next: ThemeMode) => {
    setModeState(next);
    localStorage.setItem(STORAGE_MODE, next);
  }, []);

  const setPalette = useCallback((next: ThemePalette) => {
    setPaletteState(next);
    localStorage.setItem(STORAGE_PALETTE, next);
  }, []);

  const value = useMemo(
    () => ({ mode, palette, resolvedMode, setMode, setPalette }),
    [mode, palette, resolvedMode, setMode, setPalette],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}
