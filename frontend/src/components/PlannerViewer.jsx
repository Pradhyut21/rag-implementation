import { useState } from 'react';
import { api } from '../api/client';
import { BrainCircuit } from 'lucide-react';

export default function PlannerViewer() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  
  const handlePlan = async () => {
    if(!query) return;
    try {
      const res = await api.planQuery({ query });
      setResults(res.data.sub_queries);
    } catch(e) { console.error(e); }
  };
  
  return (
    <div className="p-4 border border-border bg-panel rounded-lg mt-4">
      <h3 className="font-semibold mb-3">Planner Viewer</h3>
      <div className="flex gap-2 mb-4">
        <input className="flex-1 bg-dark px-3 py-2 border border-border rounded" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Test planner..." />
        <button onClick={handlePlan} className="px-3 py-2 bg-blue-600 rounded"><BrainCircuit size={18} /></button>
      </div>
      <div className="space-y-2">
        {results.map((c, i) => (
          <div key={i} className="text-sm bg-dark p-2 rounded border border-border text-blue-300">
             {c}
          </div>
        ))}
      </div>
    </div>
  );
}