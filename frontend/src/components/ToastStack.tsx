import { useState } from "react";
import { AlertCircle, Check, FolderOpen, Loader2, X } from "lucide-react";
import type { Toast } from "../hooks/useToasts";

interface Props {
  toasts: Toast[];
  onDismiss: (id: string) => void;
  onRevealInFolder?: (historyId: number) => Promise<void>;
}

const variantStyles = {
  success: {
    container: "border-success/40 bg-success/10 text-foreground",
    icon: "text-success",
    Icon: Check,
  },
  error: {
    container: "border-danger/40 bg-danger/10 text-foreground",
    icon: "text-danger",
    Icon: AlertCircle,
  },
} as const;

export function ToastStack({ toasts, onDismiss, onRevealInFolder }: Props) {
  const [revealingToastId, setRevealingToastId] = useState<string | null>(null);

  if (toasts.length === 0) return null;

  const handleReveal = async (toast: Toast) => {
    if (toast.historyId == null || !onRevealInFolder) return;
    setRevealingToastId(toast.id);
    try {
      await onRevealInFolder(toast.historyId);
    } finally {
      setRevealingToastId(null);
    }
  };

  return (
    <div
      className="pointer-events-none fixed bottom-4 right-4 z-50 flex max-h-[min(50vh,20rem)] w-[min(100vw-2rem,22rem)] flex-col gap-2 overflow-y-auto"
      role="status"
      aria-live="polite"
      aria-atomic="false"
    >
      {toasts.map((toast) => {
        const { container, icon, Icon } = variantStyles[toast.variant];
        return (
          <div
            key={toast.id}
            className={`toast-enter pointer-events-auto flex gap-3 rounded-lg border p-3.5 shadow-lg ${container}`}
          >
            <Icon size={18} className={`mt-0.5 shrink-0 ${icon}`} aria-hidden />
            <div className="min-w-0 flex-1">
              <p className="m-0 text-sm font-semibold">{toast.title}</p>
              {toast.description && (
                <p className="m-0 mt-0.5 truncate text-xs text-muted">{toast.description}</p>
              )}
              {toast.variant === "success" && toast.historyId != null && onRevealInFolder && (
                <button
                  type="button"
                  className="mt-2 inline-flex items-center gap-1.5 text-xs font-semibold text-accent hover:text-accent-hover disabled:opacity-60"
                  disabled={revealingToastId === toast.id}
                  onClick={() => void handleReveal(toast)}
                >
                  {revealingToastId === toast.id ? (
                    <Loader2 size={14} className="animate-spin" aria-hidden />
                  ) : (
                    <FolderOpen size={14} aria-hidden />
                  )}
                  Show in folder
                </button>
              )}
            </div>
            <button
              type="button"
              className="shrink-0 rounded p-0.5 text-muted opacity-70 hover:bg-surface-hover hover:text-foreground hover:opacity-100"
              aria-label="Dismiss notification"
              onClick={() => onDismiss(toast.id)}
            >
              <X size={16} aria-hidden />
            </button>
          </div>
        );
      })}
    </div>
  );
}
