import { useState } from 'react';
import { CheckCircle2, XCircle, RotateCcw, BookOpen, AlertTriangle, ChevronDown, ChevronUp, Copy, Check, Sparkles } from 'lucide-react';
import StatusBadge from './StatusBadge';

// Simple markdown-to-JSX renderer
function renderMarkdown(text) {
  if (!text) return null;
  const lines = text.split('\n');
  const elements = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (line.startsWith('### ')) {
      elements.push(<h3 key={i} className="text-sm font-bold text-gray-300 mt-4 mb-1">{line.slice(4)}</h3>);
    } else if (line.startsWith('## ')) {
      elements.push(<h2 key={i} className="text-base font-bold text-gray-200 mt-5 mb-2">{line.slice(3)}</h2>);
    } else if (line.startsWith('# ')) {
      elements.push(<h1 key={i} className="text-lg font-bold text-white mt-5 mb-2">{line.slice(2)}</h1>);
    } else if (line.startsWith('- ') || line.startsWith('* ')) {
      elements.push(
        <li key={i} className="text-gray-300 text-sm leading-relaxed ml-4 mb-1 list-disc">
          {inlineFormat(line.slice(2))}
        </li>
      );
    } else if (/^\d+\. /.test(line)) {
      elements.push(
        <li key={i} className="text-gray-300 text-sm leading-relaxed ml-4 mb-1 list-decimal">
          {inlineFormat(line.replace(/^\d+\. /, ''))}
        </li>
      );
    } else if (line.startsWith('```')) {
      const lang = line.slice(3);
      i++;
      const codeLines = [];
      while (i < lines.length && !lines[i].startsWith('```')) {
        codeLines.push(lines[i]);
        i++;
      }
      elements.push(
        <pre key={i} className="bg-[#0d1117] border border-border rounded-lg p-4 my-3 overflow-x-auto">
          <code className="text-teal-300 text-xs font-mono leading-relaxed">{codeLines.join('\n')}</code>
        </pre>
      );
    } else if (line.trim() === '') {
      elements.push(<div key={i} className="h-2" />);
    } else {
      elements.push(
        <p key={i} className="text-gray-300 text-sm leading-relaxed mb-2">
          {inlineFormat(line)}
        </p>
      );
    }
    i++;
  }
  return elements;
}

function inlineFormat(text) {
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i} className="text-white font-semibold">{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return <code key={i} className="bg-primary/10 border border-primary/20 rounded px-1.5 py-0.5 text-blue-300 text-xs font-mono">{part.slice(1, -1)}</code>;
    }
    if (part.startsWith('*') && part.endsWith('*')) {
      return <em key={i} className="text-gray-400 italic">{part.slice(1, -1)}</em>;
    }
    return part;
  });
}

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <button
      onClick={handleCopy}
      className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs text-gray-500 hover:text-white border border-border hover:border-gray-500 rounded-lg transition-all"
    >
      {copied ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
      {copied ? 'Copied!' : 'Copy'}
    </button>
  );
}

function MetricBadge({ icon: Icon, label, value, variant = 'default' }) {
  const variants = {
    success: 'bg-emerald-900/20 border-emerald-500/30 text-emerald-400',
    error: 'bg-red-900/20 border-red-500/30 text-red-400',
    warning: 'bg-amber-900/20 border-amber-500/30 text-amber-400',
    default: 'bg-panel/60 border-border text-gray-400',
    blue: 'bg-blue-900/20 border-blue-500/30 text-blue-400',
  };
  return (
    <div className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-xs font-medium ${variants[variant]}`}>
      {Icon && <Icon size={13} />}
      <span className="text-gray-500">{label}:</span>
      <span className="font-semibold">{value}</span>
    </div>
  );
}

export default function AnswerPanel({ result, isLoading }) {
  const [showTrace, setShowTrace] = useState(false);

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-72 gap-6 animate-fade-in">
        {/* Animated thinking indicator */}
        <div className="relative">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/20 to-accent/20 border border-primary/30 flex items-center justify-center animate-pulse-glow">
            <Sparkles size={24} className="text-primary animate-spin-slow" />
          </div>
          <div className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-primary animate-ping opacity-50" />
        </div>

        <div className="text-center space-y-2">
          <p className="text-gray-300 font-semibold">Agentic RAG in Progress</p>
          <p className="text-xs text-gray-600">Planning → Retrieving → Auditing → Synthesizing</p>
        </div>

        {/* Animated dots */}
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-primary typing-dot" />
          <div className="w-2 h-2 rounded-full bg-accent typing-dot" />
          <div className="w-2 h-2 rounded-full bg-primary typing-dot" />
        </div>

        {/* Shimmer skeleton */}
        <div className="w-full max-w-lg space-y-3">
          {[1, 0.7, 0.85, 0.5].map((w, i) => (
            <div key={i} className="h-3 rounded-full shimmer bg-panel" style={{ width: `${w * 100}%` }} />
          ))}
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="flex flex-col items-center justify-center h-72 gap-4 text-center animate-fade-in">
        <div className="w-16 h-16 rounded-2xl bg-panel border border-border flex items-center justify-center">
          <BookOpen size={24} className="text-gray-600" />
        </div>
        <div>
          <p className="text-gray-400 font-medium">Ready to Query</p>
          <p className="text-xs text-gray-600 mt-1">Select a document and submit a query to see agentic reasoning in action</p>
        </div>
        <div className="flex items-center gap-3 mt-2">
          {['Standard', 'CoT', 'ToT'].map(m => (
            <div key={m} className="px-3 py-1.5 bg-panel border border-border rounded-lg text-xs text-gray-600">{m}</div>
          ))}
        </div>
      </div>
    );
  }

  const { answer, mode, context_sufficient, evidence_type, iterations, missing_information, fallback_used, citations } = result;

  const evidenceVariant = evidence_type === 'explicit' ? 'success' : evidence_type === 'partial' ? 'warning' : 'error';

  return (
    <div className="animate-slide-in-up space-y-5">
      {/* Header + metrics */}
      <div className="glass rounded-2xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary/20 to-accent/20 border border-primary/30 flex items-center justify-center">
              <Sparkles size={14} className="text-primary" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white">Final Answer</h2>
              <p className="text-[10px] text-gray-600 capitalize">{mode} mode</p>
            </div>
          </div>
          <CopyButton text={answer} />
        </div>

        {/* Metric badges */}
        {mode !== 'vanilla' && (
          <div className="flex flex-wrap gap-2">
            <MetricBadge
              icon={context_sufficient ? CheckCircle2 : XCircle}
              label="Context"
              value={context_sufficient ? 'Sufficient' : 'Insufficient'}
              variant={context_sufficient ? 'success' : 'error'}
            />
            <MetricBadge
              label="Evidence"
              value={(evidence_type || 'N/A').charAt(0).toUpperCase() + (evidence_type || 'N/A').slice(1)}
              variant={evidenceVariant}
            />
            <MetricBadge
              icon={RotateCcw}
              label="Iterations"
              value={iterations || 1}
              variant={iterations > 1 ? 'warning' : 'blue'}
            />
            {fallback_used && (
              <MetricBadge
                icon={AlertTriangle}
                label="Parser"
                value="Fallback Used"
                variant="warning"
              />
            )}
          </div>
        )}
      </div>

      {/* Answer body */}
      <div className="glass rounded-2xl p-6">
        <div className="prose-rag">{renderMarkdown(answer)}</div>
      </div>

      {/* Citations */}
      {citations && citations.length > 0 && (
        <div className="glass rounded-2xl p-5 space-y-3">
          <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest flex items-center gap-2">
            <BookOpen size={12} />
            Sources ({citations.length})
          </h3>
          <div className="grid gap-2">
            {citations.slice(0, 5).map((c, idx) => (
              <div key={idx} className="flex items-start gap-3 p-3 bg-panel/60 border border-border/60 rounded-xl">
                <span className="flex-shrink-0 w-5 h-5 rounded-md bg-primary/10 border border-primary/20 flex items-center justify-center text-[10px] font-bold text-primary">
                  {idx + 1}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-gray-400 leading-relaxed line-clamp-2">{c.text_preview}</p>
                  <div className="flex items-center gap-2 mt-1.5">
                    <span className="text-[10px] text-gray-700">Chunk #{c.chunk_index}</span>
                    {c.score && (
                      <span className="text-[10px] font-mono text-primary bg-primary/10 px-1.5 py-0.5 rounded">
                        {c.score.toFixed(3)}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Missing info */}
      {missing_information && missing_information.length > 0 && (
        <div className="glass rounded-2xl p-5 space-y-3 border-red-500/20 bg-red-900/5">
          <h3 className="text-xs font-bold text-red-400 uppercase tracking-widest flex items-center gap-2">
            <AlertTriangle size={12} />
            Missing Information
          </h3>
          <ul className="space-y-1.5">
            {missing_information.map((info, idx) => (
              <li key={idx} className="flex items-start gap-2 text-xs text-red-200/80">
                <span className="flex-shrink-0 text-red-500 mt-0.5">•</span>
                {info}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Why it stopped (trace reasoning) */}
      {result.trace && result.trace.length > 0 && (
        <div className="glass rounded-2xl p-5 space-y-2">
          <button
            onClick={() => setShowTrace(!showTrace)}
            className="w-full flex items-center justify-between text-xs font-bold text-gray-400 uppercase tracking-widest hover:text-gray-200 transition-colors"
          >
            <span>Why It Stopped</span>
            {showTrace ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
          {showTrace && (
            <p className="text-sm text-gray-300 leading-relaxed animate-slide-in-up border-l-2 border-primary/40 pl-3 pt-1">
              {result.trace[result.trace.length - 1]?.sufficient_context_result?.reasoning_summary ||
               result.trace[result.trace.length - 1]?.sufficient_context_result?.feedback_log ||
               'Context evaluated and determined sufficient for synthesis.'}
            </p>
          )}
        </div>
      )}
    </div>
  );
}