

import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './index.css';

import Navbar      from './components/Navbar';
import Dashboard   from './components/Dashboard';
import UploadPage  from './components/UploadPage';

function App() {
  // Shared forecast state — when UploadPage sets this,
  // Dashboard will automatically re-render with new data
  const [uploadedForecast, setUploadedForecast] = useState(null);

  return (
    <Router>
      <Navbar />
      <Routes>
        <Route
          path="/"
          element={<Dashboard uploadedForecast={uploadedForecast} />}
        />
        <Route
          path="/upload"
          element={<UploadPage onForecastReady={setUploadedForecast} />}
        />
      </Routes>
    </Router>
  );
}

export default App;
