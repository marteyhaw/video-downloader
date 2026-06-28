import { AlertTriangle, Check, FolderOpen, Loader2, Pencil, Trash2, X } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { HistoryEntry } from "../api/client";
import { basenameFromPath, formatSize } from "../utils/format";
import type { PushToastInput } from "../hooks/useToasts";
import { ConfirmDialog } from "./ConfirmDialog";
import { IconButton } from "./IconButton";
import { Tooltip } from "./Tooltip";
import { btnDangerClass, inputClass } from "./ui";

interface Props {
  entries: HistoryEntry[];
  loading: boolean;
  error?: string | null;
  onRename: (id: number, name: string) => Promise<void>;
  onReveal: (id: number) => Promise<void>;
  onDelete: (id: number, deleteFile: boolean) => Promise<void>;
  /** Called once after a delete (single or batch) lands, to refresh history. */
  onChanged: () => void;
  onToast: (input: PushToastInput) => void;
}

const ICON_SIZE = 16;

function formatDate(iso: string) {
  return new Date(iso).toLocaleString();
}

function preventFocusSteal(e: React.MouseEvent) {
  e.preventDefault();
}

function ActionSpinner() {
  return <Loader2 size={ICON_SIZE} className="animate-spin" aria-hidden />;
}

export function HistoryTable({
  entries,
  loading,
  error,
  onRename,
  onReveal,
  onDelete,
  onChanged,
  onToast,
}: Props) {
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editValue, setEditValue] = useState("");
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [revealingId, setRevealingId] = useState<number | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<HistoryEntry | null>(null);
  const [deleteFileToo, setDeleteFileToo] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [bulkConfirm, setBulkConfirm] = useState(false);
  const [bulkDeleting, setBulkDeleting] = useState(false);
  const [bulkDeleteFileToo, setBulkDeleteFileToo] = useState(false);
  const selectAllRef = useRef<HTMLInputElement>(null);

  // Drop ids that no longer exist (e.g. after a delete refreshed the list).
  useEffect(() => {
    setSelectedIds((prev) => {
      const valid = new Set<number>();
      for (const entry of entries) {
        if (prev.has(entry.id)) valid.add(entry.id);
      }
      return valid.size === prev.size ? prev : valid;
    });
  }, [entries]);

  const selectedCount = selectedIds.size;
  const allSelected = entries.length > 0 && selectedCount === entries.length;

  useEffect(() => {
    if (selectAllRef.current) {
      selectAllRef.current.indeterminate = selectedCount > 0 && !allSelected;
    }
  }, [selectedCount, allSelected]);

  const selectedEntries = useMemo(
    () => entries.filter((entry) => selectedIds.has(entry.id)),
    [entries, selectedIds],
  );

  const toggleSelect = (id: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleSelectAll = () => {
    setSelectedIds((prev) =>
      prev.size === entries.length ? new Set() : new Set(entries.map((e) => e.id)),
    );
  };

  const confirmBulkDelete = async () => {
    if (selectedEntries.length === 0) return;
    setBulkDeleting(true);
    // Fan out the existing per-record DELETE endpoint rather than adding a
    // dedicated bulk-delete API. History is a small, capped, local list, so
    // a handful of sequential requests is cheap and keeps the surface area
    // minimal — no new endpoint, schema, or backend tests to maintain.
    // Sequential (not Promise.all) avoids hammering the single local backend
    // and gives deterministic ordering; revisit with a real batch endpoint
    // only if history ever grows large enough for this to feel slow.
    // Each delete is isolated so one failure doesn't strand the rest: failed
    // ids stay selected for retry. Results are aggregated into a single
    // success/error toast pair rather than one toast per request.
    const total = selectedEntries.length;
    const failed = new Set<number>();
    let firstError = "";
    try {
      for (const entry of selectedEntries) {
        try {
          await onDelete(entry.id, bulkDeleteFileToo);
        } catch (e) {
          failed.add(entry.id);
          if (!firstError) firstError = (e as Error).message;
        }
      }
    } finally {
      const deleted = total - failed.size;
      if (deleted > 0) {
        onChanged();
        onToast({
          variant: "success",
          title: `Deleted ${deleted} ${deleted === 1 ? "record" : "records"}`,
        });
      }
      if (failed.size > 0) {
        onToast({
          variant: "error",
          title: `Failed to delete ${failed.size} ${failed.size === 1 ? "record" : "records"}`,
          description: firstError || undefined,
        });
      }
      setBulkDeleting(false);
      setBulkConfirm(false);
      setBulkDeleteFileToo(false);
      setSelectedIds(failed);
    }
  };

  const startEdit = (entry: HistoryEntry) => {
    setEditingId(entry.id);
    setEditValue(entry.display_name);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditValue("");
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    const target = deleteTarget;
    setDeletingId(target.id);
    try {
      await onDelete(target.id, deleteFileToo);
      onChanged();
      onToast({
        variant: "success",
        title: "Removed from history",
        description: target.display_name,
      });
      setDeleteTarget(null);
      setDeleteFileToo(false);
    } catch (e) {
      onToast({ variant: "error", title: "Delete failed", description: (e as Error).message });
    } finally {
      setDeletingId(null);
    }
  };

  const handleReveal = async (id: number) => {
    setRevealingId(id);
    try {
      await onReveal(id);
    } finally {
      setRevealingId(null);
    }
  };

  const saveEdit = async (entry: HistoryEntry) => {
    const trimmed = editValue.trim();
    if (!trimmed || trimmed === entry.display_name) {
      cancelEdit();
      return;
    }
    setSaving(true);
    try {
      await onRename(entry.id, trimmed);
      cancelEdit();
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <p className="py-6 text-center text-sm text-muted">Loading history…</p>;
  }
  if (error) {
    return <p className="py-6 text-center text-sm text-danger">Could not load history. {error}</p>;
  }
  if (!entries.length) {
    return <p className="py-6 text-center text-sm text-muted">No downloads yet.</p>;
  }

  return (
    <>
      <div className="mb-3 flex min-h-8 items-center gap-3" aria-live="polite">
        {selectedCount > 0 && (
          <div className="filter-chip-enter flex items-center gap-3">
            <span className="text-sm text-muted">{selectedCount} selected</span>
            <button
              type="button"
              className={btnDangerClass}
              disabled={bulkDeleting}
              onClick={() => {
                setBulkDeleteFileToo(false);
                setBulkConfirm(true);
              }}
            >
              <Trash2 size={14} className="mr-1 inline" aria-hidden />
              Delete selected
            </button>
            <button
              type="button"
              className="text-sm text-muted hover:text-foreground"
              disabled={bulkDeleting}
              onClick={() => setSelectedIds(new Set())}
            >
              Clear
            </button>
          </div>
        )}
      </div>
      <table className="w-full border-collapse text-sm" aria-label="Download history">
        <thead>
          <tr>
            <th scope="col" className="w-8 border-b border-border px-2 pb-3 text-left">
              <input
                ref={selectAllRef}
                type="checkbox"
                className="size-4 rounded border-border accent-accent disabled:cursor-not-allowed disabled:opacity-50"
                checked={allSelected}
                disabled={bulkDeleting}
                onChange={toggleSelectAll}
                aria-label="Select all"
              />
            </th>
            <th
              scope="col"
              className="border-b border-border px-2 pb-3 text-left text-xs font-medium uppercase tracking-wide text-muted"
            >
              Name
            </th>
            <th
              scope="col"
              className="border-b border-border px-2 pb-3 text-left text-xs font-medium uppercase tracking-wide text-muted"
            >
              Date
            </th>
            <th
              scope="col"
              className="border-b border-border px-2 pb-3 text-left text-xs font-medium uppercase tracking-wide text-muted"
            >
              Size
            </th>
            <th
              scope="col"
              className="min-w-[7.5rem] whitespace-nowrap border-b border-border px-2 pb-3 text-left text-xs font-medium uppercase tracking-wide text-muted"
            >
              Actions
            </th>
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) => (
            <tr key={entry.id} className="border-b border-border last:border-b-0">
              <td className="px-2 py-2.5 align-middle">
                <input
                  type="checkbox"
                  className="size-4 rounded border-border accent-accent disabled:cursor-not-allowed disabled:opacity-50"
                  checked={selectedIds.has(entry.id)}
                  disabled={bulkDeleting}
                  onChange={() => toggleSelect(entry.id)}
                  aria-label={`Select ${entry.display_name}`}
                />
              </td>
              <td className="px-2 py-2.5 align-middle">
                {editingId === entry.id ? (
                  <div className="flex flex-col gap-2">
                    <input
                      type="text"
                      className={inputClass}
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") void saveEdit(entry);
                        if (e.key === "Escape") cancelEdit();
                      }}
                      disabled={saving}
                      autoFocus
                      aria-label="Edit display name"
                    />
                    <div className="flex gap-1">
                      <Tooltip text="Save" variant="floating">
                        <IconButton
                          label="Save"
                          variant="primary"
                          disabled={saving}
                          onClick={() => void saveEdit(entry)}
                        >
                          {saving ? <ActionSpinner /> : <Check size={ICON_SIZE} />}
                        </IconButton>
                      </Tooltip>
                      <Tooltip text="Cancel" variant="floating">
                        <IconButton
                          label="Cancel"
                          variant="secondary"
                          disabled={saving}
                          onClick={cancelEdit}
                        >
                          <X size={ICON_SIZE} />
                        </IconButton>
                      </Tooltip>
                    </div>
                  </div>
                ) : (
                  <div className="max-w-[420px]">
                    <Tooltip text={entry.display_name} className="block max-w-full">
                      <span
                        className={`tooltip-text block cursor-default ${
                          entry.file_status === "missing" ? "line-through text-muted" : ""
                        }`}
                        onDoubleClick={() => startEdit(entry)}
                      >
                        {entry.display_name}
                      </span>
                    </Tooltip>
                    {entry.file_status === "missing" && (
                      <span className="mt-1 inline-block rounded px-1.5 py-0.5 text-[0.65rem] font-semibold uppercase tracking-wide bg-danger/15 text-danger">
                        Missing
                      </span>
                    )}
                    {entry.file_status === "moved" && entry.resolved_path && (
                      <p className="m-0 mt-1 flex items-center gap-1 text-xs text-muted">
                        <AlertTriangle size={12} className="shrink-0 text-warn" aria-hidden />
                        On disk: {basenameFromPath(entry.resolved_path)}
                      </p>
                    )}
                  </div>
                )}
              </td>
              <td className="px-2 py-2.5 align-middle">{formatDate(entry.created_at)}</td>
              <td className="px-2 py-2.5 align-middle">{formatSize(entry.file_size)}</td>
              <td className="px-2 py-2.5 align-middle">
                {editingId === entry.id ? null : (
                  <div className="flex flex-nowrap items-center gap-1">
                    <Tooltip text="Rename" variant="floating">
                      <IconButton
                        label="Rename"
                        variant="secondary"
                        disabled={bulkDeleting}
                        onMouseDown={preventFocusSteal}
                        onClick={() => startEdit(entry)}
                      >
                        <Pencil size={ICON_SIZE} />
                      </IconButton>
                    </Tooltip>
                    <Tooltip
                      text={
                        entry.file_status === "missing"
                          ? "File not found on disk"
                          : "Show in folder"
                      }
                      variant="floating"
                    >
                      <IconButton
                        label="Show in folder"
                        variant="secondary"
                        disabled={
                          revealingId === entry.id ||
                          entry.file_status === "missing" ||
                          bulkDeleting
                        }
                        onMouseDown={preventFocusSteal}
                        onClick={() => void handleReveal(entry.id)}
                      >
                        {revealingId === entry.id ? (
                          <ActionSpinner />
                        ) : (
                          <FolderOpen size={ICON_SIZE} />
                        )}
                      </IconButton>
                    </Tooltip>
                    <Tooltip text="Delete record" variant="floating">
                      <IconButton
                        label="Delete record"
                        variant="danger"
                        disabled={deletingId === entry.id || bulkDeleting}
                        onMouseDown={preventFocusSteal}
                        onClick={() => {
                          setDeleteFileToo(false);
                          setDeleteTarget(entry);
                        }}
                      >
                        {deletingId === entry.id ? <ActionSpinner /> : <Trash2 size={ICON_SIZE} />}
                      </IconButton>
                    </Tooltip>
                  </div>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <ConfirmDialog
        open={deleteTarget !== null}
        title="Delete record"
        message={
          deleteTarget
            ? `Remove "${deleteTarget.display_name}" from download history?${
                deleteTarget.file_status === "missing"
                  ? " The file is no longer on disk; only the history record will be removed."
                  : ""
              }`
            : ""
        }
        checkbox={
          deleteTarget?.file_status !== "missing"
            ? {
                label: "Also delete the file from downloads",
                checked: deleteFileToo,
                onChange: setDeleteFileToo,
              }
            : undefined
        }
        confirmLabel="Delete"
        cancelLabel="Cancel"
        variant="danger"
        loading={deleteTarget !== null && deletingId === deleteTarget.id}
        onConfirm={() => void confirmDelete()}
        onCancel={() => {
          setDeleteTarget(null);
          setDeleteFileToo(false);
        }}
      />

      <ConfirmDialog
        open={bulkConfirm}
        title="Delete selected records"
        message={`Remove ${selectedCount} ${
          selectedCount === 1 ? "record" : "records"
        } from download history?`}
        checkbox={
          selectedEntries.some((entry) => entry.file_status !== "missing")
            ? {
                label: "Also delete the files from downloads",
                checked: bulkDeleteFileToo,
                onChange: setBulkDeleteFileToo,
              }
            : undefined
        }
        confirmLabel="Delete"
        cancelLabel="Cancel"
        variant="danger"
        loading={bulkDeleting}
        onConfirm={() => void confirmBulkDelete()}
        onCancel={() => {
          setBulkConfirm(false);
          setBulkDeleteFileToo(false);
        }}
      />
    </>
  );
}
