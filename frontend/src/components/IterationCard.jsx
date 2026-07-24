import { useState } from 'react';
import { ChevronDown, ChevronUp, Search, BrainCircuit, FileSearch, CheckCircle2, AlertTriangle, ArrowRight, Sparkles } from 'lucide-react';
import StatusBadge from './StatusBadge';

export default function IterationCard({ iteration, index, isLast }) {
  const [expanded, setExpanded] = useState(true);

  const {
    sub_queries,
    fanout_results,
    sufficient_context_result: sc_result,
    intermediate_draft
  } = iteration;

  const isSufficient = sc_result?.is_context_sufficient;

  return (
    <div className="relative pl-6 animate-slide-in-up" style={{ animationDelay: `${index * 100}ms` }}>
      {/* Timeline dot */}
      <div className={`absolute left-0 top-4 w-4 h-4 rounded-full border-2 flex items-center justify-center transform -translate-x-1/2 ${
        isSufficient
          ? 'bg-emerald-900/30 border-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.4)]'
          : 'bg-amber-900/30 border-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.4)]'
      }`}>
        <span className="text-[8px] font-bold text-white">{index + 1}</span>
      </div>

      <div className={`glass rounded-xl overflow-hidden border ${
        isSufficient ? 'border-emerald-500/20' : 'border-amber-500/15'
      }`}>
        {/* Accordion header */}
        <div
          className="px-4 py-3 flex justify-between items-center cursor-pointer hover:bg-white/5 transition-colors"
          onClick={() => setExpanded(!expanded)}
        >
          <div className="flex items-center gap-3">
            <span className="text-xs font-bold text-gray-300">Iteration {index + 1}</span>
            {sc_result && (
              <StatusBadge
                status={isSufficient ? 'success' : 'warning'}
                label={isSufficient ? 'Sufficient' : 'Needs More Info'}
              />
            )}
            {sub_queries && (
              <span className="text-[10px] text-gray-600">{sub_queries.length} sub-queries</span>
            )}
          </div>
          {expanded
            ? <ChevronUp size={14} className="text-gray-600" />
            : <ChevronDown size={14} className="text-gray-600" />
          }
        </div>

        {expanded && (
          <div className="px-4 pb-4 space-y-4 border-t border-border/40 pt-4">

            {/* Sub-queries (Planner) */}
            {sub_queries && sub_queries.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-2 text-xs font-semibold text-blue-400">
                  <BrainCircuit size={13} />
                  Planner — {sub_queries.length} Sub-Queries
                </div>
                <div className="flex flex-wrap gap-2">
                  {sub_queries.map((q, i) => (
                    <span key={i} className="bg-blue-500/10 border border-blue-500/20 text-blue-300 px-2.5 py-1.5 rounded-lg text-xs">
                      {q}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Fanout results */}
            {fanout_results && fanout_results.length > 0 && (
              <div className="bg-panel/40 rounded-xl p-3 border border-border/60">
                <div className="flex items-center gap-2 mb-3 text-xs font-semibold text-purple-400">
                  <Search size={13} />
                  Search Fanout — {fanout_results.length} queries
                </div>
                <div className="space-y-3">
                  {fanout_results.map((fanout, i) => (
                    <div key={i} className="space-y-1.5">
                      <div className="text-[10px] text-gray-500">Sub-query: {fanout.sub_query}</div>
                      <div className="flex items-center gap-2 text-xs text-purple-300 font-mono bg-purple-900/15 border border-purple-500/10 p-2 rounded-lg">
                        <ArrowRight size={10} className="text-purple-500 flex-shrink-0" />
                        <span className="truncate">{fanout.rewritten_query}</span>
                      </div>
                      {fanout.retrieved && fanout.retrieved.length > 0 && (
                        <div className="flex gap-2 overflow-x-auto pb-1 mt-1">
                          {fanout.retrieved.slice(0, 3).map((chunk, j) => (
                            <div key={j} className="flex-shrink-0 w-56 bg-panel border border-border/70 rounded-lg p-2.5">
                              <div className="text-[9px] font-mono text-primary mb-1">
                                Score: {chunk.score ? chunk.score.toFixed(4) : 'N/A'}
                              </div>
                              <div className="text-[10px] text-gray-500 line-clamp-3 leading-relaxed">
                                {chunk.chunk || chunk.text}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Intermediate draft */}
            {intermediate_draft && (
              <div className="bg-panel/30 rounded-xl p-3 border border-border/60">
                <div className="flex items-center gap-1.5 mb-2">
                  <Sparkles size={11} className="text-violet-400" />
                  <span className="text-[10px] font-bold text-violet-400 uppercase tracking-wider">Intermediate Draft</span>
                </div>
                <p className="text-xs text-gray-400 italic border-l-2 border-violet-500/40 pl-3 leading-relaxed">
                  "{intermediate_draft}"
                </p>
              </div>
            )}

            {/* SC Agent result */}
            {sc_result && (
              <div className={`rounded-xl p-3 border ${
                isSufficient
                  ? 'bg-emerald-900/10 border-emerald-500/20'
                  : 'bg-amber-900/10 border-amber-500/20'
              }`}>
                <div className={`flex items-center gap-2 mb-2 text-xs font-semibold ${
                  isSufficient ? 'text-emerald-400' : 'text-amber-400'
                }`}>
                  <FileSearch size={13} />
                  Sufficient Context Agent
                  {sc_result.evidence_type && (
                    <span className="ml-auto text-[10px] font-mono capitalize opacity-70">
                      [{sc_result.evidence_type}]
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-300 leading-relaxed">
                  {sc_result.reasoning_summary || sc_result.feedback_log}
                </p>
                {!isSufficient && sc_result.missing_information?.length > 0 && (
                  <div className="mt-3 space-y-1">
                    <div className="text-[10px] font-bold text-amber-500/70 uppercase tracking-wider">Missing:</div>
                    <ul className="space-y-0.5">
                      {sc_result.missing_information.map((info, i) => (
                        <li key={i} className="text-xs text-amber-200/70 flex items-start gap-1.5">
                          <AlertTriangle size={10} className="flex-shrink-0 text-amber-500 mt-0.5" />
                          {info}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* Loop indicator */}
            {!isLast && !isSufficient && (
              <div className="flex items-center justify-center gap-3 text-amber-500/40 text-xs">
                <div className="h-px flex-1 bg-amber-500/20" />
                <span className="flex items-center gap-1.5 font-medium">
                  <AlertTriangle size={11} />
                  Triggering feedback loop...
                </span>
                <div className="h-px flex-1 bg-amber-500/20" />
              </div>
            )}
            {isLast && isSufficient && (
              <div className="flex items-center justify-center gap-3 text-emerald-500/40 text-xs">
                <div className="h-px flex-1 bg-emerald-500/20" />
                <span className="flex items-center gap-1.5 font-medium text-emerald-400/60">
                  <CheckCircle2 size={11} />
                  Proceeding to synthesis
                </span>
                <div className="h-px flex-1 bg-emerald-500/20" />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}