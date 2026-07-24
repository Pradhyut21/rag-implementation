import { useState } from 'react';
import LandingPage from './pages/LandingPage';
import MainApp from './MainApp';

export default function App() {
  const [page, setPage] = useState('landing');

  if (page === 'app') {
    return <MainApp onGoHome={() => setPage('landing')} />;
  }

  return <LandingPage onEnterApp={() => setPage('app')} />;
}