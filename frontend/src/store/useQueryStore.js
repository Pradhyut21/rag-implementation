/**
 * useQueryStore.js — Query submission and result state via Zustand.
 *
 * Centralizes query execution, streaming SSE progress, result history,
 * and reasoning mode selection that was previously spread across MainApp.jsx.
 */
import { create } from 'zustand';
import apiClient from '../api/client';

const MAX_HISTORY = 20;

const useQueryStore = create((set, get) => ({
  // Current query state
  query: '',
  reasoningMode: 'standard',
  topK: 3,
  isQuerying: false,
  streamingStages: [],

  // Results
  queryResult: null,
  error: null,

  // Query history (last N queries)
  queryHistory: [],

  setQuery: (q) => set({ query: q }),
  setReasoningMode: (mode) => set({ reasoningMode: mode }),
  setTopK: (k) => set({ topK: k }),

  /**
   * Submit a query to the /stream-ask endpoint and accumulate SSE stage events.
   * Falls back to /ask for non-streaming if EventSource fails.
   *
   * @param {string} docId - The document ID to query against.
   */
  submitQuery: async (docId) => {
    const { query, reasoningMode, topK } = get();
    if (!query.trim() || !docId) return;

    set({ isQuerying: true, error: null, streamingStages: [], queryResult: null });

    try {
      const response = await apiClient.post('/ask', {
        query,
        doc_id: docId,
        top_k: topK,
        reasoning_mode: reasoningMode,
        include_trace: true,
      });

      const result = response.data;
      set({
        queryResult: result,
        isQuerying: false,
        queryHistory: [
          { query, result, timestamp: new Date().toISOString() },
          ...get().queryHistory,
        ].slice(0, MAX_HISTORY),
      });
    } catch (err) {
      const msg = err.response?.data?.detail || 'Query failed. Please try again.';
      set({ error: msg, isQuerying: false });
    }
  },

  /**
   * Add a streaming stage update (from SSE).
   */
  addStreamingStage: (stage) =>
    set((state) => ({
      streamingStages: [...state.streamingStages, stage],
    })),

  clearResult: () => set({ queryResult: null, streamingStages: [], error: null }),
  clearError: () => set({ error: null }),
}));

export default useQueryStore;
