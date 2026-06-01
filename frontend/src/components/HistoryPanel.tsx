import { useQueryClient } from "@tanstack/react-query";
import type { HistoryEntry } from "../api/client";
import { deleteHistory, renameHistory, revealInFolder } from "../api/client";
import { HistoryTable } from "./HistoryTable";
import { sectionClass, sectionTitleClass } from "./ui";

interface HistoryPanelProps {
  entries: HistoryEntry[];
  loading: boolean;
  error: string | null;
  onError: (message: string | null) => void;
}

export function HistoryPanel({ entries, loading, error, onError }: HistoryPanelProps) {
  const queryClient = useQueryClient();
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
            try {
              onError(null);
              await deleteHistory(id, deleteFile);
              queryClient.invalidateQueries({ queryKey: ["history"] });
            } catch (e) {
              onError((e as Error).message);
              throw e;
            }
          }}
        />
      </section>
    </div>
  );
}
