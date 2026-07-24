import { useState } from 'react';
import { api } from '../api/client';
import { BrainCircuit, ArrowRight, Loader2 } from 'lucide-react';

export default function PlannerViewer() {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handlePlan = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const res = await api.planQuery({ query });
      setResult(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass rounded-2xl p-5 space-y-4">
      <div className="flex items-center gap-2">
        <BrainCircuit size={14} className="text-blue-400" />
        <h3 className="text-sm font-bold text-gray-200">Planner Agent</h3>
        <span className="ml-auto text-[10px] text-gray-600 bg-panel border border-border px-2 py-0.5 rounded-full">Decomposition</span>
      </div>

      <div className="flex gap-2">
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handlePlan()}
          placeholder="Enter a complex query to decompose..."
          className="flex-1 bg-panel border border-border rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-blue-500/50 transition-colors placeholder-gray-600"
        />
        <button
          onClick={handlePlan}
          disabled={loading || !query.trim()}
          className="px-4 py-2.5 bg-blue-600/80 hover:bg-blue-500 text-white rounded-xl text-sm font-medium disabled:opacity-40 transition-all flex items-center gap-2"
        >
          {loading ? <Loader2 size={14} className="animate-spin" /> : <ArrowRight size={14} />}
          Plan
        </button>
      </div>

      {result?.sub_queries && (
        <div className="space-y-2 animate-slide-in-up">
          <div className="text-[10px] font-bold text-gray-600 uppercase tracking-wider">
            {result.sub_queries.length} Sub-Queries Generated
          </div>
          {result.sub_queries.map((sq, idx) => (
            <div key={idx} className="flex items-start gap-2.5 p-3 bg-blue-500/5 border border-blue-500/15 rounded-xl">
              <span className="flex-shrink-0 w-5 h-5 rounded-lg bg-blue-500/15 border border-blue-500/25 flex items-center justify-center text-[10px] font-bold text-blue-400">
                {idx + 1}
              </span>
              <span className="text-xs text-gray-300 leading-relaxed">{sq}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}