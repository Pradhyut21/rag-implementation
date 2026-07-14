import { useState } from 'react';
import { ChevronDown, ChevronUp, Search, BrainCircuit, FileSearch, CheckCircle2, AlertTriangle } from 'lucide-react';
import StatusBadge from './StatusBadge';

export default function IterationCard({ iteration, index, isLast }) {
  const [expanded, setExpanded] = useState(true);

  const {
    sub_queries,
    fanout_results,
    sufficient_context_result: sc_result,
    intermediate_draft
  } = iteration;

  return (
    <div className="relative z-10 pl-14">
      {/* Timeline dot */}
      <div className="absolute left-4 top-5 w-5 h-5 rounded-full bg-panel border-4 border-accent shadow-[0_0_10px_rgba(139,92,246,0.5)] transform -translate-x-1/2 flex items-center justify-center">
        <span className="text-[10px] font-bold text-accent">{index + 1}</span>
      </div>

      <div className="glass rounded-xl border border-border overflow-hidden">
        <div 
          className="p-4 bg-panel/50 border-b border-border flex justify-between items-center cursor-pointer hover:bg-panel transition-colors"
          onClick={() => setExpanded(!expanded)}
        >
          <div className="flex items-center gap-3">
            <h3 className="font-medium text-gray-200">Iteration {index + 1}</h3>
            {sc_result && (
              <StatusBadge 
                status={sc_result.is_context_sufficient ? 'success' : 'warning'} 
                label={sc_result.is_context_sufficient ? 'Sufficient' : 'Needs More Info'} 
              />
            )}
          </div>
          {expanded ? <ChevronUp size={16} className="text-gray-500" /> : <ChevronDown size={16} className="text-gray-500" />}
        </div>

        {expanded && (
          <div className="p-5 flex flex-col gap-6">
            
            {/* Planner Section */}
            {sub_queries && sub_queries.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-3 text-sm font-medium text-blue-400">
                  <BrainCircuit size={16} /> Planner / Decomposed Queries
                </div>
                <div className="flex flex-wrap gap-2">
                  {sub_queries.map((q, i) => (
                    <span key={i} className="bg-blue-500/10 border border-blue-500/20 text-blue-200 px-3 py-1.5 rounded-lg text-sm">
                      {q}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Rewriter & Retrieval Section */}
            {fanout_results && fanout_results.length > 0 && (
              <div className="bg-panel/40 rounded-lg p-4 border border-border">
                <div className="flex items-center gap-2 mb-3 text-sm font-medium text-purple-400">
                  <Search size={16} /> Search Fanout
                </div>
                {fanout_results.map((fanout, i) => (
                  <div key={i} className="mb-4 last:mb-0 border-b border-border pb-4 last:border-0 last:pb-0">
                    <div className="text-xs text-gray-400 mb-1">Sub-query: {fanout.sub_query}</div>
                    <div className="text-sm text-purple-200 font-mono bg-purple-900/20 p-2 rounded mb-2">→ {fanout.rewritten_query}</div>
                    
                    {fanout.retrieved && fanout.retrieved.length > 0 && (
                      <div className="mt-2">
                        <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Retrieved Chunks ({fanout.retrieved.length})</div>
                        <div className="flex gap-2 overflow-x-auto pb-2">
                          {fanout.retrieved.slice(0, 3).map((chunk, j) => (
                            <div key={j} className="flex-shrink-0 w-64 bg-panel border border-border rounded p-3 text-xs text-gray-400">
                              <div className="font-mono text-[10px] mb-1 text-gray-500">Score: {chunk.score ? chunk.score.toFixed(3) : 'N/A'}</div>
                              <div className="line-clamp-3">{chunk.chunk || chunk.text}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Intermediate Draft */}
            {intermediate_draft && (
              <div className="bg-panel/30 rounded-lg p-4 border border-border mt-2">
                <div className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Intermediate Draft</div>
                <div className="text-sm text-gray-300 italic border-l-2 border-primary/50 pl-3 py-1">
                  "{intermediate_draft}"
                </div>
              </div>
            )}

            {/* SC Agent Result */}
            {sc_result && (
              <div className={`rounded-lg p-4 border ${sc_result.is_context_sufficient ? 'bg-emerald-900/10 border-emerald-500/20' : 'bg-amber-900/10 border-amber-500/20'}`}>
                <div className={`flex items-center gap-2 mb-3 text-sm font-medium ${sc_result.is_context_sufficient ? 'text-emerald-400' : 'text-amber-400'}`}>
                  <FileSearch size={16} /> Sufficient Context Agent
                </div>
                <p className="text-sm text-gray-300 mb-3">{sc_result.reasoning_summary || sc_result.feedback_log}</p>
                
                {!sc_result.is_context_sufficient && sc_result.missing_information && sc_result.missing_information.length > 0 && (
                  <div className="mt-3">
                    <div className="text-xs font-semibold text-amber-500/70 uppercase tracking-wider mb-2">Missing Information:</div>
                    <ul className="list-disc list-inside text-sm text-amber-200/80 space-y-1">
                      {sc_result.missing_information.map((info, i) => <li key={i}>{info}</li>)}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* Loop Indicator */}
            {!isLast && sc_result && !sc_result.is_context_sufficient && (
              <div className="flex items-center justify-center text-amber-500/50 pt-2">
                <div className="h-px bg-amber-500/20 flex-1"></div>
                <div className="px-4 text-xs font-medium uppercase tracking-wider flex items-center gap-1">
                  <AlertTriangle size={12} /> Triggering Feedback Loop
                </div>
                <div className="h-px bg-amber-500/20 flex-1"></div>
              </div>
            )}
            
            {isLast && sc_result && sc_result.is_context_sufficient && (
              <div className="flex items-center justify-center text-emerald-500/50 pt-2">
                <div className="h-px bg-emerald-500/20 flex-1"></div>
                <div className="px-4 text-xs font-medium uppercase tracking-wider flex items-center gap-1">
                  <CheckCircle2 size={12} /> Proceeding to Synthesis
                </div>
                <div className="h-px bg-emerald-500/20 flex-1"></div>
              </div>
            )}

          </div>
        )}
      </div>
    </div>
  );
}