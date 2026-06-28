import { useQueryClient } from "@tanstack/react-query";
import type { HistoryEntry } from "../api/client";
import { deleteHistory, renameHistory, revealInFolder } from "../api/client";
import type { PushToastInput } from "../hooks/useToasts";
import { HistoryTable } from "./HistoryTable";
import { sectionClass, sectionTitleClass } from "./ui";

interface HistoryPanelProps {
  entries: HistoryEntry[];
  loading: boolean;
  error: string | null;
  onError: (message: string | null) => void;
  onToast: (input: PushToastInput) => void;
}

export function HistoryPanel({ entries, loading, error, onError, onToast }: HistoryPanelProps) {
  const queryClient = useQueryClient();
  // One refetch after a delete batch completes (not once per row), so the App's
  // history-count + unread read-state re-sync via its history-query effects.
  const refreshHistory = () => {
    queryClient.invalidateQueries({ queryKey: ["history"] });
  };
  return (
    <div role="tabpanel" id="panel-history" aria-labelledby="tab-history">
      <section className={sectionClass}>
        <h2 className={sectionTitleClass}>Download history</h2>
        <HistoryTable
          entries={entries}
          loading={loading}
          error={error}
          onRename={async (id, name) => {
            try {
              onError(null);
              await renameHistory(id, name);
              queryClient.invalidateQueries({ queryKey: ["history"] });
            } catch (e) {
              onError((e as Error).message);
              throw e;
            }
          }}
          onReveal={async (id) => {
            try {
              onError(null);
              await revealInFolder(id);
            } catch (e) {
              onError((e as Error).message);
              throw e;
            }
          }}
          onDelete={async (id, deleteFile) => {
            // Network only — no cache invalidation here (HistoryTable batches
            // that into a single onChanged after the whole delete completes) and
            // no banner: results surface via toast so bulk deletes can aggregate.
            // Clear any stale rename/reveal banner; rethrow so the caller can
            // track per-item failures.
            onError(null);
            await deleteHistory(id, deleteFile);
          }}
          onChanged={refreshHistory}
          onToast={onToast}
        />
      </section>
    </div>
  );
}
