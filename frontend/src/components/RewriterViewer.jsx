import { useState } from 'react';
import { api } from '../api/client';
import { Sparkles } from 'lucide-react';

export default function RewriterViewer() {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState('');
  
  const handleRewrite = async () => {
    if(!query) return;
    try {
      const res = await api.rewriteQuery({ query });
      setResult(res.data.rewritten_query);
    } catch(e) { console.error(e); }
  };
  
  return (
    <div className="p-4 border border-border bg-panel rounded-lg mt-4">
      <h3 className="font-semibold mb-3">Rewriter Viewer</h3>
      <div className="flex gap-2 mb-4">
        <input className="flex-1 bg-dark px-3 py-2 border border-border rounded" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Test rewriter..." />
        <button onClick={handleRewrite} className="px-3 py-2 bg-purple-600 rounded"><Sparkles size={18} /></button>
      </div>
      {result && (
        <div className="text-sm bg-dark p-2 rounded border border-border text-purple-300 font-mono">
           {result}
        </div>
      )}
    </div>
  );
}