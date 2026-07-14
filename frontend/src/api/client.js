import axios from 'axios';

const API_URL = 'http://127.0.0.1:8002';

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
  
  // Observability APIs
  getSessions: (params) => client.get('/observability/sessions', { params }),
  getSessionDetails: (id) => client.get(`/observability/session/${id}`),
  getTraces: () => client.get('/observability/traces'),
  getEvents: () => client.get('/observability/events'),
  getErrors: () => client.get('/observability/errors'),
  getMetrics: () => client.get('/observability/metrics'),
  getTokens: () => client.get('/observability/tokens'),
  getLatency: () => client.get('/observability/latency'),
  getReplay: (sessionId) => client.get(`/observability/replay/${sessionId}`),
  getDashboard: () => client.get('/observability/dashboard'),
  
  // Reasoning APIs
  getReasoningCoT: (sessionId) => client.get(`/reasoning/cot/${sessionId}`),
  getReasoningChain: (sessionId) => client.get(`/reasoning/chain/${sessionId}`),
  getReasoningToT: (sessionId) => client.get(`/reasoning/tot/${sessionId}`),
  getReasoningTree: (sessionId) => client.get(`/reasoning/tree/${sessionId}`),
};