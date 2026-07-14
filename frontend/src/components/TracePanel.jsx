import IterationCard from './IterationCard';
import { Network } from 'lucide-react';

export default function TracePanel({ trace }) {
  if (!trace || !trace.trace) return null;

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center gap-3 mb-6 sticky top-0 bg-panel/30 backdrop-blur pb-4 pt-2 z-10 border-b border-border">
        <div className="p-2 bg-accent/20 rounded-lg text-accent">
          <Network size={20} />
        </div>
        <h2 className="text-lg font-semibold">Agentic Reasoning Trace</h2>
      </div>
      
      <div className="flex flex-col gap-8 relative">
        {/* Timeline connector line */}
        <div className="absolute left-6 top-0 bottom-0 w-px bg-border z-0"></div>
        
        {trace.trace.map((iter, idx) => (
          <IterationCard 
            key={idx} 
            iteration={iter} 
            index={idx} 
            isLast={idx === trace.trace.length - 1} 
          />
        ))}
      </div>
    </div>
  );
}