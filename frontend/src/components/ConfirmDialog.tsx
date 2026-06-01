import { Loader2 } from "lucide-react";
import { useEffect, useId, useRef } from "react";
import { btnDangerClass, btnSecondaryClass } from "./ui";

export interface ConfirmDialogCheckbox {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}

interface Props {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: "danger" | "default";
  loading?: boolean;
  checkbox?: ConfirmDialogCheckbox;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  variant = "default",
  loading = false,
  checkbox,
  onConfirm,
  onCancel,
}: Props) {
  const titleId = useId();
  const messageId = useId();
  const checkboxId = useId();
  const cancelRef = useRef<HTMLButtonElement>(null);

  const dialogPanelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;

    cancelRef.current?.focus();

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onCancel();
        return;
      }
      if (e.key === "Tab") {
        const panel = dialogPanelRef.current;
        if (!panel) return;
        const focusable = panel.querySelectorAll<HTMLElement>(
          'a[href], button:not([disabled]), input:not([disabled]), textarea:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])',
        );
        if (focusable.length === 0) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [open, onCancel]);

  if (!open) return null;

  const confirmClass = variant === "danger" ? btnDangerClass : btnSecondaryClass;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
      onClick={onCancel}
      role="presentation"
    >
      <div
        ref={dialogPanelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={checkbox ? `${messageId} ${checkboxId}` : messageId}
        className="w-full max-w-md rounded-lg border border-border bg-surface p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id={titleId} className="text-lg font-semibold text-foreground">
          {title}
        </h2>
        <p id={messageId} className="mt-2 text-sm text-muted">
          {message}
        </p>
        {checkbox && (
          <label
            htmlFor={checkboxId}
            className="mt-4 flex cursor-pointer items-start gap-2.5 text-sm text-foreground"
          >
            <input
              id={checkboxId}
              type="checkbox"
              checked={checkbox.checked}
              disabled={loading}
              onChange={(e) => checkbox.onChange(e.target.checked)}
              className="mt-0.5 size-4 shrink-0 rounded border-border accent-accent"
            />
            <span>{checkbox.label}</span>
          </label>
        )}
        <div className="mt-6 flex justify-end gap-2">
          <button
            ref={cancelRef}
            type="button"
            className={btnSecondaryClass}
            disabled={loading}
            onClick={onCancel}
          >
            {cancelLabel}
          </button>
          <button type="button" className={confirmClass} disabled={loading} onClick={onConfirm}>
            {loading && <Loader2 size={16} className="inline animate-spin" aria-hidden />}
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
