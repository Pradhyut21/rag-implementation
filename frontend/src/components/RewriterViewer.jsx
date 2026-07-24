import { useState } from 'react';
import { api } from '../api/client';
import { Pencil, ArrowRight, Loader2 } from 'lucide-react';

export default function RewriterViewer() {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleRewrite = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const res = await api.rewriteQuery({ query });
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
        <Pencil size={14} className="text-violet-400" />
        <h3 className="text-sm font-bold text-gray-200">Query Rewriter Agent</h3>
        <span className="ml-auto text-[10px] text-gray-600 bg-panel border border-border px-2 py-0.5 rounded-full">Dense Retrieval</span>
      </div>

      <div className="flex gap-2">
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleRewrite()}
          placeholder="Enter a raw sub-query to rewrite..."
          className="flex-1 bg-panel border border-border rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-violet-500/50 transition-colors placeholder-gray-600"
        />
        <button
          onClick={handleRewrite}
          disabled={loading || !query.trim()}
          className="px-4 py-2.5 bg-violet-700/80 hover:bg-violet-600 text-white rounded-xl text-sm font-medium disabled:opacity-40 transition-all flex items-center gap-2"
        >
          {loading ? <Loader2 size={14} className="animate-spin" /> : <ArrowRight size={14} />}
          Rewrite
        </button>
      </div>

      {result && (
        <div className="space-y-3 animate-slide-in-up">
          <div className="space-y-2">
            <div className="text-[10px] font-bold text-gray-600 uppercase tracking-wider">Original</div>
            <div className="p-3 bg-panel/50 border border-border rounded-xl text-xs text-gray-400">{result.query}</div>
          </div>
          <div className="flex items-center justify-center">
            <ArrowRight size={14} className="text-violet-500" />
          </div>
          <div className="space-y-2">
            <div className="text-[10px] font-bold text-violet-400 uppercase tracking-wider">Rewritten for Dense Retrieval</div>
            <div className="p-3 bg-violet-900/10 border border-violet-500/25 rounded-xl text-xs text-violet-200 font-medium leading-relaxed">
              {result.rewritten_query}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}