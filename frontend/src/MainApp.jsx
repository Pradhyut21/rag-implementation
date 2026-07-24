import { useState, useEffect, useRef, useCallback, useReducer } from 'react';
import {
  Brain, Upload, FileText, Trash2, Search, Send,
  MessageSquare, Activity, Wrench, ChevronDown, ChevronRight,
  CheckCircle2, XCircle, RotateCcw, AlertTriangle, ArrowLeft,
  Zap, GitBranch, Cpu, Layers, Copy, Check, Sparkles, X,
  AlertCircle, ArrowRight, BookOpen, Loader2, FileSearch,
  BrainCircuit, Pencil, Menu, ChevronUp, Scan, Hash,
  Clock, Star, Shield, RefreshCw
} from 'lucide-react';
import { api, streamAsk } from './api/client';
import ObservabilityWorkspace from './components/ObservabilityWrapper';
import { ToastContainer, useToast } from './components/Toast';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

/* ─── MARKDOWN RENDERER ──────────────────────────────────── */
function MD({ content }) {
  return (
    <div className="prose-claude">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={{
        h1: ({children}) => <h1 className="text-xl font-black text-text-primary mt-4 mb-2">{children}</h1>,
        h2: ({children}) => <h2 className="text-lg font-bold text-text-primary mt-4 mb-2">{children}</h2>,
        h3: ({children}) => <h3 className="text-base font-semibold text-text-primary mt-3 mb-1.5">{children}</h3>,
        p: ({children}) => <p className="text-sm text-text-secondary leading-relaxed mb-3">{children}</p>,
        ul: ({children}) => <ul className="list-disc pl-5 mb-3 space-y-1">{children}</ul>,
        ol: ({children}) => <ol className="list-decimal pl-5 mb-3 space-y-1">{children}</ol>,
        li: ({children}) => <li className="text-sm text-text-secondary leading-relaxed">{children}</li>,
        strong: ({children}) => <strong className="font-semibold text-text-primary">{children}</strong>,
        code: ({inline, children}) => inline
          ? <code className="bg-bg-tertiary border border-border rounded px-1.5 py-0.5 text-[11px] font-mono text-violet-700">{children}</code>
          : <code className="text-teal-300 text-[11px] font-mono">{children}</code>,
        pre: ({children}) => <pre className="bg-[#1E1E2E] border border-[#3F3F5F] rounded-xl p-4 overflow-x-auto my-3 text-xs">{children}</pre>,
        blockquote: ({children}) => <blockquote className="border-l-4 border-brand pl-4 my-3 italic text-text-muted bg-brand-50 rounded-r-lg py-2 pr-3">{children}</blockquote>,
        table: ({children}) => <div className="overflow-x-auto my-3"><table className="min-w-full border-collapse text-sm">{children}</table></div>,
        th: ({children}) => <th className="bg-brand-50 text-brand font-semibold px-4 py-2 text-left border border-border text-xs">{children}</th>,
        td: ({children}) => <td className="px-4 py-2 border border-border text-xs text-text-secondary">{children}</td>,
      }}>{content}</ReactMarkdown>
    </div>
  );
}

/* ─── COPY BUTTON ────────────────────────────────────────── */
function CopyBtn({ text }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 1500); }}
      aria-label="Copy answer to clipboard"
      className="flex items-center gap-1 text-[11px] text-text-muted hover:text-text-primary transition-colors px-2 py-1 rounded-lg hover:bg-bg-secondary focus-visible:ring-2 focus-visible:ring-brand focus-visible:outline-none"
    >
      {copied ? <Check size={12} className="text-emerald-500" /> : <Copy size={12} />}
      {copied ? 'Copied' : 'Copy'}
    </button>
  );
}

/* ─── STAGE INDICATOR ────────────────────────────────────── */
const STAGES = [
  { label: 'Planning', icon: BrainCircuit, color: 'text-violet-600 bg-violet-50 border-violet-200' },
  { label: 'Rewriting', icon: Pencil, color: 'text-blue-600 bg-blue-50 border-blue-200' },
  { label: 'Retrieving', icon: Search, color: 'text-amber-600 bg-amber-50 border-amber-200' },
  { label: 'Auditing', icon: Shield, color: 'text-emerald-600 bg-emerald-50 border-emerald-200' },
  { label: 'Synthesizing', icon: Sparkles, color: 'text-brand bg-brand-50 border-brand/20' },
];

function StageIndicator({ currentStage }) {
  return (
    <div role="status" aria-live="polite" aria-label={`Processing: ${currentStage}`} className="flex items-center gap-2 flex-wrap mb-4">
      {STAGES.map((s, i) => {
        const Icon = s.icon;
        const active = i === currentStage;
        const done = i < currentStage;
        return (
          <div key={s.label} className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-[11px] font-semibold transition-all ${
            active ? s.color + ' shadow-sm scale-105' : done ? 'bg-emerald-50 border-emerald-200 text-emerald-600' : 'bg-bg-secondary border-border text-text-muted'
          }`}>
            {done ? <Check size={10} /> : active ? <Loader2 size={10} className="animate-spin" /> : <Icon size={10} />}
            {s.label}
          </div>
        );
      })}
    </div>
  );
}

/* ─── ITERATION TRACE ────────────────────────────────────── */
function IterationTrace({ trace }) {
  const [open, setOpen] = useState(false);
  if (!trace || trace.length === 0) return null;
  return (
    <div className="border border-border rounded-2xl overflow-hidden mb-4">
      <button
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        aria-controls="trace-panel"
        className="w-full flex items-center justify-between px-4 py-3 bg-bg-secondary hover:bg-bg-tertiary transition-colors text-sm font-semibold text-text-secondary focus-visible:ring-2 focus-visible:ring-brand focus-visible:outline-none"
      >
        <span className="flex items-center gap-2">
          <Layers size={14} className="text-brand" aria-hidden="true" />
          Agentic Loop Trace — {trace.length} iteration{trace.length !== 1 ? 's' : ''}
        </span>
        {open ? <ChevronUp size={14} aria-hidden="true" /> : <ChevronDown size={14} aria-hidden="true" />}
      </button>
      {open && (
        <div id="trace-panel" className="divide-y divide-border animate-slide-up">
          {trace.map((iter, idx) => {
            const sc = iter.sufficient_context_result;
            const isSuff = sc?.is_context_sufficient;
            return (
              <details key={idx} className="bg-white group">
                <summary className="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-bg-secondary list-none focus-visible:ring-2 focus-visible:ring-brand focus-visible:outline-none">
                  <div className={`w-6 h-6 rounded-lg flex items-center justify-center text-[10px] font-bold ${isSuff ? 'bg-emerald-100 text-emerald-600' : 'bg-amber-100 text-amber-700'}`}>{idx + 1}</div>
                  <span className="text-sm font-medium text-text-primary flex-1">Iteration {idx + 1}</span>
                  {sc && <span className={`text-[11px] px-2 py-0.5 rounded-full font-medium ${isSuff ? 'bg-emerald-50 text-emerald-600 border border-emerald-200' : 'bg-amber-50 text-amber-700 border border-amber-200'}`}>{isSuff ? '✓ Sufficient' : '↻ Retry'}</span>}
                  <ChevronDown size={13} className="text-text-muted group-open:rotate-180 transition-transform" aria-hidden="true" />
                </summary>
                <div className="px-4 pb-4 space-y-3 bg-bg-secondary/30 animate-slide-up">
                  {iter.sub_queries?.length > 0 && (
                    <div>
                      <p className="text-[10px] font-bold text-text-muted uppercase tracking-wider mb-1.5">Sub-Queries</p>
                      <div className="flex flex-wrap gap-1.5">
                        {iter.sub_queries.map((q, i) => <span key={i} className="px-2.5 py-1.5 bg-brand-50 border border-brand/20 text-brand text-[11px] rounded-lg">{q}</span>)}
                      </div>
                    </div>
                  )}
                  {sc && (
                    <div className={`p-3 rounded-xl border text-[11px] ${isSuff ? 'bg-emerald-50 border-emerald-200' : 'bg-amber-50 border-amber-200'}`}>
                      <p className={`font-bold mb-1 ${isSuff ? 'text-emerald-700' : 'text-amber-700'}`}>Evidence: {sc.evidence_type || 'N/A'}</p>
                      <p className="text-text-secondary leading-relaxed">{sc.reasoning_summary || sc.feedback_log}</p>
                    </div>
                  )}
                </div>
              </details>
            );
          })}
        </div>
      )}
    </div>
  );
}

/* ─── MESSAGE BUBBLE ─────────────────────────────────────── */
function MessageBubble({ msg }) {
  if (msg.role === 'user') {
    return (
      <div className="flex justify-end animate-fade-in" role="listitem">
        <div className="max-w-[80%] bg-brand text-white px-4 py-3 rounded-2xl rounded-br-md text-sm leading-relaxed shadow-brand">
          {msg.content}
        </div>
      </div>
    );
  }

  // Loading bubble
  if (msg.loading) {
    return (
      <div className="flex gap-3 animate-fade-in" role="listitem" aria-label="Loading response">
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-brand to-accent-blue flex items-center justify-center shadow-brand" aria-hidden="true">
          <Brain size={14} className="text-white" />
        </div>
        <div className="flex-1 min-w-0 pt-1">
          {msg.stage !== undefined && <StageIndicator currentStage={msg.stage} />}
          <div className="space-y-2 max-w-md">
            {[1, 0.7, 0.85, 0.5].map((w, i) => (
              <div key={i} className="h-3 shimmer rounded-full" style={{ width: `${w * 100}%` }} />
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Answer bubble
  const { answer, mode, context_sufficient, evidence_type, iterations, citations, trace, missing_information, fallback_used } = msg;
  return (
    <div className="flex gap-3 animate-slide-up" role="listitem">
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-brand to-accent-blue flex items-center justify-center shadow-brand flex-shrink-0" aria-hidden="true">
        <Brain size={14} className="text-white" />
      </div>
      <div className="flex-1 min-w-0">
        {/* Meta badges */}
        {mode !== 'vanilla' && (
          <div className="flex flex-wrap gap-2 mb-3" role="group" aria-label="Response metadata">
            <span className={`inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-full text-[11px] font-semibold border ${context_sufficient ? 'bg-emerald-50 border-emerald-200 text-emerald-700' : 'bg-red-50 border-red-200 text-red-600'}`}>
              {context_sufficient ? <CheckCircle2 size={11} aria-hidden="true" /> : <XCircle size={11} aria-hidden="true" />}
              {context_sufficient ? 'Context Sufficient' : 'Insufficient'}
            </span>
            <span className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-full text-[11px] font-semibold border bg-bg-secondary border-border text-text-secondary capitalize">
              {evidence_type || 'partial'}
            </span>
            <span className={`inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-full text-[11px] font-semibold border ${iterations > 1 ? 'bg-amber-50 border-amber-200 text-amber-700' : 'bg-brand-50 border-brand/20 text-brand'}`}>
              <RotateCcw size={11} aria-hidden="true" />
              {iterations || 1} iteration{(iterations || 1) > 1 ? 's' : ''}
            </span>
            {fallback_used && (
              <span className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-full text-[11px] font-semibold border bg-orange-50 border-orange-200 text-orange-700">
                <AlertTriangle size={11} aria-hidden="true" /> Fallback used
              </span>
            )}
            <CopyBtn text={answer} />
          </div>
        )}

        {/* Answer */}
        <div className="bg-white rounded-2xl border border-border shadow-soft p-5 mb-3">
          <MD content={answer} />
        </div>

        {/* Citations */}
        {citations?.length > 0 && (
          <div className="bg-bg-secondary rounded-2xl border border-border p-4 mb-3">
            <div className="flex items-center gap-2 mb-3 text-xs font-bold text-text-muted uppercase tracking-widest">
              <BookOpen size={12} aria-hidden="true" /> Sources ({citations.length})
            </div>
            <div className="space-y-2">
              {citations.slice(0, 4).map((c, i) => (
                <div key={i} className="flex items-start gap-3 p-3 bg-white rounded-xl border border-border">
                  <span className="flex-shrink-0 w-5 h-5 rounded-lg bg-brand-50 border border-brand/20 flex items-center justify-center text-[10px] font-bold text-brand" aria-label={`Source ${i + 1}`}>{i + 1}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-[11px] text-text-secondary leading-relaxed line-clamp-2">{c.text_preview}</p>
                    {c.score != null && <span className="text-[10px] font-mono text-brand mt-1 block">Score: {c.score.toFixed(4)}</span>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Missing info */}
        {missing_information?.length > 0 && (
          <div className="bg-red-50 rounded-2xl border border-red-200 p-4 mb-3" role="alert">
            <div className="flex items-center gap-2 mb-2 text-xs font-bold text-red-600 uppercase tracking-widest">
              <AlertTriangle size={12} aria-hidden="true" /> Missing Information
            </div>
            <ul className="space-y-1">
              {missing_information.map((info, i) => <li key={i} className="text-xs text-red-700 flex items-start gap-2"><span className="text-red-400 mt-0.5" aria-hidden="true">•</span>{info}</li>)}
            </ul>
          </div>
        )}

        <IterationTrace trace={trace} />
      </div>
    </div>
  );
}

/* ─── QUERY BAR ──────────────────────────────────────────── */
function QueryBar({ onQuery, isLoading, hasDocs, onCancel }) {
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState('debug');
  const [topK, setTopK] = useState(5);
  const [reasoningMode, setReasoningMode] = useState('standard');
  const textareaRef = useRef(null);

  const handleSubmit = () => {
    const q = query.trim();
    if (q && !isLoading && hasDocs) { onQuery({ query: q, mode, topK, reasoningMode }); setQuery(''); }
  };

  const handleKey = (e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(); } };

  const reasoningModes = [
    { id: 'standard', label: 'Standard', icon: Zap, color: 'text-amber-600' },
    { id: 'cot', label: 'Chain of Thought', icon: Cpu, color: 'text-brand' },
    { id: 'tot', label: 'Tree of Thought', icon: GitBranch, color: 'text-violet-600' },
  ];

  return (
    <div className="border-t border-border bg-white p-3 sm:p-4 flex-shrink-0">
      <div className="max-w-4xl mx-auto space-y-3">
        {/* Options row */}
        <div className="flex items-center gap-2 flex-wrap text-xs">
          {/* Mode selector */}
          <div className="flex items-center bg-bg-secondary rounded-lg border border-border p-0.5 gap-0.5" role="group" aria-label="Pipeline mode">
            {['vanilla', 'agentic', 'debug'].map(m => (
              <button key={m} type="button" onClick={() => setMode(m)}
                aria-pressed={mode === m}
                className={`px-3 py-1.5 rounded-md font-medium transition-all capitalize focus-visible:ring-2 focus-visible:ring-brand focus-visible:outline-none ${mode === m ? 'bg-brand text-white shadow-sm' : 'text-text-secondary hover:text-text-primary'}`}>
                {m}
              </button>
            ))}
          </div>

          {(mode === 'agentic' || mode === 'debug') && (
            <div className="flex items-center bg-bg-secondary rounded-lg border border-border p-0.5 gap-0.5" role="group" aria-label="Reasoning mode">
              {reasoningModes.map(({ id, label, icon: Icon, color }) => (
                <button key={id} type="button" onClick={() => setReasoningMode(id)}
                  aria-pressed={reasoningMode === id}
                  className={`px-2.5 py-1.5 rounded-md font-medium transition-all flex items-center gap-1.5 focus-visible:ring-2 focus-visible:ring-brand focus-visible:outline-none ${reasoningMode === id ? `bg-white shadow-sm border border-border ${color}` : 'text-text-secondary hover:text-text-primary'}`}>
                  <Icon size={12} aria-hidden="true" />
                  <span className="hidden sm:inline">{label}</span>
                </button>
              ))}
            </div>
          )}

          <div className="flex items-center gap-1.5 ml-auto text-text-muted" role="group" aria-label="Top-K results">
            <span className="text-[11px]">K:</span>
            <button onClick={() => setTopK(Math.max(1, topK - 1))} aria-label="Decrease K" className="w-5 text-center hover:text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand rounded">−</button>
            <span className="font-bold text-brand w-4 text-center" aria-live="polite">{topK}</span>
            <button onClick={() => setTopK(Math.min(20, topK + 1))} aria-label="Increase K" className="w-5 text-center hover:text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand rounded">+</button>
          </div>
        </div>

        {/* Input */}
        <div className={`flex gap-3 items-end p-3 rounded-2xl border-2 transition-all ${!hasDocs ? 'border-border opacity-60' : 'border-border focus-within:border-brand focus-within:shadow-sm'} bg-white`}>
          <label htmlFor="query-input" className="sr-only">Ask a question about the document</label>
          <textarea
            id="query-input"
            ref={textareaRef}
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={handleKey}
            placeholder={hasDocs ? 'Ask a question... (Enter to send, Shift+Enter for new line)' : 'Upload a document to start querying'}
            disabled={!hasDocs || isLoading}
            rows={2}
            maxLength={2000}
            aria-label="Query input"
            aria-disabled={!hasDocs}
            className="flex-1 resize-none text-sm text-text-primary placeholder-text-muted bg-transparent focus:outline-none leading-relaxed"
          />
          {isLoading ? (
            <button onClick={onCancel} aria-label="Cancel query" className="flex-shrink-0 w-10 h-10 rounded-xl bg-red-50 border border-red-200 text-red-600 flex items-center justify-center hover:bg-red-100 transition-all focus-visible:ring-2 focus-visible:ring-red-400 focus-visible:outline-none">
              <X size={15} />
            </button>
          ) : (
            <button onClick={handleSubmit} disabled={!hasDocs || !query.trim()} aria-label="Send query"
              className="flex-shrink-0 w-10 h-10 rounded-xl btn-brand flex items-center justify-center disabled:opacity-40 disabled:cursor-not-allowed focus-visible:ring-2 focus-visible:ring-brand focus-visible:ring-offset-2 focus-visible:outline-none">
              <Send size={15} aria-hidden="true" />
            </button>
          )}
        </div>
        {query.length > 1800 && (
          <p className="text-[11px] text-amber-600" role="alert">{2000 - query.length} characters remaining</p>
        )}
      </div>
    </div>
  );
}

/* ─── SIDEBAR ────────────────────────────────────────────── */
function Sidebar({ documents, selectedDocId, onSelect, onDelete, onUpload, activeTab, setActiveTab, isOpen, onClose }) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [ocrMode, setOcrMode] = useState(false);
  const fileRef = useRef(null);

  const handleFile = async (file) => {
    if (!file) return;
    setIsUploading(true);
    try { await onUpload(file, ocrMode); }
    finally { setIsUploading(false); }
  };

  const navItems = [
    { id: 'chat', icon: MessageSquare, label: 'Chat' },
    { id: 'tools', icon: Wrench, label: 'Dev Tools' },
    { id: 'observability', icon: Activity, label: 'Observability' },
  ];

  const sidebarContent = (
    <aside
      id="main-sidebar"
      aria-label="Navigation and document management"
      className="flex flex-col h-full bg-bg-secondary border-r border-border"
    >
      {/* Logo */}
      <div className="px-4 py-4 border-b border-border flex items-center gap-3">
        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-brand to-accent-blue flex items-center justify-center shadow-brand flex-shrink-0" aria-hidden="true">
          <Brain size={16} className="text-white" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-bold text-text-primary text-sm leading-none">Agentic RAG</p>
          <p className="text-[10px] text-text-muted leading-none mt-0.5">Enterprise Platform v3.0</p>
        </div>
        {/* Mobile close */}
        <button onClick={onClose} className="lg:hidden text-text-muted hover:text-text-primary" aria-label="Close sidebar">
          <X size={18} />
        </button>
      </div>

      {/* Nav */}
      <nav className="px-3 py-3 border-b border-border space-y-0.5" aria-label="Main navigation">
        {navItems.map(({ id, icon: Icon, label }) => (
          <button key={id} onClick={() => { setActiveTab(id); onClose?.(); }}
            aria-current={activeTab === id ? 'page' : undefined}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all focus-visible:ring-2 focus-visible:ring-brand focus-visible:outline-none ${activeTab === id ? 'bg-brand-100 text-brand border border-brand/20' : 'text-text-secondary hover:bg-surface-hover hover:text-text-primary'}`}>
            <Icon size={15} aria-hidden="true" />
            {label}
          </button>
        ))}
      </nav>

      {/* Upload */}
      <div className="px-3 py-3 border-b border-border">
        <p className="text-[10px] font-bold uppercase tracking-widest text-text-muted mb-2 px-1" id="kb-label">Knowledge Base</p>
        <div
          role="button"
          tabIndex={0}
          aria-label={`Upload document${ocrMode ? ' with OCR' : ''}`}
          aria-labelledby="kb-label"
          onClick={() => fileRef.current?.click()}
          onKeyDown={e => e.key === 'Enter' && fileRef.current?.click()}
          onDrop={e => { e.preventDefault(); setIsDragging(false); handleFile(e.dataTransfer.files?.[0]); }}
          onDragOver={e => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          className={`flex items-center gap-3 p-3 rounded-xl border-2 border-dashed cursor-pointer transition-all focus-visible:ring-2 focus-visible:ring-brand focus-visible:outline-none ${isDragging ? 'border-brand bg-brand-50' : 'border-border hover:border-brand/50 hover:bg-brand-50/50'}`}
        >
          <input type="file" className="sr-only" ref={fileRef} onChange={e => handleFile(e.target.files?.[0])} accept=".pdf,.docx" aria-hidden="true" />
          {isUploading ? <Loader2 size={15} className="text-brand animate-spin flex-shrink-0" aria-hidden="true" /> : <Upload size={15} className="text-brand flex-shrink-0" aria-hidden="true" />}
          <span className="text-xs text-text-secondary">{isUploading ? 'Indexing...' : 'Upload PDF / DOCX'}</span>
        </div>
        {/* OCR toggle */}
        <button
          onClick={() => setOcrMode(o => !o)}
          aria-pressed={ocrMode}
          className={`mt-2 w-full flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-medium border transition-all focus-visible:ring-2 focus-visible:ring-brand focus-visible:outline-none ${ocrMode ? 'bg-violet-50 border-violet-200 text-violet-700' : 'bg-bg-secondary border-border text-text-muted hover:text-text-primary'}`}
        >
          <Scan size={12} aria-hidden="true" />
          OCR Mode {ocrMode ? '(On — scanned PDFs)' : '(Off)'}
        </button>
      </div>

      {/* Doc list */}
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1" role="list" aria-label="Indexed documents">
        {documents.length === 0 ? (
          <div className="text-center py-8 text-xs text-text-muted" aria-live="polite">
            <FileText size={24} className="mx-auto mb-2 text-border-strong" aria-hidden="true" />
            No documents uploaded
          </div>
        ) : documents.map(doc => {
          const isActive = selectedDocId === doc.doc_id;
          return (
            <div key={doc.doc_id} role="listitem"
              className={`group relative flex items-start gap-2.5 px-3 py-2.5 rounded-xl cursor-pointer transition-all ${isActive ? 'bg-brand-100 border border-brand/20' : 'hover:bg-surface-hover border border-transparent'}`}
              onClick={() => onSelect(doc.doc_id)}
              tabIndex={0}
              onKeyDown={e => e.key === 'Enter' && onSelect(doc.doc_id)}
              aria-pressed={isActive}
              aria-label={`Select document: ${doc.file_name}`}
            >
              <FileText size={14} className={`flex-shrink-0 mt-0.5 ${isActive ? 'text-brand' : 'text-text-muted'}`} aria-hidden="true" />
              <div className="flex-1 min-w-0">
                <p className={`text-xs font-semibold truncate ${isActive ? 'text-brand' : 'text-text-primary'}`}>{doc.file_name}</p>
                <p className="text-[10px] text-text-muted">{doc.num_chunks} chunks</p>
              </div>
              <button
                onClick={e => { e.stopPropagation(); onDelete(doc.doc_id); }}
                aria-label={`Delete document: ${doc.file_name}`}
                className="opacity-0 group-hover:opacity-100 group-focus-within:opacity-100 flex-shrink-0 text-text-muted hover:text-red-500 transition-all focus-visible:opacity-100 focus-visible:ring-2 focus-visible:ring-red-400 focus-visible:outline-none rounded"
              >
                <Trash2 size={12} />
              </button>
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-border">
        <div className="flex items-center gap-2 text-[10px] text-text-muted">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-400" aria-hidden="true" />
          <span>Backend: port 8002</span>
          <span className="ml-auto flex items-center gap-1"><Shield size={9} /> Secured</span>
        </div>
      </div>
    </aside>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <div className="hidden lg:flex w-64 flex-shrink-0 h-full flex-col">{sidebarContent}</div>
      {/* Mobile drawer */}
      {isOpen && (
        <div className="lg:hidden fixed inset-0 z-40 flex">
          <div className="w-64 flex-shrink-0 h-full flex flex-col">{sidebarContent}</div>
          <div className="flex-1 bg-black/40" onClick={onClose} aria-label="Close sidebar overlay" />
        </div>
      )}
    </>
  );
}

/* ─── DEV TOOLS ──────────────────────────────────────────── */
function DevTools({ selectedDocId }) {
  const [retrieveQuery, setRetrieveQuery] = useState('');
  const [planQuery, setPlanQuery] = useState('');
  const [rewriteQuery, setRewriteQuery] = useState('');
  const [results, setResults] = useState({});
  const [loading, setLoading] = useState({});

  const run = async (key, fn, payload) => {
    setLoading(l => ({ ...l, [key]: true }));
    try {
      const res = await fn(payload);
      setResults(r => ({ ...r, [key]: res.data }));
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(l => ({ ...l, [key]: false }));
    }
  };

  const toolCard = (title, icon, color, children) => (
    <section className="bg-white rounded-2xl border border-border shadow-soft p-5 space-y-3" aria-label={title}>
      <div className="flex items-center gap-2 text-sm font-bold text-text-primary">
        <span className={color} aria-hidden="true">{icon}</span>{title}
      </div>
      {children}
    </section>
  );

  return (
    <main className="max-w-3xl mx-auto p-6 space-y-5" role="main" aria-label="Developer inspection tools">
      <div className="flex items-center gap-3 pb-4 border-b border-border">
        <div className="w-10 h-10 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-center" aria-hidden="true"><Wrench size={18} className="text-amber-600" /></div>
        <div><h1 className="font-bold text-text-primary">Agent Inspection Tools</h1><p className="text-xs text-text-muted">Debug individual pipeline components</p></div>
      </div>

      {toolCard('Retrieval Inspector', <Search size={14} />, 'text-brand', <>
        <div className="flex gap-2">
          <label htmlFor="retrieve-input" className="sr-only">Retrieval query</label>
          <input id="retrieve-input" value={retrieveQuery} onChange={e => setRetrieveQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && run('retrieve', api.retrieveOnly, { query: retrieveQuery, doc_id: selectedDocId, top_k: 5 })}
            placeholder={selectedDocId ? 'Query for FAISS retrieval inspection...' : 'Select a document first'}
            disabled={!selectedDocId} maxLength={2000}
            className="flex-1 border border-border rounded-xl px-4 py-2.5 text-sm bg-bg-secondary disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-brand" />
          <button onClick={() => run('retrieve', api.retrieveOnly, { query: retrieveQuery, doc_id: selectedDocId, top_k: 5 })}
            disabled={loading.retrieve || !selectedDocId || !retrieveQuery.trim()} aria-label="Run retrieval"
            className="btn-brand px-4 py-2.5 rounded-xl text-sm flex items-center gap-2 disabled:opacity-40 focus-visible:ring-2 focus-visible:ring-brand focus-visible:outline-none">
            {loading.retrieve ? <Loader2 size={14} className="animate-spin" /> : <ArrowRight size={14} />} Retrieve
          </button>
        </div>
        {results.retrieve && <div className="space-y-2 animate-slide-up" role="region" aria-label="Retrieval results">
          <div className="flex items-center gap-2 text-xs flex-wrap">
            <span className="text-text-muted">Rewritten:</span>
            <span className="font-mono text-brand bg-brand-50 border border-brand/20 px-2.5 py-1 rounded-lg">{results.retrieve.rewritten_query}</span>
          </div>
          {results.retrieve.retrieved_chunks?.map((c, i) => (
            <div key={i} className="p-3 bg-bg-secondary border border-border rounded-xl">
              <div className="flex justify-between mb-1">
                <span className="text-[10px] font-bold text-text-muted uppercase">Chunk #{c.index}</span>
                <span className="text-[10px] font-mono text-brand">{c.score?.toFixed(4)}</span>
              </div>
              <p className="text-xs text-text-secondary line-clamp-2">{c.chunk}</p>
            </div>
          ))}
        </div>}
      </>)}

      {toolCard('Planner — Query Decomposition', <BrainCircuit size={14} />, 'text-accent-blue', <>
        <div className="flex gap-2">
          <label htmlFor="plan-input" className="sr-only">Query for planning</label>
          <input id="plan-input" value={planQuery} onChange={e => setPlanQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && run('plan', api.planQuery, { query: planQuery })}
            placeholder="Enter a complex query to decompose..." maxLength={2000}
            className="flex-1 border border-border rounded-xl px-4 py-2.5 text-sm bg-bg-secondary focus:outline-none focus:ring-2 focus:ring-accent-blue" />
          <button onClick={() => run('plan', api.planQuery, { query: planQuery })}
            disabled={loading.plan || !planQuery.trim()} aria-label="Run planner"
            className="bg-accent-blue hover:bg-blue-600 text-white px-4 py-2.5 rounded-xl text-sm flex items-center gap-2 transition-all disabled:opacity-40 focus-visible:ring-2 focus-visible:ring-accent-blue focus-visible:outline-none">
            {loading.plan ? <Loader2 size={14} className="animate-spin" /> : <ArrowRight size={14} />} Plan
          </button>
        </div>
        {results.plan?.sub_queries && <div className="space-y-2 animate-slide-up" role="list" aria-label="Sub-queries">
          {results.plan.sub_queries.map((q, i) => (
            <div key={i} role="listitem" className="flex items-start gap-2.5 p-3 bg-blue-50 border border-blue-100 rounded-xl">
              <span className="flex-shrink-0 w-5 h-5 rounded-lg bg-accent-blue/10 border border-accent-blue/20 flex items-center justify-center text-[10px] font-bold text-accent-blue" aria-hidden="true">{i+1}</span>
              <span className="text-xs text-text-secondary leading-relaxed">{q}</span>
            </div>
          ))}
        </div>}
      </>)}

      {toolCard('Query Rewriter — Dense Retrieval Optimizer', <Pencil size={14} />, 'text-violet-600', <>
        <div className="flex gap-2">
          <label htmlFor="rewrite-input" className="sr-only">Query to rewrite</label>
          <input id="rewrite-input" value={rewriteQuery} onChange={e => setRewriteQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && run('rewrite', api.rewriteQuery, { query: rewriteQuery })}
            placeholder="Enter a raw sub-query to rewrite..." maxLength={2000}
            className="flex-1 border border-border rounded-xl px-4 py-2.5 text-sm bg-bg-secondary focus:outline-none focus:ring-2 focus:ring-violet-400" />
          <button onClick={() => run('rewrite', api.rewriteQuery, { query: rewriteQuery })}
            disabled={loading.rewrite || !rewriteQuery.trim()} aria-label="Run rewriter"
            className="bg-violet-600 hover:bg-violet-700 text-white px-4 py-2.5 rounded-xl text-sm flex items-center gap-2 transition-all disabled:opacity-40 focus-visible:ring-2 focus-visible:ring-violet-400 focus-visible:outline-none">
            {loading.rewrite ? <Loader2 size={14} className="animate-spin" /> : <ArrowRight size={14} />} Rewrite
          </button>
        </div>
        {results.rewrite && <div className="space-y-2 animate-slide-up" role="region" aria-label="Rewrite result">
          <div className="p-3 bg-bg-secondary border border-border rounded-xl text-xs text-text-secondary">{results.rewrite.query}</div>
          <div className="flex justify-center"><ArrowRight size={14} className="text-violet-400 rotate-90" aria-hidden="true" /></div>
          <div className="p-3 bg-violet-50 border border-violet-200 rounded-xl text-xs text-violet-800 font-medium leading-relaxed">{results.rewrite.rewritten_query}</div>
        </div>}
      </>)}
    </main>
  );
}

/* ─── MAIN APP ───────────────────────────────────────────── */
export default function MainApp({ onGoHome }) {
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('chat');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const chatRef = useRef(null);
  const cancelRef = useRef(null);
  const { toasts, toast, dismiss } = useToast();

  useEffect(() => { fetchDocuments(); }, []);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTo({ top: chatRef.current.scrollHeight, behavior: 'smooth' });
    }
  }, [messages]);

  const fetchDocuments = async () => {
    try {
      const res = await api.listDocuments();
      const docs = Array.isArray(res.data) ? res.data : (res.data.documents || []);
      setDocuments(docs);
      if (docs.length > 0 && !selectedDocId) setSelectedDocId(docs[0].doc_id);
    } catch (err) { console.error('Failed to load documents:', err); }
  };

  const handleUpload = async (file, useOcr = false) => {
    try {
      const res = useOcr ? await api.uploadDocumentOCR(file) : await api.uploadDocument(file);
      await fetchDocuments();
      setSelectedDocId(res.data.doc_id);
      toast({ type: 'success', message: `"${res.data.file_name}" indexed successfully (${res.data.num_chunks} chunks${useOcr ? ', OCR' : ''}).` });
    } catch (err) {
      toast({ type: 'error', message: err.userMessage || 'Upload failed.' });
    }
  };

  const handleDelete = async (docId) => {
    const doc = documents.find(d => d.doc_id === docId);
    try {
      await api.deleteDocument(docId);
      if (selectedDocId === docId) setSelectedDocId(null);
      await fetchDocuments();
      toast({ type: 'success', message: `"${doc?.file_name || docId}" deleted.` });
    } catch (err) {
      toast({ type: 'error', message: err.userMessage || 'Delete failed.' });
    }
  };

  const handleQuery = useCallback(async ({ query, mode, topK, reasoningMode }) => {
    if (!selectedDocId) { toast({ type: 'warning', message: 'Select a document before querying.' }); return; }
    if (query.length > 2000) { toast({ type: 'error', message: 'Query too long (max 2000 chars).' }); return; }

    const userMsg = { id: Date.now(), role: 'user', content: query };
    const loadingMsg = { id: Date.now() + 1, role: 'assistant', loading: true, stage: 0 };
    setMessages(prev => [...prev, userMsg, loadingMsg]);
    setIsLoading(true);

    const payload = { query, doc_id: selectedDocId, top_k: topK, reasoning_mode: reasoningMode, include_trace: true, response_mode: 'detailed' };

    // Use streaming for agentic/debug mode
    if (mode !== 'vanilla') {
      const cancel = streamAsk(payload, {
        onStage: ({ step }) => {
          setMessages(prev => prev.map(m => m.id === loadingMsg.id ? { ...m, stage: step - 1 } : m));
        },
        onResult: (result) => {
          setCurrentSessionId(result.session_id);
          setMessages(prev => prev.map(m => m.id === loadingMsg.id ? {
            ...m, loading: false,
            role: 'assistant', mode,
            answer: result.answer,
            context_sufficient: result.context_sufficient,
            evidence_type: result.evidence_type,
            iterations: result.iterations,
            citations: result.citations,
            trace: result.trace,
            missing_information: result.missing_information || [],
            fallback_used: result.fallback_used,
          } : m));
          setIsLoading(false);
          toast({ type: 'success', message: `Response ready — ${result.iterations} iteration${result.iterations !== 1 ? 's' : ''}`, duration: 2500 });
        },
        onError: (errMsg) => {
          setMessages(prev => prev.filter(m => m.id !== loadingMsg.id));
          toast({ type: 'error', message: errMsg || 'Pipeline failed.' });
          setIsLoading(false);
        },
        onDone: () => setIsLoading(false),
      });
      cancelRef.current = cancel;
    } else {
      // Vanilla RAG — no streaming
      try {
        const res = await api.askVanilla(payload);
        setMessages(prev => prev.map(m => m.id === loadingMsg.id ? {
          ...m, loading: false, role: 'assistant', mode: 'vanilla',
          answer: res.data.answer, citations: res.data.citations || [],
          context_sufficient: true, evidence_type: 'explicit', iterations: 1, trace: [], missing_information: [],
        } : m));
        toast({ type: 'success', message: 'Response ready.', duration: 2000 });
      } catch (err) {
        setMessages(prev => prev.filter(m => m.id !== loadingMsg.id));
        toast({ type: 'error', message: err.userMessage || 'Query failed.' });
      } finally {
        setIsLoading(false);
      }
    }
  }, [selectedDocId, toast]);

  const handleCancel = () => {
    cancelRef.current?.();
    setMessages(prev => prev.filter(m => !m.loading));
    setIsLoading(false);
    toast({ type: 'info', message: 'Query cancelled.', duration: 2000 });
  };

  const handleClearChat = () => {
    setMessages([]);
    setCurrentSessionId(null);
  };

  return (
    <div className="h-screen flex flex-col bg-white text-text-primary overflow-hidden">
      {/* Toast notifications */}
      <ToastContainer toasts={toasts} onDismiss={dismiss} />

      {/* Top bar */}
      <header className="flex-shrink-0 border-b border-border bg-bg-secondary px-4 py-2 flex items-center justify-between" role="banner">
        <div className="flex items-center gap-3">
          {/* Mobile menu button */}
          <button onClick={() => setSidebarOpen(true)} className="lg:hidden text-text-muted hover:text-text-primary focus-visible:ring-2 focus-visible:ring-brand focus-visible:outline-none rounded" aria-label="Open navigation" aria-expanded={sidebarOpen} aria-controls="main-sidebar">
            <Menu size={18} />
          </button>
          <button onClick={onGoHome} className="flex items-center gap-2 text-xs text-text-muted hover:text-brand transition-colors focus-visible:ring-2 focus-visible:ring-brand focus-visible:outline-none rounded" aria-label="Go to home page">
            <ArrowLeft size={13} aria-hidden="true" />
            <Brain size={13} className="text-brand" aria-hidden="true" />
            <span className="font-semibold hidden sm:inline">Agentic RAG</span>
          </button>
        </div>

        <div className="flex items-center gap-3">
          {currentSessionId && (
            <div className="hidden sm:flex items-center gap-2 text-[10px] font-mono text-emerald-600 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-full" aria-label={`Session ID: ${currentSessionId}`}>
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" aria-hidden="true" />
              {currentSessionId.slice(0, 14)}…
            </div>
          )}
          {messages.length > 0 && activeTab === 'chat' && (
            <button onClick={handleClearChat} className="text-[11px] text-text-muted hover:text-text-primary flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg hover:bg-bg-tertiary transition-all focus-visible:ring-2 focus-visible:ring-brand focus-visible:outline-none" aria-label="Clear conversation history">
              <RefreshCw size={11} aria-hidden="true" /> Clear
            </button>
          )}
          <div className="hidden sm:flex items-center gap-2 text-xs text-text-muted">
            <Zap size={12} className="text-amber-500" aria-hidden="true" />
            <span>Groq LPU · llama-3.3-70b</span>
          </div>
        </div>
      </header>

      <div className="flex-1 flex min-h-0">
        {/* Sidebar */}
        <Sidebar
          documents={documents}
          selectedDocId={selectedDocId}
          onSelect={setSelectedDocId}
          onDelete={handleDelete}
          onUpload={handleUpload}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
        />

        {/* Main content */}
        <div className="flex-1 flex flex-col min-w-0">

          {/* Chat tab */}
          {activeTab === 'chat' && (
            <>
              <main
                ref={chatRef}
                id="chat-content"
                className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6"
                role="log"
                aria-label="Conversation history"
                aria-live="polite"
              >
                {messages.length === 0 ? (
                  /* Empty state */
                  <div className="flex flex-col items-center justify-center h-full gap-6 text-center py-16 animate-fade-in" aria-label="Ready to query">
                    <div className="w-16 h-16 rounded-3xl bg-brand-50 border border-brand/20 flex items-center justify-center float-b" aria-hidden="true">
                      <Brain size={28} className="text-brand" />
                    </div>
                    <div>
                      <h2 className="text-xl font-bold text-text-primary mb-2">Ready to Query</h2>
                      <p className="text-sm text-text-secondary max-w-sm">Upload a PDF or DOCX, select it, and ask a question. Responses are streamed in real-time.</p>
                    </div>
                    <div className="flex items-center gap-2 flex-wrap justify-center">
                      {[
                        { icon: Zap, label: 'Standard 5-phase loop', color: 'text-amber-600 bg-amber-50 border-amber-200' },
                        { icon: Cpu, label: 'Chain of Thought', color: 'text-brand bg-brand-50 border-brand/20' },
                        { icon: GitBranch, label: 'Tree of Thought', color: 'text-violet-600 bg-violet-50 border-violet-200' },
                      ].map(({ icon: Icon, label, color }) => (
                        <div key={label} className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-xs font-medium ${color}`}>
                          <Icon size={13} aria-hidden="true" />{label}
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  messages.map(msg => <MessageBubble key={msg.id} msg={msg} />)
                )}
              </main>
              <QueryBar
                onQuery={handleQuery}
                isLoading={isLoading}
                hasDocs={documents.length > 0}
                onCancel={handleCancel}
              />
            </>
          )}

          {activeTab === 'tools' && (
            <div className="flex-1 overflow-y-auto">
              <DevTools selectedDocId={selectedDocId} />
            </div>
          )}

          {activeTab === 'observability' && (
            <div className="flex-1 overflow-hidden">
              <ObservabilityWorkspace />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
