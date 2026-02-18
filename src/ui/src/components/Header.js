import React from 'react';
import './Header.css';

function Header() {
  return (
    <header className="header">
      <div className="header-content">
        <div className="logo">
          <h1>📊 Payslip Analyzer</h1>
          <span className="tagline">Détection intelligente d'anomalies</span>
        </div>
        <div className="header-info">
          <span className="badge">CEGI x ESILV</span>
        </div>
      </div>
    </header>
  );
}

export default Header;
