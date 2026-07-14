import StatusBadge from './StatusBadge';

export default function AnswerPanel({ result, isLoading }) {
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-500 space-y-4">
        <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
        <p>Synthesizing response...</p>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        <p>Select a document and ask a question to see the result.</p>
      </div>
    );
  }

  const { answer, mode, context_sufficient, evidence_type, iterations, missing_information, fallback_used } = result;

  return (
    <div className="glass rounded-2xl p-8 shadow-xl">
      <div className="mb-6 pb-6 border-b border-border">
        <div className="flex justify-between items-center mb-5">
            <h2 className="text-2xl font-semibold">Final Answer</h2>
            <span className="px-3 py-1 bg-panel border border-border rounded-full text-xs font-medium text-gray-400 uppercase tracking-wide">
                {mode} mode
            </span>
        </div>
        {mode !== 'vanilla' && (
            <div className="flex flex-wrap gap-3">
                <div className={`px-4 py-2 rounded-lg border font-medium text-sm flex items-center gap-2 ${context_sufficient ? 'bg-emerald-900/20 border-emerald-500/30 text-emerald-400' : 'bg-red-900/20 border-red-500/30 text-red-400'}`}>
                    {context_sufficient ? '🟢 Context Sufficient' : '🔴 Context Insufficient'}
                </div>
                <div className="px-4 py-2 bg-panel/50 border border-border rounded-lg font-medium text-sm text-gray-300 flex items-center gap-2">
                    <span className="text-gray-500">Evidence:</span> <span className="capitalize">{evidence_type || (context_sufficient ? 'Found' : 'Missing')}</span>
                </div>
                <div className="px-4 py-2 bg-panel/50 border border-border rounded-lg font-medium text-sm text-gray-300 flex items-center gap-2">
                    <span className="text-gray-500">Iterations:</span> {iterations || 1}
                </div>
                {fallback_used && (
                    <div className="px-4 py-2 bg-amber-900/20 border border-amber-500/30 rounded-lg font-medium text-sm text-amber-400 flex items-center gap-2">
                        ⚠️ Parser Fallback Used
                    </div>
                )}
            </div>
        )}
      </div>
      
      <div className="prose prose-invert max-w-none mb-8">
        <p className="text-lg leading-relaxed text-gray-200 whitespace-pre-wrap">{answer}</p>
      </div>

      {mode !== 'vanilla' && (
        <div className="flex flex-col gap-5 mt-8 pt-6 border-t border-border">
          {/* Why it stopped */}
          {(result.trace && result.trace.length > 0) && (
            <div className="bg-panel/50 rounded-xl p-5 border border-border">
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-2">Why It Stopped</h3>
              <p className="text-gray-300 text-sm leading-relaxed">
                {result.trace[result.trace.length - 1].sufficient_context_result?.reasoning_summary || 
                 result.trace[result.trace.length - 1].sufficient_context_result?.feedback_log || 
                 "Context analyzed and determined to be sufficient."}
              </p>
            </div>
          )}
          
          {/* Missing Info */}
          {missing_information && missing_information.length > 0 && (
            <div className="bg-red-900/10 rounded-xl p-5 border border-red-500/30">
              <h3 className="text-sm font-semibold text-red-400 uppercase tracking-wider mb-3">Missing Information</h3>
              <ul className="list-disc list-inside text-red-200/90 text-sm space-y-1.5">
                {missing_information.map((info, idx) => (
                  <li key={idx}>{info}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}