import { useState, useEffect, useRef } from 'react';
import { 
  Activity, Play, Pause, ChevronRight, ChevronLeft, RotateCcw, 
  AlertTriangle, Cpu, Clock, Coins, Search, CheckCircle2, XCircle, 
  BarChart3, Database, History, Layers, ArrowRight, Terminal, RefreshCw
} from 'lucide-react';
import { api } from '../api/client';

export default function ObservabilityWorkspace() {
  const [activeSubTab, setActiveSubTab] = useState('dashboard');
  const [dashboardData, setDashboardData] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [selectedSessionId, setSelectedSessionId] = useState(null);
  const [sessionDetails, setSessionDetails] = useState(null);
  const [traces, setTraces] = useState([]);
  const [events, setEvents] = useState([]);
  const [errorsList, setErrorsList] = useState([]);
  const [metricsData, setMetricsData] = useState(null);
  const [tokenData, setTokenData] = useState(null);
  const [latencyData, setLatencyData] = useState(null);
  const [analyticsData, setAnalyticsData] = useState(null);
  
  // Replay state
  const [replaySessionId, setReplaySessionId] = useState('');
  const [replayData, setReplayData] = useState(null);
  const [replayStep, setReplayStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [replayError, setReplayError] = useState('');
  const playIntervalRef = useRef(null);

  // Search/Filter state for Sessions
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    fetchDataForTab(activeSubTab);
    return () => {
      if (playIntervalRef.current) clearInterval(playIntervalRef.current);
    };
  }, [activeSubTab]);

  const fetchDataForTab = async (tab) => {
    setIsLoading(true);
    try {
      if (tab === 'dashboard') {
        const res = await api.getDashboard();
        setDashboardData(res.data);
      } else if (tab === 'sessions') {
        const res = await api.getSessions();
        setSessions(res.data.sessions || []);
      } else if (tab === 'live-trace') {
        const resTraces = await api.getTraces();
        const resEvents = await api.getEvents();
        setTraces(resTraces.data.traces || []);
        setEvents(resEvents.data.events || []);
      } else if (tab === 'metrics') {
        const res = await api.getMetrics();
        setMetricsData(res);
      } else if (tab === 'latency') {
        const res = await api.getLatency();
        setLatencyData(res.data);
      } else if (tab === 'tokens') {
        const res = await api.getTokens();
        setTokenData(res.data);
      } else if (tab === 'errors') {
        const res = await api.getErrors();
        setErrorsList(res.data.errors || []);
      } else if (tab === 'analytics') {
        const res = await api.getDashboard(); // contains metrics and analytics
        setAnalyticsData(res.data.analytics);
      }
    } catch (err) {
      console.error(`Failed to fetch data for ${tab}`, err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectSession = async (id) => {
    setSelectedSessionId(id);
    try {
      const res = await api.getSessionDetails(id);
      setSessionDetails(res.data);
    } catch (err) {
      console.error("Failed to load session details", err);
    }
  };

  const handleLoadReplay = async (id) => {
    if (!id) return;
    setReplayError('');
    setIsPlaying(false);
    setReplayStep(0);
    try {
      const res = await api.getReplay(id);
      setReplayData(res.data);
      setReplaySessionId(id);
      setActiveSubTab('replay');
    } catch (err) {
      setReplayError('Session not found or failed to load replay data.');
    }
  };

  // Replay loop controls
  useEffect(() => {
    if (isPlaying && replayData && replayData.spans) {
      playIntervalRef.current = setInterval(() => {
        setReplayStep(prev => {
          if (prev >= replayData.spans.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 1500);
    } else {
      if (playIntervalRef.current) clearInterval(playIntervalRef.current);
    }
    return () => {
      if (playIntervalRef.current) clearInterval(playIntervalRef.current);
    };
  }, [isPlaying, replayData]);

  // Formatter helpers
  const formatTime = (isoString) => {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toLocaleTimeString() + `.${String(date.getMilliseconds()).padStart(3, '0')}`;
  };

  const formatDate = (isoString) => {
    if (!isoString) return '';
    return new Date(isoString).toLocaleString();
  };

  // Render Functions for Sub-pages
  const renderDashboard = () => {
    if (!dashboardData) return <div className="text-gray-400">Loading dashboard...</div>;
    const m = dashboardData.metrics || {};
    const a = dashboardData.analytics || {};

    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-bold tracking-tight">Observability Dashboard</h2>
          <button onClick={() => fetchDataForTab('dashboard')} className="flex items-center gap-2 px-3 py-1 bg-panel border border-border rounded text-sm text-gray-300 hover:bg-border transition">
            <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} /> Refresh
          </button>
        </div>

        {/* 4 Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl glass bg-panel/30 border border-border flex items-center gap-4">
            <div className="p-3 rounded-lg bg-blue-500/10 text-blue-400">
              <Activity size={24} />
            </div>
            <div>
              <p className="text-xs text-gray-400 font-medium">Total Requests</p>
              <h3 className="text-2xl font-bold">{m.total_requests || 0}</h3>
              <p className="text-[10px] text-gray-500 mt-1">across all RAG sessions</p>
            </div>
          </div>

          <div className="p-4 rounded-xl glass bg-panel/30 border border-border flex items-center gap-4">
            <div className="p-3 rounded-lg bg-purple-500/10 text-purple-400">
              <Clock size={24} />
            </div>
            <div>
              <p className="text-xs text-gray-400 font-medium">Avg Latency</p>
              <h3 className="text-2xl font-bold">{m.avg_latency || 0}s</h3>
              <p className="text-[10px] text-gray-500 mt-1">end-to-end workflow</p>
            </div>
          </div>

          <div className="p-4 rounded-xl glass bg-panel/30 border border-border flex items-center gap-4">
            <div className="p-3 rounded-lg bg-yellow-500/10 text-yellow-400">
              <Coins size={24} />
            </div>
            <div>
              <p className="text-xs text-gray-400 font-medium">Avg Tokens / Cost</p>
              <h3 className="text-2xl font-bold">{m.avg_tokens ? Math.round(m.avg_tokens) : 0}</h3>
              <p className="text-[10px] text-yellow-500/80 mt-0.5 font-mono">${(m.avg_tokens ? (m.avg_tokens * 0.00000069) : 0).toFixed(5)} / ₹{(m.avg_tokens ? (m.avg_tokens * 0.00000069 * 85) : 0).toFixed(3)} avg</p>
            </div>
          </div>

          <div className="p-4 rounded-xl glass bg-panel/30 border border-border flex items-center gap-4">
            <div className="p-3 rounded-lg bg-green-500/10 text-green-400">
              <CheckCircle2 size={24} />
            </div>
            <div>
              <p className="text-xs text-gray-400 font-medium">Success Rate</p>
              <h3 className="text-2xl font-bold text-green-400">{m.success_rate || 0}%</h3>
              <p className="text-[10px] text-red-400 mt-1">{m.failure_rate || 0}% failures</p>
            </div>
          </div>
        </div>

        {/* Breakdown Panel */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Recent Sessions */}
          <div className="p-6 rounded-xl border border-border glass bg-panel/20">
            <h3 className="text-base font-semibold mb-4 flex items-center gap-2">
              <History size={16} className="text-primary" /> Recent Runs
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-border text-gray-400 font-medium text-xs">
                    <th className="pb-2">Session ID</th>
                    <th className="pb-2">Query</th>
                    <th className="pb-2">Status</th>
                    <th className="pb-2 text-right">Latency</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/40">
                  {dashboardData.recent_sessions?.map(s => (
                    <tr key={s.session_id} className="group hover:bg-panel/50 cursor-pointer transition" onClick={() => { setSelectedSessionId(s.session_id); handleSelectSession(s.session_id); setActiveSubTab('sessions'); }}>
                      <td className="py-2 text-xs font-mono text-gray-400 group-hover:text-primary">{s.session_id.substring(0, 8)}</td>
                      <td className="py-2 truncate max-w-[150px] text-gray-200">{s.query}</td>
                      <td className="py-2">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${s.status === 'SUCCESS' ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'}`}>
                          {s.status}
                        </span>
                      </td>
                      <td className="py-2 text-right text-xs font-mono text-gray-400">{s.total_latency.toFixed(2)}s</td>
                    </tr>
                  ))}
                  {(!dashboardData.recent_sessions || dashboardData.recent_sessions.length === 0) && (
                    <tr>
                      <td colSpan={4} className="py-4 text-center text-gray-500 text-xs">No recent sessions found. Run a query to generate logs.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Quick Analytics Summary */}
          <div className="p-6 rounded-xl border border-border glass bg-panel/20 flex flex-col justify-between">
            <div>
              <h3 className="text-base font-semibold mb-4 flex items-center gap-2">
                <BarChart3 size={16} className="text-accent" /> System Bottlenecks
              </h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-400">Most Active Agent:</span>
                  <span className="font-semibold text-primary">{a.most_active_agent}</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-400">Slowest Agent Component:</span>
                  <span className="font-semibold text-purple-400">{a.slowest_agent}</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-400">Avg Iterations per Workflow:</span>
                  <span className="font-semibold text-yellow-400">{m.avg_iterations}</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-400">Avg Retrieval Duration:</span>
                  <span className="font-mono">{m.avg_retrieval_time}s</span>
                </div>
              </div>
            </div>
            
            <div className="border-t border-border mt-4 pt-4">
              <h4 className="text-xs font-semibold uppercase text-gray-500 tracking-wider mb-2">Longest Session</h4>
              {a.longest_session ? (
                <div className="p-2 rounded bg-panel/40 border border-border/40 text-xs flex justify-between items-center">
                  <div className="truncate max-w-[200px]">
                    <p className="text-gray-300 truncate">"{a.longest_session.query}"</p>
                    <p className="text-[10px] text-gray-500 font-mono mt-0.5">{a.longest_session.session_id.substring(0,8)}</p>
                  </div>
                  <span className="font-mono text-purple-400 font-bold ml-2">{a.longest_session.latency}s</span>
                </div>
              ) : (
                <p className="text-xs text-gray-500">No session metrics logged yet.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderSessions = () => {
    const filteredSessions = sessions.filter(s => {
      const matchSearch = s.session_id.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          (s.query && s.query.toLowerCase().includes(searchQuery.toLowerCase()));
      const matchStatus = statusFilter === 'ALL' || s.status === statusFilter;
      return matchSearch && matchStatus;
    });

    return (
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full items-stretch">
        {/* Left List */}
        <div className="lg:col-span-1 flex flex-col gap-4 border-r border-border/60 pr-6 h-[72vh] overflow-y-auto">
          <div className="space-y-2">
            <h2 className="text-lg font-bold">Execution Sessions</h2>
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 text-gray-500" size={16} />
              <input 
                type="text" 
                placeholder="Search query or ID..." 
                className="w-full pl-9 pr-4 py-1.5 bg-panel border border-border rounded text-sm text-gray-200 focus:outline-none focus:border-primary"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
              />
            </div>
            <div className="flex gap-2 text-xs">
              {['ALL', 'SUCCESS', 'FAILED'].map(st => (
                <button 
                  key={st} 
                  onClick={() => setStatusFilter(st)}
                  className={`px-2 py-0.5 rounded border transition ${statusFilter === st ? 'bg-primary/25 border-primary text-primary' : 'bg-panel border-border text-gray-400 hover:text-gray-200'}`}
                >
                  {st}
                </button>
              ))}
            </div>
          </div>

          <div className="flex-1 space-y-2 overflow-y-auto">
            {filteredSessions.map(s => (
              <div 
                key={s.session_id} 
                onClick={() => handleSelectSession(s.session_id)}
                className={`p-3 rounded-lg border transition cursor-pointer text-left ${selectedSessionId === s.session_id ? 'bg-primary/10 border-primary shadow-lg' : 'bg-panel/40 border-border/80 hover:bg-panel/75'}`}
              >
                <div className="flex justify-between items-start gap-2 mb-1.5">
                  <span className="text-[10px] font-mono text-gray-500 uppercase tracking-tight">{s.session_id.substring(0, 8)}</span>
                  <span className={`px-1.5 py-0.5 rounded text-[8px] font-bold ${s.status === 'SUCCESS' ? 'bg-green-500/15 text-green-400' : 'bg-red-500/15 text-red-400'}`}>
                    {s.status}
                  </span>
                </div>
                <p className="text-xs text-gray-200 line-clamp-2 mb-2 font-medium">"{s.query}"</p>
                <div className="flex justify-between text-[10px] text-gray-400 border-t border-border/20 pt-1.5">
                  <span>{formatTime(s.timestamp)}</span>
                  <span className="font-mono text-gray-300">{s.total_latency.toFixed(2)}s | {s.total_tokens} tokens</span>
                </div>
              </div>
            ))}
            {filteredSessions.length === 0 && (
              <p className="text-xs text-center text-gray-500 py-8">No matching sessions found.</p>
            )}
          </div>
        </div>

        {/* Right Detail Panel */}
        <div className="lg:col-span-2 overflow-y-auto h-[72vh] pl-2">
          {sessionDetails ? (
            <div className="space-y-6 text-left">
              <div className="flex justify-between items-start border-b border-border/60 pb-4">
                <div>
                  <h3 className="text-base font-bold text-gray-100 mb-1">Session Logs & Metadata</h3>
                  <p className="text-xs font-mono text-gray-500">ID: {sessionDetails.session.session_id}</p>
                </div>
                <button 
                  onClick={() => handleLoadReplay(sessionDetails.session.session_id)}
                  className="flex items-center gap-1.5 px-3 py-1 bg-accent/25 hover:bg-accent/40 border border-accent/40 rounded text-xs text-accent font-semibold transition"
                >
                  <Play size={12} fill="currentColor" /> Replay Execution
                </button>
              </div>

              {/* Specs card */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4 p-4 bg-panel/30 border border-border/80 rounded-xl">
                <div>
                  <p className="text-[10px] text-gray-400 uppercase">Duration</p>
                  <p className="text-sm font-semibold font-mono text-purple-400">{sessionDetails.session.total_latency.toFixed(3)}s</p>
                </div>
                <div>
                  <p className="text-[10px] text-gray-400 uppercase">Tokens Used</p>
                  <p className="text-sm font-semibold font-mono text-yellow-400">{sessionDetails.session.total_tokens}</p>
                </div>
                <div>
                  <p className="text-[10px] text-gray-400 uppercase">Est. Cost</p>
                  <p className="text-sm font-semibold font-mono text-green-400">${(sessionDetails.session.estimated_cost || 0).toFixed(5)} / ₹{((sessionDetails.session.estimated_cost || 0) * 85).toFixed(3)}</p>
                </div>
                <div>
                  <p className="text-[10px] text-gray-400 uppercase">RAG Loops</p>
                  <p className="text-sm font-semibold font-mono text-blue-400">{sessionDetails.session.iterations_count}</p>
                </div>
                <div>
                  <p className="text-[10px] text-gray-400 uppercase">Doc ID</p>
                  <p className="text-sm font-semibold font-mono text-gray-300">{sessionDetails.session.doc_id || 'N/A'}</p>
                </div>
              </div>

              {/* Query & Answer */}
              <div className="space-y-4">
                <div>
                  <h4 className="text-xs font-semibold uppercase text-gray-400 mb-1">User Query</h4>
                  <div className="p-3 bg-panel/50 border border-border rounded-lg text-sm text-gray-200">
                    {sessionDetails.session.query}
                  </div>
                </div>

                <div>
                  <h4 className="text-xs font-semibold uppercase text-gray-400 mb-1">Final Answer</h4>
                  <div className="p-4 bg-panel/20 border border-border rounded-lg text-sm text-gray-300 leading-relaxed">
                    {sessionDetails.session.answer || <span className="text-red-400 italic">No output generated (Workflow failed)</span>}
                  </div>
                </div>
              </div>

              {/* Traces Timeline */}
              <div>
                <h4 className="text-xs font-semibold uppercase text-gray-400 mb-3">Agent Execution Timeline</h4>
                <div className="space-y-3 relative before:absolute before:left-3 before:top-2 before:bottom-2 before:w-[2px] before:bg-border/60">
                  {sessionDetails.spans.map((sp, idx) => (
                    <div key={sp.span_id} className="pl-8 relative flex flex-col gap-1">
                      {/* Timeline dot */}
                      <span className={`absolute left-2 top-1.5 w-2 h-2 rounded-full ring-4 ring-dark ${sp.status === 'SUCCESS' ? 'bg-primary' : 'bg-red-500'}`} />
                      
                      <div className="flex justify-between items-start text-xs border-b border-border/20 pb-1">
                        <span className="font-semibold text-gray-200">{sp.name.replace("_", " ").toUpperCase()}</span>
                        <span className="font-mono text-gray-400">{sp.latency.toFixed(3)}s</span>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px] p-2 bg-panel/30 rounded border border-border/40 font-mono text-gray-400">
                        <div>
                          <p className="text-[10px] text-gray-500 font-semibold mb-0.5">INPUTS:</p>
                          <pre className="overflow-x-auto whitespace-pre-wrap max-h-24 bg-dark/30 p-1.5 rounded">{JSON.stringify(sp.inputs, null, 2)}</pre>
                        </div>
                        <div>
                          <p className="text-[10px] text-gray-500 font-semibold mb-0.5">OUTPUTS:</p>
                          <pre className="overflow-x-auto whitespace-pre-wrap max-h-24 bg-dark/30 p-1.5 rounded">{JSON.stringify(sp.outputs, null, 2)}</pre>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Errors Panel */}
              {sessionDetails.errors.length > 0 && (
                <div className="p-4 bg-red-950/20 border border-red-500/30 rounded-lg">
                  <h4 className="text-xs font-semibold uppercase text-red-400 mb-2 flex items-center gap-1.5">
                    <AlertTriangle size={14} /> Exceptions Raised
                  </h4>
                  {sessionDetails.errors.map(err => (
                    <div key={err.error_id} className="text-xs space-y-1">
                      <p className="font-semibold text-red-300">{err.error_type}: {err.message}</p>
                      <pre className="p-2 bg-red-950/40 border border-red-500/20 text-red-200 rounded font-mono text-[10px] overflow-x-auto max-h-48 text-left leading-normal">{err.stack_trace}</pre>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-gray-500">
              <Layers size={40} className="mb-2 text-gray-600" />
              <p className="text-sm">Select a session from the list to view its execution details.</p>
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderLiveTrace = () => {
    return (
      <div className="space-y-6 text-left">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-lg font-bold">Live Execution Trace</h2>
            <p className="text-xs text-gray-500">Visualizing RAG agent steps as they execute chronologically</p>
          </div>
          <button onClick={() => fetchDataForTab('live-trace')} className="flex items-center gap-1 px-3 py-1 bg-panel border border-border rounded text-xs text-gray-300 hover:bg-border transition">
            <RefreshCw size={12} className={isLoading ? 'animate-spin' : ''} /> Refresh Traces
          </button>
        </div>

        <div className="space-y-4">
          {traces.length > 0 ? (
            traces.map((trace, idx) => (
              <div key={trace.span_id} className="p-4 rounded-xl border border-border glass bg-panel/30 space-y-2">
                <div className="flex flex-wrap justify-between items-center gap-2 border-b border-border/40 pb-2">
                  <div className="flex items-center gap-2">
                    <span className={`w-2.5 h-2.5 rounded-full ${trace.status === 'SUCCESS' ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
                    <span className="font-bold text-xs uppercase tracking-wider text-gray-200">{trace.name.replace("_", " ")}</span>
                    <span className="text-[10px] text-gray-400 px-2 py-0.5 rounded bg-panel border border-border/80">Iteration {trace.iteration}</span>
                  </div>
                  <div className="flex items-center gap-4 text-xs font-mono text-gray-400">
                    <span>{formatTime(trace.timestamp)}</span>
                    <span className="text-purple-400 font-bold">{trace.latency.toFixed(3)}s</span>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
                  <div className="p-2 bg-dark/40 border border-border/60 rounded">
                    <p className="text-[10px] text-gray-500 font-semibold mb-1">INPUT PARAMS:</p>
                    <div className="overflow-x-auto whitespace-pre text-gray-300 max-h-32 text-[11px] leading-tight">
                      {JSON.stringify(trace.inputs, null, 2)}
                    </div>
                  </div>
                  <div className="p-2 bg-dark/40 border border-border/60 rounded">
                    <p className="text-[10px] text-gray-500 font-semibold mb-1">OUTPUT DETAILS:</p>
                    <div className="overflow-x-auto whitespace-pre text-gray-300 max-h-32 text-[11px] leading-tight">
                      {JSON.stringify(trace.outputs, null, 2)}
                    </div>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="p-8 border border-dashed border-border rounded-xl text-center text-gray-500 text-sm">
              No trace spans have been logged. Execute a query to view traces in real-time.
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderMetrics = () => {
    if (!metricsData) return <div className="text-gray-400">Loading metrics...</div>;
    const m = metricsData.data || metricsData;

    return (
      <div className="space-y-6 text-left">
        <h2 className="text-lg font-bold">System Performance Metrics</h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Card 1 */}
          <div className="p-6 bg-panel/30 border border-border rounded-xl space-y-2 flex flex-col justify-between">
            <h3 className="text-xs uppercase text-gray-400 font-semibold tracking-wider">Workflow Success Ratio</h3>
            <div className="flex items-center justify-between">
              <span className="text-4xl font-extrabold text-green-400">{m.success_rate}%</span>
              <span className="text-xs text-gray-400">Success</span>
            </div>
            <div className="w-full bg-border rounded-full h-2.5 overflow-hidden">
              <div className="bg-green-400 h-2.5 rounded-full" style={{ width: `${m.success_rate}%` }}></div>
            </div>
            <p className="text-[10px] text-gray-500 mt-2">Failure rate: {m.failure_rate}% | Total runs: {m.total_requests}</p>
          </div>

          {/* Card 2 */}
          <div className="p-6 bg-panel/30 border border-border rounded-xl space-y-2 flex flex-col justify-between">
            <h3 className="text-xs uppercase text-gray-400 font-semibold tracking-wider">Retry & Pipeline Recoveries</h3>
            <div className="flex items-center justify-between">
              <span className="text-4xl font-extrabold text-yellow-400">{m.retry_count}</span>
              <span className="text-xs text-gray-400">Retries</span>
            </div>
            <p className="text-[10px] text-gray-500 leading-normal">Total exceptions caught and handled in feedback loop checkpoints</p>
          </div>

          {/* Card 3 */}
          <div className="p-6 bg-panel/30 border border-border rounded-xl space-y-2 flex flex-col justify-between">
            <h3 className="text-xs uppercase text-gray-400 font-semibold tracking-wider">Average RAG Loops</h3>
            <div className="flex items-center justify-between">
              <span className="text-4xl font-extrabold text-blue-400">{m.avg_iterations}</span>
              <span className="text-xs text-gray-400">Iterations</span>
            </div>
            <p className="text-[10px] text-gray-500 leading-normal">Average number of context checks performed before synthesis</p>
          </div>
        </div>

        {/* Latency distribution bar charts */}
        <div className="p-6 bg-panel/20 border border-border rounded-xl space-y-4">
          <h3 className="text-sm font-semibold">Average Execution Cost Breakdown (Seconds)</h3>
          
          <div className="space-y-4 pt-2">
            {[
              { label: "Planner Agent", val: m.avg_planner_time, color: "bg-blue-500", percent: 20 },
              { label: "Query Rewriter", val: m.avg_rewrite_time, color: "bg-purple-500", percent: 15 },
              { label: "Retriever Service", val: m.avg_retrieval_time, color: "bg-yellow-500", percent: 25 },
              { label: "Sufficient Context check", val: m.avg_context_eval_time, color: "bg-indigo-500", percent: 25 },
              { label: "Final Synthesis", val: m.avg_synthesis_time, color: "bg-green-500", percent: 15 }
            ].map(agent => (
              <div key={agent.label} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-gray-300 font-medium">{agent.label}</span>
                  <span className="font-mono text-gray-400">{agent.val ? agent.val.toFixed(3) : '0.000'}s</span>
                </div>
                <div className="w-full bg-border/40 rounded-full h-2">
                  <div className={`h-2 rounded-full ${agent.color}`} style={{ width: `${Math.min(100, Math.max(10, agent.val * 30))}%` }}></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderLatency = () => {
    if (!latencyData) return <div className="text-gray-400 text-left">Loading latency data...</div>;

    const b = latencyData.breakdown || {};
    const maxVal = Math.max(0.1, b.planner, b.rewriter, b.retriever, b.context_eval, b.synthesis);

    return (
      <div className="space-y-6 text-left">
        <h2 className="text-lg font-bold">Latency Observation & Breakdown</h2>
        
        {/* Latency gauge */}
        <div className="p-6 bg-panel/30 border border-border rounded-xl space-y-4">
          <h3 className="text-sm font-semibold flex items-center gap-2">
            <Clock size={16} className="text-purple-400" /> Relative Latency Distribution
          </h3>
          <div className="space-y-4">
            {[
              { name: "Planner", duration: b.planner, color: "bg-blue-500" },
              { name: "Query Rewriter", duration: b.rewriter, color: "bg-purple-500" },
              { name: "Retriever", duration: b.retriever, color: "bg-yellow-500" },
              { name: "Sufficient Context Agent", duration: b.context_eval, color: "bg-indigo-500" },
              { name: "Synthesis Agent", duration: b.synthesis, color: "bg-green-500" }
            ].map(item => (
              <div key={item.name} className="flex items-center gap-4 text-xs">
                <div className="w-40 text-gray-400">{item.name}</div>
                <div className="flex-1 bg-border/40 h-3 rounded-full overflow-hidden">
                  <div className={`h-3 rounded-full ${item.color}`} style={{ width: `${(item.duration / maxVal) * 100}%` }}></div>
                </div>
                <div className="w-16 text-right font-mono font-bold text-gray-200">{item.duration.toFixed(3)}s</div>
              </div>
            ))}
          </div>
        </div>

        {/* Latency history */}
        <div className="p-6 bg-panel/20 border border-border rounded-xl">
          <h3 className="text-sm font-semibold mb-4">Recent workflow duration times</h3>
          <div className="h-32 flex items-end justify-between gap-1 border-b border-border/80 pb-2">
            {latencyData.recent_latencies?.slice(0, 20).reverse().map((s, idx) => (
              <div 
                key={s.session_id} 
                className="flex-1 bg-purple-500/60 hover:bg-purple-400 rounded-t transition cursor-pointer relative group"
                style={{ height: `${Math.min(100, Math.max(5, (s.total_latency / 15) * 100))}%` }}
                onClick={() => { setSelectedSessionId(s.session_id); handleSelectSession(s.session_id); setActiveSubTab('sessions'); }}
              >
                {/* Tooltip */}
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 p-2 bg-dark border border-border text-[9px] font-mono text-gray-300 rounded shadow-xl opacity-0 group-hover:opacity-100 transition pointer-events-none z-20 whitespace-nowrap">
                  <p>Latency: {s.total_latency.toFixed(2)}s</p>
                  <p>ID: {s.session_id.substring(0,8)}</p>
                </div>
              </div>
            ))}
          </div>
          <div className="flex justify-between text-[10px] text-gray-500 mt-2 font-mono">
            <span>Older runs</span>
            <span>Most recent</span>
          </div>
        </div>
      </div>
    );
  };

  const renderTokens = () => {
    if (!tokenData) return <div className="text-gray-400 text-left">Loading token metrics...</div>;
    const t = tokenData.totals || {};

    return (
      <div className="space-y-6 text-left">
        <h2 className="text-lg font-bold">LLM Token Usage & Pricing</h2>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-4 bg-panel/30 border border-border rounded-xl">
            <p className="text-xs text-gray-400">Total Tokens</p>
            <p className="text-2xl font-bold font-mono mt-1">{t.total_tokens}</p>
          </div>
          <div className="p-4 bg-panel/30 border border-border rounded-xl">
            <p className="text-xs text-gray-400">Prompt / Input Tokens</p>
            <p className="text-2xl font-bold font-mono text-blue-400 mt-1">{t.prompt_tokens}</p>
          </div>
          <div className="p-4 bg-panel/30 border border-border rounded-xl">
            <p className="text-xs text-gray-400">Completion / Output Tokens</p>
            <p className="text-2xl font-bold font-mono text-purple-400 mt-1">{t.completion_tokens}</p>
          </div>
          <div className="p-4 bg-panel/30 border border-border rounded-xl">
            <p className="text-xs text-gray-400">Estimated API Cost (USD/INR)</p>
            <p className="text-xl font-bold font-mono text-green-400 mt-1">${t.estimated_cost.toFixed(5)}</p>
            <p className="text-xs text-gray-400 font-mono mt-0.5">₹{(t.estimated_cost * 85).toFixed(3)} Rs.</p>
          </div>
        </div>

        {/* Model summary */}
        <div className="p-6 bg-panel/20 border border-border rounded-xl space-y-2">
          <h3 className="text-sm font-semibold">Active LLM Model Stats</h3>
          <div className="flex justify-between items-center text-xs p-3 bg-panel border border-border rounded-lg">
            <div>
              <p className="font-bold text-gray-200">llama-3.3-70b-versatile</p>
              <p className="text-gray-500 text-[10px] mt-0.5">Groq Cloud Versatile API Instance</p>
            </div>
            <div className="text-right text-gray-400 font-mono">
              <p>Input: $0.59 / M tokens</p>
              <p>Output: $0.79 / M tokens</p>
            </div>
          </div>
        </div>

        {/* Runs list */}
        <div className="space-y-3">
          <h3 className="text-sm font-semibold">Token distribution by session</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-border text-gray-500 pb-2">
                  <th className="pb-2">Session ID</th>
                  <th className="pb-2">Query</th>
                  <th className="pb-2 text-right">Tokens</th>
                  <th className="pb-2 text-right">Cost</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border/30">
                {tokenData.recent_sessions?.map(s => (
                  <tr key={s.session_id} className="hover:bg-panel/40 transition">
                    <td className="py-2 text-gray-400">{s.session_id.substring(0,8)}</td>
                    <td className="py-2 truncate max-w-[200px] text-gray-300 font-sans">"{s.query}"</td>
                    <td className="py-2 text-right font-bold text-gray-200">{s.total_tokens}</td>
                    <td className="py-2 text-right text-green-400">${s.estimated_cost.toFixed(5)} (₹{(s.estimated_cost * 85).toFixed(3)})</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  };

  const renderErrors = () => {
    return (
      <div className="space-y-6 text-left">
        <h2 className="text-lg font-bold">Error logs & Exceptions</h2>

        <div className="space-y-4">
          {errorsList.map((err, idx) => (
            <div key={err.error_id} className="p-4 bg-red-950/10 border border-red-500/20 rounded-xl space-y-2">
              <div className="flex justify-between items-center gap-2 border-b border-red-500/10 pb-2">
                <span className="px-2 py-0.5 bg-red-500/20 text-red-400 text-[9px] font-bold rounded uppercase tracking-wider">{err.error_type}</span>
                <span className="text-[10px] text-gray-500 font-mono">{formatDate(err.timestamp)}</span>
              </div>
              <p className="text-xs text-red-200 font-semibold">{err.message}</p>
              
              <div className="text-[10px] text-gray-400 font-mono space-y-1">
                <span className="text-[9px] text-gray-500 font-bold uppercase block">Stack Trace:</span>
                <pre className="p-3 bg-dark/60 border border-border/80 text-gray-300 rounded overflow-x-auto max-h-48 whitespace-pre leading-normal">{err.stack_trace}</pre>
              </div>
            </div>
          ))}
          {errorsList.length === 0 && (
            <div className="p-8 border border-dashed border-border rounded-xl text-center text-gray-500 text-sm">
              No errors or exceptions have been logged. All systems operating normally.
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderReplay = () => {
    const isReady = replayData && replayData.spans && replayData.spans.length > 0;
    const currentSpan = isReady ? replayData.spans[replayStep] : null;

    return (
      <div className="space-y-6 text-left">
        <div className="flex flex-wrap justify-between items-center gap-4">
          <div>
            <h2 className="text-lg font-bold">Execution Session Replay</h2>
            <p className="text-xs text-gray-500">Chronological execution replay simulator</p>
          </div>
          
          <div className="flex gap-2 items-center">
            <input 
              type="text" 
              placeholder="Paste Session ID..."
              className="bg-panel border border-border rounded px-3 py-1 text-xs font-mono text-gray-200 focus:outline-none focus:border-accent"
              value={replaySessionId}
              onChange={e => setReplaySessionId(e.target.value)}
            />
            <button 
              onClick={() => handleLoadReplay(replaySessionId)}
              className="px-3 py-1 bg-accent border border-accent rounded text-xs text-white hover:bg-accent/80 transition"
            >
              Load
            </button>
          </div>
        </div>

        {replayError && <div className="p-3 bg-red-950/20 border border-red-500/30 text-red-200 text-xs rounded">{replayError}</div>}

        {isReady ? (
          <div className="space-y-6">
            {/* Player Controls */}
            <div className="p-4 bg-panel/30 border border-border/80 rounded-xl flex items-center justify-between">
              <div className="flex items-center gap-4">
                <button 
                  onClick={() => setIsPlaying(!isPlaying)}
                  className="p-2.5 bg-primary/20 hover:bg-primary/30 border border-primary/30 text-primary rounded-full transition"
                >
                  {isPlaying ? <Pause size={18} fill="currentColor" /> : <Play size={18} fill="currentColor" />}
                </button>
                <div className="flex gap-2">
                  <button 
                    disabled={replayStep === 0}
                    onClick={() => setReplayStep(p => Math.max(0, p - 1))}
                    className="p-2 bg-panel border border-border rounded text-gray-400 hover:text-gray-200 disabled:opacity-40 transition"
                  >
                    <ChevronLeft size={16} />
                  </button>
                  <button 
                    disabled={replayStep === replayData.spans.length - 1}
                    onClick={() => setReplayStep(p => Math.min(replayData.spans.length - 1, p + 1))}
                    className="p-2 bg-panel border border-border rounded text-gray-400 hover:text-gray-200 disabled:opacity-40 transition"
                  >
                    <ChevronRight size={16} />
                  </button>
                  <button 
                    onClick={() => { setReplayStep(0); setIsPlaying(false); }}
                    className="p-2 bg-panel border border-border rounded text-gray-400 hover:text-gray-200 transition"
                  >
                    <RotateCcw size={16} />
                  </button>
                </div>
              </div>
              
              <div className="text-xs font-mono text-gray-400">
                Step <span className="font-bold text-gray-200">{replayStep + 1}</span> of {replayData.spans.length}
              </div>
            </div>

            {/* Pipeline Visual Block Rendering */}
            <div className="p-6 bg-panel/10 border border-border rounded-xl overflow-x-auto">
              <div className="flex items-center gap-4 min-w-[700px] justify-between py-4">
                {[
                  { name: "planner", label: "Planner" },
                  { name: "rewriter", label: "Query Rewriter" },
                  { name: "retriever", label: "Retriever" },
                  { name: "sufficient_context", label: "Context Eval" },
                  { name: "synthesis", label: "Synthesis" }
                ].map((block, idx) => {
                  const isActive = currentSpan && currentSpan.name === block.name;
                  const isFinished = replayData.spans.slice(0, replayStep).some(s => s.name === block.name);
                  
                  return (
                    <div key={block.name} className="flex-1 flex items-center gap-2">
                      <div className={`flex-1 p-3 rounded-lg border text-center transition ${isActive ? 'bg-primary/20 border-primary ring-2 ring-primary ring-offset-2 ring-offset-dark animate-pulse shadow-lg scale-105' : isFinished ? 'bg-panel border-border text-gray-400' : 'bg-panel/40 border-border/40 text-gray-600'}`}>
                        <p className="text-[10px] uppercase font-bold tracking-wider">{block.label}</p>
                        {isActive && <p className="text-[9px] font-mono text-primary font-bold mt-1">ACTIVE</p>}
                        {isFinished && !isActive && <p className="text-[9px] font-mono text-green-500 font-bold mt-1">DONE</p>}
                        {!isFinished && !isActive && <p className="text-[9px] font-mono mt-1">WAITING</p>}
                      </div>
                      {idx < 4 && <ArrowRight size={16} className="text-gray-600 flex-shrink-0" />}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Step Detail display */}
            {currentSpan && (
              <div className="p-6 border border-border rounded-xl glass bg-panel/30 space-y-4">
                <div className="flex justify-between items-center border-b border-border/50 pb-2">
                  <h3 className="text-sm font-bold uppercase text-primary">Active Step: {currentSpan.name.replace("_", " ")}</h3>
                  <div className="text-xs font-mono text-gray-400">
                    <span>Latency: </span><span className="font-bold text-gray-200">{currentSpan.latency.toFixed(3)}s</span>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono text-left">
                  <div className="space-y-1">
                    <span className="text-[10px] text-gray-500 font-bold uppercase">Inputs</span>
                    <pre className="p-3 bg-dark/60 border border-border/60 rounded text-gray-200 overflow-x-auto whitespace-pre-wrap max-h-56 leading-normal">{JSON.stringify(currentSpan.inputs, null, 2)}</pre>
                  </div>
                  <div className="space-y-1">
                    <span className="text-[10px] text-gray-500 font-bold uppercase">Outputs</span>
                    <pre className="p-3 bg-dark/60 border border-border/60 rounded text-gray-200 overflow-x-auto whitespace-pre-wrap max-h-56 leading-normal">{JSON.stringify(currentSpan.outputs, null, 2)}</pre>
                  </div>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center p-12 border border-dashed border-border rounded-xl text-gray-500">
            <Terminal size={40} className="mb-2 text-gray-600" />
            <p className="text-sm font-medium">No session loaded for replay.</p>
            <p className="text-xs text-gray-600 mt-1">Select a session from the Runs page, or copy a Session ID and click Load.</p>
          </div>
        )}
      </div>
    );
  };

  const renderAnalytics = () => {
    if (!analyticsData) return <div className="text-gray-400 text-left">Loading analytics...</div>;
    const a = analyticsData;

    return (
      <div className="space-y-6 text-left">
        <h2 className="text-lg font-bold">System Performance Analytics</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Section 1: Top Errors */}
          <div className="p-6 bg-panel/30 border border-border rounded-xl space-y-4">
            <h3 className="text-sm font-semibold flex items-center gap-1.5 text-red-400">
              <AlertTriangle size={16} /> Most Frequent Error Types
            </h3>
            <div className="space-y-3">
              {a.most_frequent_errors?.map((err, idx) => (
                <div key={idx} className="flex justify-between items-start text-xs p-2.5 bg-panel border border-border rounded">
                  <div className="max-w-[250px]">
                    <span className="font-bold text-gray-300">{err.type}</span>
                    <p className="text-[10px] text-gray-500 truncate mt-0.5">"{err.message}"</p>
                  </div>
                  <span className="font-mono bg-red-500/10 border border-red-500/20 text-red-400 px-2 py-0.5 rounded font-bold">{err.count} times</span>
                </div>
              ))}
              {(!a.most_frequent_errors || a.most_frequent_errors.length === 0) && (
                <p className="text-xs text-gray-500 italic">No errors logged.</p>
              )}
            </div>
          </div>

          {/* Section 2: Top Token Consumers */}
          <div className="p-6 bg-panel/30 border border-border rounded-xl space-y-4">
            <h3 className="text-sm font-semibold flex items-center gap-1.5 text-yellow-400">
              <Coins size={16} /> Highest Token Usage Sessions
            </h3>
            <div className="space-y-3">
              {a.highest_token_usage?.map((session, idx) => (
                <div key={idx} className="flex justify-between items-center text-xs p-2.5 bg-panel border border-border rounded">
                  <div>
                    <span className="font-mono text-gray-400">{session.session_id.substring(0,8)}</span>
                    <p className="text-[10px] text-gray-500 truncate mt-0.5">"{session.query}"</p>
                  </div>
                  <div className="text-right text-gray-200">
                    <p className="font-bold">{session.total_tokens} tokens</p>
                    <p className="text-[10px] text-green-400 font-mono">${session.estimated_cost.toFixed(5)} (₹{(session.estimated_cost * 85).toFixed(3)})</p>
                  </div>
                </div>
              ))}
              {(!a.highest_token_usage || a.highest_token_usage.length === 0) && (
                <p className="text-xs text-gray-500 italic">No token records logged.</p>
              )}
            </div>
          </div>
        </div>

        {/* Section 3: Summary table */}
        <div className="p-6 bg-panel/20 border border-border rounded-xl space-y-2">
          <h3 className="text-sm font-semibold">Workflow Analytics Averages</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-2 text-xs">
            <div className="p-4 bg-panel border border-border rounded-lg">
              <span className="text-gray-500 font-semibold block mb-1 text-[10px] uppercase">Avg Duration</span>
              <span className="text-base font-bold font-mono text-gray-200">{a.avg_workflow_duration}s</span>
            </div>
            <div className="p-4 bg-panel border border-border rounded-lg">
              <span className="text-gray-500 font-semibold block mb-1 text-[10px] uppercase">Avg Retrievals</span>
              <span className="text-base font-bold font-mono text-gray-200">{a.avg_retrieval_count}</span>
            </div>
            <div className="p-4 bg-panel border border-border rounded-lg">
              <span className="text-gray-500 font-semibold block mb-1 text-[10px] uppercase">Avg Loops</span>
              <span className="text-base font-bold font-mono text-gray-200">{a.avg_iterations}</span>
            </div>
            <div className="p-4 bg-panel border border-border rounded-lg">
              <span className="text-gray-500 font-semibold block mb-1 text-[10px] uppercase">Bottleneck</span>
              <span className="text-base font-bold text-purple-400">{a.slowest_agent}</span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="flex-1 flex overflow-hidden">
      {/* Sub tabs sidebar */}
      <div className="w-56 flex-shrink-0 border-r border-border bg-dark/60 p-4 flex flex-col gap-1.5 text-left">
        <h3 className="text-[10px] uppercase tracking-wider font-extrabold text-gray-500 mb-3 px-3">OBSERVE</h3>
        {[
          { id: 'dashboard', label: 'Dashboard', icon: BarChart3 },
          { id: 'sessions', label: 'Runs & Sessions', icon: History },
          { id: 'live-trace', label: 'Live Trace', icon: Activity },
          { id: 'metrics', label: 'System Metrics', icon: Database },
          { id: 'latency', label: 'Latency Analyzer', icon: Clock },
          { id: 'tokens', label: 'Tokens & Costs', icon: Coins },
          { id: 'errors', label: 'Errors & Retries', icon: AlertTriangle },
          { id: 'replay', label: 'Session Replay', icon: Play },
          { id: 'analytics', label: 'Component Analytics', icon: Layers }
        ].map(item => {
          const Icon = item.icon;
          return (
            <button 
              key={item.id}
              onClick={() => setActiveSubTab(item.id)}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition font-medium ${activeSubTab === item.id ? 'bg-primary text-white shadow-lg shadow-primary/10' : 'text-gray-400 hover:text-gray-200 hover:bg-panel/40'}`}
            >
              <Icon size={16} />
              {item.label}
            </button>
          );
        })}
      </div>

      {/* Main Workspace content */}
      <div className="flex-1 p-8 overflow-y-auto bg-dark/20">
        {activeSubTab === 'dashboard' && renderDashboard()}
        {activeSubTab === 'sessions' && renderSessions()}
        {activeSubTab === 'live-trace' && renderLiveTrace()}
        {activeSubTab === 'metrics' && renderMetrics()}
        {activeSubTab === 'latency' && renderLatency()}
        {activeSubTab === 'tokens' && renderTokens()}
        {activeSubTab === 'errors' && renderErrors()}
        {activeSubTab === 'replay' && renderReplay()}
        {activeSubTab === 'analytics' && renderAnalytics()}
      </div>
    </div>
  );
}
