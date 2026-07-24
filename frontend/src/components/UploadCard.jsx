import { useState, useCallback } from 'react';
import { Upload, FileText, X, CheckCircle2, Loader2 } from 'lucide-react';

export default function UploadCard({ onUpload }) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);

  const handleFile = async (file) => {
    if (!file) return;
    setIsUploading(true);
    setUploadedFile(file.name);
    try {
      await onUpload(file);
    } finally {
      setIsUploading(false);
    }
  };

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  }, []);

  const handleDragOver = (e) => { e.preventDefault(); setIsDragging(true); };
  const handleDragLeave = () => setIsDragging(false);
  const handleChange = (e) => { if (e.target.files?.[0]) handleFile(e.target.files[0]); };

  return (
    <label
      className={`relative flex flex-col items-center justify-center gap-2 p-4 rounded-xl border-2 border-dashed cursor-pointer transition-all duration-300 min-h-[90px] group ${
        isDragging
          ? 'border-primary bg-primary/10 scale-[1.02]'
          : 'border-border hover:border-primary/50 hover:bg-primary/5 bg-panel/30'
      }`}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
    >
      <input type="file" className="hidden" onChange={handleChange} accept=".pdf,.docx" />

      {isUploading ? (
        <>
          <Loader2 size={20} className="text-primary animate-spin" />
          <span className="text-xs text-primary font-medium">Indexing...</span>
          <div className="w-full bg-border rounded-full h-1 mt-1 overflow-hidden">
            <div className="h-full bg-gradient-to-r from-primary to-accent rounded-full progress-bar" />
          </div>
        </>
      ) : uploadedFile ? (
        <>
          <CheckCircle2 size={20} className="text-emerald-400" />
          <span className="text-xs text-emerald-400 font-medium truncate max-w-full px-2">{uploadedFile}</span>
        </>
      ) : (
        <>
          <div className="w-8 h-8 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
            <Upload size={14} className="text-primary" />
          </div>
          <div className="text-center">
            <span className="text-xs font-medium text-gray-300 block">Drop PDF or DOCX</span>
            <span className="text-[10px] text-gray-600">or click to browse</span>
          </div>
        </>
      )}
    </label>
  );
}