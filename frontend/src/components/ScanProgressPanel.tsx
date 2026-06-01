import { type ScanProgressEvent } from "../api/client";

interface Props {
  events: ScanProgressEvent[];
  active: boolean;
  stopped?: boolean;
}

const STAGE_LABELS: Record<string, string> = {
  validating: "Validate",
  ytdlp: "yt-dlp",
  ytdlp_ok: "yt-dlp",
  ytdlp_empty: "yt-dlp",
  ytdlp_failed: "yt-dlp",
  ytdlp_embed: "yt-dlp",
  embed_discover: "Embeds",
  playwright: "Network capture",
  playwright_browser: "Browser",
  playwright_page: "Page load",
  playwright_autoplay: "Playback",
  playwright_manifests: "Manifests",
  playwright_ok: "Network capture",
  playwright_empty: "Network capture",
  complete: "Done",
  result: "Done",
};

export function ScanProgressPanel({ events, active, stopped = false }: Props) {
  if (!active && events.length === 0) return null;

  const latest = events[events.length - 1];
  const headerText = active ? "Scan in progress" : stopped ? "Scan stopped" : "Scan finished";

  return (
    <div
      className="mt-3 rounded-md border border-border bg-background/60 px-4 py-3"
      role="status"
      aria-live="polite"
      aria-busy={active}
    >
      <div className="mb-2 flex items-center gap-2">
        {active && (
          <span
            className="inline-block size-4 shrink-0 animate-spin rounded-full border-2 border-accent border-t-transparent"
            aria-hidden
          />
        )}
        <span className={`text-sm font-semibold ${stopped ? "text-warn" : "text-foreground"}`}>
          {headerText}
        </span>
      </div>
      {latest && <p className="m-0 text-sm text-muted">{latest.message}</p>}
      {events.length > 1 && (
        <ul className="mt-2.5 mb-0 max-h-32 list-none space-y-1 overflow-y-auto p-0 text-xs text-muted">
          {events.map((ev, i) => (
            <li
              key={`${ev.stage}-${i}`}
              className={
                i === events.length - 1 && active ? "font-medium text-foreground" : undefined
              }
            >
              <span className="text-badge-muted">{STAGE_LABELS[ev.stage] ?? ev.stage}</span>
              {": "}
              {ev.message}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
