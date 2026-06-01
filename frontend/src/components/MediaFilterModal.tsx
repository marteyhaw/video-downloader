import { useEffect, useId, useRef } from "react";
import { MediaItem } from "../api/client";
import { useDialogTransition } from "../hooks/useDialogTransition";
import { MediaFilterState } from "../utils/mediaFilters";
import { MediaFilterBar } from "./MediaFilterBar";

interface Props {
  open: boolean;
  items: MediaItem[];
  filters: MediaFilterState;
  onChange: (filters: MediaFilterState) => void;
  onClose: () => void;
}

export function MediaFilterModal({ open, items, filters, onChange, onClose }: Props) {
  const titleId = useId();
  const dialogRef = useRef<HTMLDivElement>(null);
  const { mounted, shown } = useDialogTransition(open);

  useEffect(() => {
    if (!open) return;

    const t = window.setTimeout(() => {
      const first = dialogRef.current?.querySelector<HTMLElement>("button:not([disabled])");
      first?.focus();
    }, 50);

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
        return;
      }
      if (e.key === "Tab") {
        const panel = dialogRef.current;
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
    return () => {
      clearTimeout(t);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open, onClose]);

  if (!mounted) return null;

  return (
    <div
      className={`dialog-overlay fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 ${
        shown ? "opacity-100" : "opacity-0"
      }`}
      onClick={onClose}
      role="presentation"
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className={`dialog-panel flex max-h-[min(85vh,640px)] w-full max-w-lg flex-col rounded-lg border border-border bg-surface shadow-xl ${
          shown ? "scale-100 opacity-100" : "scale-95 opacity-0"
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="shrink-0 border-b border-border px-6 py-4">
          <h2 id={titleId} className="text-lg font-semibold text-foreground">
            Filter found media
          </h2>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto px-6 py-4">
          <MediaFilterBar
            items={items}
            filters={filters}
            onChange={onChange}
            variant="modal"
            onDone={onClose}
          />
        </div>
      </div>
    </div>
  );
}
