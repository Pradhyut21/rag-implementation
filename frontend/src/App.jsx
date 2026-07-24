import { useEffect, useState } from 'react';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import MainApp from './MainApp';
import useAuthStore from './store/useAuthStore';

export default function App() {
  const [page, setPage] = useState('landing');
  const { isAuthenticated, restoreToken } = useAuthStore();

  // On mount, restore JWT from localStorage into axios headers
  useEffect(() => {
    restoreToken();
  }, [restoreToken]);

  // Not authenticated → show login gate
  if (!isAuthenticated()) {
    return <LoginPage onLoginSuccess={() => setPage('landing')} />;
  }

  if (page === 'app') {
    return <MainApp onGoHome={() => setPage('landing')} />;
  }

  return <LandingPage onEnterApp={() => setPage('app')} />;
}