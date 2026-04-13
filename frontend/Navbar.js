// ── DemandSense — Navbar.js ─────────────────────────────
// Top navigation bar shown on every page

import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

const styles = {
  navbar: {
    background: '#0B1220',
    borderBottom: '0.5px solid rgba(255,255,255,0.08)',
    padding: '0 24px',
    height: '60px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    position: 'sticky',
    top: 0,
    zIndex: 100,
  },
  logo: {
    fontSize: '22px',
    fontWeight: '600',
    cursor: 'pointer',
    letterSpacing: '-0.3px',
  },
  logoBlue:   { color: '#4A9EFF' },
  logoOrange: { color: '#F47B20' },
  nav: {
    display: 'flex',
    gap: '6px',
    alignItems: 'center',
  },
  navTag: {
    fontSize: '12px',
    color: 'rgba(255,255,255,0.35)',
    marginRight: '8px',
    letterSpacing: '0.5px',
  }
};

function Navbar() {
  const navigate  = useNavigate();
  const location  = useLocation();

  const linkStyle = (path) => ({
    color:        location.pathname === path ? '#4A9EFF' : 'rgba(255,255,255,0.5)',
    background:   location.pathname === path ? 'rgba(74,158,255,0.12)' : 'transparent',
    padding:      '7px 16px',
    borderRadius: '6px',
    fontSize:     '13px',
    cursor:       'pointer',
    border:       'none',
    fontFamily:   'inherit',
    transition:   'all 0.15s',
  });

  return (
    <nav style={styles.navbar}>
      {/* Logo */}
      <div style={styles.logo} onClick={() => navigate('/')}>
        <span style={styles.logoBlue}>Demand</span>
        <span style={styles.logoOrange}>Sense</span>
      </div>

      {/* Navigation Links */}
      <div style={styles.nav}>
        <span style={styles.navTag}>AI-Powered Forecasting</span>
        <button style={linkStyle('/')}       onClick={() => navigate('/')}>
          Dashboard
        </button>
        <button style={linkStyle('/upload')} onClick={() => navigate('/upload')}>
          Upload Data
        </button>
      </div>
    </nav>
  );
}

export default Navbar;
