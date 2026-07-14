import { useState, useEffect } from 'react';
import Layout from './components/Layout';
import SidebarDocuments from './components/SidebarDocuments';
import QueryPanel from './components/QueryPanel';
import AnswerPanel from './components/AnswerPanel';
import TracePanel from './components/TracePanel';
import RetrievalInspector from './components/RetrievalInspector';
import PlannerViewer from './components/PlannerViewer';
import RewriterViewer from './components/RewriterViewer';
import ObservabilityWorkspace from './components/ObservabilityWorkspace';
import ReasoningVisualizer from './components/ReasoningVisualizer';
import { api } from './api/client';

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [queryResult, setQueryResult] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('chat'); // 'chat' or 'tools'
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [currentReasoningMode, setCurrentReasoningMode] = useState('standard');

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const res = await api.listDocuments();
      if (Array.isArray(res.data)) {
        setDocuments(res.data);
      } else {
        setDocuments(res.data.documents || []);
      }
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

  const handleQuery = async ({ query, mode, topK, reasoningMode }) => {
    if (!selectedDocId) {
      setError('Please select a document first.');
      return;
    }
    setIsLoading(true);
    setError(null);
    setQueryResult(null);
    setCurrentSessionId(null);
    setCurrentReasoningMode(reasoningMode || 'standard');
    try {
      const payload = { query, doc_id: selectedDocId, top_k: topK, reasoning_mode: reasoningMode };
      let res;
      if (mode === 'vanilla') res = await api.askVanilla(payload);
      else if (mode === 'agentic') res = await api.askAgentic(payload);
      else if (mode === 'debug') res = await api.askDebug(payload);
      
      setQueryResult({ ...res.data, mode });
      if (res.data && res.data.session_id) {
        setCurrentSessionId(res.data.session_id);
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Layout>
      <div className="flex w-full h-screen overflow-hidden bg-dark text-gray-200">
        {activeTab !== 'observability' && (
          <div className="w-72 flex-shrink-0 border-r border-border glass p-4 flex flex-col gap-4 overflow-y-auto">
            <SidebarDocuments 
              documents={documents}
              selectedDocId={selectedDocId}
              onSelect={setSelectedDocId}
              onDelete={handleDelete}
              onUpload={handleUpload}
            />
          </div>
        )}
        <div className="flex-1 flex flex-col min-w-0">
          <div className="p-6 border-b border-border glass z-10 flex flex-col gap-4">
            <div className="flex justify-between items-center w-full">
               <h1 className="text-xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-primary to-accent">Agentic RAG Control Center</h1>
               <div className="flex bg-panel rounded-lg p-1 border border-border flex-shrink-0">
                  <button onClick={()=>setActiveTab('chat')} className={`px-4 py-1 text-sm rounded ${activeTab === 'chat' ? 'bg-primary text-white' : 'text-gray-400'}`}>Chat</button>
                  <button onClick={()=>setActiveTab('tools')} className={`px-4 py-1 text-sm rounded ${activeTab === 'tools' ? 'bg-primary text-white' : 'text-gray-400'}`}>Demo Tools</button>
                  <button onClick={()=>setActiveTab('observability')} className={`px-4 py-1 text-sm rounded ${activeTab === 'observability' ? 'bg-primary text-white' : 'text-gray-400'}`}>Observability</button>
               </div>
            </div>
            {activeTab !== 'observability' && (
              <QueryPanel onQuery={handleQuery} isLoading={isLoading} hasDocs={documents.length > 0} />
            )}
          </div>
          {error && <div className="m-6 p-3 bg-red-900/50 border border-red-500/50 text-red-200 rounded-lg">{error}</div>}
          
          <div className="flex-1 flex overflow-hidden">
            {activeTab === 'chat' && (
               <>
                 <div className="flex-1 p-6 overflow-y-auto">
                   {currentSessionId && (currentReasoningMode === 'cot' || currentReasoningMode === 'tot') && (
                     <ReasoningVisualizer sessionId={currentSessionId} mode={currentReasoningMode} />
                   )}
                   <AnswerPanel result={queryResult} isLoading={isLoading} />
                 </div>
                 {queryResult?.mode === 'debug' && (
                   <div className="w-[600px] border-l border-border bg-panel/30 overflow-y-auto p-6 shadow-2xl">
                     <TracePanel trace={queryResult} />
                   </div>
                 )}
               </>
            )}
            {activeTab === 'tools' && (
               <div className="flex-1 p-6 overflow-y-auto max-w-3xl mx-auto w-full">
                  <h2 className="text-xl font-semibold mb-6">Individual Agent Tool Inspection</h2>
                  <RetrievalInspector docId={selectedDocId} />
                  <PlannerViewer />
                  <RewriterViewer />
               </div>
            )}
            {activeTab === 'observability' && (
               <ObservabilityWorkspace />
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}