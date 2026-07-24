import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8002';

/** Read JWT token from Zustand-persisted localStorage (avoids circular import). */
function getAuthToken() {
  try {
    const raw = localStorage.getItem('rag-auth-storage');
    if (!raw) return null;
    return JSON.parse(raw)?.state?.token || null;
  } catch {
    return null;
  }
}

const client = axios.create({
  baseURL: API_URL,
  timeout: 120000, // 2 min timeout for long queries
});

// Request interceptor — inject JWT Bearer token on every request
client.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor — normalize error messages
client.interceptors.response.use(
  (res) => res,
  (err) => {
    const status = err.response?.status;
    const detail = err.response?.data?.detail;

    const userMessages = {
      400: detail || 'Invalid request. Check your input.',
      401: detail || 'Session expired. Please log in again.',
      403: 'Access denied.',
      404: 'Document not found. It may have been deleted.',
      413: 'File too large. Maximum upload size is 20MB.',
      422: 'Validation error. Check query length and document ID.',
      429: 'Too many requests. Please wait a moment and try again.',
      500: detail || 'Server error. The AI pipeline encountered a problem.',
      502: detail || 'LLM service error. Please check LLM provider key / quota.',
    };

    err.userMessage = detail || userMessages[status] || 'An unexpected error occurred.';

    // On 401 — clear stale token so the app returns to login screen
    if (status === 401) {
      localStorage.removeItem('rag-auth-storage');
      window.location.reload();
    }

    return Promise.reject(err);
  }
);

// ── SSE Streaming helper ───────────────────────────────────────
export function streamAsk(payload, callbacks) {
  const { onStage, onResult, onError, onDone } = callbacks;
  const ctrl = new AbortController();

  fetch(`${API_URL}/stream-ask`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(getAuthToken() ? { 'Authorization': `Bearer ${getAuthToken()}` } : {}),
    },
    body: JSON.stringify(payload),
    signal: ctrl.signal,
  }).then(async (response) => {
    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Stream failed' }));
      onError?.(err.detail || `HTTP ${response.status}`);
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) { onDone?.(); break; }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('event: ')) {
          // handled in next line
        } else if (line.startsWith('data: ')) {
          const data = line.slice(6).trim();
          if (!data || data === '[DONE]') continue;
          try {
            const parsed = JSON.parse(data);
            // Determine event type from parsed structure
            if ('stage' in parsed) onStage?.(parsed);
            else if ('answer' in parsed) onResult?.(parsed);
            else if ('message' in parsed) onError?.(parsed.message);
          } catch (_) {}
        }
      }
    }
  }).catch((err) => {
    if (err.name !== 'AbortError') {
      onError?.(err.message || 'Connection failed.');
    }
  });

  return () => ctrl.abort(); // Returns cancel function
}

export const api = {
  healthCheck: () => client.get('/health'),
  listDocuments: () => client.get('/documents'),
  uploadDocument: (file) => {
    const fd = new FormData();
    fd.append('file', file);
    return client.post('/upload-doc', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  uploadDocumentOCR: (file) => {
    const fd = new FormData();
    fd.append('file', file);
    return client.post('/upload-doc-ocr', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  deleteDocument: (docId) => client.delete(`/documents/${docId}`),

  askVanilla: (payload) => client.post('/vanilla-ask', payload),
  askAgentic: (payload) => client.post('/ask', payload),
  askDebug: (payload) => client.post('/ask-debug', payload),

  retrieveOnly: (payload) => client.post('/retrieve-only', payload),
  planQuery: (payload) => client.post('/plan', payload),
  rewriteQuery: (payload) => client.post('/rewrite', payload),

  // Observability
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

  // Reasoning
  getReasoningCoT: (sessionId) => client.get(`/reasoning/cot/${sessionId}`),
  getReasoningChain: (sessionId) => client.get(`/reasoning/chain/${sessionId}`),
  getReasoningToT: (sessionId) => client.get(`/reasoning/tot/${sessionId}`),
  getReasoningTree: (sessionId) => client.get(`/reasoning/tree/${sessionId}`),
};