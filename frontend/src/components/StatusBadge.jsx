import { CheckCircle2, AlertTriangle, XCircle, Clock, Loader2 } from 'lucide-react';

const VARIANTS = {
  success: {
    classes: 'bg-emerald-900/20 border-emerald-500/30 text-emerald-400',
    Icon: CheckCircle2,
  },
  warning: {
    classes: 'bg-amber-900/20 border-amber-500/30 text-amber-400',
    Icon: AlertTriangle,
  },
  error: {
    classes: 'bg-red-900/20 border-red-500/30 text-red-400',
    Icon: XCircle,
  },
  pending: {
    classes: 'bg-blue-900/20 border-blue-500/30 text-blue-400',
    Icon: Loader2,
  },
  default: {
    classes: 'bg-panel/60 border-border text-gray-400',
    Icon: Clock,
  },
};

export default function StatusBadge({ status = 'default', label }) {
  const variant = VARIANTS[status] || VARIANTS.default;
  const Icon = variant.Icon;

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg border text-[11px] font-semibold ${variant.classes}`}>
      <Icon size={11} className={status === 'pending' ? 'animate-spin' : ''} />
      {label}
    </span>
  );
}