import React, { useState, useEffect } from 'react';
import './App.css';
import UploadZone from './components/UploadZone';
import ResultsPanel from './components/ResultsPanel';
import AdminPanel from './components/AdminPanel';

const API_BASE = 'http://localhost:8000';

function App() {
  const [tab, setTab] = useState('analyze');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [refValues, setRefValues] = useState(null);

  useEffect(() => {
    fetchRefValues();
  }, []);

  const fetchRefValues = async () => {
    try {
      const res = await fetch(`${API_BASE}/admin/values`);
      if (res.ok) setRefValues(await res.json());
    } catch {
      // fallback defaults
      setRefValues({
        smic: { value: 1823.03, updated: '2026-01-01T00:00:00.000Z' },
        plafond_ss: { value: 4005.00, updated: '2026-01-01T00:00:00.000Z' },
      });
    }
  };

  const handleUpload = async (file) => {
    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Erreur serveur');
      setResult(data);
    } catch (err) {
      setError(err.message || 'Erreur lors de l\'upload');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setError(null);
  };

  const handleRefUpdate = async (key, value) => {
    try {
      const res = await fetch(`${API_BASE}/admin/values/${key}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Erreur');
      await fetchRefValues();
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-inner">
          <div className="logo">
            <div className="logo-mark">CGI</div>
            <div className="logo-text">Paie · Analyse</div>
          </div>
          <nav className="nav">
            <button
              className={`nav-btn ${tab === 'analyze' ? 'active' : ''}`}
              onClick={() => setTab('analyze')}
            >
              Analyser
            </button>
            <button
              className={`nav-btn ${tab === 'admin' ? 'active' : ''}`}
              onClick={() => setTab('admin')}
            >
              Admin
            </button>
          </nav>
        </div>
      </header>

      <main className="main">
        {tab === 'analyze' && (
          <div className="page-analyze">
            {/* Hero */}
            <div className="hero">
              <h1>Vérification de<br /><span className="accent">fiche de paie</span></h1>
              <p className="hero-sub">Upload PDF → Parser → Détection d'anomalies</p>
            </div>

            {/* Indicators */}
            {refValues && (
              <div className="indicators">
                <div className="indicator-card">
                  <div className="indicator-label">SMIC mensuel brut</div>
                  <div className="indicator-value">{formatEur(refValues.smic.value)}</div>
                  <div className="indicator-sub">Base 151,67h · {formatDate(refValues.smic.updated)}</div>
                </div>
                <div className="indicator-card">
                  <div className="indicator-label">Plafond Séc. Sociale mensuel</div>
                  <div className="indicator-value">{formatEur(refValues.plafond_ss.value)}</div>
                  <div className="indicator-sub">PSS mensuel · {formatDate(refValues.plafond_ss.updated)}</div>
                </div>
              </div>
            )}

            {/* Upload or Results */}
            {!result ? (
              <div className="upload-section">
                {error && (
                  <div className="error-banner">
                    <span>⚠</span> {error}
                  </div>
                )}
                <UploadZone onUpload={handleUpload} loading={loading} />
              </div>
            ) : (
              <ResultsPanel result={result} onReset={handleReset} />
            )}
          </div>
        )}

        {tab === 'admin' && (
          <AdminPanel
            refValues={refValues}
            onUpdate={handleRefUpdate}
          />
        )}
      </main>
    </div>
  );
}

function formatEur(v) {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency', currency: 'EUR', maximumFractionDigits: 2
  }).format(v);
}

function formatDate(iso) {
  return new Date(iso).toLocaleDateString('fr-FR', {
    day: '2-digit', month: 'short', year: 'numeric'
  });
}

export default App;
