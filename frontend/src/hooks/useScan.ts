import { useCallback, useEffect, useRef, useState } from "react";
import { scanUrlStream, type MediaItem, type ScanProgressEvent } from "../api/client";
import { emptyFilters, type MediaFilterState } from "../utils/mediaFilters";

const MAX_PROGRESS_EVENTS = 100;

export interface ScanState {
  url: string;
  setUrl: (url: string) => void;
  pageUrl: string;
  items: MediaItem[];
  pageTitle: string;
  warning: string | null;
  pending: boolean;
  stopped: boolean;
  error: string | null;
  progress: ScanProgressEvent[];
  selected: MediaItem | null;
  setSelected: (item: MediaItem | null) => void;
  mediaFilters: MediaFilterState;
  setMediaFilters: (filters: MediaFilterState) => void;
  handleScan: () => void;
  handleStop: () => void;
}

export function useScan(): ScanState {
  const [url, setUrl] = useState("");
  const [pageUrl, setPageUrl] = useState("");
  const [items, setItems] = useState<MediaItem[]>([]);
  const [pageTitle, setPageTitle] = useState("");
  const [scanWarning, setScanWarning] = useState<string | null>(null);
  const [scanPending, setScanPending] = useState(false);
  const [scanStopped, setScanStopped] = useState(false);
  const [scanError, setScanError] = useState<string | null>(null);
  const [scanProgress, setScanProgress] = useState<ScanProgressEvent[]>([]);
  const scanAbortRef = useRef<AbortController | null>(null);
  const [selected, setSelected] = useState<MediaItem | null>(null);
  const [mediaFilters, setMediaFilters] = useState<MediaFilterState>(emptyFilters);

  const handleScan = useCallback(() => {
    if (!url.trim() || scanPending) return;

    scanAbortRef.current?.abort();
    const controller = new AbortController();
    scanAbortRef.current = controller;

    const target = url.trim();
    setPageUrl(target);
    setItems([]);
    setSelected(null);
    setScanWarning(null);
    setScanError(null);
    setScanProgress([]);
    setPageTitle("");
    setScanStopped(false);
    setScanPending(true);
    setMediaFilters(emptyFilters());

    void scanUrlStream(
      target,
      (event) => {
        setScanProgress((prev) =>
          prev.length >= MAX_PROGRESS_EVENTS
            ? [...prev.slice(-MAX_PROGRESS_EVENTS + 1), event]
            : [...prev, event],
        );
      },
      controller.signal,
    )
      .then((data) => {
        setItems(data.items);
        setPageTitle(data.page_title);
        setScanWarning(data.warning ?? null);
        setSelected(data.items[0] ?? null);
      })
      .catch((err) => {
        if ((err as Error).name === "AbortError") return;
        setScanError((err as Error).message);
      })
      .finally(() => {
        setScanPending(false);
        scanAbortRef.current = null;
      });
  }, [url, scanPending]);

  const handleStop = useCallback(() => {
    // Aborts the in-flight scan: client.ts closes the EventSource and rejects
    // with AbortError, which useScan's .catch swallows and .finally clears
    // scanPending. The backend SSE generator sees the disconnect and cancels
    // its task (the underlying scan thread still runs to completion).
    if (!scanAbortRef.current) return;
    scanAbortRef.current.abort();
    setScanStopped(true);
  }, []);

  useEffect(() => {
    return () => {
      scanAbortRef.current?.abort();
    };
  }, []);

  return {
    url,
    setUrl,
    pageUrl,
    items,
    pageTitle,
    warning: scanWarning,
    pending: scanPending,
    stopped: scanStopped,
    error: scanError,
    progress: scanProgress,
    selected,
    setSelected,
    mediaFilters,
    setMediaFilters,
    handleScan,
    handleStop,
  };
}
