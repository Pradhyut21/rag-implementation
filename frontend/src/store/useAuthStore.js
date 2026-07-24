/**
 * useAuthStore.js — Authentication state via Zustand.
 *
 * Stores JWT token and user info.
 * Token is persisted in localStorage so page reloads stay authenticated.
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import apiClient from '../api/client';

const useAuthStore = create(
  persist(
    (set, get) => ({
      token: null,
      user: null,
      isLoggingIn: false,
      loginError: null,

      /**
       * Authenticate with username + password.
       * On success, stores the JWT token and wires it into the axios client.
       */
      login: async (username, password) => {
        set({ isLoggingIn: true, loginError: null });
        try {
          const params = new URLSearchParams();
          params.append('username', username);
          params.append('password', password);

          const response = await apiClient.post('/auth/token', params, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          });

          const { access_token } = response.data;
          // Set default authorization header for all future requests
          apiClient.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
          set({ token: access_token, user: { username }, isLoggingIn: false });
          return true;
        } catch (err) {
          const msg = err.response?.data?.detail || 'Login failed. Check credentials.';
          set({ isLoggingIn: false, loginError: msg });
          return false;
        }
      },

      /**
       * Restore JWT from persisted storage into axios headers on app startup.
       */
      restoreToken: () => {
        const { token } = get();
        if (token) {
          apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        }
      },

      logout: () => {
        delete apiClient.defaults.headers.common['Authorization'];
        set({ token: null, user: null, loginError: null });
      },

      isAuthenticated: () => !!get().token,
    }),
    {
      name: 'rag-auth-storage', // localStorage key
      partialize: (state) => ({ token: state.token, user: state.user }),
    }
  )
);

export default useAuthStore;
