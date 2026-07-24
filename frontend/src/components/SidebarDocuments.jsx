import { FileText, Trash2, Hash, Layers, Clock, ChevronRight } from 'lucide-react';
import UploadCard from './UploadCard';

export default function SidebarDocuments({ documents, selectedDocId, onSelect, onDelete, onUpload }) {
  return (
    <div className="flex flex-col gap-5 h-full">
      {/* Upload section */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <div className="h-px flex-1 bg-border" />
          <span className="text-[10px] font-semibold text-gray-600 uppercase tracking-widest">Upload</span>
          <div className="h-px flex-1 bg-border" />
        </div>
        <UploadCard onUpload={onUpload} />
      </div>

      {/* Knowledge Base */}
      <div className="flex-1 min-h-0 flex flex-col">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className="h-px flex-1 bg-border" />
            <span className="text-[10px] font-semibold text-gray-600 uppercase tracking-widest">Knowledge Base</span>
            <div className="h-px flex-1 bg-border" />
          </div>
          {documents.length > 0 && (
            <span className="ml-2 text-[10px] font-bold text-primary bg-primary/10 rounded-full px-2 py-0.5 flex-shrink-0">
              {documents.length}
            </span>
          )}
        </div>

        <div className="flex flex-col gap-2 overflow-y-auto flex-1 pr-0.5">
          {documents.map((doc, idx) => {
            const isSelected = selectedDocId === doc.doc_id;
            return (
              <div
                key={doc.doc_id}
                onClick={() => onSelect(doc.doc_id)}
                className={`relative p-3 rounded-xl border cursor-pointer transition-all duration-200 group overflow-hidden animate-slide-in-up ${
                  isSelected
                    ? 'bg-primary/10 border-primary/40 glow-blue ring-1 ring-primary/20'
                    : 'bg-panel/40 border-border hover:border-gray-600 hover:bg-panel/70'
                }`}
                style={{ animationDelay: `${idx * 50}ms` }}
              >
                {/* Selection shimmer */}
                {isSelected && (
                  <div className="absolute inset-0 shimmer opacity-30 pointer-events-none" />
                )}

                {/* Active badge */}
                {isSelected && (
                  <div className="absolute top-0 right-0 bg-gradient-to-r from-primary to-accent text-white text-[8px] font-bold px-2 py-0.5 rounded-bl-lg uppercase tracking-widest">
                    Active
                  </div>
                )}

                <div className="flex items-start gap-2.5">
                  <div className={`flex-shrink-0 w-7 h-7 rounded-lg flex items-center justify-center ${
                    isSelected ? 'bg-primary/20' : 'bg-panel border border-border'
                  }`}>
                    <FileText size={13} className={isSelected ? 'text-primary' : 'text-gray-500'} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className={`text-xs font-semibold truncate mb-1 ${isSelected ? 'text-white' : 'text-gray-300'}`}>
                      {doc.file_name}
                    </p>
                    <div className="flex items-center gap-2 text-[10px] text-gray-600">
                      <span className="flex items-center gap-0.5">
                        <Hash size={9} />
                        {doc.doc_id.substring(0, 8)}
                      </span>
                      <span className="flex items-center gap-0.5">
                        <Layers size={9} />
                        {doc.num_chunks} chunks
                      </span>
                    </div>
                    {doc.uploaded_at && (
                      <div className="flex items-center gap-0.5 text-[10px] text-gray-700 mt-0.5">
                        <Clock size={9} />
                        {new Date(doc.uploaded_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    )}
                  </div>

                  {/* Delete button */}
                  <button
                    onClick={(e) => { e.stopPropagation(); onDelete(doc.doc_id); }}
                    className="flex-shrink-0 w-6 h-6 rounded-md flex items-center justify-center text-gray-700 hover:text-red-400 hover:bg-red-900/20 opacity-0 group-hover:opacity-100 transition-all duration-150"
                  >
                    <Trash2 size={11} />
                  </button>
                </div>
              </div>
            );
          })}

          {documents.length === 0 && (
            <div className="flex flex-col items-center justify-center gap-3 p-6 text-center border border-dashed border-border/50 rounded-xl mt-2">
              <div className="w-10 h-10 rounded-xl bg-panel border border-border flex items-center justify-center">
                <FileText size={18} className="text-gray-600" />
              </div>
              <div>
                <p className="text-xs font-medium text-gray-500">No documents yet</p>
                <p className="text-[10px] text-gray-700 mt-0.5">Upload a PDF or DOCX to begin</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Footer hint */}
      {documents.length > 0 && (
        <div className="flex-shrink-0 text-[10px] text-gray-700 text-center border-t border-border pt-3">
          Click a document to set as active knowledge base
        </div>
      )}
    </div>
  );
}