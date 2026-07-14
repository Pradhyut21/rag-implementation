import os
import json

base_dir = r"d:\Gemini ai agentic rag\frontend"
os.makedirs(base_dir, exist_ok=True)

files = {
    "package.json": """{
  "name": "agentic-rag-frontend",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "axios": "^1.6.8",
    "clsx": "^2.1.0",
    "lucide-react": "^0.368.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "tailwind-merge": "^2.2.2"
  },
  "devDependencies": {
    "@types/react": "^18.2.66",
    "@types/react-dom": "^18.2.22",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.38",
    "tailwindcss": "^3.4.3",
    "vite": "^5.2.0"
  }
}""",
    "vite.config.js": """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
})""",
    "postcss.config.js": """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}""",
    "tailwind.config.js": """/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: '#0f1115',
        panel: '#1a1d24',
        border: '#2a2d36',
        primary: '#3b82f6',
        accent: '#8b5cf6',
      }
    },
  },
  plugins: [],
}""",
    "index.html": """<!doctype html>
<html lang="en" class="dark">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Agentic RAG Demo</title>
  </head>
  <body class="bg-dark text-gray-200 antialiased">
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>""",
    "src/main.jsx": """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)""",
    "src/index.css": """@tailwind base;
@tailwind components;
@tailwind utilities;

@layer utilities {
  .glass {
    @apply bg-panel/80 backdrop-blur-md border border-border;
  }
}""",
    "src/api/client.js": """import axios from 'axios';

const API_URL = 'http://127.0.0.1:8000';

const client = axios.create({
  baseURL: API_URL,
});

export const api = {
  healthCheck: () => client.get('/health'),
  listDocuments: () => client.get('/documents'),
  uploadDocument: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return client.post('/upload-doc', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  deleteDocument: (docId) => client.delete(`/documents/${docId}`),
  askVanilla: (payload) => client.post('/vanilla-ask', payload),
  askAgentic: (payload) => client.post('/ask', payload),
  askDebug: (payload) => client.post('/ask-debug', payload),
  retrieveOnly: (payload) => client.post('/retrieve-only', payload),
  planQuery: (payload) => client.post('/plan', payload),
  rewriteQuery: (payload) => client.post('/rewrite', payload),
};""",
    "src/utils/formatters.js": """export function formatConfidence(score) {
  if (score === undefined || score === null) return 'N/A';
  return (score * 100).toFixed(1) + '%';
}""",
    "src/components/Layout.jsx": """export default function Layout({ children }) {
  return <div className="font-sans antialiased h-screen flex">{children}</div>;
}""",
    "src/components/StatusBadge.jsx": """import { clsx } from 'clsx';
import { CheckCircle2, XCircle, AlertCircle, Loader2 } from 'lucide-react';

export default function StatusBadge({ status, label }) {
  const styles = {
    success: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    error: 'bg-red-500/10 text-red-400 border-red-500/20',
    warning: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    info: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  };

  const icons = {
    success: <CheckCircle2 size={14} />,
    error: <XCircle size={14} />,
    warning: <AlertCircle size={14} />,
    info: <Loader2 size={14} className="animate-spin" />,
  };

  return (
    <div className={clsx('flex items-center gap-1.5 px-3 py-1 rounded-full border text-xs font-medium', styles[status])}>
      {icons[status]}
      {label}
    </div>
  );
}""",
    "src/components/UploadCard.jsx": """import { useRef } from 'react';
import { Upload } from 'lucide-react';

export default function UploadCard({ onUpload }) {
  const fileInput = useRef(null);

  const handleChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      onUpload(e.target.files[0]);
    }
  };

  return (
    <div 
      onClick={() => fileInput.current?.click()}
      className="border border-dashed border-gray-600 rounded-lg p-4 flex flex-col items-center justify-center text-gray-400 hover:text-white hover:border-primary cursor-pointer transition-colors bg-panel/50"
    >
      <Upload size={20} className="mb-2" />
      <span className="text-xs font-medium text-center">Click to upload PDF/DOCX</span>
      <input type="file" className="hidden" ref={fileInput} onChange={handleChange} accept=".pdf,.docx" />
    </div>
  );
}""",
    "src/components/SidebarDocuments.jsx": """import { FileText, Trash2 } from 'lucide-react';
import UploadCard from './UploadCard';

export default function SidebarDocuments({ documents, selectedDocId, onSelect, onDelete, onUpload }) {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">Upload</h2>
        <UploadCard onUpload={onUpload} />
      </div>
      <div>
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">Knowledge Base</h2>
        <div className="flex flex-col gap-2">
          {documents.map(doc => (
            <div 
              key={doc.doc_id}
              onClick={() => onSelect(doc.doc_id)}
              className={`p-3 rounded-lg border cursor-pointer transition-all ${selectedDocId === doc.doc_id ? 'bg-primary/20 border-primary shadow-lg shadow-primary/10' : 'bg-panel border-border hover:border-gray-500'}`}
            >
              <div className="flex justify-between items-start">
                <div className="flex items-center gap-2 overflow-hidden">
                  <FileText size={16} className="text-gray-400 flex-shrink-0" />
                  <span className="text-sm font-medium truncate" title={doc.file_name}>{doc.file_name}</span>
                </div>
                <button onClick={(e) => { e.stopPropagation(); onDelete(doc.doc_id); }} className="text-gray-500 hover:text-red-400 p-1">
                  <Trash2 size={14} />
                </button>
              </div>
              <div className="text-xs text-gray-500 mt-2 flex justify-between">
                <span>ID: {doc.doc_id.substring(0,6)}...</span>
                <span>{doc.num_chunks} chunks</span>
              </div>
            </div>
          ))}
          {documents.length === 0 && (
            <div className="text-xs text-gray-500 text-center p-4 border border-dashed border-border rounded-lg">
              No documents uploaded
            </div>
          )}
        </div>
      </div>
    </div>
  );
}""",
    "src/components/QueryPanel.jsx": """import { useState } from 'react';
import { Search, Settings2 } from 'lucide-react';

export default function QueryPanel({ onQuery, isLoading, hasDocs }) {
  const [query, setQuery] = useState('What latency measurements did Google report for the Sufficient Context Agent?');
  const [mode, setMode] = useState('debug');
  const [topK, setTopK] = useState(5);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onQuery({ query, mode, topK });
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <div className="flex gap-4 items-center">
        <div className="flex-1 relative">
          <input 
            type="text" 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a question about the document..."
            className="w-full bg-panel border border-border rounded-xl px-4 py-3 pl-11 text-white focus:outline-none focus:border-primary shadow-inner"
            disabled={!hasDocs}
          />
          <Search className="absolute left-4 top-3.5 text-gray-500" size={18} />
        </div>
        <button 
          type="submit" 
          disabled={isLoading || !hasDocs}
          className="bg-primary hover:bg-blue-500 text-white px-6 py-3 rounded-xl font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
        >
          {isLoading ? 'Thinking...' : 'Ask'}
        </button>
      </div>
      <div className="flex items-center gap-6 text-sm">
        <div className="flex items-center gap-2 bg-panel px-3 py-1.5 rounded-lg border border-border">
          <Settings2 size={14} className="text-gray-400" />
          <select 
            value={mode} 
            onChange={(e) => setMode(e.target.value)}
            className="bg-transparent text-gray-300 focus:outline-none"
          >
            <option value="vanilla">Vanilla RAG</option>
            <option value="agentic">Agentic RAG</option>
            <option value="debug">Agentic Debug (Show Trace)</option>
          </select>
        </div>
        <div className="flex items-center gap-2 text-gray-400">
          <span>Top K:</span>
          <input 
            type="number" 
            value={topK} 
            onChange={(e) => setTopK(parseInt(e.target.value))}
            className="bg-panel border border-border rounded px-2 py-1 w-16 focus:outline-none focus:border-primary text-center"
            min="1" max="10"
          />
        </div>
      </div>
    </form>
  );
}""",
    "src/components/AnswerPanel.jsx": """import StatusBadge from './StatusBadge';

export default function AnswerPanel({ result, isLoading }) {
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-500 space-y-4">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
        <p>Synthesizing response...</p>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        <p>Select a document and ask a question to see the result.</p>
      </div>
    );
  }

  const { answer, mode, context_sufficient, evidence_type, iterations, missing_information, fallback_used } = result;

  return (
    <div className="glass rounded-2xl p-8 shadow-xl">
      <div className="flex justify-between items-start mb-6 pb-6 border-b border-border">
        <h2 className="text-2xl font-semibold">Final Answer</h2>
        <div className="flex gap-2">
          <span className="px-3 py-1 bg-panel border border-border rounded-full text-xs font-medium text-gray-400 uppercase tracking-wide">
            {mode} mode
          </span>
          {mode !== 'vanilla' && (
            <StatusBadge 
              status={context_sufficient ? 'success' : 'error'} 
              label={context_sufficient ? 'Context Sufficient' : 'Context Insufficient'} 
            />
          )}
          {fallback_used && (
             <StatusBadge status="warning" label="Parser Fallback Used" />
          )}
        </div>
      </div>
      
      <div className="prose prose-invert max-w-none mb-8">
        <p className="text-lg leading-relaxed text-gray-200 whitespace-pre-wrap">{answer}</p>
      </div>

      {mode !== 'vanilla' && (
        <div className="grid grid-cols-2 gap-4 mt-8 pt-6 border-t border-border">
          <div className="bg-panel/50 rounded-xl p-4 border border-border">
            <h3 className="text-sm text-gray-400 mb-1">Iterations</h3>
            <p className="text-xl font-medium text-white">{iterations || 1}</p>
          </div>
          <div className="bg-panel/50 rounded-xl p-4 border border-border">
            <h3 className="text-sm text-gray-400 mb-1">Evidence Type</h3>
            <p className="text-xl font-medium text-white capitalize">{evidence_type || 'N/A'}</p>
          </div>
          
          {missing_information && missing_information.length > 0 && (
            <div className="col-span-2 bg-red-900/20 rounded-xl p-4 border border-red-500/30">
              <h3 className="text-sm text-red-400 mb-2 font-medium">Missing Information Identified:</h3>
              <ul className="list-disc list-inside text-red-200 text-sm space-y-1">
                {missing_information.map((info, idx) => (
                  <li key={idx}>{info}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}""",
    "src/components/IterationCard.jsx": """import { useState } from 'react';
import { ChevronDown, ChevronUp, Search, BrainCircuit, FileSearch, CheckCircle2, AlertTriangle } from 'lucide-react';
import StatusBadge from './StatusBadge';

export default function IterationCard({ iteration, index, isLast }) {
  const [expanded, setExpanded] = useState(true);

  const {
    planner_output,
    rewritten_queries,
    retrieved_chunks,
    sc_result
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
            {planner_output && (
              <div>
                <div className="flex items-center gap-2 mb-3 text-sm font-medium text-blue-400">
                  <BrainCircuit size={16} /> Planner Decomposed Query
                </div>
                <div className="flex flex-wrap gap-2">
                  {planner_output.map((q, i) => (
                    <span key={i} className="bg-blue-500/10 border border-blue-500/20 text-blue-200 px-3 py-1.5 rounded-lg text-sm">
                      {q}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Rewriter & Retrieval Section */}
            {(rewritten_queries || retrieved_chunks) && (
              <div className="bg-panel/40 rounded-lg p-4 border border-border">
                <div className="flex items-center gap-2 mb-3 text-sm font-medium text-purple-400">
                  <Search size={16} /> Search Fanout
                </div>
                {rewritten_queries && Object.entries(rewritten_queries).map(([sub, rewritten], i) => (
                  <div key={i} className="mb-3 last:mb-0">
                    <div className="text-xs text-gray-400 mb-1">Sub-query: {sub}</div>
                    <div className="text-sm text-purple-200 font-mono bg-purple-900/20 p-2 rounded">→ {rewritten}</div>
                  </div>
                ))}
                
                {retrieved_chunks && (
                  <div className="mt-4">
                    <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Retrieved Chunks ({retrieved_chunks.length})</div>
                    <div className="flex gap-2 overflow-x-auto pb-2">
                      {retrieved_chunks.slice(0, 3).map((chunk, i) => (
                        <div key={i} className="flex-shrink-0 w-64 bg-panel border border-border rounded p-3 text-xs text-gray-400">
                          <div className="font-mono text-[10px] mb-1 text-gray-500">Score: {chunk.score ? chunk.score.toFixed(3) : 'N/A'}</div>
                          <div className="line-clamp-3">{chunk.text}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* SC Agent Result */}
            {sc_result && (
              <div className={`rounded-lg p-4 border ${sc_result.is_context_sufficient ? 'bg-emerald-900/10 border-emerald-500/20' : 'bg-amber-900/10 border-amber-500/20'}`}>
                <div className={`flex items-center gap-2 mb-3 text-sm font-medium ${sc_result.is_context_sufficient ? 'text-emerald-400' : 'text-amber-400'}`}>
                  <FileSearch size={16} /> Sufficient Context Agent
                </div>
                <p className="text-sm text-gray-300 mb-3">{sc_result.reasoning_summary}</p>
                
                {!sc_result.is_context_sufficient && sc_result.missing_information && (
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
}""",
    "src/components/TracePanel.jsx": """import IterationCard from './IterationCard';
import { Network } from 'lucide-react';

export default function TracePanel({ trace }) {
  if (!trace || !trace.trace) return null;

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-3 mb-6 sticky top-0 bg-panel/30 backdrop-blur pb-4 pt-2 z-10 border-b border-border">
        <div className="p-2 bg-accent/20 rounded-lg text-accent">
          <Network size={20} />
        </div>
        <h2 className="text-lg font-semibold">Agentic Reasoning Trace</h2>
      </div>
      
      <div className="flex flex-col gap-8 relative">
        {/* Timeline connector line */}
        <div className="absolute left-6 top-0 bottom-0 w-px bg-border z-0"></div>
        
        {trace.trace.map((iter, idx) => (
          <IterationCard 
            key={idx} 
            iteration={iter} 
            index={idx} 
            isLast={idx === trace.trace.length - 1} 
          />
        ))}
      </div>
    </div>
  );
}""",
    "src/components/RetrievalInspector.jsx": """import { useState } from 'react';
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
}""",
    "src/components/PlannerViewer.jsx": """import { useState } from 'react';
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
}""",
    "src/components/RewriterViewer.jsx": """import { useState } from 'react';
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
}""",
    "src/App.jsx": """import { useState, useEffect } from 'react';
import Layout from './components/Layout';
import SidebarDocuments from './components/SidebarDocuments';
import QueryPanel from './components/QueryPanel';
import AnswerPanel from './components/AnswerPanel';
import TracePanel from './components/TracePanel';
import RetrievalInspector from './components/RetrievalInspector';
import PlannerViewer from './components/PlannerViewer';
import RewriterViewer from './components/RewriterViewer';
import { api } from './api/client';

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [queryResult, setQueryResult] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('chat'); // 'chat' or 'tools'

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const res = await api.listDocuments();
      setDocuments(res.data.documents || []);
    } catch (err) {
      console.error('Failed to fetch documents', err);
    }
  };

  const handleUpload = async (file) => {
    try {
      const res = await api.uploadDocument(file);
      await fetchDocuments();
      setSelectedDocId(res.data.doc_id);
    } catch (err) {
      setError('Upload failed');
    }
  };

  const handleDelete = async (docId) => {
    try {
      await api.deleteDocument(docId);
      if (selectedDocId === docId) setSelectedDocId(null);
      await fetchDocuments();
    } catch (err) {
      setError('Delete failed');
    }
  };

  const handleQuery = async ({ query, mode, topK }) => {
    if (!selectedDocId) {
      setError('Please select a document first.');
      return;
    }
    setIsLoading(true);
    setError(null);
    setQueryResult(null);
    try {
      const payload = { query, doc_id: selectedDocId, top_k: topK };
      let res;
      if (mode === 'vanilla') res = await api.askVanilla(payload);
      else if (mode === 'agentic') res = await api.askAgentic(payload);
      else if (mode === 'debug') res = await api.askDebug(payload);
      
      setQueryResult({ ...res.data, mode });
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Layout>
      <div className="flex w-full h-screen overflow-hidden bg-dark text-gray-200">
        <div className="w-72 flex-shrink-0 border-r border-border glass p-4 flex flex-col gap-4 overflow-y-auto">
          <SidebarDocuments 
            documents={documents}
            selectedDocId={selectedDocId}
            onSelect={setSelectedDocId}
            onDelete={handleDelete}
            onUpload={handleUpload}
          />
        </div>
        <div className="flex-1 flex flex-col min-w-0">
          <div className="p-6 border-b border-border glass z-10 flex justify-between items-start">
            <div>
               <h1 className="text-xl font-bold tracking-tight mb-4 bg-clip-text text-transparent bg-gradient-to-r from-primary to-accent">Agentic RAG Control Center</h1>
               <QueryPanel onQuery={handleQuery} isLoading={isLoading} hasDocs={documents.length > 0} />
            </div>
            <div className="flex bg-panel rounded-lg p-1 border border-border">
               <button onClick={()=>setActiveTab('chat')} className={`px-4 py-1 text-sm rounded ${activeTab === 'chat' ? 'bg-primary text-white' : 'text-gray-400'}`}>Chat</button>
               <button onClick={()=>setActiveTab('tools')} className={`px-4 py-1 text-sm rounded ${activeTab === 'tools' ? 'bg-primary text-white' : 'text-gray-400'}`}>Demo Tools</button>
            </div>
          </div>
          {error && <div className="m-6 p-3 bg-red-900/50 border border-red-500/50 text-red-200 rounded-lg">{error}</div>}
          
          <div className="flex-1 flex overflow-hidden">
            {activeTab === 'chat' ? (
               <>
                 <div className="flex-1 p-6 overflow-y-auto">
                   <AnswerPanel result={queryResult} isLoading={isLoading} />
                 </div>
                 {queryResult?.mode === 'debug' && (
                   <div className="w-[500px] border-l border-border bg-panel/30 overflow-y-auto p-6 shadow-2xl">
                     <TracePanel trace={queryResult} />
                   </div>
                 )}
               </>
            ) : (
               <div className="flex-1 p-6 overflow-y-auto max-w-3xl mx-auto w-full">
                  <h2 className="text-xl font-semibold mb-6">Individual Agent Tool Inspection</h2>
                  <RetrievalInspector docId={selectedDocId} />
                  <PlannerViewer />
                  <RewriterViewer />
               </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}"""
}

for path, content in files.items():
    full_path = os.path.join(base_dir, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("SUCCESS")
