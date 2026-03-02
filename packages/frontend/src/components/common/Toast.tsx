import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { AlertTriangle, CheckCircle2, ShieldAlert, X, XCircle } from "lucide-react";
import clsx from "clsx";

export type ToastVariant = "success" | "error" | "warning" | "critical";

export interface ToastInput {
  title?: string;
  message: string;
  variant: ToastVariant;
  durationMs?: number;
}

interface ToastRecord extends ToastInput {
  id: number;
}

interface ToastContextValue {
  pushToast: (toast: ToastInput) => void;
  dismissToast: (id: number) => void;
  clearToasts: () => void;
}

const DEFAULT_DURATION_MS = 5000;

const ToastContext = createContext<ToastContextValue | null>(null);

const TOAST_STYLE: Record<ToastVariant, string> = {
  success: "border-green-500/40 bg-green-500/20 text-green-300",
  error: "border-red-500/40 bg-red-500/20 text-red-300",
  warning: "border-yellow-500/40 bg-yellow-500/20 text-yellow-200",
  critical: "border-red-500 bg-red-500/30 text-red-200",
};

function ToastIcon({ variant }: { variant: ToastVariant }) {
  if (variant === "success") {
    return <CheckCircle2 className="h-4 w-4" aria-hidden="true" />;
  }

  if (variant === "error") {
    return <XCircle className="h-4 w-4" aria-hidden="true" />;
  }

  if (variant === "warning") {
    return <AlertTriangle className="h-4 w-4" aria-hidden="true" />;
  }

  return <ShieldAlert className="h-4 w-4" aria-hidden="true" />;
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastRecord[]>([]);
  const nextId = useRef(1);

  const dismissToast = useCallback((id: number) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const pushToast = useCallback(
    ({ durationMs = DEFAULT_DURATION_MS, ...toast }: ToastInput) => {
      const id = nextId.current++;
      setToasts((current) => [...current, { ...toast, id, durationMs }]);

      window.setTimeout(() => {
        dismissToast(id);
      }, durationMs);
    },
    [dismissToast],
  );

  const clearToasts = useCallback(() => {
    setToasts([]);
  }, []);

  const value = useMemo(
    () => ({ pushToast, dismissToast, clearToasts }),
    [pushToast, dismissToast, clearToasts],
  );

  return (
    <ToastContext.Provider value={value}>
      {children}

      <div className="pointer-events-none fixed right-4 top-4 z-[100] flex w-full max-w-sm flex-col gap-2 sm:right-6 sm:top-6">
        {toasts.map((toast) => (
          <div
            key={toast.id}
            role="status"
            className={clsx(
              "pointer-events-auto rounded-lg border p-3 shadow-lg backdrop-blur",
              TOAST_STYLE[toast.variant],
              toast.variant === "critical" && "animate-pulse",
            )}
          >
            <div className="flex items-start gap-2">
              <span className="mt-0.5">
                <ToastIcon variant={toast.variant} />
              </span>

              <div className="min-w-0 flex-1">
                {toast.title && <p className="text-sm font-semibold text-white">{toast.title}</p>}
                <p className="text-sm">{toast.message}</p>
              </div>

              <button
                type="button"
                onClick={() => dismissToast(toast.id)}
                className="rounded p-1 text-gray-200/80 transition hover:bg-white/10 hover:text-white"
                aria-label="Dismiss notification"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return context;
}
