import { useState } from 'react';
import { api } from '../api/client';
import { Search, ArrowRight, Loader2 } from 'lucide-react';

export default function RetrievalInspector({ docId }) {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleRetrieve = async () => {
    if (!query.trim() || !docId) return;
    setLoading(true);
    try {
      const res = await api.retrieveOnly({ query, doc_id: docId, top_k: 5 });
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
        <Search size={14} className="text-primary" />
        <h3 className="text-sm font-bold text-gray-200">Retrieval Inspector</h3>
      </div>

      <div className="flex gap-2">
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleRetrieve()}
          placeholder={docId ? 'Enter a query to inspect retrieval...' : 'Select a document first'}
          disabled={!docId}
          className="flex-1 bg-panel border border-border rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-primary transition-colors placeholder-gray-600 disabled:opacity-40"
        />
        <button
          onClick={handleRetrieve}
          disabled={loading || !docId || !query.trim()}
          className="px-4 py-2.5 bg-primary hover:bg-blue-500 text-white rounded-xl text-sm font-medium disabled:opacity-40 transition-all flex items-center gap-2"
        >
          {loading ? <Loader2 size={14} className="animate-spin" /> : <ArrowRight size={14} />}
          Retrieve
        </button>
      </div>

      {result && (
        <div className="space-y-3 animate-slide-in-up">
          <div className="flex items-center gap-2 text-xs">
            <span className="text-gray-600">Rewritten:</span>
            <span className="text-primary font-mono bg-primary/10 border border-primary/20 px-2.5 py-1 rounded-lg">{result.rewritten_query}</span>
          </div>

          <div className="space-y-2">
            {result.retrieved_chunks?.map((chunk, idx) => (
              <div key={idx} className="bg-panel/60 border border-border rounded-xl p-3 space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-bold text-gray-600 uppercase tracking-wider">Chunk #{chunk.index}</span>
                  <span className="text-[10px] font-mono text-primary bg-primary/10 px-2 py-0.5 rounded">
                    {chunk.score?.toFixed(4)}
                  </span>
                </div>
                <p className="text-xs text-gray-400 leading-relaxed line-clamp-3">{chunk.chunk}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}