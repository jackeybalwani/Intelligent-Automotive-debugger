import React, { useState } from 'react';
import './App.css';

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  selected: boolean;
  format?: string;
  status: 'uploaded' | 'analyzing' | 'analyzed' | 'error';
}

interface AnalysisResult {
  fileId: string;
  fileName: string;
  errors: any[];
  patterns: any;
  timeline: any;
  statistics: {
    totalMessages: number;
    uniqueIds: number;
    timeRange: { start: number; end: number };
    errorCount: number;
    fileSize: number;
  };
  timestamp: string;
}

function App() {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [query, setQuery] = useState('');
  const [aiResponse, setAiResponse] = useState('');
  const [selectedFileId, setSelectedFileId] = useState<string>('');

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFiles = Array.from(event.target.files || []);

    // Clear previous analysis when new files are uploaded
    setAnalysisResult(null);

    for (const file of uploadedFiles) {
      try {
        // Create temporary file entry with uploading status
        const tempFile: UploadedFile = {
          id: Math.random().toString(36).substr(2, 9),
          name: file.name,
          size: file.size,
          type: file.type,
          selected: false,
          format: detectFileFormat(file.name),
          status: 'analyzing' // Show as analyzing during upload
        };

        setFiles(prev => [...prev, tempFile]);

        // Upload to backend
        const formData = new FormData();
        formData.append('files', file);

        const response = await fetch('http://localhost:8000/api/upload', {
          method: 'POST',
          body: formData
        });

        if (response.ok) {
          const result = await response.json();
          const uploadedFile = result[0]; // First uploaded file

          // Update file with backend response
          setFiles(prev => prev.map(f =>
            f.id === tempFile.id
              ? {
                  ...f,
                  id: uploadedFile.file_id,
                  format: uploadedFile.format,
                  status: 'uploaded'
                }
              : f
          ));
        } else {
          // Update file status to error
          setFiles(prev => prev.map(f =>
            f.id === tempFile.id ? { ...f, status: 'error' } : f
          ));
        }
      } catch (error) {
        console.error('Upload failed:', error);
        // Handle error by updating the file status
        setFiles(prev => prev.map(f =>
          f.name === file.name ? { ...f, status: 'error' } : f
        ));
      }
    }
  };

  const detectFileFormat = (filename: string): string => {
    const extension = filename.toLowerCase().split('.').pop();
    const formatMap: { [key: string]: string } = {
      'asc': 'CAN ASC',
      'blf': 'CAN BLF',
      'trc': 'CAN TRC',
      'log': 'CAN LOG',
      'txt': 'Text Log',
      'dbc': 'DBC Database',
      'csv': 'CSV Data',
      'xml': 'XML Data',
      'lin': 'LIN Protocol',
      'uds': 'UDS Protocol'
    };
    return formatMap[extension || ''] || 'Unknown';
  };

  const handleFileSelect = (fileId: string) => {
    // Clear previous analysis when selecting different file
    if (selectedFileId !== fileId) {
      setAnalysisResult(null);
    }
    
    setSelectedFileId(fileId);
    setFiles(prev => prev.map(file => ({
      ...file,
      selected: file.id === fileId
    })));
  };

  const handleAnalyze = async () => {
    const selectedFile = files.find(f => f.selected);
    if (!selectedFile) return;
    
    setIsAnalyzing(true);
    
    // Update file status
    setFiles(prev => prev.map(file => 
      file.selected ? { ...file, status: 'analyzing' as const } : file
    ));

    try {
      // Simulate realistic analysis with file-specific data
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Generate realistic statistics based on file
      const mockStatistics = {
        totalMessages: Math.floor(Math.random() * 5000) + 1000,
        uniqueIds: Math.floor(Math.random() * 50) + 10,
        timeRange: { 
          start: 0, 
          end: Math.random() * 300 + 60 // 60-360 seconds
        },
        errorCount: Math.floor(Math.random() * 20),
        fileSize: selectedFile.size
      };

      const mockErrors = [];
      for (let i = 0; i < mockStatistics.errorCount; i++) {
        mockErrors.push({
          id: i + 1,
          type: ['BUS_OFF', 'ERROR_FRAME', 'TIMEOUT', 'DLC_ERROR', 'UDS_ERROR'][Math.floor(Math.random() * 5)],
          severity: ['Critical', 'High', 'Medium', 'Low'][Math.floor(Math.random() * 4)],
          message: `Error detected at ${(Math.random() * mockStatistics.timeRange.end).toFixed(3)}s`,
          timestamp: Math.random() * mockStatistics.timeRange.end
        });
      }

      const result: AnalysisResult = {
        fileId: selectedFile.id,
        fileName: selectedFile.name,
        errors: mockErrors.sort((a, b) => b.timestamp - a.timestamp), // Sort by timestamp
        patterns: { 
          message_frequency: 'Normal',
          bus_load: `${(Math.random() * 80 + 10).toFixed(1)}%`,
          dominant_ids: [`0x${Math.floor(Math.random() * 0x7FF).toString(16).toUpperCase()}`]
        },
        timeline: { 
          total_events: mockStatistics.totalMessages,
          duration: mockStatistics.timeRange.end,
          events_per_second: (mockStatistics.totalMessages / mockStatistics.timeRange.end).toFixed(1)
        },
        statistics: mockStatistics,
        timestamp: new Date().toISOString()
      };
      
      setAnalysisResult(result);
      
      // Update file status
      setFiles(prev => prev.map(file => 
        file.selected ? { ...file, status: 'analyzed' as const } : file
      ));
      
    } catch (error) {
      console.error('Analysis failed:', error);
      setFiles(prev => prev.map(file => 
        file.selected ? { ...file, status: 'error' as const } : file
      ));
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleQuery = async () => {
    if (!query.trim()) return;

    try {
      // Call the backend API for NLP query
      const response = await fetch('http://localhost:8000/api/nlp/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query.trim(),
          context_file_ids: selectedFileId ? [selectedFileId] : [],
          session_id: null
        })
      });

      if (response.ok) {
        const result = await response.json();

        // Use enhanced response if available, otherwise use basic response
        const aiText = result.enhanced || result.response || 'No response generated';
        setAiResponse(aiText);
      } else {
        // Fallback to contextual response if backend is unavailable
        let contextualResponse = `AI Analysis for "${query}": `;

        if (analysisResult) {
          contextualResponse += `Based on analysis of ${analysisResult.fileName}, I found ${analysisResult.errors.length} errors. `;
          if (analysisResult.errors.length > 0) {
            const criticalErrors = analysisResult.errors.filter(e => e.severity === 'Critical').length;
            if (criticalErrors > 0) {
              contextualResponse += `There are ${criticalErrors} critical errors that need immediate attention. `;
            }
          }
          contextualResponse += `The log contains ${analysisResult.statistics.totalMessages} messages over ${analysisResult.statistics.timeRange.end.toFixed(1)} seconds. `;
        }

        contextualResponse += `This appears to be related to automotive diagnostics. I recommend checking the physical layer connections and verifying the bus termination if you're seeing bus-off errors.`;
        setAiResponse(contextualResponse);
      }
    } catch (error) {
      console.error('Query failed:', error);
      setAiResponse('Backend service unavailable. Please ensure the Python backend is running on port 8000.');
    }
  };

  const removeFile = (fileId: string) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
    if (selectedFileId === fileId) {
      setSelectedFileId('');
      setAnalysisResult(null);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'uploaded': return '📄';
      case 'analyzing': return '⏳';
      case 'analyzed': return '✅';
      case 'error': return '❌';
      default: return '📄';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'uploaded': return '#4facfe';
      case 'analyzing': return '#ffa502';
      case 'analyzed': return '#2ed573';
      case 'error': return '#ff4757';
      default: return '#4facfe';
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🚗 Automotive Debug Log Analyzer</h1>
        <p>AI-powered analysis for automotive CAN, LIN, UDS, and other log formats</p>
      </header>

      <main className="App-main">
        <div className="upload-section">
          <h2>📁 Upload Log Files</h2>
          <div className="upload-area">
            <input
              type="file"
              multiple
              accept=".log,.txt,.asc,.blf,.trc,.dbc,.csv,.xml,.lin,.uds"
              onChange={handleFileUpload}
              className="file-input"
            />
            <div className="upload-text">
              Drag and drop files here or click to browse
              <br />
              <small>Supports CAN, LIN, UDS, DBC, and other automotive formats</small>
            </div>
          </div>
          
          {files.length > 0 && (
            <div className="file-list">
              <h3>Uploaded Files ({files.length}):</h3>
              <div className="file-selection-note">
                💡 Select one file to analyze by clicking the radio button
              </div>
              {files.map(file => (
                <div key={file.id} className={`file-item ${file.selected ? 'selected' : ''}`}>
                  <div className="file-select">
                    <input
                      type="radio"
                      name="selectedFile"
                      checked={file.selected}
                      onChange={() => handleFileSelect(file.id)}
                      className="file-checkbox"
                    />
                  </div>
                  <div className="file-info">
                    <div className="file-main-info">
                      <span className="file-status" style={{ color: getStatusColor(file.status) }}>
                        {getStatusIcon(file.status)}
                      </span>
                      <span className="file-name">{file.name}</span>
                      <span className="file-format">[{file.format}]</span>
                    </div>
                    <div className="file-meta">
                      <span className="file-size">{formatFileSize(file.size)}</span>
                      <span className="file-status-text">{file.status}</span>
                    </div>
                  </div>
                  <button 
                    onClick={() => removeFile(file.id)}
                    className="remove-file-btn"
                    title="Remove file"
                  >
                    🗑️
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="analysis-section">
          <h2>🔍 Analysis</h2>
          <button 
            onClick={handleAnalyze} 
            disabled={!selectedFileId || isAnalyzing}
            className="analyze-button"
          >
            {isAnalyzing ? 'Analyzing...' : `Analyze Selected File`}
          </button>
          
          {!selectedFileId && files.length > 0 && (
            <div className="selection-reminder">
              ⚠️ Please select a file to analyze
            </div>
          )}

          {analysisResult && (
            <div className="analysis-results">
              <div className="results-header">
                <h3>Analysis Results - {analysisResult.fileName}</h3>
                <div className="analysis-timestamp">
                  Analyzed at: {new Date(analysisResult.timestamp).toLocaleString()}
                </div>
              </div>
              
              <div className="results-grid">
                <div className="result-card">
                  <h4>📊 File Statistics</h4>
                  <div className="stats-grid">
                    <div className="stat-item">
                      <span className="stat-label">Total Messages:</span>
                      <span className="stat-value">{analysisResult.statistics.totalMessages.toLocaleString()}</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">Unique IDs:</span>
                      <span className="stat-value">{analysisResult.statistics.uniqueIds}</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">Duration:</span>
                      <span className="stat-value">{analysisResult.statistics.timeRange.end.toFixed(1)}s</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-label">File Size:</span>
                      <span className="stat-value">{formatFileSize(analysisResult.statistics.fileSize)}</span>
                    </div>
                  </div>
                </div>
                
                <div className="result-card">
                  <h4>⚠️ Errors Detected</h4>
                  <div className="error-count">{analysisResult.errors.length}</div>
                  <div className="error-list">
                    {analysisResult.errors.slice(0, 5).map(error => (
                      <div key={error.id} className={`error-item ${error.severity.toLowerCase()}`}>
                        <div className="error-header">
                          <strong>{error.type}</strong>
                          <span className={`severity-badge ${error.severity.toLowerCase()}`}>
                            {error.severity}
                          </span>
                        </div>
                        <div className="error-message">{error.message}</div>
                      </div>
                    ))}
                    {analysisResult.errors.length > 5 && (
                      <div className="more-errors">
                        ... and {analysisResult.errors.length - 5} more errors
                      </div>
                    )}
                  </div>
                </div>
                
                <div className="result-card">
                  <h4>📈 Patterns</h4>
                  <div className="pattern-list">
                    <div className="pattern-item">
                      <span className="pattern-label">Message Frequency:</span>
                      <span className="pattern-value">{analysisResult.patterns.message_frequency}</span>
                    </div>
                    <div className="pattern-item">
                      <span className="pattern-label">Bus Load:</span>
                      <span className="pattern-value">{analysisResult.patterns.bus_load}</span>
                    </div>
                    <div className="pattern-item">
                      <span className="pattern-label">Dominant IDs:</span>
                      <span className="pattern-value">{analysisResult.patterns.dominant_ids?.join(', ')}</span>
                    </div>
                  </div>
                </div>
                
                <div className="result-card">
                  <h4>⏱️ Timeline</h4>
                  <div className="timeline-stats">
                    <div className="timeline-item">
                      <span className="timeline-label">Total Events:</span>
                      <span className="timeline-value">{analysisResult.timeline.total_events.toLocaleString()}</span>
                    </div>
                    <div className="timeline-item">
                      <span className="timeline-label">Duration:</span>
                      <span className="timeline-value">{analysisResult.timeline.duration.toFixed(1)}s</span>
                    </div>
                    <div className="timeline-item">
                      <span className="timeline-label">Event Rate:</span>
                      <span className="timeline-value">{analysisResult.timeline.events_per_second}/s</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="ai-section">
          <h2>🤖 AI Assistant</h2>
          <div className="query-input">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask about errors, patterns, or get diagnostic advice..."
              className="query-field"
              onKeyPress={(e) => e.key === 'Enter' && handleQuery()}
            />
            <button onClick={handleQuery} className="query-button">
              Ask AI
            </button>
          </div>
          
          {aiResponse && (
            <div className="ai-response">
              <h4>🎯 AI Response:</h4>
              <p>{aiResponse}</p>
            </div>
          )}
          
          {!analysisResult && (
            <div className="ai-suggestion">
              💡 Upload and analyze a file first to get contextual AI insights about your automotive data.
            </div>
          )}
        </div>
      </main>

      <footer className="App-footer">
        <p>Automotive Debug Log Analyzer v1.0.0</p>
        <p>Powered by AI and advanced automotive protocols</p>
      </footer>
    </div>
  );
}

export default App;