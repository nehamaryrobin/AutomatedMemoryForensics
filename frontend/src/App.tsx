import React, { useState } from 'react';
import axios from 'axios';
import { UploadCloud, File as FileIcon, AlertCircle, CheckCircle } from 'lucide-react';

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');
  const [caseId, setCaseId] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setStatus('idle');
      setProgress(0);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setStatus('uploading');
    
    try {
      // In dev, assuming FastAPI runs on 8000
      const response = await axios.post('http://localhost:8000/api/v1/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setProgress(percentCompleted);
          }
        }
      });
      
      setStatus('success');
      setCaseId(response.data.case_id);
      setMessage(response.data.message);
    } catch (error: any) {
      console.error(error);
      setStatus('error');
      setMessage(error?.response?.data?.detail || 'An error occurred during upload.');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center py-10">
      <header className="mb-10 text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">Automated Memory Forensics</h1>
        <p className="text-gray-500">SIH Rootkit Detection Pipeline</p>
      </header>

      <main className="w-full max-w-3xl bg-white shadow rounded-lg p-8">
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-4 border-b pb-2">Create New Case</h2>
          
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-10 text-center hover:bg-gray-50 transition-colors">
            <UploadCloud className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <p className="text-sm text-gray-600 mb-4">
              Drag and drop your memory dump here, or click to browse.
            </p>
            <p className="text-xs text-gray-400 mb-4">
              Supported formats: .raw, .dmp, .mem, .zip
            </p>
            <label className="cursor-pointer bg-blue-600 text-white px-4 py-2 rounded shadow hover:bg-blue-700 transition">
              Select File
              <input type="file" className="hidden" accept=".raw,.dmp,.mem,.zip" onChange={handleFileChange} />
            </label>
          </div>
        </div>

        {file && (
          <div className="mb-6 bg-gray-50 p-4 rounded border">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <FileIcon className="h-6 w-6 text-blue-500 mr-3" />
                <div>
                  <p className="text-sm font-medium text-gray-900">{file.name}</p>
                  <p className="text-xs text-gray-500">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
                </div>
              </div>
              {status === 'idle' && (
                <button 
                  onClick={handleUpload}
                  className="bg-green-600 text-white px-4 py-2 rounded text-sm hover:bg-green-700 transition"
                >
                  Start Upload
                </button>
              )}
            </div>

            {status === 'uploading' && (
              <div className="mt-4">
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div className="bg-blue-600 h-2.5 rounded-full" style={{ width: `${progress}%` }}></div>
                </div>
                <p className="text-xs text-right text-gray-500 mt-1">{progress}% uploaded</p>
              </div>
            )}
            
            {status === 'success' && (
              <div className="mt-4 flex items-start text-green-700 bg-green-50 p-3 rounded">
                <CheckCircle className="h-5 w-5 mr-2 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium">Upload Complete!</p>
                  <p className="text-xs">{message}</p>
                  <p className="text-xs font-mono mt-1 text-gray-600">Case ID: {caseId}</p>
                </div>
              </div>
            )}
            
            {status === 'error' && (
              <div className="mt-4 flex items-start text-red-700 bg-red-50 p-3 rounded">
                <AlertCircle className="h-5 w-5 mr-2 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium">Upload Failed</p>
                  <p className="text-xs">{message}</p>
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
