import type { HistoryEntry } from "../api/client";

export const LAST_SEEN_HISTORY_ID_KEY = "vd-last-seen-history-id";

export function maxHistoryId(entries: HistoryEntry[]): number {
  if (entries.length === 0) return 0;
  return Math.max(...entries.map((e) => e.id));
}

export function readLastSeenHistoryId(): number | null {
  try {
    const raw = localStorage.getItem(LAST_SEEN_HISTORY_ID_KEY);
    if (raw === null) return null;
    const n = Number.parseInt(raw, 10);
    return Number.isFinite(n) ? n : null;
  } catch {
    return null;
  }
}

export function writeLastSeenHistoryId(id: number): void {
  try {
    localStorage.setItem(LAST_SEEN_HISTORY_ID_KEY, String(id));
  } catch {
    /* ignore quota / private mode */
  }
}

export function hasUnreadHistory(entries: HistoryEntry[], lastSeenMaxId: number): boolean {
  return maxHistoryId(entries) > lastSeenMaxId;
}
