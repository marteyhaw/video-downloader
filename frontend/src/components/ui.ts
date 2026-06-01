/** Shared Tailwind class strings for form controls and layout */

export const sectionClass = "mb-5 rounded-lg border border-border bg-surface p-5 sm:p-6";

export const sectionTitleClass = "mb-4 text-sm font-semibold uppercase tracking-wider text-muted";

const fieldBase =
  "rounded-md border border-border bg-background text-sm text-foreground font-sans focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/30";

export const inputClass = `${fieldBase} w-full px-3 py-2.5`;

/** Native select with hidden UA arrow; pair with SelectField for chevron icon. */
export const selectClass = `${fieldBase} w-full appearance-none py-2.5 pl-3 pr-9`;

export const selectClassCompact = `${fieldBase} appearance-none py-1.5 pl-2 pr-9`;

export const labelClass = "mb-1.5 block text-xs text-muted";

export const btnPrimaryClass =
  "rounded-md bg-accent px-4 py-2.5 text-sm font-semibold text-white hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-50 whitespace-nowrap";

export const btnStopClass =
  "rounded-md bg-danger px-4 py-2.5 text-sm font-semibold text-white hover:bg-danger/90 disabled:cursor-not-allowed disabled:opacity-50 whitespace-nowrap";

export const btnSecondaryClass =
  "rounded-md bg-surface-hover px-3 py-1.5 text-sm font-semibold text-foreground hover:bg-border disabled:cursor-not-allowed disabled:opacity-50";

export const btnDangerClass =
  "rounded-md bg-danger/15 px-3 py-1.5 text-sm font-semibold text-danger hover:bg-danger/30 hover:text-white disabled:cursor-not-allowed disabled:opacity-50";

const btnIconBase =
  "inline-flex size-8 shrink-0 items-center justify-center rounded-md disabled:cursor-not-allowed disabled:opacity-50";

export const btnIconSecondaryClass = `${btnIconBase} bg-surface-hover text-foreground hover:bg-border`;

export const btnIconPrimaryClass = `${btnIconBase} bg-accent text-white hover:bg-accent-hover`;

export const btnIconDangerClass = `${btnIconBase} bg-danger/15 text-danger hover:bg-danger/30 hover:text-white`;

const filterChipBase =
  "rounded px-1.5 py-0.5 text-[0.68rem] font-semibold uppercase tracking-wide transition-colors border";

export function filterChipClass(active: boolean, activeClass: string): string {
  if (active) {
    return `${filterChipBase} border-transparent ${activeClass}`;
  }
  return `${filterChipBase} border-border bg-transparent text-muted hover:bg-surface-hover hover:text-foreground`;
}
