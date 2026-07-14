import { useState, useEffect } from 'react';
import { 
  GitBranch, HelpCircle, FileText, CheckCircle2, XCircle, Clock, 
  ArrowDown, GitCommit, Settings, Layers, ChevronDown, ChevronRight 
} from 'lucide-react';
import { api } from '../api/client';

export default function ReasoningVisualizer({ sessionId, mode }) {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [expandedBranch, setExpandedBranch] = useState(null);

  useEffect(() => {
    if (sessionId && (mode === 'cot' || mode === 'tot')) {
      fetchReasoningData();
    } else {
      setData(null);
    }
  }, [sessionId, mode]);

  const fetchReasoningData = async () => {
    setLoading(true);
    try {
      if (mode === 'cot') {
        const res = await api.getReasoningCoT(sessionId);
        setData(res.data);
      } else if (mode === 'tot') {
        const res = await api.getReasoningToT(sessionId);
        setData(res.data);
        // Default expand winning branch if exists
        const winningId = res.data?.winning_branch?.branch_id;
        if (winningId) setExpandedBranch(winningId);
      }
    } catch (err) {
      console.error("Failed to load reasoning details", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-8 bg-panel/30 border border-border rounded-xl space-y-3">
        <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm text-gray-400">Loading reasoning details...</p>
      </div>
    );
  }

  if (!sessionId || !data) return null;

  if (mode === 'cot') {
    const stages = data.stages || [];
    return (
      <div className="flex flex-col bg-panel/30 border border-border rounded-xl p-6 shadow-xl mb-6">
        <div className="flex items-center gap-2 mb-6 pb-4 border-b border-border">
          <Layers size={18} className="text-primary" />
          <h3 className="font-semibold text-gray-200">Chain of Thought (CoT) Reasoning Flow</h3>
        </div>

        <div className="flex flex-col items-center">
          {stages.map((stage, idx) => {
            const isSuccess = stage.status === 'SUCCESS';
            return (
              <div key={stage.stage_id} className="w-full flex flex-col items-center">
                {/* Stage Card */}
                <div className="w-full bg-panel/70 border border-border hover:border-primary/50 transition-all rounded-xl p-4 shadow-sm">
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex items-center gap-2.5">
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                        isSuccess ? 'bg-emerald-500/15 text-emerald-400' : 'bg-red-500/15 text-red-400'
                      }`}>
                        {idx + 1}
                      </div>
                      <span className="font-medium text-gray-200 text-sm">{stage.stage_name}</span>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-gray-500">
                      <span className="flex items-center gap-1">
                        <Clock size={12} /> {stage.execution_time}s
                      </span>
                      {isSuccess ? (
                        <span className="text-emerald-400 font-medium">SUCCESS</span>
                      ) : (
                        <span className="text-red-400 font-medium">FAILED</span>
                      )}
                    </div>
                  </div>
                  
                  <div className="mt-3 text-xs space-y-2">
                    <div className="text-gray-500">
                      <span className="font-medium text-gray-400">Input:</span> {stage.input_data}
                    </div>
                    <div className="bg-panel border border-border/60 p-2.5 rounded-lg text-gray-300 font-sans leading-relaxed">
                      <span className="font-semibold text-primary block mb-1">Output Summary</span>
                      {stage.output_summary}
                    </div>
                  </div>
                </div>

                {/* Connector Arrow */}
                {idx < stages.length - 1 && (
                  <div className="my-3 text-gray-600 flex flex-col items-center">
                    <ArrowDown size={18} className="animate-pulse text-primary/70" />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  if (mode === 'tot') {
    const branches = data.branches || [];
    const winningBranchId = data.winning_branch?.branch_id;

    return (
      <div className="flex flex-col bg-panel/30 border border-border rounded-xl p-6 shadow-xl mb-6">
        <div className="flex items-center gap-2 mb-6 pb-4 border-b border-border justify-between">
          <div className="flex items-center gap-2">
            <GitBranch size={18} className="text-primary" />
            <h3 className="font-semibold text-gray-200">Tree of Thought (ToT) Evaluation</h3>
          </div>
          {data.decision_latency && (
            <span className="text-xs text-gray-500 flex items-center gap-1">
              <Clock size={12} /> Latency: {data.decision_latency.toFixed(2)}s
            </span>
          )}
        </div>

        {/* Structured Tree Diagram */}
        <div className="bg-panel/40 border border-border/80 rounded-xl p-4 mb-6 font-mono text-sm leading-relaxed">
          <div className="text-blue-400 font-semibold mb-2">Planner</div>
          {branches.map((b, idx) => {
            const isWinner = b.branch_id === winningBranchId;
            const isLast = idx === branches.length - 1;
            return (
              <div key={b.branch_id} className="pl-4">
                <div>
                  {isLast ? '└── ' : '├── '} 
                  <span className={isWinner ? 'text-emerald-400 font-bold' : 'text-gray-300'}>
                    {b.branch_name}
                  </span>
                </div>
                <div className="pl-6 text-xs text-gray-500">
                  {isLast ? ' ' : '│'}    Score {b.final_score ? b.final_score.toFixed(2) : '0.00'}
                  {isWinner && <span className="text-emerald-500/80 ml-2 font-bold">(Selected)</span>}
                </div>
                {!isLast && <div className="pl-4 text-gray-700">│</div>}
              </div>
            );
          })}
        </div>

        {/* Detailed Branch Lists */}
        <div className="flex flex-col gap-4">
          <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Branch Details</h4>
          {branches.map((b) => {
            const isWinner = b.branch_id === winningBranchId;
            const isExpanded = expandedBranch === b.branch_id;
            const scores = b.score || {};

            return (
              <div 
                key={b.branch_id} 
                className={`glass border rounded-xl overflow-hidden transition-all ${
                  isWinner ? 'border-emerald-500/30 bg-emerald-900/5' : 'border-border'
                }`}
              >
                <div 
                  onClick={() => setExpandedBranch(isExpanded ? null : b.branch_id)}
                  className="p-4 flex justify-between items-center cursor-pointer hover:bg-panel transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {isExpanded ? <ChevronDown size={16} className="text-gray-500" /> : <ChevronRight size={16} className="text-gray-500" />}
                    <div>
                      <span className="font-medium text-gray-200 text-sm block">{b.branch_name}</span>
                      <span className="text-xs text-gray-500">
                        Evidence Strategy: {b.expected_evidence}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {isWinner && (
                      <span className="px-2 py-0.5 bg-emerald-500/15 border border-emerald-500/25 text-emerald-400 rounded text-[10px] font-bold uppercase">
                        Selected Branch
                      </span>
                    )}
                    <span className={`text-sm font-mono font-bold px-2 py-1 rounded bg-panel ${
                      isWinner ? 'text-emerald-400' : 'text-primary'
                    }`}>
                      {b.final_score ? b.final_score.toFixed(2) : '0.00'}
                    </span>
                  </div>
                </div>

                {isExpanded && (
                  <div className="px-4 pb-4 border-t border-border/40 pt-4 bg-panel/30 text-xs text-gray-300 space-y-4">
                    {/* Sub Queries */}
                    <div>
                      <span className="font-semibold text-gray-400 uppercase tracking-wider block mb-1">Sub-Queries Generated:</span>
                      <div className="flex flex-wrap gap-2 mt-1">
                        {b.retrieval_query.split(', ').map((q, idx) => (
                          <span key={idx} className="bg-panel border border-border/80 px-2.5 py-1 rounded-lg text-gray-300">
                            {q}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Scores Metrics Breakdown */}
                    <div>
                      <span className="font-semibold text-gray-400 uppercase tracking-wider block mb-2">Metrics Breakdown:</span>
                      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                        <div className="bg-panel p-2.5 rounded-lg border border-border/60 text-center">
                          <span className="text-[10px] text-gray-500 block mb-1">Similarity</span>
                          <span className="font-mono text-sm font-semibold text-blue-400">{scores.retrieval_similarity || 0}</span>
                        </div>
                        <div className="bg-panel p-2.5 rounded-lg border border-border/60 text-center">
                          <span className="text-[10px] text-gray-500 block mb-1">Coverage</span>
                          <span className="font-mono text-sm font-semibold text-purple-400">{scores.coverage || 0}</span>
                        </div>
                        <div className="bg-panel p-2.5 rounded-lg border border-border/60 text-center">
                          <span className="text-[10px] text-gray-500 block mb-1">Completeness</span>
                          <span className="font-mono text-sm font-semibold text-pink-400">{scores.completeness || 0}</span>
                        </div>
                        <div className="bg-panel p-2.5 rounded-lg border border-border/60 text-center">
                          <span className="text-[10px] text-gray-500 block mb-1">Evidence Quality</span>
                          <span className="font-mono text-sm font-semibold text-amber-400">{scores.evidence_quality || 0}</span>
                        </div>
                        <div className="bg-panel p-2.5 rounded-lg border border-border/60 text-center">
                          <span className="text-[10px] text-gray-500 block mb-1">Confidence</span>
                          <span className="font-mono text-sm font-semibold text-teal-400">{scores.confidence || 0}</span>
                        </div>
                      </div>
                    </div>

                    {/* Evaluation Details */}
                    {b.evaluation && (
                      <div className="bg-panel border border-border/60 rounded-lg p-3">
                        <span className="font-semibold text-gray-400 uppercase block mb-1">Evaluation Details:</span>
                        <p className="text-gray-300 leading-relaxed font-sans">{b.evaluation.evaluation_details}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  return null;
}
