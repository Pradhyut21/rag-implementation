import { useRef } from 'react';
import { Upload } from 'lucide-react';

export default function UploadCard({ onUpload }) {
  const fileInput = useRef(null);

  const handleChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      onUpload(e.target.files[0]);
    }
  };

  return (
    <div 
      onClick={() => fileInput.current?.click()}
      className="border border-dashed border-gray-600 rounded-lg p-4 flex flex-col items-center justify-center text-gray-400 hover:text-white hover:border-primary cursor-pointer transition-colors bg-panel/50"
    >
      <Upload size={20} className="mb-2" />
      <span className="text-xs font-medium text-center">Click to upload PDF/DOCX</span>
      <input type="file" className="hidden" ref={fileInput} onChange={handleChange} accept=".pdf,.docx" />
    </div>
  );
}