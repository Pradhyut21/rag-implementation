import { FileText, Trash2 } from 'lucide-react';
import UploadCard from './UploadCard';

export default function SidebarDocuments({ documents, selectedDocId, onSelect, onDelete, onUpload }) {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">Upload</h2>
        <UploadCard onUpload={onUpload} />
      </div>
      <div>
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">Knowledge Base</h2>
        <div className="flex flex-col gap-2">
          {documents.map(doc => (
            <div 
              key={doc.doc_id}
              onClick={() => onSelect(doc.doc_id)}
              className={`p-3 rounded-lg border cursor-pointer transition-all relative overflow-hidden group ${selectedDocId === doc.doc_id ? 'bg-primary/10 border-primary shadow-[0_0_15px_rgba(59,130,246,0.15)] ring-1 ring-primary/50' : 'bg-panel border-border hover:border-gray-500'}`}
              title={doc.file_name}
            >
              {selectedDocId === doc.doc_id && (
                <div className="absolute top-0 right-0 bg-primary text-white text-[9px] font-bold px-2 py-0.5 rounded-bl-lg uppercase tracking-wider">
                  Active
                </div>
              )}
              <div className="flex justify-between items-start mt-1">
                <div className="flex items-center gap-2 overflow-hidden pr-6">
                  <FileText size={16} className={`flex-shrink-0 ${selectedDocId === doc.doc_id ? 'text-primary' : 'text-gray-400'}`} />
                  <span className={`text-sm font-medium truncate ${selectedDocId === doc.doc_id ? 'text-white' : 'text-gray-300'}`}>{doc.file_name}</span>
                </div>
              </div>
              <div className="text-[11px] text-gray-500 mt-2 flex flex-col gap-1">
                <div className="flex justify-between">
                  <span>ID: {doc.doc_id.substring(0,8)}</span>
                  <span>{doc.num_chunks} chunks</span>
                </div>
                {doc.uploaded_at && (
                  <div className="text-gray-600">
                    Uploaded: {new Date(doc.uploaded_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                  </div>
                )}
              </div>
              <button onClick={(e) => { e.stopPropagation(); onDelete(doc.doc_id); }} className="absolute bottom-2 right-2 text-gray-600 hover:text-red-400 p-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <Trash2 size={14} />
              </button>
            </div>
          ))}
          {documents.length === 0 && (
            <div className="text-xs text-gray-500 text-center p-4 border border-dashed border-border rounded-lg">
              No documents uploaded
            </div>
          )}
        </div>
      </div>
    </div>
  );
}