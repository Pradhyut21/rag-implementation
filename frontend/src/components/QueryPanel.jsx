import { useState } from 'react';
import { Search, Settings2 } from 'lucide-react';

export default function QueryPanel({ onQuery, isLoading, hasDocs }) {
  const [query, setQuery] = useState('What latency measurements did Google report for the Sufficient Context Agent?');
  const [mode, setMode] = useState('debug');
  const [topK, setTopK] = useState(5);
  const [reasoningMode, setReasoningMode] = useState('standard');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onQuery({ query, mode, topK, reasoningMode });
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-3 w-[850px] max-w-full">
      <div className="flex gap-3 items-center">
        <div className="flex-1 relative">
          <input 
            type="text" 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a question about the document..."
            className="w-full bg-panel border border-border rounded-xl px-5 py-3.5 pl-12 text-white focus:outline-none focus:border-primary shadow-inner text-base transition-all"
            disabled={!hasDocs}
          />
          <Search className="absolute left-4 top-4 text-gray-500" size={18} />
        </div>
        <button 
          type="submit" 
          disabled={isLoading || !hasDocs}
          className="bg-primary hover:bg-blue-500 text-white px-6 py-3.5 rounded-xl text-base font-semibold transition-colors disabled:opacity-50 flex items-center gap-2 shadow-lg hover:shadow-primary/20"
        >
          {isLoading ? 'Thinking...' : 'Ask'}
        </button>
      </div>
      <div className="flex items-center gap-6 text-xs text-gray-400">
        <div className="flex items-center gap-1.5">
          <Settings2 size={14} className="text-gray-500" />
          <select 
            value={mode} 
            onChange={(e) => setMode(e.target.value)}
            className="bg-transparent text-gray-300 focus:outline-none cursor-pointer"
          >
            <option value="vanilla">Vanilla RAG</option>
            <option value="agentic">Agentic RAG</option>
            <option value="debug">Agentic Debug (Show Trace)</option>
          </select>
        </div>
        
        {(mode === 'agentic' || mode === 'debug') && (
          <div className="flex items-center gap-1.5">
            <span className="text-gray-500">Reasoning:</span>
            <select 
              value={reasoningMode} 
              onChange={(e) => setReasoningMode(e.target.value)}
              className="bg-transparent text-gray-300 focus:outline-none cursor-pointer font-medium text-blue-400"
            >
              <option value="standard">Standard RAG</option>
              <option value="cot">Chain of Thought (CoT)</option>
              <option value="tot">Tree of Thought (ToT)</option>
            </select>
          </div>
        )}

        <div className="flex items-center gap-1.5">
          <span>Top K:</span>
          <input 
            type="number" 
            value={topK} 
            onChange={(e) => setTopK(parseInt(e.target.value))}
            className="bg-panel border border-border rounded px-2 py-0.5 w-14 focus:outline-none focus:border-primary text-center text-gray-300"
            min="1" max="10"
          />
        </div>
      </div>
    </form>
  );
}