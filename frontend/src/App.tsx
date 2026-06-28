import { useCallback, useEffect, useRef, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchHealth, fetchHistory, revealInFolder } from "./api/client";
import { DownloadPanel } from "./components/DownloadPanel";
import { HistoryPanel } from "./components/HistoryPanel";
import { ThemeSwitcher } from "./components/ThemeSwitcher";
import { ToastStack } from "./components/ToastStack";
import { useDownloadJob } from "./hooks/useDownloadJob";
import { useScan } from "./hooks/useScan";
import { useToasts } from "./hooks/useToasts";
import {
  hasUnreadHistory as computeHasUnread,
  maxHistoryId,
  readLastSeenHistoryId,
  writeLastSeenHistoryId,
} from "./utils/historyReadState";

type TabId = "download" | "history";

const TAB_BASE = "flex-1 rounded-md px-4 py-2.5 text-sm font-semibold transition-colors";
const TAB_INACTIVE = "text-muted hover:bg-surface-hover hover:text-foreground";
const TAB_ACTIVE = "bg-accent text-white hover:bg-accent-hover";

export default function App() {
  const [activeTab, setActiveTab] = useState<TabId>("download");
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [lastSeenHistoryMaxId, setLastSeenHistoryMaxId] = useState(
    () => readLastSeenHistoryId() ?? 0,
  );
  const [hasUnreadHistory, setHasUnreadHistory] = useState(false);

  const downloadSectionRef = useRef<HTMLElement>(null);
  const pageTopRef = useRef<HTMLDivElement>(null);
  const scanSectionRef = useRef<HTMLElement>(null);
  // Refs mirror state for use inside callbacks that would otherwise close over stale values
  const activeTabRef = useRef(activeTab);
  const lastSeenRef = useRef(lastSeenHistoryMaxId);
  const historyInitializedRef = useRef(false);

  activeTabRef.current = activeTab;
  lastSeenRef.current = lastSeenHistoryMaxId;

  const queryClient = useQueryClient();
  const { toasts, pushToast, dismissToast } = useToasts();

  const scan = useScan();

  const markHistorySeen = useCallback((maxId: number) => {
    setLastSeenHistoryMaxId(maxId);
    writeLastSeenHistoryId(maxId);
    setHasUnreadHistory(false);
  }, []);

  const onHistoryUpdate = useCallback(
    (maxId: number) => {
      if (activeTabRef.current === "history") {
        markHistorySeen(maxId);
      } else if (maxId > lastSeenRef.current) {
        setHasUnreadHistory(true);
      }
    },
    [markHistorySeen],
  );

  const download = useDownloadJob(onHistoryUpdate, pushToast);

  const health = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
    refetchInterval: 60_000,
  });

  const history = useQuery({
    queryKey: ["history"],
    queryFn: fetchHistory,
  });

  const historyFetchError = history.isError ? (history.error as Error).message : null;

  useEffect(() => {
    if (!history.data || historyInitializedRef.current) return;
    historyInitializedRef.current = true;
    const maxId = maxHistoryId(history.data);
    const stored = readLastSeenHistoryId();
    if (stored === null) {
      markHistorySeen(maxId);
    } else {
      setLastSeenHistoryMaxId(stored);
      setHasUnreadHistory(computeHasUnread(history.data, stored));
    }
  }, [history.data, markHistorySeen]);

  useEffect(() => {
    if (activeTab !== "history" || !history.data?.length) return;
    markHistorySeen(maxHistoryId(history.data));
  }, [activeTab, history.data, markHistorySeen]);

  useEffect(() => {
    if (activeTab === "history") {
      void queryClient.invalidateQueries({ queryKey: ["history"] });
    }
  }, [activeTab, queryClient]);

  const handleDownload = (opts: { container: string; includeAudio: boolean; filename: string }) => {
    if (!scan.selected) return;
    download.handleDownload(scan.selected, opts, scan.pageUrl || scan.url);
  };

  const historyCount = history.data?.length ?? 0;
  const historyTabLabel = historyCount > 0 ? `History (${historyCount})` : "History";
  const historyAriaLabel =
    hasUnreadHistory && activeTab !== "history"
      ? `${historyTabLabel}, new download`
      : historyTabLabel;

  const errors = [
    scan.error,
    download.jobError,
    historyError,
    historyFetchError ? `Failed to load history: ${historyFetchError}` : null,
  ].filter(Boolean);

  const handleTabKey = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowLeft" || e.key === "ArrowRight") {
      e.preventDefault();
      setActiveTab((t) => (t === "download" ? "history" : "download"));
    }
  };

  return (
    <div className="mx-auto max-w-4xl px-6 pb-16 pt-8">
      <div ref={pageTopRef} className="h-px w-full shrink-0" aria-hidden />
      <header className="mb-6 flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h1 className="m-0 text-[1.75rem] font-bold tracking-tight text-foreground">
            Video Downloader
          </h1>
          <p className="mt-1 mb-0 text-[0.95rem] text-muted">
            Scan a page, pick a stream, download safely.
          </p>
        </div>
        <ThemeSwitcher />
      </header>

      <nav
        className="mb-5 flex gap-1.5 rounded-lg border border-border bg-surface p-1"
        role="tablist"
        onKeyDown={handleTabKey}
      >
        <button
          type="button"
          role="tab"
          id="tab-download"
          aria-selected={activeTab === "download"}
          aria-controls="panel-download"
          className={`${TAB_BASE} ${activeTab === "download" ? TAB_ACTIVE : TAB_INACTIVE}`}
          onClick={() => setActiveTab("download")}
        >
          Download
        </button>
        <button
          type="button"
          role="tab"
          id="tab-history"
          aria-selected={activeTab === "history"}
          aria-controls="panel-history"
          aria-label={historyAriaLabel}
          className={`${TAB_BASE} ${activeTab === "history" ? TAB_ACTIVE : TAB_INACTIVE} ${
            hasUnreadHistory && activeTab !== "history" ? "ring-2 ring-accent/30" : ""
          }`}
          onClick={() => setActiveTab("history")}
        >
          <span className="inline-flex items-center justify-center gap-1.5">
            {historyTabLabel}
            {hasUnreadHistory && activeTab !== "history" && (
              <span className="size-2 shrink-0 rounded-full bg-accent" aria-hidden />
            )}
          </span>
        </button>
      </nav>

      {health.data && !health.data.ffmpeg_available && (
        <div className="mb-4 rounded-md border border-warn-border bg-warn/10 px-4 py-3 text-sm text-warn">
          ffmpeg not found on PATH. HLS downloads will fail until ffmpeg is installed.
        </div>
      )}

      {health.data &&
        health.data.ytdlp_impersonate_enabled &&
        !health.data.ytdlp_impersonate_available && (
          <div className="mb-4 rounded-md border border-warn-border bg-warn/10 px-4 py-3 text-sm text-warn">
            yt-dlp browser impersonation is enabled but curl_cffi is missing. Cloudflare-protected
            sites may fail with HTTP 403. Run{" "}
            <code className="rounded bg-background px-1">uv sync</code> from the project root.
          </div>
        )}

      {errors.length > 0 && (
        <div className="mb-4 flex flex-col gap-2">
          {errors.map((msg, i) => (
            <div
              key={i}
              className="rounded-md border border-danger bg-danger/10 px-4 py-3 text-sm text-danger"
            >
              {msg}
            </div>
          ))}
        </div>
      )}

      {activeTab === "download" && (
        <DownloadPanel
          scan={scan}
          download={download}
          onDownload={handleDownload}
          pageTopRef={pageTopRef}
          scanSectionRef={scanSectionRef}
          downloadSectionRef={downloadSectionRef}
        />
      )}

      {activeTab === "history" && (
        <HistoryPanel
          entries={history.data ?? []}
          loading={history.isLoading}
          error={historyFetchError}
          onError={setHistoryError}
          onToast={pushToast}
        />
      )}

      <ToastStack
        toasts={toasts}
        onDismiss={dismissToast}
        onRevealInFolder={async (id) => {
          try {
            await revealInFolder(id);
          } catch (e) {
            pushToast({
              variant: "error",
              title: "Could not open folder",
              description: (e as Error).message,
            });
          }
        }}
      />
    </div>
  );
}
