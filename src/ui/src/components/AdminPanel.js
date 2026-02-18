import React, { useState } from 'react';
import './AdminPanel.css';

const ONE_YEAR_MS = 365 * 24 * 60 * 60 * 1000;
const ADMIN_PASSWORD = '0000';

// ── Password gate ────────────────────────────────────────────
function PasswordGate({ onUnlock }) {
  const [digits, setDigits] = useState(['', '', '', '']);
  const [error, setError]   = useState(false);
  const refs = [React.createRef(), React.createRef(), React.createRef(), React.createRef()];

  const handleChange = (i, val) => {
    if (!/^\d?$/.test(val)) return;
    const next = [...digits];
    next[i] = val;
    setDigits(next);
    setError(false);
    if (val && i < 3) refs[i + 1].current.focus();
    if (next.every(d => d !== '') && next.join('').length === 4) {
      setTimeout(() => checkPassword(next), 80);
    }
  };

  const handleKeyDown = (i, e) => {
    if (e.key === 'Backspace' && !digits[i] && i > 0) {
      refs[i - 1].current.focus();
    }
  };

  const checkPassword = (d) => {
    const entered = d.join('');
    if (entered === ADMIN_PASSWORD) {
      onUnlock();
    } else {
      setError(true);
      setDigits(['', '', '', '']);
      setTimeout(() => refs[0].current.focus(), 50);
    }
  };

  return (
    <div className="gate-wrap">
      <div className="gate-card">
        <div className="gate-icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
            <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
            <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
          </svg>
        </div>
        <h2 className="gate-title">Accès Administration</h2>
        <p className="gate-sub">Entrez le code à 4 chiffres</p>

        <div className={`pin-row ${error ? 'pin-error' : ''}`}>
          {digits.map((d, i) => (
            <input
              key={i}
              ref={refs[i]}
              className={`pin-input ${error ? 'input-error' : ''}`}
              type="password"
              inputMode="numeric"
              maxLength={1}
              value={d}
              onChange={e => handleChange(i, e.target.value)}
              onKeyDown={e => handleKeyDown(i, e)}
              autoFocus={i === 0}
            />
          ))}
        </div>

        {error && (
          <p className="gate-error-msg">Code incorrect — réessayez</p>
        )}
      </div>
    </div>
  );
}

// ── Main admin panel ─────────────────────────────────────────
function AdminPanel({ refValues, onUpdate }) {
  const [unlocked, setUnlocked] = useState(false);
  const [inputs, setInputs]     = useState({ smic: '', plafond_ss: '' });
  const [status, setStatus]     = useState({});

  if (!unlocked) return <PasswordGate onUnlock={() => setUnlocked(true)} />;
  if (!refValues) return <div className="admin-loading">Chargement…</div>;

  const handleUpdate = async (key) => {
    const val = parseFloat(inputs[key]);
    if (isNaN(val) || val <= 0) {
      setStatus(s => ({ ...s, [key]: { type: 'error', msg: 'Valeur invalide.' } }));
      return;
    }
    setStatus(s => ({ ...s, [key]: { type: 'loading', msg: 'Enregistrement…' } }));
    const res = await onUpdate(key, val);
    if (res.success) {
      setStatus(s => ({ ...s, [key]: { type: 'ok', msg: 'Mis à jour ✓' } }));
      setInputs(i => ({ ...i, [key]: '' }));
      setTimeout(() => setStatus(s => ({ ...s, [key]: null })), 3000);
    } else {
      setStatus(s => ({ ...s, [key]: { type: 'error', msg: res.error || 'Erreur serveur' } }));
    }
  };

  const cards = [
    {
      key: 'smic',
      label: 'SMIC mensuel brut',
      sub: 'Base 151,67 heures · Art. L3231-2 Code du travail',
      data: refValues.smic,
    },
    {
      key: 'plafond_ss',
      label: 'Plafond Sécurité Sociale mensuel',
      sub: 'Plafond de la SS · Art. L241-3 Code de la sécurité sociale',
      data: refValues.plafond_ss,
    },
  ];

  return (
    <div className="admin-page">
      <div className="admin-hero">
        <div className="admin-hero-row">
          <div>
            <h1>Administration</h1>
            <p className="admin-sub">Valeurs de référence SMIC &amp; Plafond SS</p>
          </div>
          <button className="lock-btn" onClick={() => setUnlocked(false)} title="Verrouiller">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
              <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
            </svg>
            Verrouiller
          </button>
        </div>
      </div>

      <div className="admin-cards">
        {cards.map(({ key, label, sub, data }) => {
          const stale = Date.now() - new Date(data.updated).getTime() > ONE_YEAR_MS;
          const s = status[key];
          return (
            <div key={key} className={`admin-card ${stale ? 'stale' : ''}`}>
              <div className="admin-card-label">{label}</div>
              <div className={`admin-value ${stale ? 'val-stale' : 'val-ok'}`}>
                {formatEur(data.value)}
              </div>
              <div className="admin-update-row">
                <span className={`update-dot ${stale ? 'dot-red' : 'dot-green'}`} />
                <span className="update-date">Dernière MàJ : {formatDate(data.updated)}</span>
              </div>
              {stale && (
                <div className="stale-warning">
                  ⚠ Non mis à jour depuis plus d'un an — vérifiez la valeur légale en vigueur
                </div>
              )}
              <div className="admin-sub-text">{sub}</div>
              <div className="admin-form">
                <div className="form-row">
                  <input
                    type="number"
                    className="admin-input"
                    placeholder={`Ex: ${data.value}`}
                    value={inputs[key]}
                    onChange={e => setInputs(i => ({ ...i, [key]: e.target.value }))}
                    step="0.01"
                    onKeyDown={e => e.key === 'Enter' && handleUpdate(key)}
                  />
                  <button
                    className="admin-btn"
                    onClick={() => handleUpdate(key)}
                    disabled={s?.type === 'loading'}
                  >
                    {s?.type === 'loading' ? '…' : 'Mettre à jour'}
                  </button>
                </div>
                {s && <div className={`form-status ${s.type}`}>{s.msg}</div>}
              </div>
            </div>
          );
        })}
      </div>

      <div className="admin-info-box">
        <div className="info-icon">ℹ</div>
        <div>
          <strong>Ces valeurs sont utilisées pour toutes les analyses</strong>
          <p>Le SMIC et le Plafond SS servent de référence pour calculer la réduction RGDU et le plafonnement SS. Mettez-les à jour à chaque début d'année ou après publication au Journal Officiel.</p>
        </div>
      </div>
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
    day: '2-digit', month: 'long', year: 'numeric'
  });
}

export default AdminPanel;
