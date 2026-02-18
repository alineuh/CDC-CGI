import React, { useState } from 'react';
import './ResultsPanel.css';

function ResultsPanel({ result, onReset }) {
  const [activeIdx, setActiveIdx] = useState(0);

  const analysis = result.analysis || [];
  const bulletin = analysis[activeIdx];
  const header = bulletin?.header || {};
  const checks = bulletin?.checks || [];
  const totalKO = result.total_ko || 0;
  const totalOK = (result.total_checks || 0) - totalKO;

  const downloadJSON = () => {
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analyse_${result.filename?.replace('.pdf', '') || 'bulletin'}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="results-panel">
      {/* Top bar */}
      <div className="results-topbar">
        <div className="results-title-row">
          <h2 className="results-title">Résultats d'analyse</h2>
          <span className="filename-tag">📎 {result.filename}</span>
        </div>
        <div className="results-actions">
          <button className="btn-outline" onClick={downloadJSON}>↓ JSON</button>
          <button className="btn-outline" onClick={onReset}>← Nouvelle</button>
        </div>
      </div>

      {/* Summary badges */}
      <div className="summary-badges">
        <div className="summary-badge badge-ok">
          <span className="badge-num">{totalOK}</span>
          <span className="badge-label">Vérifications OK</span>
        </div>
        <div className={`summary-badge ${totalKO > 0 ? 'badge-ko' : 'badge-ok'}`}>
          <span className="badge-num">{totalKO}</span>
          <span className="badge-label">{totalKO > 0 ? 'Anomalies détectées' : 'Aucune anomalie'}</span>
        </div>
        <div className="summary-badge badge-info">
          <span className="badge-num">{analysis.length}</span>
          <span className="badge-label">Bulletin(s) analysé(s)</span>
        </div>
        <div className="summary-badge badge-info">
          <span className="badge-num">{formatEur(result.ref?.smic)}</span>
          <span className="badge-label">SMIC utilisé</span>
        </div>
      </div>

      {/* Bulletin selector if multiple */}
      {analysis.length > 1 && (
        <div className="bulletin-tabs">
          {analysis.map((b, i) => (
            <button
              key={i}
              className={`bulletin-tab ${activeIdx === i ? 'active' : ''} ${b.has_errors ? 'has-error' : ''}`}
              onClick={() => setActiveIdx(i)}
            >
              Bulletin #{b.header?.bulletin_num || i + 1}
              {b.has_errors && <span className="tab-dot" />}
            </button>
          ))}
        </div>
      )}

      {/* Header meta */}
      <div className="meta-grid">
        {[
          ['Bulletin n°', header.bulletin_num ?? '—'],
          ['Matricule', header.matricule ?? '—'],
          ['Période', header.periode ? `${header.periode.du} → ${header.periode.au}` : '—'],
          ['Convention', header.convention_collective ?? '—'],
          ['Coefficient', header.coefficient ?? '—'],
          ['Échelon', header.echelon ? `${header.echelon.niveau} · ${header.echelon.apres_ans} ans` : '—'],
        ].map(([k, v]) => (
          <div className="meta-item" key={k}>
            <div className="meta-key">{k}</div>
            <div className="meta-val">{v}</div>
          </div>
        ))}
      </div>

      {/* Checks table */}
      <div className="checks-section">
        <h3 className="checks-title">Contrôles de conformité</h3>
        <div className="checks-table-wrap">
          <table className="checks-table">
            <thead>
              <tr>
                <th>Ligne vérifiée</th>
                <th>Statut</th>
                <th className="num">Valeur extraite</th>
                <th className="num">Valeur attendue</th>
                <th className="num">Écart</th>
              </tr>
            </thead>
            <tbody>
              {checks.map((row, i) => {
                const [label, status, extracted, expected] = row;
                const isKO = status === 'KO';
                const isErr = label === 'ERREUR';
                const ecart = (typeof extracted === 'number' && typeof expected === 'number')
                  ? (extracted - expected).toFixed(2)
                  : '—';
                return (
                  <tr key={i} className={isKO ? 'row-ko' : 'row-ok'}>
                    <td className="check-label">{label}</td>
                    <td>
                      <span className={`status-pill ${isKO ? 'pill-ko' : 'pill-ok'}`}>
                        {isKO ? '✗ KO' : '✓ OK'}
                      </span>
                    </td>
                    <td className="num">
                      {isErr ? '—' : formatNum(extracted)}
                    </td>
                    <td className="num">
                      {typeof expected === 'string' ? expected : formatNum(expected)}
                    </td>
                    <td className={`num ${isKO ? 'ecart-ko' : 'ecart-ok'}`}>
                      {isErr ? '—' : (isKO ? ecart + ' €' : '0,00 €')}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Raw bulletin lignes */}
      {result.raw_bulletins?.[activeIdx]?.table?.lignes?.length > 0 && (
        <details className="raw-section">
          <summary className="raw-summary">
            <span>Détail des lignes parsées</span>
            <span className="raw-count">{result.raw_bulletins[activeIdx].table.lignes.length} lignes</span>
          </summary>
          <div className="checks-table-wrap" style={{ marginTop: '12px' }}>
            <table className="checks-table">
              <thead>
                <tr>
                  <th>Section</th>
                  <th>Intitulé</th>
                  <th className="num">Base</th>
                  <th className="num">Taux</th>
                  <th className="num">Salarié</th>
                  <th className="num">Employeur</th>
                </tr>
              </thead>
              <tbody>
                {result.raw_bulletins[activeIdx].table.lignes.map((ligne, i) => (
                  <tr key={i}>
                    <td className="section-cell">{ligne.section || '—'}</td>
                    <td>{ligne.intitule}</td>
                    <td className="num">{ligne.salarie?.base != null ? formatNum(ligne.salarie.base) : '—'}</td>
                    <td className="num">{ligne.salarie?.taux != null ? ligne.salarie.taux + ' %' : '—'}</td>
                    <td className="num">{ligne.salarie?.montant != null ? formatNum(ligne.salarie.montant) : '—'}</td>
                    <td className="num">{ligne.employeur?.montant != null ? formatNum(ligne.employeur.montant) : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </details>
      )}
    </div>
  );
}

function formatEur(v) {
  if (v == null) return '—';
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR', maximumFractionDigits: 2 }).format(v);
}

function formatNum(n) {
  if (n == null) return '—';
  return new Intl.NumberFormat('fr-FR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(n);
}

export default ResultsPanel;
