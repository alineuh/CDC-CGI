import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import './UploadZone.css';

function UploadZone({ onUpload, loading }) {
  const onDrop = useCallback(acceptedFiles => {
    if (acceptedFiles.length > 0) {
      onUpload(acceptedFiles[0]);
    }
  }, [onUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/json': ['.json']
    },
    multiple: false
  });

  return (
    <div 
      {...getRootProps()} 
      className={`upload-zone ${isDragActive ? 'drag-active' : ''} ${loading ? 'loading' : ''}`}
    >
      <input {...getInputProps()} />
      
      {loading ? (
        <div className="upload-loading">
          <div className="spinner"></div>
          <p>Analyse en cours...</p>
          <span className="loading-subtitle">Extraction et validation des données</span>
        </div>
      ) : (
        <>
          <div className="upload-icon">📄</div>
          <h3>
            {isDragActive 
              ? 'Déposez le fichier ici' 
              : 'Glissez-déposez votre fiche de paie'}
          </h3>
          <p>ou cliquez pour sélectionner un fichier</p>
          <span className="file-info">Formats acceptés: PDF, JSON</span>
        </>
      )}
    </div>
  );
}

export default UploadZone;
