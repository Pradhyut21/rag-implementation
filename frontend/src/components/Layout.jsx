import { Brain, Zap, Activity } from 'lucide-react';

export default function Layout({ children }) {
  return (
    <div className="font-sans antialiased h-screen flex flex-col bg-dark overflow-hidden relative">
      {/* Ambient background effects */}
      <div className="absolute inset-0 grid-bg pointer-events-none" />
      <div className="absolute inset-0 pointer-events-none" style={{
        background: 'radial-gradient(ellipse at 20% 0%, rgba(59,130,246,0.07) 0%, transparent 50%), radial-gradient(ellipse at 80% 0%, rgba(139,92,246,0.07) 0%, transparent 50%)'
      }} />

      {/* Top navbar */}
      <header className="relative z-20 flex-shrink-0 flex items-center justify-between px-6 py-3 border-b border-border bg-panel/60 backdrop-blur-xl">
        <div className="flex items-center gap-3">
          {/* Animated logo */}
          <div className="relative w-8 h-8">
            <div className="absolute inset-0 rounded-lg bg-gradient-to-br from-primary to-accent opacity-20 animate-pulse" />
            <div className="relative w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center">
              <Brain size={16} className="text-white" />
            </div>
          </div>
          <div>
            <h1 className="text-sm font-bold tracking-tight text-white">Agentic RAG</h1>
            <p className="text-[10px] text-gray-500 leading-none">Enterprise AI Platform</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Status indicators */}
          <div className="hidden md:flex items-center gap-4 text-xs text-gray-500">
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>Backend Live</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Zap size={11} className="text-amber-400" />
              <span>Groq LPU</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Activity size={11} className="text-primary" />
              <span>FAISS Index</span>
            </div>
          </div>

          {/* Version badge */}
          <div className="px-2.5 py-1 bg-primary/10 border border-primary/20 rounded-full">
            <span className="text-[10px] font-bold text-primary tracking-wider uppercase">v3.0</span>
          </div>
        </div>
      </header>

      {/* Main content */}
      <div className="flex-1 flex min-h-0 relative z-10">
        {children}
      </div>
    </div>
  );
}