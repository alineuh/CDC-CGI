import React, { useState } from 'react';
import './App.css';
import UploadZone from './components/UploadZone';

function App() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleUpload = async (file) => {
    setLoading(true);
    setError(null);
    setResult(null);
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }

      const data = await response.json();
      setResult(data);
      
    } catch (err) {
      console.error('Error:', err);
      setError(err.message || 'Erreur lors de l\'upload');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setError(null);
  };

  return (
    <div className="App">
      <header className="header">
        <div className="header-content">
          <h1>📊 CDC-CGI - Payslip Upload</h1>
          <p>Upload PDF → Get JSON</p>
        </div>
      </header>
      
      <main className="container">
        {!result ? (
          <div className="upload-section">
            <h2>Upload Payslip PDF</h2>
            <p className="subtitle">
              Upload your PDF payslip to extract data as JSON
            </p>
            
            {error && (
              <div className="error-banner">
                <span className="error-icon">⚠️</span>
                {error}
              </div>
            )}
            
            <UploadZone onUpload={handleUpload} loading={loading} />
          </div>
        ) : (
          <div className="result-section">
            <div className="result-header">
              <div>
                <h2>✅ Upload Successful!</h2>
                <p className="filename">📎 {result.filename}</p>
                <p className="success-message">{result.message}</p>
              </div>
              <button onClick={handleReset} className="btn-reset">
                Upload Another
              </button>
            </div>

            <div className="json-display">
              <h3>Extracted JSON Data:</h3>
              <pre className="json-content">
                {JSON.stringify(result.data, null, 2)}
              </pre>
            </div>

            <div className="next-steps">
              <h3>Next Steps:</h3>
              <p>✅ JSON data is ready for the backend team to validate and analyze</p>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
