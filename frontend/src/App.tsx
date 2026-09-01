import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { UploadCloud, File as FileIcon, AlertCircle, Loader2, ShieldAlert, Clock, Activity, Download } from 'lucide-react';

interface CaseStatus {
  id: string;
  filename: string;
  file_size: number;
  sha256: string;
  status: 'QUEUED' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  risk_score: number;
}

interface Finding {
  id: string;
  finding_type: string;
  severity: string;
  description: string;
  confidence: number;
  evidence_data: string;
}

interface TimelineEvent {
  id: string;
  timestamp: string;
  event_type: string;
  details: string;
}

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [progress, setProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');
  const [caseId, setCaseId] = useState('');
  const [caseData, setCaseData] = useState<CaseStatus | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([]);
  const [searchId, setSearchId] = useState('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setUploadStatus('idle');
      setProgress(0);
      setCaseId('');
      setCaseData(null);
      setFindings([]);
      setTimelineEvents([]);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchId.trim()) return;
    
    setFile(null);
    setUploadStatus('idle');
    setCaseData(null);
    setFindings([]);
    setTimelineEvents([]);
    setCaseId(searchId.trim());
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

  const fetchFindingsAndTimeline = async (id: string) => {
    try {
      const resFindings = await axios.get(`http://localhost:8000/api/v1/cases/${id}/findings`);
      setFindings(resFindings.data);

      const resTimeline = await axios.get(`http://localhost:8000/api/v1/cases/${id}/timeline`);
      setTimelineEvents(resTimeline.data);
    } catch (err) {
      console.error("Failed to fetch findings or timeline", err);
    }
  };

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;

    const pollStatus = async () => {
      try {
        const response = await axios.get(`http://localhost:8000/api/v1/cases/${caseId}`);
        setCaseData(response.data);

        if (response.data.status === 'COMPLETED' || response.data.status === 'FAILED') {
          clearInterval(interval);
          if (response.data.status === 'COMPLETED') {
            fetchFindingsAndTimeline(caseId);
          }
        }
      } catch (error) {
        console.error("Error polling case status:", error);
      }
    };

    if (caseId && (!caseData || (caseData.status !== 'COMPLETED' && caseData.status !== 'FAILED'))) {
      pollStatus(); 
      interval = setInterval(pollStatus, 3000);
    }

    return () => clearInterval(interval);
  }, [caseId, caseData?.status]);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center py-10">
      <header className="mb-10 text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">Automated Memory Forensics</h1>
        <p className="text-gray-500 mb-6">SIH Rootkit Detection Pipeline</p>
        
        <form onSubmit={handleSearch} className="flex justify-center max-w-md mx-auto">
          <input 
            type="text" 
            placeholder="Enter existing Case ID (e.g. mock-case-123)"
            className="border border-gray-300 rounded-l px-4 py-2 w-full focus:outline-none focus:border-blue-500"
            value={searchId}
            onChange={(e) => setSearchId(e.target.value)}
          />
          <button type="submit" className="bg-gray-800 text-white px-4 py-2 rounded-r hover:bg-gray-700">
            Lookup
          </button>
        </form>
      </header>

      <main className="w-full max-w-4xl bg-white shadow rounded-lg p-8">
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

        {(file || caseId) && (
          <div className="mb-6 bg-gray-50 p-4 rounded border">
            {file && (
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
            )}

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
            
            {caseData && (
              <div className="mt-6 border-t pt-4">
                <div className="flex justify-between items-center mb-3">
                  <h3 className="text-lg font-semibold">Analysis Status</h3>
                  {caseData.status === 'COMPLETED' && (
                    <a 
                      href={`http://localhost:8000/api/v1/cases/${caseId}/report/pdf`} 
                      target="_blank" 
                      rel="noreferrer"
                      className="flex items-center text-sm bg-blue-600 text-white px-3 py-1.5 rounded hover:bg-blue-700 transition"
                    >
                      <Download className="w-4 h-4 mr-2" /> Download PDF Report
                    </a>
                  )}
                </div>
                
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

            {caseData?.status === 'COMPLETED' && (
              <div className="mt-8 border-t pt-6">
                <h3 className="text-xl font-bold mb-4 flex items-center text-gray-900">
                  <ShieldAlert className="mr-2 text-red-600" /> Forensic Findings
                </h3>
                
                {findings.length === 0 ? (
                  <p className="text-gray-500 italic bg-white p-4 rounded border">No suspicious artifacts detected.</p>
                ) : (
                  <div className="space-y-4">
                    {findings.map((f) => (
                      <div key={f.id} className="bg-white border-l-4 border-red-500 p-4 rounded shadow-sm">
                        <div className="flex justify-between items-start mb-2">
                          <h4 className="font-bold text-red-700">{f.finding_type.replace('_', ' ')}</h4>
                          <span className="px-2 py-1 bg-red-100 text-red-800 text-xs rounded font-mono">
                            Confidence: {(f.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                        <p className="text-sm text-gray-800 mb-2">{f.description}</p>
                        
                        <details className="mt-2 text-xs text-gray-500 cursor-pointer">
                          <summary className="font-medium hover:text-gray-700">View Raw Evidence Metadata</summary>
                          <pre className="mt-2 p-2 bg-gray-100 rounded overflow-x-auto border border-gray-200 text-[10px]">
                            {f.evidence_data}
                          </pre>
                        </details>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {caseData?.status === 'COMPLETED' && timelineEvents.length > 0 && (
              <div className="mt-8 border-t pt-6">
                <h3 className="text-xl font-bold mb-4 flex items-center text-gray-900">
                  <Clock className="mr-2 text-blue-600" /> Event Timeline
                </h3>
                <div className="bg-white p-6 rounded border shadow-sm max-h-96 overflow-y-auto">
                  <div className="relative border-l border-gray-200 ml-3">
                    {timelineEvents.map((event, index) => (
                      <div key={event.id} className="mb-6 ml-6">
                        <span className="absolute flex items-center justify-center w-6 h-6 bg-blue-100 rounded-full -left-3 ring-4 ring-white">
                          <Activity className="w-3 h-3 text-blue-600" />
                        </span>
                        <h3 className="flex items-center mb-1 text-sm font-semibold text-gray-900">
                          {event.event_type.replace('_', ' ')}
                        </h3>
                        <time className="block mb-2 text-xs font-normal leading-none text-gray-400">
                          {new Date(event.timestamp).toLocaleString()}
                        </time>
                        <p className="mb-4 text-sm font-normal text-gray-600">{event.details}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

          </div>
        )}
      </main>
    </div>
  );
}
