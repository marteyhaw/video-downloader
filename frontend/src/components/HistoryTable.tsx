import { AlertTriangle, Check, FolderOpen, Loader2, Pencil, Trash2, X } from "lucide-react";
import { useState } from "react";
import { HistoryEntry } from "../api/client";
import { basenameFromPath, formatSize } from "../utils/format";
import { ConfirmDialog } from "./ConfirmDialog";
import { IconButton } from "./IconButton";
import { Tooltip } from "./Tooltip";
import { inputClass } from "./ui";

interface Props {
  entries: HistoryEntry[];
  loading: boolean;
  error?: string | null;
  onRename: (id: number, name: string) => Promise<void>;
  onReveal: (id: number) => Promise<void>;
  onDelete: (id: number, deleteFile: boolean) => Promise<void>;
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

export function HistoryTable({ entries, loading, error, onRename, onReveal, onDelete }: Props) {
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editValue, setEditValue] = useState("");
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [revealingId, setRevealingId] = useState<number | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<HistoryEntry | null>(null);
  const [deleteFileToo, setDeleteFileToo] = useState(false);

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
    setDeletingId(deleteTarget.id);
    try {
      await onDelete(deleteTarget.id, deleteFileToo);
      setDeleteTarget(null);
      setDeleteFileToo(false);
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
      <table className="w-full border-collapse text-sm" aria-label="Download history">
        <thead>
          <tr>
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
                        disabled={revealingId === entry.id || entry.file_status === "missing"}
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
                        disabled={deletingId === entry.id}
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
    </>
  );
}
