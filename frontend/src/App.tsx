import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { UploadCloud, File as FileIcon, AlertCircle, CheckCircle, Loader2 } from 'lucide-react';

interface CaseStatus {
  id: string;
  filename: string;
  file_size: number;
  sha256: string;
  status: 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  risk_score: number;
}

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [progress, setProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');
  const [caseId, setCaseId] = useState('');
  const [caseData, setCaseData] = useState<CaseStatus | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setUploadStatus('idle');
      setProgress(0);
      setCaseId('');
      setCaseData(null);
    }
  };

  const handleUpload = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setUploadStatus('uploading');
    
    try {
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
      
      setUploadStatus('success');
      setCaseId(response.data.case_id);
      setMessage(response.data.message);
    } catch (error: any) {
      console.error(error);
      setUploadStatus('error');
      setMessage(error?.response?.data?.detail || 'An error occurred during upload.');
    }
  };

  // Poll for Case Status once Case ID is available
  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;

    const pollStatus = async () => {
      try {
        const response = await axios.get(`http://localhost:8000/api/v1/cases/${caseId}`);
        setCaseData(response.data);

        // Stop polling if completed or failed
        if (response.data.status === 'COMPLETED' || response.data.status === 'FAILED') {
          clearInterval(interval);
        }
      } catch (error) {
        console.error("Error polling case status:", error);
      }
    };

    if (caseId && (!caseData || (caseData.status !== 'COMPLETED' && caseData.status !== 'FAILED'))) {
      pollStatus(); // Initial fetch
      interval = setInterval(pollStatus, 3000);
    }

    return () => clearInterval(interval);
  }, [caseId, caseData?.status]);

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
              {uploadStatus === 'idle' && (
                <button 
                  onClick={handleUpload}
                  className="bg-green-600 text-white px-4 py-2 rounded text-sm hover:bg-green-700 transition"
                >
                  Start Upload
                </button>
              )}
            </div>

            {uploadStatus === 'uploading' && (
              <div className="mt-4">
                <div className="w-full bg-gray-200 rounded-full h-2.5">
                  <div className="bg-blue-600 h-2.5 rounded-full" style={{ width: `${progress}%` }}></div>
                </div>
                <p className="text-xs text-right text-gray-500 mt-1">{progress}% uploaded</p>
              </div>
            )}
            
            {uploadStatus === 'error' && (
              <div className="mt-4 flex items-start text-red-700 bg-red-50 p-3 rounded">
                <AlertCircle className="h-5 w-5 mr-2 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium">Upload Failed</p>
                  <p className="text-xs">{message}</p>
                </div>
              </div>
            )}
            
            {/* Analysis Status Area */}
            {caseData && (
              <div className="mt-6 border-t pt-4">
                <h3 className="text-lg font-semibold mb-3">Analysis Status</h3>
                
                <div className="bg-white p-4 rounded border shadow-sm flex items-center justify-between">
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Case ID: {caseId}</p>
                    <p className="text-xs text-gray-500 mb-1">SHA-256: {caseData.sha256}</p>
                    <div className="flex items-center mt-2">
                      <span className="text-sm font-medium mr-2">Status:</span>
                      {caseData.status === 'QUEUED' && <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded-full">QUEUED</span>}
                      {caseData.status === 'RUNNING' && (
                        <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full flex items-center">
                          <Loader2 className="animate-spin h-3 w-3 mr-1" /> RUNNING
                        </span>
                      )}
                      {caseData.status === 'COMPLETED' && <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">COMPLETED</span>}
                      {caseData.status === 'FAILED' && <span className="px-2 py-1 bg-red-100 text-red-800 text-xs rounded-full">FAILED</span>}
                    </div>
                  </div>
                  
                  {caseData.status === 'COMPLETED' && (
                    <div className="text-center p-3 bg-red-50 border border-red-100 rounded">
                      <p className="text-xs text-red-800 font-bold uppercase tracking-wider mb-1">Risk Score</p>
                      <p className="text-3xl font-black text-red-600">{caseData.risk_score}</p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
