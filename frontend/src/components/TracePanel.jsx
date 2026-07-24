import { useState } from 'react';
import { Terminal, ChevronDown, ChevronRight, Clock, CheckCircle2, XCircle, Copy, Check } from 'lucide-react';

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };
  return (
    <button onClick={handleCopy} className="flex items-center gap-1 text-[10px] text-gray-600 hover:text-gray-300 transition-colors">
      {copied ? <Check size={10} className="text-emerald-400" /> : <Copy size={10} />}
      {copied ? 'Copied' : 'Copy'}
    </button>
  );
}

function SpanCard({ span, depth = 0 }) {
  const [expanded, setExpanded] = useState(depth === 0);
  const isSuccess = span.status === 'SUCCESS' || span.status === 'success';

  const statusColor = isSuccess ? 'text-emerald-400' : 'text-red-400';
  const borderColor = isSuccess ? 'border-emerald-500/20' : 'border-red-500/20';

  const extraData = span.extra_data ? (() => {
    try { return JSON.parse(span.extra_data); } catch { return null; }
  })() : null;

  return (
    <div className={`border rounded-xl overflow-hidden ${borderColor} bg-panel/30`}>
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-2 p-3 hover:bg-white/5 transition-colors text-left"
      >
        {expanded ? <ChevronDown size={12} className="text-gray-500 flex-shrink-0" /> : <ChevronRight size={12} className="text-gray-500 flex-shrink-0" />}
        <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${isSuccess ? 'bg-emerald-900/20 text-emerald-400' : 'bg-red-900/20 text-red-400'}`}>
          {span.name}
        </span>
        <span className="text-[10px] text-gray-600 ml-auto flex items-center gap-1">
          <Clock size={9} />
          {span.latency ? `${span.latency.toFixed(3)}s` : 'N/A'}
        </span>
      </button>

      {expanded && (
        <div className="px-3 pb-3 space-y-2 border-t border-border/40 pt-2 text-[11px]">
          {span.inputs && (
            <div>
              <div className="text-gray-600 font-medium mb-1">Input:</div>
              <pre className="bg-[#0a0c12] border border-border/50 rounded-lg p-2 text-gray-400 overflow-x-auto whitespace-pre-wrap break-all leading-relaxed max-h-32 overflow-y-auto font-mono text-[10px]">
                {typeof span.inputs === 'string' ? span.inputs : JSON.stringify(span.inputs, null, 2)}
              </pre>
            </div>
          )}
          {span.outputs && (
            <div>
              <div className="text-gray-600 font-medium mb-1">Output:</div>
              <pre className="bg-[#0a0c12] border border-border/50 rounded-lg p-2 text-primary/80 overflow-x-auto whitespace-pre-wrap break-all leading-relaxed max-h-32 overflow-y-auto font-mono text-[10px]">
                {typeof span.outputs === 'string' ? span.outputs : JSON.stringify(span.outputs, null, 2)}
              </pre>
            </div>
          )}
          {extraData && (
            <div className="flex flex-wrap gap-2 pt-1">
              {extraData.model && (
                <span className="px-2 py-0.5 bg-violet-900/20 border border-violet-500/20 text-violet-400 rounded text-[10px]">
                  {extraData.model}
                </span>
              )}
              {extraData.total_tokens && (
                <span className="px-2 py-0.5 bg-amber-900/20 border border-amber-500/20 text-amber-400 rounded text-[10px]">
                  {extraData.total_tokens} tokens
                </span>
              )}
              {extraData.estimated_cost && (
                <span className="px-2 py-0.5 bg-emerald-900/20 border border-emerald-500/20 text-emerald-400 rounded text-[10px]">
                  ${extraData.estimated_cost.toFixed(6)}
                </span>
              )}
            </div>
          )}
          {span.error && (
            <div className="text-red-400 text-[10px] bg-red-900/10 border border-red-500/20 rounded-lg p-2">
              Error: {span.error}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function TracePanel({ trace }) {
  if (!trace) return null;

  const spans = trace.trace || [];
  const totalLatency = trace.total_latency || spans.reduce((a, s) => a + (s.latency || 0), 0);
  const totalTokens = trace.total_tokens || 0;
  const estimatedCost = trace.estimated_cost || 0;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex-shrink-0 px-4 py-4 border-b border-border">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-6 h-6 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
            <Terminal size={12} className="text-amber-400" />
          </div>
          <h3 className="text-sm font-bold text-white">Execution Trace</h3>
        </div>

        {/* Quick stats */}
        <div className="grid grid-cols-3 gap-2">
          <div className="bg-panel/60 border border-border rounded-lg p-2 text-center">
            <div className="text-[10px] text-gray-600 mb-0.5">Latency</div>
            <div className="text-xs font-bold text-amber-400 font-mono">{totalLatency.toFixed(2)}s</div>
          </div>
          <div className="bg-panel/60 border border-border rounded-lg p-2 text-center">
            <div className="text-[10px] text-gray-600 mb-0.5">Tokens</div>
            <div className="text-xs font-bold text-blue-400 font-mono">{totalTokens}</div>
          </div>
          <div className="bg-panel/60 border border-border rounded-lg p-2 text-center">
            <div className="text-[10px] text-gray-600 mb-0.5">Cost</div>
            <div className="text-xs font-bold text-emerald-400 font-mono">${estimatedCost.toFixed(5)}</div>
          </div>
        </div>
      </div>

      {/* Spans list */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {spans.length > 0 ? (
          spans.map((span, idx) => <SpanCard key={span.span_id || idx} span={span} depth={0} />)
        ) : (
          <div className="text-center text-xs text-gray-600 py-8">No spans available</div>
        )}
      </div>
    </div>
  );
}