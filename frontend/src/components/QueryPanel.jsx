import { useState } from 'react';
import { Search, Cpu, GitBranch, Zap, ChevronDown, Send, Settings2 } from 'lucide-react';

const REASONING_MODES = [
  {
    id: 'standard',
    label: 'Standard',
    icon: Zap,
    color: 'text-amber-400',
    bg: 'bg-amber-500/10 border-amber-500/20',
    desc: '5-Phase Loop'
  },
  {
    id: 'cot',
    label: 'Chain of Thought',
    icon: Cpu,
    color: 'text-blue-400',
    bg: 'bg-blue-500/10 border-blue-500/20',
    desc: '6-Stage CoT'
  },
  {
    id: 'tot',
    label: 'Tree of Thought',
    icon: GitBranch,
    color: 'text-purple-400',
    bg: 'bg-purple-500/10 border-purple-500/20',
    desc: '3-Branch ToT'
  },
];

const QUERY_MODES = [
  { id: 'vanilla', label: 'Vanilla RAG', color: 'text-gray-400' },
  { id: 'agentic', label: 'Agentic RAG', color: 'text-primary' },
  { id: 'debug', label: 'Debug Mode', color: 'text-amber-400' },
];

export default function QueryPanel({ onQuery, isLoading, hasDocs }) {
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState('debug');
  const [topK, setTopK] = useState(5);
  const [reasoningMode, setReasoningMode] = useState('standard');
  const [showSettings, setShowSettings] = useState(false);

  const selectedReasoning = REASONING_MODES.find(r => r.id === reasoningMode);
  const ReasoningIcon = selectedReasoning?.icon || Zap;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onQuery({ query, mode, topK, reasoningMode });
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3">
      {/* Main query input */}
      <div className="flex gap-3 items-end">
        <div className="flex-1 relative">
          <div className={`relative rounded-xl border transition-all duration-200 ${
            !hasDocs ? 'border-border opacity-50' : 'border-border focus-within:border-primary/60 focus-within:glow-blue'
          } bg-panel/80`}>
            <textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={hasDocs ? 'Ask a question about the document... (Enter to submit)' : 'Upload a document first to enable queries'}
              disabled={!hasDocs}
              rows={2}
              className="w-full bg-transparent px-4 py-3 pl-11 text-white focus:outline-none text-sm placeholder-gray-600 resize-none leading-relaxed"
            />
            <Search className="absolute left-3.5 top-3.5 text-gray-600" size={16} />
          </div>
        </div>

        <button
          type="submit"
          disabled={isLoading || !hasDocs || !query.trim()}
          className="flex-shrink-0 h-[72px] w-14 bg-gradient-to-b from-primary to-blue-600 hover:from-blue-500 hover:to-primary text-white rounded-xl font-medium transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed flex flex-col items-center justify-center gap-1 shadow-lg hover:shadow-primary/30 hover:scale-105 active:scale-95"
          id="ask-button"
        >
          {isLoading ? (
            <>
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              <span className="text-[8px] font-bold uppercase tracking-wider">Wait</span>
            </>
          ) : (
            <>
              <Send size={15} />
              <span className="text-[8px] font-bold uppercase tracking-wider">Ask</span>
            </>
          )}
        </button>
      </div>

      {/* Mode selector row */}
      <div className="flex items-center gap-3 flex-wrap">
        {/* Query mode pills */}
        <div className="flex items-center bg-panel/60 border border-border rounded-lg p-0.5 gap-0.5">
          {QUERY_MODES.map(m => (
            <button
              key={m.id}
              type="button"
              onClick={() => setMode(m.id)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all duration-150 ${
                mode === m.id
                  ? 'bg-primary text-white shadow-md'
                  : 'text-gray-500 hover:text-gray-300'
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>

        {/* Reasoning mode (only for agentic/debug) */}
        {(mode === 'agentic' || mode === 'debug') && (
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-gray-600 uppercase tracking-wider">Reasoning:</span>
            <div className="flex items-center bg-panel/60 border border-border rounded-lg p-0.5 gap-0.5">
              {REASONING_MODES.map(r => {
                const Icon = r.icon;
                return (
                  <button
                    key={r.id}
                    type="button"
                    onClick={() => setReasoningMode(r.id)}
                    className={`px-2.5 py-1.5 rounded-md text-xs font-medium transition-all duration-150 flex items-center gap-1.5 ${
                      reasoningMode === r.id
                        ? `${r.bg} ${r.color} border`
                        : 'text-gray-500 hover:text-gray-300'
                    }`}
                  >
                    <Icon size={11} />
                    <span className="hidden sm:inline">{r.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Top K */}
        <div className="flex items-center gap-1.5 ml-auto">
          <span className="text-[10px] text-gray-600 uppercase tracking-wider">Top-K:</span>
          <div className="flex items-center gap-1 bg-panel/60 border border-border rounded-lg px-2 py-1">
            <button type="button" onClick={() => setTopK(Math.max(1, topK - 1))} className="text-gray-500 hover:text-white w-4 text-center">−</button>
            <span className="text-xs font-mono font-bold text-primary w-4 text-center">{topK}</span>
            <button type="button" onClick={() => setTopK(Math.min(10, topK + 1))} className="text-gray-500 hover:text-white w-4 text-center">+</button>
          </div>
        </div>
      </div>

      {/* Active config summary */}
      {(mode === 'agentic' || mode === 'debug') && (
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs ${selectedReasoning?.bg} ${selectedReasoning?.color}`}>
          <ReasoningIcon size={11} />
          <span className="font-medium">{selectedReasoning?.desc}</span>
          <span className="text-gray-600 mx-1">·</span>
          <span className="text-gray-500">{selectedReasoning?.label} reasoning active</span>
          {mode === 'debug' && (
            <>
              <span className="text-gray-600 mx-1">·</span>
              <span className="text-amber-400">Trace panel enabled</span>
            </>
          )}
        </div>
      )}
    </form>
  );
}