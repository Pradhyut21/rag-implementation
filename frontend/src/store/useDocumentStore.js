/**
 * useDocumentStore.js — Document list and selection state via Zustand.
 *
 * Centralizes all document-related state that was previously scattered
 * across MainApp.jsx as individual useState calls.
 */
import { create } from 'zustand';
import apiClient from '../api/client';

const useDocumentStore = create((set, get) => ({
  documents: [],
  selectedDocId: null,
  isLoading: false,
  uploadProgress: null,
  error: null,

  /**
   * Fetch the list of indexed documents from the backend.
   */
  fetchDocuments: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await apiClient.get('/documents');
      set({ documents: response.data, isLoading: false });
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to fetch documents.';
      set({ error: msg, isLoading: false });
    }
  },

  /**
   * Select a document by its doc_id.
   */
  setSelectedDocId: (docId) => set({ selectedDocId: docId }),

  /**
   * Upload a document file to the backend.
   * @param {File} file - The file object to upload.
   */
  uploadDocument: async (file) => {
    set({ isLoading: true, error: null, uploadProgress: 0 });
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await apiClient.post('/upload-doc', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (evt) => {
          const pct = Math.round((evt.loaded * 100) / evt.total);
          set({ uploadProgress: pct });
        },
      });

      // Refresh document list after upload
      await get().fetchDocuments();
      set({ isLoading: false, uploadProgress: null });
      return response.data;
    } catch (err) {
      const msg = err.response?.data?.detail || 'Upload failed.';
      set({ error: msg, isLoading: false, uploadProgress: null });
      throw err;
    }
  },

  /**
   * Delete a document by doc_id.
   */
  deleteDocument: async (docId) => {
    set({ isLoading: true, error: null });
    try {
      await apiClient.delete(`/documents/${docId}`);
      if (get().selectedDocId === docId) {
        set({ selectedDocId: null });
      }
      await get().fetchDocuments();
      set({ isLoading: false });
    } catch (err) {
      const msg = err.response?.data?.detail || 'Delete failed.';
      set({ error: msg, isLoading: false });
      throw err;
    }
  },

  clearError: () => set({ error: null }),
}));

export default useDocumentStore;
