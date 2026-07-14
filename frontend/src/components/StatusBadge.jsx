import { clsx } from 'clsx';
import { CheckCircle2, XCircle, AlertCircle, Loader2 } from 'lucide-react';

export default function StatusBadge({ status, label }) {
  const styles = {
    success: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    error: 'bg-red-500/10 text-red-400 border-red-500/20',
    warning: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    info: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  };

  const icons = {
    success: <CheckCircle2 size={14} />,
    error: <XCircle size={14} />,
    warning: <AlertCircle size={14} />,
    info: <Loader2 size={14} className="animate-spin" />,
  };

  return (
    <div className={clsx('flex items-center gap-1.5 px-3 py-1 rounded-full border text-xs font-medium', styles[status])}>
      {icons[status]}
      {label}
    </div>
  );
}