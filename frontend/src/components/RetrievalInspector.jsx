import { useState } from 'react';
import { api } from '../api/client';
import { Search } from 'lucide-react';

export default function RetrievalInspector({ docId }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  
  const handleRetrieve = async () => {
    if(!query || !docId) return;
    try {
      const res = await api.retrieveOnly({ query, doc_id: docId, top_k: 5 });
      setResults(res.data.chunks);
    } catch(e) { console.error(e); }
  };
  
  return (
    <div className="p-4 border border-border bg-panel rounded-lg mt-4">
      <h3 className="font-semibold mb-3">Retrieval Inspector</h3>
      <div className="flex gap-2 mb-4">
        <input className="flex-1 bg-dark px-3 py-2 border border-border rounded" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Test raw retrieval..." />
        <button onClick={handleRetrieve} className="px-3 py-2 bg-primary rounded"><Search size={18} /></button>
      </div>
      <div className="space-y-2">
        {results.map((c, i) => (
          <div key={i} className="text-xs bg-dark p-2 rounded border border-border text-gray-300">
            <span className="text-purple-400 font-mono">Score: {c.score.toFixed(3)}</span>
            <p className="mt-1">{c.text}</p>
          </div>
        ))}
      </div>
    </div>
  );
}