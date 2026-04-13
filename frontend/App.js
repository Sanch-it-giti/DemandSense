// ── DemandSense — App.js ────────────────────────────────
// This is the root component. It sets up:
// 1. Routing between Dashboard and Upload pages
// 2. Navbar shown on every page

import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './index.css';

import Navbar      from './components/Navbar';
import Dashboard   from './components/Dashboard';
import UploadPage  from './components/UploadPage';

function App() {
  return (
    <Router>
      {/* Navbar always visible at the top */}
      <Navbar />

      {/* Page content changes based on URL */}
      <Routes>
        <Route path="/"       element={<Dashboard />} />
        <Route path="/upload" element={<UploadPage />} />
      </Routes>
    </Router>
  );
}

export default App;
