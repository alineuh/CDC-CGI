import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import './UploadZone.css';

function UploadZone({ onUpload, loading }) {
  const onDrop = useCallback(acceptedFiles => {
    if (acceptedFiles.length > 0) onUpload(acceptedFiles[0]);
  }, [onUpload]);

  const { getRootProps, getInputProps, isDragActive, acceptedFiles } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    multiple: false,
    disabled: loading,
  });

  const file = acceptedFiles[0];

  return (
    <div className="upload-wrap">
      <div
        {...getRootProps()}
        className={`upload-zone ${isDragActive ? 'drag-active' : ''} ${loading ? 'is-loading' : ''}`}
      >
        <input {...getInputProps()} />

        {loading ? (
          <div className="upload-loading">
            <div className="loading-ring">
              <div /><div /><div /><div />
            </div>
            <p className="loading-title">Analyse en cours…</p>
            <div className="loading-steps">
              <span className="step done">✓ Lecture PDF</span>
              <span className="sep">·</span>
              <span className="step active">▶ Extraction</span>
              <span className="sep">·</span>
              <span className="step">Vérification</span>
            </div>
          </div>
        ) : (
          <>
            <div className="upload-icon-wrap">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
                <line x1="12" y1="18" x2="12" y2="12"/>
                <polyline points="9 15 12 12 15 15"/>
              </svg>
            </div>
            <h3 className="upload-title">
              {isDragActive ? 'Déposez ici' : 'Déposer la fiche de paie'}
            </h3>
            <p className="upload-hint">Glisser-déposer ou cliquer · PDF uniquement</p>
          </>
        )}
      </div>

      {file && !loading && (
        <div className="file-pill">
          <span className="file-pill-icon">📋</span>
          <span className="file-pill-name">{file.name}</span>
          <span className="file-pill-size">{formatSize(file.size)}</span>
        </div>
      )}
    </div>
  );
}

function formatSize(b) {
  if (b < 1024) return b + ' B';
  if (b < 1024 * 1024) return (b / 1024).toFixed(1) + ' KB';
  return (b / (1024 * 1024)).toFixed(1) + ' MB';
}

export default UploadZone;
