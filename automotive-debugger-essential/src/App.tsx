import React, { useState, useEffect } from 'react';
import './App.css';

interface UploadedFile {
  id: string;
  name: string;
  size: number;
  type: string;
}

interface AnalysisResult {
  errors: any[];
  patterns: any;
  timeline: any;
}

function App() {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [query, setQuery] = useState('');
  const [aiResponse, setAiResponse] = useState('');

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFiles = Array.from(event.target.files || []);
    const newFiles: UploadedFile[] = uploadedFiles.map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      name: file.name,
      size: file.size,
      type: file.type
    }));
    setFiles(prev => [...prev, ...newFiles]);
  };

  const handleAnalyze = async () => {
    if (files.length === 0) return;
    
    setIsAnalyzing(true);
    try {
      // Simulate analysis
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      setAnalysisResult({
        errors: [
          { id: 1, type: 'BUS_OFF', severity: 'Critical', message: 'Bus-off detected at 123.456s' },
          { id: 2, type: 'ERROR_FRAME', severity: 'High', message: 'Error frame detected at 125.789s' }
        ],
        patterns: { message_frequency: 'Normal' },
        timeline: { total_events: 1000, duration: 60.5 }
      });
    } catch (error) {
      console.error('Analysis failed:', error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleQuery = async () => {
    if (!query.trim()) return;
    
    try {
      // Simulate AI response
      await new Promise(resolve => setTimeout(resolve, 1000));
      setAiResponse(`AI Response to "${query}": This is a placeholder response. The actual AI integration would analyze your automotive log data and provide insights about potential issues, patterns, and recommendations.`);
    } catch (error) {
      console.error('Query failed:', error);
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
              accept=".log,.txt,.asc,.blf,.trc,.dbc,.csv,.xml"
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
              <h3>Uploaded Files:</h3>
              {files.map(file => (
                <div key={file.id} className="file-item">
                  <span className="file-name">{file.name}</span>
                  <span className="file-size">{(file.size / 1024).toFixed(1)} KB</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="analysis-section">
          <h2>🔍 Analysis</h2>
          <button 
            onClick={handleAnalyze} 
            disabled={files.length === 0 || isAnalyzing}
            className="analyze-button"
          >
            {isAnalyzing ? 'Analyzing...' : 'Start Analysis'}
          </button>

          {analysisResult && (
            <div className="analysis-results">
              <h3>Analysis Results</h3>
              <div className="results-grid">
                <div className="result-card">
                  <h4>Errors Detected</h4>
                  <div className="error-count">{analysisResult.errors.length}</div>
                  <ul>
                    {analysisResult.errors.map(error => (
                      <li key={error.id} className={`error-item ${error.severity.toLowerCase()}`}>
                        <strong>{error.type}:</strong> {error.message}
                      </li>
                    ))}
                  </ul>
                </div>
                
                <div className="result-card">
                  <h4>Patterns</h4>
                  <p>{JSON.stringify(analysisResult.patterns, null, 2)}</p>
                </div>
                
                <div className="result-card">
                  <h4>Timeline</h4>
                  <p>Total Events: {analysisResult.timeline.total_events}</p>
                  <p>Duration: {analysisResult.timeline.duration}s</p>
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
              placeholder="Ask a question about your log data..."
              className="query-field"
            />
            <button onClick={handleQuery} className="query-button">
              Ask AI
            </button>
          </div>
          
          {aiResponse && (
            <div className="ai-response">
              <h4>AI Response:</h4>
              <p>{aiResponse}</p>
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
