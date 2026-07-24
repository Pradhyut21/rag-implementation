import ObservabilityWorkspaceInner from './ObservabilityWorkspace';

/**
 * Light-theme wrapper for ObservabilityWorkspace.
 * Applies CSS variable overrides so the dark-themed component
 * renders correctly inside the white Claude-style app.
 */
export default function ObservabilityWrapper() {
  return (
    <div className="flex-1 overflow-hidden" style={{ '--tw-bg-opacity': 1 }}>
      <style>{`
        .obs-wrapper {
          --color-dark: #F7F7F8;
          --color-panel: #FFFFFF;
          --color-border: #E5E5E5;
          --color-primary: #7C3AED;
          background: #F7F7F8;
          color: #1A1A1A;
          height: 100%;
          overflow: auto;
        }
        .obs-wrapper .bg-dark { background-color: #F7F7F8 !important; }
        .obs-wrapper .bg-panel { background-color: #FFFFFF !important; }
        .obs-wrapper .border-border { border-color: #E5E5E5 !important; }
        .obs-wrapper .text-gray-200 { color: #1A1A1A !important; }
        .obs-wrapper .text-gray-300 { color: #374151 !important; }
        .obs-wrapper .text-gray-400 { color: #6B7280 !important; }
        .obs-wrapper .text-gray-500 { color: #9CA3AF !important; }
        .obs-wrapper .text-gray-600 { color: #BFDBFE !important; }
        .obs-wrapper .text-white { color: #1A1A1A !important; }
        .obs-wrapper .glass {
          background: rgba(255,255,255,0.9) !important;
          border-color: #E5E5E5 !important;
          backdrop-filter: blur(8px);
        }
        .obs-wrapper .bg-panel\\/30,
        .obs-wrapper .bg-panel\\/40,
        .obs-wrapper .bg-panel\\/50,
        .obs-wrapper .bg-panel\\/60,
        .obs-wrapper .bg-panel\\/80 {
          background-color: rgba(255,255,255,0.7) !important;
        }
        .obs-wrapper .bg-primary { background-color: #7C3AED !important; }
        .obs-wrapper .text-primary { color: #7C3AED !important; }
        .obs-wrapper .border-primary { border-color: #7C3AED !important; }
        .obs-wrapper .bg-primary\\/10 { background-color: rgba(124,58,237,0.1) !important; }
        .obs-wrapper .bg-primary\\/5 { background-color: rgba(124,58,237,0.05) !important; }
        .obs-wrapper input,
        .obs-wrapper textarea,
        .obs-wrapper select {
          background-color: #F7F7F8 !important;
          color: #1A1A1A !important;
          border-color: #E5E5E5 !important;
        }
        .obs-wrapper button:not(.bg-primary):not(.bg-blue-600):not(.bg-red-600):not(.bg-emerald-600) {
          color: #374151 !important;
        }
        .obs-wrapper .font-mono { font-family: 'JetBrains Mono', monospace !important; }
        .obs-wrapper pre, .obs-wrapper code {
          background: #F7F7F8 !important;
          color: #6D28D9 !important;
        }
      `}</style>
      <div className="obs-wrapper">
        <ObservabilityWorkspaceInner />
      </div>
    </div>
  );
}
