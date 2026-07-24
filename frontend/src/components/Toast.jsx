import { useState, useCallback, useRef } from 'react';
import { CheckCircle2, XCircle, AlertTriangle, Info, X } from 'lucide-react';

const ICONS = {
  success: <CheckCircle2 size={15} className="text-emerald-500 flex-shrink-0" />,
  error:   <XCircle size={15} className="text-red-500 flex-shrink-0" />,
  warning: <AlertTriangle size={15} className="text-amber-500 flex-shrink-0" />,
  info:    <Info size={15} className="text-brand flex-shrink-0" />,
};

const BORDER = {
  success: 'border-emerald-200 bg-emerald-50',
  error:   'border-red-200 bg-red-50',
  warning: 'border-amber-200 bg-amber-50',
  info:    'border-brand/20 bg-brand-50',
};

function Toast({ id, type = 'info', message, onDismiss }) {
  return (
    <div
      role="alert"
      aria-live="assertive"
      className={`flex items-start gap-3 px-4 py-3 rounded-xl border shadow-card text-sm font-medium animate-slide-up max-w-sm ${BORDER[type]}`}
    >
      {ICONS[type]}
      <span className="flex-1 text-text-primary leading-snug">{message}</span>
      <button
        onClick={() => onDismiss(id)}
        aria-label="Dismiss notification"
        className="text-text-muted hover:text-text-primary transition-colors flex-shrink-0"
      >
        <X size={13} />
      </button>
    </div>
  );
}

export function ToastContainer({ toasts, onDismiss }) {
  return (
    <div
      aria-label="Notifications"
      className="fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none"
    >
      {toasts.map((t) => (
        <div key={t.id} className="pointer-events-auto">
          <Toast {...t} onDismiss={onDismiss} />
        </div>
      ))}
    </div>
  );
}

export function useToast() {
  const [toasts, setToasts] = useState([]);
  const timers = useRef({});

  const dismiss = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
    clearTimeout(timers.current[id]);
    delete timers.current[id];
  }, []);

  const toast = useCallback(({ type = 'info', message, duration = 4000 }) => {
    const id = Math.random().toString(36).slice(2);
    setToasts((prev) => [...prev.slice(-4), { id, type, message }]); // max 5
    if (duration > 0) {
      timers.current[id] = setTimeout(() => dismiss(id), duration);
    }
    return id;
  }, [dismiss]);

  return { toasts, toast, dismiss };
}
