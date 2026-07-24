import { useEffect, useRef, useState } from 'react';
import {
  Brain, Zap, GitBranch, Shield, BarChart3, Search,
  ArrowRight, CheckCircle2, Star, ChevronDown, Layers,
  Database, Lock, Activity, RefreshCw, FileText, Award,
  Cpu, Eye, TrendingUp, Globe, Clock, X
} from 'lucide-react';

/* ── Scroll Reveal Hook ────────────────────────────────────── */
function useScrollReveal() {
  useEffect(() => {
    const els = document.querySelectorAll('.reveal, .reveal-left, .reveal-right');
    const obs = new IntersectionObserver(
      (entries) => entries.forEach(e => { if (e.isIntersecting) e.target.classList.add('visible'); }),
      { threshold: 0.12 }
    );
    els.forEach(el => obs.observe(el));
    return () => obs.disconnect();
  }, []);
}

/* ── 3D Floating Node ──────────────────────────────────────── */
function FloatingNode({ icon: Icon, label, color, className, delay = 0 }) {
  return (
    <div
      className={`absolute flex flex-col items-center gap-1.5 ${className}`}
      style={{ animationDelay: `${delay}s` }}
    >
      <div className={`w-12 h-12 rounded-2xl flex items-center justify-center shadow-float glass-white ${color} card-3d`}
        style={{ border: '1.5px solid rgba(255,255,255,0.8)' }}>
        <Icon size={22} />
      </div>
      <span className="text-[10px] font-semibold text-text-secondary bg-white/90 px-2 py-0.5 rounded-full shadow-soft border border-border">
        {label}
      </span>
    </div>
  );
}

/* ── Pipeline Step ─────────────────────────────────────────── */
function PipelineStep({ number, title, desc, icon: Icon, active }) {
  return (
    <div className={`flex items-start gap-4 p-5 rounded-2xl transition-all duration-300 ${
      active ? 'bg-brand-50 border-2 border-brand/20' : 'bg-bg-secondary border border-border hover:bg-bg-tertiary'
    }`}>
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 font-bold text-sm ${
        active ? 'bg-brand text-white shadow-brand' : 'bg-white border border-border text-text-secondary'
      }`}>
        {number}
      </div>
      <div>
        <h4 className="font-semibold text-text-primary text-sm mb-0.5">{title}</h4>
        <p className="text-xs text-text-secondary leading-relaxed">{desc}</p>
      </div>
    </div>
  );
}

/* ── Feature Card ──────────────────────────────────────────── */
function FeatureCard({ icon: Icon, title, desc, tag, gradient, delay = 0 }) {
  const [hovered, setHovered] = useState(false);
  const cardRef = useRef(null);

  const handleMouseMove = (e) => {
    const card = cardRef.current;
    if (!card) return;
    const rect = card.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    card.style.transform = `perspective(1000px) rotateY(${x * 12}deg) rotateX(${-y * 12}deg) translateZ(10px)`;
  };

  const handleMouseLeave = () => {
    if (cardRef.current) {
      cardRef.current.style.transform = 'perspective(1000px) rotateY(0deg) rotateX(0deg) translateZ(0px)';
    }
    setHovered(false);
  };

  return (
    <div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={handleMouseLeave}
      className="reveal bg-white rounded-2xl p-6 border border-border shadow-soft hover:shadow-card-hover transition-shadow duration-300 cursor-default"
      style={{ transitionDelay: `${delay}ms`, transformStyle: 'preserve-3d', transition: 'transform 0.15s ease, box-shadow 0.3s ease' }}
    >
      <div className={`w-12 h-12 rounded-2xl mb-4 flex items-center justify-center ${gradient}`}>
        <Icon size={22} className="text-white" />
      </div>
      {tag && (
        <span className="inline-block text-[10px] font-bold uppercase tracking-wider text-brand bg-brand-100 px-2.5 py-1 rounded-full mb-3">
          {tag}
        </span>
      )}
      <h3 className="font-bold text-text-primary text-base mb-2">{title}</h3>
      <p className="text-sm text-text-secondary leading-relaxed">{desc}</p>
    </div>
  );
}

/* ── Stat Card ─────────────────────────────────────────────── */
function StatCard({ value, label, icon: Icon, color }) {
  const [count, setCount] = useState(0);
  const ref = useRef(null);
  const end = parseInt(value.replace(/\D/g, '')) || 0;

  useEffect(() => {
    const obs = new IntersectionObserver(([e]) => {
      if (e.isIntersecting) {
        let start = 0;
        const step = end / 40;
        const t = setInterval(() => {
          start = Math.min(start + step, end);
          setCount(Math.floor(start));
          if (start >= end) clearInterval(t);
        }, 40);
        obs.disconnect();
      }
    }, { threshold: 0.5 });
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, [end]);

  const displayValue = value.replace(/\d+/, count.toString());

  return (
    <div ref={ref} className="reveal text-center p-6 bg-white rounded-2xl border border-border shadow-soft">
      <div className={`w-12 h-12 rounded-2xl mx-auto mb-3 flex items-center justify-center ${color}`}>
        <Icon size={22} className="text-white" />
      </div>
      <div className="text-3xl font-black text-text-primary mb-1">{displayValue}</div>
      <div className="text-sm text-text-secondary">{label}</div>
    </div>
  );
}

/* ── Hackathon Score Banner ─────────────────────────────────── */
function ScoreBanner({ onClose }) {
  return (
    <div className="fixed top-4 right-4 z-50 max-w-sm animate-slide-in-right">
      <div className="bg-white rounded-2xl shadow-float border border-border p-4">
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex items-center gap-2">
            <Award size={18} className="text-brand" />
            <span className="font-bold text-sm text-text-primary">Hackathon Report</span>
          </div>
          <button onClick={onClose} className="text-text-muted hover:text-text-primary">
            <X size={14} />
          </button>
        </div>
        <div className="space-y-2 text-xs text-text-secondary">
          <div className="flex items-center gap-2">
            <div className="w-full bg-bg-tertiary rounded-full h-2">
              <div className="bg-gradient-to-r from-brand to-accent-blue h-2 rounded-full" style={{ width: '45%' }} />
            </div>
            <span className="font-bold text-brand whitespace-nowrap">45%</span>
          </div>
          <p className="text-text-muted">Track: AI Engineer — Self-Correcting RAG Pipeline</p>
          <div className="flex flex-wrap gap-1 mt-2">
            {['JWT Auth', 'PostgreSQL', 'OCR Ingestion', '15-query Eval'].map(gap => (
              <span key={gap} className="px-2 py-0.5 bg-red-50 border border-red-100 text-red-600 rounded-full text-[10px] font-medium">
                + {gap}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ── MAIN LANDING PAGE ─────────────────────────────────────── */
export default function LandingPage({ onEnterApp }) {
  const [activeStep, setActiveStep] = useState(0);
  const [showBanner, setShowBanner] = useState(true);
  useScrollReveal();

  // Auto-cycle pipeline steps
  useEffect(() => {
    const t = setInterval(() => setActiveStep(s => (s + 1) % 5), 2000);
    return () => clearInterval(t);
  }, []);

  const steps = [
    { title: 'Planner Agent', desc: 'Decomposes query into 2-5 targeted sub-questions via LLM structured output', icon: Brain },
    { title: 'Query Rewriter', desc: 'Translates raw questions into dense-retrieval-optimized semantic search queries', icon: Search },
    { title: 'FAISS Fanout', desc: 'Concurrent vector search across all-MiniLM-L6-v2 embeddings with deduplication', icon: Database },
    { title: 'Sufficient Context Agent', desc: '3-state audit: explicit / partial / missing — triggers feedback loop if insufficient', icon: Eye },
    { title: 'Synthesis Agent', desc: 'Zero-hallucination contract — answers only from verified, cited context', icon: Zap },
  ];

  const features = [
    { icon: RefreshCw, title: 'Self-Correcting Feedback Loop', desc: 'Up to 2 adaptive iterations. Detects explicit vs. partial vs. missing evidence. Rewriters re-target gaps before re-retrieval.', tag: 'Core Feature', gradient: 'bg-gradient-to-br from-violet-500 to-purple-600', delay: 0 },
    { icon: GitBranch, title: 'Tree of Thought (ToT)', desc: '3 parallel strategy branches scored on 5 metrics: coverage, completeness, evidence quality, confidence, retrieval similarity.', tag: 'Advanced', gradient: 'bg-gradient-to-br from-blue-500 to-indigo-600', delay: 100 },
    { icon: Layers, title: 'Chain of Thought (CoT)', desc: '6-stage linear reasoning pipeline: Understand → Identify → Plan → Retrieve → Evaluate → Synthesize. Every stage timed & logged.', tag: 'Advanced', gradient: 'bg-gradient-to-br from-emerald-500 to-teal-600', delay: 200 },
    { icon: Activity, title: 'Full Observability Stack', desc: 'SQLite telemetry with 10 tables. Monkey-patched LLM spans. Per-agent latency, token cost, and evidence type attribution.', tag: 'Production', gradient: 'bg-gradient-to-br from-amber-500 to-orange-600', delay: 300 },
    { icon: Shield, title: 'Zero-Hallucination Contract', desc: 'Synthesis agent explicitly instructed to refuse generating facts not present in verified context. Fallback states missing info clearly.', tag: 'Safety', gradient: 'bg-gradient-to-br from-rose-500 to-pink-600', delay: 400 },
    { icon: BarChart3, title: 'A/B Version Testing', desc: '6 SQL metrics for comparing knowledge base versions: sufficiency rate, iterations, FAISS score, evidence type, cost, ToT score.', tag: 'Ops', gradient: 'bg-gradient-to-br from-cyan-500 to-blue-600', delay: 500 },
  ];

  const stats = [
    { value: '19 APIs', label: 'REST Endpoints', icon: Globe, color: 'bg-gradient-to-br from-violet-500 to-purple-600' },
    { value: '10 Tables', label: 'SQLite Telemetry', icon: Database, color: 'bg-gradient-to-br from-blue-500 to-indigo-600' },
    { value: '3 Modes', label: 'Reasoning Modes', icon: Brain, color: 'bg-gradient-to-br from-emerald-500 to-teal-600' },
    { value: '60% Cost', label: 'Saved with Routing', icon: TrendingUp, color: 'bg-gradient-to-br from-amber-500 to-orange-600' },
  ];

  const gaps = [
    { issue: 'JWT / OAuth2 Authentication', status: 'roadmap', priority: 'High' },
    { issue: 'PostgreSQL (stateless) migration', status: 'roadmap', priority: 'High' },
    { issue: 'OCR ingestion (Tesseract / Unstructured)', status: 'roadmap', priority: 'Medium' },
    { issue: '15-query evaluation harness', status: 'roadmap', priority: 'Medium' },
    { issue: 'CRISPE prompt framework docs', status: 'roadmap', priority: 'Medium' },
    { issue: 'Rate limiting & encrypted PII', status: 'roadmap', priority: 'High' },
  ];

  return (
    <div className="min-h-screen bg-white text-text-primary overflow-x-hidden">

      {showBanner && <ScoreBanner onClose={() => setShowBanner(false)} />}

      {/* ── NAV ── */}
      <nav className="fixed top-0 left-0 right-0 z-40 glass-white border-b border-border">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-brand to-accent-blue flex items-center justify-center shadow-brand">
              <Brain size={16} className="text-white" />
            </div>
            <span className="font-bold text-text-primary">Agentic RAG</span>
            <span className="text-[10px] font-bold uppercase tracking-wider text-brand bg-brand-100 px-2 py-0.5 rounded-full">v3.0</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm text-text-secondary">
            <a href="#architecture" className="hover:text-brand transition-colors">Architecture</a>
            <a href="#features" className="hover:text-brand transition-colors">Features</a>
            <a href="#observability" className="hover:text-brand transition-colors">Observability</a>
            <a href="#roadmap" className="hover:text-brand transition-colors">Roadmap</a>
          </div>
          <button
            onClick={onEnterApp}
            className="btn-brand px-5 py-2.5 rounded-xl text-sm font-semibold flex items-center gap-2 shadow-brand"
          >
            Launch App <ArrowRight size={14} />
          </button>
        </div>
      </nav>

      {/* ── HERO ── */}
      <section className="relative pt-32 pb-24 overflow-hidden">
        {/* Background mesh */}
        <div className="absolute inset-0 gradient-mesh pointer-events-none" style={{
          background: 'radial-gradient(at 30% 20%, rgba(124,58,237,0.08) 0%, transparent 60%), radial-gradient(at 80% 80%, rgba(37,99,235,0.06) 0%, transparent 50%), radial-gradient(at 60% 50%, rgba(124,58,237,0.04) 0%, transparent 40%)'
        }} />
        <div className="absolute inset-0 dot-pattern opacity-50 pointer-events-none" />

        <div className="max-w-7xl mx-auto px-6 relative z-10">
          <div className="grid lg:grid-cols-2 gap-16 items-center">

            {/* Left – Text */}
            <div>
              <div className="inline-flex items-center gap-2 bg-brand-50 border border-brand/20 rounded-full px-4 py-2 text-sm text-brand font-medium mb-8 animate-fade-in">
                <Star size={14} className="fill-brand" />
                Hackathon Submission — AI Engineer Track
              </div>

              <h1 className="text-5xl lg:text-6xl font-black leading-tight mb-6 animate-slide-up" style={{ animationDelay: '0.1s' }}>
                Self-Correcting
                <br />
                <span className="text-brand-gradient">Agentic RAG</span>
                <br />
                Pipeline
              </h1>

              <p className="text-lg text-text-secondary leading-relaxed mb-8 max-w-xl animate-slide-up" style={{ animationDelay: '0.2s' }}>
                Enterprise-grade multi-agent pipeline with active feedback loops, zero-hallucination synthesis, Tree of Thought reasoning, and full observability telemetry — powered by Groq LPU + FAISS.
              </p>

              <div className="flex flex-col sm:flex-row gap-4 animate-slide-up" style={{ animationDelay: '0.3s' }}>
                <button
                  onClick={onEnterApp}
                  className="btn-brand px-8 py-4 rounded-2xl text-base font-bold flex items-center justify-center gap-3 shadow-brand-lg"
                >
                  <Brain size={18} />
                  Launch Platform
                  <ArrowRight size={16} />
                </button>
                <a href="#architecture"
                  className="px-8 py-4 rounded-2xl text-base font-semibold border border-border hover:border-brand/40 hover:bg-brand-50 text-text-secondary hover:text-brand transition-all flex items-center justify-center gap-2">
                  <ChevronDown size={16} />
                  Explore Architecture
                </a>
              </div>

              {/* Tech stack badges */}
              <div className="flex flex-wrap gap-2 mt-8 animate-fade-in" style={{ animationDelay: '0.5s' }}>
                {['Groq LPU', 'llama-3.3-70b', 'FAISS', 'FastAPI', 'React', 'SQLite Telemetry', 'all-MiniLM-L6-v2'].map(t => (
                  <span key={t} className="px-3 py-1.5 bg-bg-secondary border border-border rounded-full text-xs font-medium text-text-secondary">
                    {t}
                  </span>
                ))}
              </div>
            </div>

            {/* Right – 3D Floating UI Preview */}
            <div className="relative h-[520px] perspective-1200 hidden lg:block">
              {/* Central brain orbit */}
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                {/* Core node */}
                <div className="relative w-32 h-32 float-b">
                  <div className="absolute inset-0 morph-blob bg-gradient-to-br from-brand to-accent-blue opacity-20" />
                  <div className="absolute inset-4 rounded-3xl bg-gradient-to-br from-brand to-accent-blue shadow-brand-lg flex items-center justify-center">
                    <Brain size={36} className="text-white" />
                  </div>
                  {/* Pulse rings */}
                  <div className="absolute inset-0 rounded-full border-2 border-brand/20 animate-ping" style={{ animationDuration: '2s' }} />
                  <div className="absolute -inset-4 rounded-full border border-brand/10 animate-ping" style={{ animationDuration: '3s' }} />
                </div>

                {/* Orbiting nodes */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                  <div className="orbit-1 absolute">
                    <div className="w-10 h-10 rounded-xl bg-white shadow-card border border-border flex items-center justify-center">
                      <Search size={16} className="text-brand" />
                    </div>
                  </div>
                  <div className="orbit-2 absolute">
                    <div className="w-9 h-9 rounded-xl bg-white shadow-card border border-border flex items-center justify-center">
                      <Database size={14} className="text-accent-blue" />
                    </div>
                  </div>
                  <div className="orbit-3 absolute">
                    <div className="w-8 h-8 rounded-xl bg-white shadow-card border border-border flex items-center justify-center">
                      <Zap size={13} className="text-amber-500" />
                    </div>
                  </div>
                </div>
              </div>

              {/* Floating cards */}
              <div className="absolute top-8 left-8 float-a">
                <div className="bg-white rounded-2xl shadow-card border border-border p-4 w-48 card-3d">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-2 h-2 rounded-full bg-emerald-400" />
                    <span className="text-xs font-bold text-text-primary">Context: Sufficient</span>
                  </div>
                  <div className="text-[10px] text-text-secondary">Evidence: explicit</div>
                  <div className="mt-2 h-1.5 bg-emerald-100 rounded-full">
                    <div className="h-full bg-emerald-400 rounded-full" style={{ width: '84%' }} />
                  </div>
                  <div className="text-[10px] text-emerald-600 mt-0.5 font-medium">84% sufficiency</div>
                </div>
              </div>

              <div className="absolute top-12 right-4 float-c" style={{ animationDelay: '1s' }}>
                <div className="bg-white rounded-2xl shadow-card border border-border p-4 w-44 card-3d">
                  <div className="text-[10px] font-bold text-text-muted mb-2 uppercase tracking-wide">Iterations</div>
                  <div className="text-2xl font-black text-brand">2</div>
                  <div className="text-[10px] text-text-secondary">feedback loops</div>
                  <div className="flex gap-1 mt-2">
                    <div className="h-6 w-4 bg-amber-200 rounded" />
                    <div className="h-8 w-4 bg-brand/20 rounded" />
                  </div>
                </div>
              </div>

              <div className="absolute bottom-16 left-4 float-b" style={{ animationDelay: '2s' }}>
                <div className="bg-white rounded-2xl shadow-card border border-border p-4 w-52 card-3d">
                  <div className="flex items-center gap-2 mb-3">
                    <GitBranch size={14} className="text-brand" />
                    <span className="text-xs font-bold text-text-primary">ToT Branches</span>
                  </div>
                  {['Architecture', 'Component', 'Evidence'].map((b, i) => (
                    <div key={b} className="flex items-center gap-2 mb-1.5">
                      <div className="flex-1 h-1.5 bg-bg-tertiary rounded-full">
                        <div className={`h-full rounded-full ${i === 1 ? 'bg-emerald-400' : 'bg-brand/30'}`}
                          style={{ width: `${[65, 84, 71][i]}%` }} />
                      </div>
                      <span className="text-[10px] font-mono text-text-muted">{[0.65, 0.84, 0.71][i]}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="absolute bottom-8 right-8 float-a" style={{ animationDelay: '0.5s' }}>
                <div className="bg-gradient-to-br from-brand to-accent-blue rounded-2xl shadow-brand-lg p-4 w-40 card-3d text-white">
                  <Clock size={16} className="mb-2 opacity-80" />
                  <div className="text-[10px] opacity-70 mb-0.5">Latency</div>
                  <div className="text-xl font-black">1.4s</div>
                  <div className="text-[10px] opacity-70">Groq LPU</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Scroll indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
          <ChevronDown size={24} className="text-text-muted" />
        </div>
      </section>

      {/* ── STATS ── */}
      <section className="py-16 bg-bg-secondary border-y border-border">
        <div className="max-w-5xl mx-auto px-6 grid grid-cols-2 md:grid-cols-4 gap-4">
          {stats.map((s, i) => <StatCard key={i} {...s} />)}
        </div>
      </section>

      {/* ── ARCHITECTURE / PIPELINE ── */}
      <section id="architecture" className="py-24 max-w-7xl mx-auto px-6">
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 bg-brand-50 border border-brand/20 rounded-full px-4 py-2 text-sm text-brand font-medium mb-5 reveal">
            <Layers size={14} />
            5-Phase Agentic Pipeline
          </div>
          <h2 className="text-4xl font-black text-text-primary mb-4 reveal">
            Cognitive RAG Architecture
          </h2>
          <p className="text-lg text-text-secondary max-w-2xl mx-auto reveal">
            Instead of a single forward pass, the pipeline actively evaluates context quality and triggers targeted re-retrieval when information is incomplete.
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-12 items-start">
          {/* Pipeline steps */}
          <div className="space-y-3 reveal-left">
            {steps.map((step, i) => (
              <PipelineStep
                key={i}
                number={i + 1}
                title={step.title}
                desc={step.desc}
                icon={step.icon}
                active={activeStep === i}
              />
            ))}
          </div>

          {/* Flow diagram (SVG-based) */}
          <div className="reveal-right">
            <div className="bg-bg-secondary rounded-3xl border border-border p-8">
              <div className="flex flex-col items-center gap-2">
                {[
                  { label: 'User Query', color: 'bg-text-primary text-white', width: 'w-40' },
                  null, // arrow
                  { label: 'Planner Agent', color: 'bg-brand text-white', width: 'w-48' },
                  null,
                  { label: 'Query Rewriter', color: 'bg-accent-blue text-white', width: 'w-48' },
                  null,
                  { label: 'FAISS Fanout', color: 'bg-emerald-600 text-white', width: 'w-48' },
                  null,
                  { label: 'Sufficient Context Agent', color: 'bg-amber-500 text-white', width: 'w-56', special: true },
                ].map((item, i) => {
                  if (!item) return (
                    <div key={i} className="flex items-center gap-2">
                      <div className="h-6 w-px bg-border" />
                      <ArrowRight size={12} className="text-text-muted -rotate-90" />
                      <div className="h-6 w-px bg-border opacity-0" />
                    </div>
                  );
                  return (
                    <div key={i} className={`${item.width} ${item.color} rounded-xl px-4 py-3 text-xs font-bold text-center shadow-soft`}>
                      {item.label}
                      {item.special && (
                        <div className="mt-1.5 flex justify-center gap-2">
                          <span className="px-2 py-0.5 bg-white/20 rounded text-[9px]">explicit ✓</span>
                          <span className="px-2 py-0.5 bg-white/20 rounded text-[9px]">partial ↻</span>
                          <span className="px-2 py-0.5 bg-white/20 rounded text-[9px]">missing ✕</span>
                        </div>
                      )}
                    </div>
                  );
                })}

                {/* Fork */}
                <div className="flex items-start gap-4 mt-2 w-full justify-center">
                  <div className="flex flex-col items-center gap-2">
                    <div className="h-4 w-px bg-border" />
                    <div className="bg-rose-500 text-white rounded-xl px-4 py-2 text-xs font-bold text-center">
                      Feedback Loop ↻
                    </div>
                  </div>
                  <div className="flex flex-col items-center gap-2">
                    <div className="h-4 w-px bg-border" />
                    <div className="bg-emerald-500 text-white rounded-xl px-4 py-2 text-xs font-bold text-center">
                      Synthesis Agent ✓
                    </div>
                  </div>
                </div>
              </div>

              {/* Legend */}
              <div className="mt-6 pt-4 border-t border-border flex flex-wrap gap-3 justify-center text-[10px] text-text-muted">
                <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-rose-400" /> Feedback (max 2×)</span>
                <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-emerald-400" /> Synthesis gate</span>
                <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-amber-400" /> Evidence audit</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── FEATURES ── */}
      <section id="features" className="py-24 bg-bg-secondary border-y border-border">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-black text-text-primary mb-4 reveal">
              Enterprise-Grade Capabilities
            </h2>
            <p className="text-lg text-text-secondary max-w-2xl mx-auto reveal">
              Three reasoning modes, full observability, and a self-correcting feedback architecture built for production environments.
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f, i) => <FeatureCard key={i} {...f} />)}
          </div>
        </div>
      </section>

      {/* ── OBSERVABILITY ── */}
      <section id="observability" className="py-24 max-w-7xl mx-auto px-6">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          <div>
            <div className="inline-flex items-center gap-2 bg-amber-50 border border-amber-200 rounded-full px-4 py-2 text-sm text-amber-700 font-medium mb-6 reveal">
              <Activity size={14} />
              Full-Stack Telemetry
            </div>
            <h2 className="text-4xl font-black text-text-primary mb-5 reveal">
              Zero-Overhead<br />Observability
            </h2>
            <p className="text-text-secondary leading-relaxed mb-8 reveal">
              Monkey-patched instrumentation wraps every agent function without touching business logic. Every LLM call, retrieval, and context evaluation is logged to a 10-table SQLite schema.
            </p>
            <div className="grid grid-cols-2 gap-4 reveal">
              {[
                { icon: Cpu, label: 'Per-agent latency', color: 'text-brand' },
                { icon: BarChart3, label: 'Token + cost tracking', color: 'text-accent-blue' },
                { icon: Eye, label: 'Evidence type audit', color: 'text-emerald-600' },
                { icon: Clock, label: 'P50/P95/P99 latency', color: 'text-amber-600' },
                { icon: Database, label: '10 SQLite tables', color: 'text-rose-500' },
                { icon: Activity, label: 'Session replay', color: 'text-violet-600' },
              ].map((item, i) => (
                <div key={i} className="flex items-center gap-3 p-3 bg-bg-secondary rounded-xl border border-border">
                  <item.icon size={16} className={item.color} />
                  <span className="text-sm font-medium text-text-secondary">{item.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* DB schema preview */}
          <div className="reveal-right">
            <div className="bg-white rounded-3xl border border-border shadow-card overflow-hidden card-3d">
              <div className="bg-gradient-to-r from-brand to-accent-blue px-6 py-4 flex items-center gap-3">
                <Database size={16} className="text-white/80" />
                <span className="text-white font-bold text-sm">observability.db — Schema</span>
              </div>
              <div className="p-5 space-y-2 font-mono text-xs">
                {[
                  { table: 'sessions', cols: 'session_id, query, answer, status, latency, tokens, cost' },
                  { table: 'spans', cols: 'span_id, name, inputs, outputs, latency, iteration' },
                  { table: 'events', cols: 'event_id, name, extra_data, timestamp' },
                  { table: 'errors', cols: 'error_id, error_type, stack_trace, retry_count' },
                  { table: 'reasoning_chains', cols: 'session_id, stages → 6 CoT stages' },
                  { table: 'reasoning_trees', cols: 'session_id, branches → 3 ToT paths' },
                  { table: 'branch_scores', cols: 'coverage, completeness, evidence_quality...' },
                  { table: 'winning_branches', cols: 'branch_id, score → selected strategy' },
                ].map((row, i) => (
                  <div key={i} className="flex flex-col p-2.5 hover:bg-bg-secondary rounded-lg transition-colors group">
                    <span className="text-brand font-bold">{row.table}</span>
                    <span className="text-text-muted text-[10px] group-hover:text-text-secondary transition-colors truncate">{row.cols}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── HACKATHON ROADMAP (addressing judge gaps) ── */}
      <section id="roadmap" className="py-24 bg-bg-secondary border-y border-border">
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-12">
            <div className="inline-flex items-center gap-2 bg-red-50 border border-red-200 rounded-full px-4 py-2 text-sm text-red-600 font-medium mb-5 reveal">
              <Award size={14} />
              Hackathon Feedback — 45% Score
            </div>
            <h2 className="text-4xl font-black text-text-primary mb-4 reveal">
              Identified Gaps &amp; Roadmap
            </h2>
            <p className="text-text-secondary max-w-xl mx-auto reveal">
              The judges identified 6 critical gaps. These are prioritized in the v3.1 roadmap.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            {gaps.map((gap, i) => (
              <div key={i} className="reveal flex items-start gap-4 p-5 bg-white rounded-2xl border border-border shadow-soft"
                style={{ animationDelay: `${i * 80}ms` }}>
                <div className={`flex-shrink-0 px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                  gap.priority === 'High'
                    ? 'bg-red-50 border border-red-200 text-red-600'
                    : 'bg-amber-50 border border-amber-200 text-amber-700'
                }`}>
                  {gap.priority}
                </div>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-text-primary">{gap.issue}</p>
                  <span className="text-[10px] text-text-muted uppercase tracking-wider">v3.1 roadmap</span>
                </div>
                <ArrowRight size={14} className="text-text-muted flex-shrink-0 mt-1" />
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="py-28 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <div className="relative inline-block mb-8 reveal">
            <div className="w-24 h-24 rounded-3xl bg-gradient-to-br from-brand to-accent-blue mx-auto flex items-center justify-center shadow-brand-lg float-b">
              <Brain size={40} className="text-white" />
            </div>
            <div className="absolute -top-2 -right-2 w-8 h-8 rounded-full bg-emerald-400 border-4 border-white flex items-center justify-center">
              <CheckCircle2 size={14} className="text-white" />
            </div>
          </div>

          <h2 className="text-5xl font-black text-text-primary mb-5 reveal">
            Try It Live
          </h2>
          <p className="text-xl text-text-secondary mb-10 reveal">
            Upload a PDF or DOCX and watch the self-correcting agentic pipeline reason in real time.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center reveal">
            <button
              onClick={onEnterApp}
              className="btn-brand px-10 py-5 rounded-2xl text-lg font-bold flex items-center justify-center gap-3 shadow-brand-lg"
            >
              <Brain size={20} />
              Launch Platform
              <ArrowRight size={18} />
            </button>
          </div>

          <div className="mt-12 flex flex-wrap justify-center gap-4 text-sm text-text-muted reveal">
            {[
              { icon: Zap, label: 'Groq LPU — sub-2s' },
              { icon: Shield, label: 'Zero hallucination' },
              { icon: Activity, label: 'Full telemetry' },
              { icon: FileText, label: 'PDF + DOCX' },
            ].map((item, i) => (
              <span key={i} className="flex items-center gap-2">
                <item.icon size={14} className="text-brand" />
                {item.label}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer className="border-t border-border py-8 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-text-muted">
          <div className="flex items-center gap-2">
            <Brain size={16} className="text-brand" />
            <span className="font-semibold text-text-secondary">Agentic RAG Platform</span>
            <span className="text-brand font-bold">v3.0</span>
          </div>
          <div className="flex items-center gap-6">
            <span>19 REST Endpoints</span>
            <span>·</span>
            <span>Groq LPU + FAISS</span>
            <span>·</span>
            <span>CoT · ToT · Standard</span>
          </div>
          <span>Hackathon — July 2026</span>
        </div>
      </footer>
    </div>
  );
}
