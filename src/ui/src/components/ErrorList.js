import React from 'react';
import './ErrorList.css';

function ErrorList({ errors, recommendations }) {
  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'critical': return '🔴';
      case 'warning': return '🟡';
      case 'info': return '🔵';
      default: return '⚪';
    }
  };

  const getSeverityLabel = (severity) => {
    switch (severity) {
      case 'critical': return 'Critique';
      case 'warning': return 'Attention';
      case 'info': return 'Information';
      default: return severity;
    }
  };

  return (
    <div className="error-list">
      <div className="errors-section">
        <h3>Anomalies détectées ({errors?.length || 0})</h3>
        
        {errors && errors.length > 0 ? (
          <div className="errors-container">
            {errors.map((error, index) => (
              <div key={index} className={`error-card severity-${error.severity}`}>
                <div className="error-header">
                  <span className="severity-badge">
                    {getSeverityIcon(error.severity)} {getSeverityLabel(error.severity)}
                  </span>
                  <span className="error-type">{error.error_type}</span>
                </div>
                
                <div className="error-body">
                  <h4>{error.field}</h4>
                  <p className="error-description">{error.description}</p>
                  
                  {error.suggested_fix && (
                    <div className="suggested-fix">
                      <span className="fix-icon">💡</span>
                      <span>{error.suggested_fix}</span>
                    </div>
                  )}
                  
                  {error.legal_reference && (
                    <div className="legal-reference">
                      <span className="reference-icon">⚖️</span>
                      <span>{error.legal_reference}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="no-errors">
            <span className="success-icon">✅</span>
            <p>Aucune anomalie détectée</p>
          </div>
        )}
      </div>

      {recommendations && recommendations.length > 0 && (
        <div className="recommendations-section">
          <h3>Recommandations</h3>
          <ul className="recommendations-list">
            {recommendations.map((rec, index) => (
              <li key={index}>
                <span className="rec-icon">💡</span>
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default ErrorList;
