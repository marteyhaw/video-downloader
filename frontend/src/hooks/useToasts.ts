import { useCallback, useEffect, useRef, useState } from "react";

export type ToastVariant = "success" | "error";

const MAX_TOASTS = 5;
const AUTO_DISMISS_MS = 4000;

export interface Toast {
  id: string;
  variant: ToastVariant;
  title: string;
  description?: string;
  /** History row to reveal when user clicks "Show in folder" on success toasts. */
  historyId?: number;
}

export interface PushToastInput {
  variant: ToastVariant;
  title: string;
  description?: string;
  historyId?: number;
}

export function useToasts() {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const timersRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
    const timer = timersRef.current.get(id);
    if (timer) {
      clearTimeout(timer);
      timersRef.current.delete(id);
    }
  }, []);

  const pushToast = useCallback(
    (input: PushToastInput) => {
      const id = crypto.randomUUID();
      setToasts((prev) => {
        const next = [...prev, { id, ...input }];
        return next.length > MAX_TOASTS ? next.slice(-MAX_TOASTS) : next;
      });
      const timer = setTimeout(() => dismissToast(id), AUTO_DISMISS_MS);
      timersRef.current.set(id, timer);
    },
    [dismissToast],
  );

  useEffect(() => {
    const timers = timersRef.current;
    return () => {
      for (const timer of timers.values()) clearTimeout(timer);
      timers.clear();
    };
  }, []);

  return { toasts, pushToast, dismissToast };
}
