/**
 * LoginPage.jsx — JWT login form for the Agentic RAG platform.
 *
 * Calls POST /auth/token with username + password (OAuth2 password flow).
 * On success, stores the JWT and redirects to the main app.
 *
 * Demo credentials: admin / demo-rag-2026
 */
import { useState } from 'react';
import useAuthStore from '../store/useAuthStore';

export default function LoginPage({ onLoginSuccess }) {
  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('demo-rag-2026');
  const { login, isLoggingIn, loginError } = useAuthStore();

  const handleSubmit = async (e) => {
    e.preventDefault();
    const ok = await login(username, password);
    if (ok && onLoginSuccess) onLoginSuccess();
  };

  return (
    <div className="login-page">
      <div className="login-card">
        {/* Logo / Brand */}
        <div className="login-brand">
          <div className="login-logo">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path strokeLinecap="round" strokeLinejoin="round"
                d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23-.693L5 14.5m14.8.8l1.402 1.402c1 1 .03 2.798-1.319 2.798H4.117c-1.35 0-2.32-1.798-1.319-2.798L5 14.5" />
            </svg>
          </div>
          <h1>Agentic RAG</h1>
          <p className="login-subtitle">Enterprise AI Document Intelligence</p>
        </div>

        {/* Form */}
        <form className="login-form" onSubmit={handleSubmit}>
          <div className="login-field">
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="admin"
              autoComplete="username"
              required
            />
          </div>

          <div className="login-field">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••"
              autoComplete="current-password"
              required
            />
          </div>

          {loginError && (
            <div className="login-error" role="alert">
              <svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clipRule="evenodd" />
              </svg>
              {loginError}
            </div>
          )}

          <button
            type="submit"
            className="login-btn"
            id="login-submit-btn"
            disabled={isLoggingIn}
          >
            {isLoggingIn ? (
              <>
                <span className="login-spinner" />
                Authenticating…
              </>
            ) : (
              'Sign In'
            )}
          </button>
        </form>

        {/* Demo hint */}
        <div className="login-demo-hint">
          <span className="demo-badge">DEMO</span>
          <span>Pre-filled with demo credentials</span>
        </div>
      </div>
    </div>
  );
}
