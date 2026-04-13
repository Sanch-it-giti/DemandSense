

import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const API = 'http://localhost:8000/api';

function UploadPage({ onForecastReady }) {
  const [file,     setFile]     = useState(null);
  const [periods,  setPeriods]  = useState(6);
  const [loading,  setLoading]  = useState(false);
  const [result,   setResult]   = useState(null);
  const [error,    setError]    = useState(null);
  const [dragging, setDragging] = useState(false);
  const fileInputRef = useRef();
  const navigate     = useNavigate();

  const handleFile = (f) => {
    if (f && f.name.endsWith('.csv')) {
      setFile(f); setError(null); setResult(null);
    } else {
      setError('Please select a valid CSV file.');
    }
  };

  const onDragOver  = (e) => { e.preventDefault(); setDragging(true);  };
  const onDragLeave = (e) => { e.preventDefault(); setDragging(false); };
  const onDrop      = (e) => {
    e.preventDefault(); setDragging(false);
    handleFile(e.dataTransfer.files[0]);
  };

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true); setError(null); setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await axios.post(
        `${API}/forecast?periods=${periods}`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      setResult(res.data);

      // ── KEY CHANGE: send forecast up to App.js ──────────
      // This makes the Dashboard update with new data
      if (onForecastReady) {
        onForecastReady(res.data);
      }

    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Upload failed. Make sure the backend is running on port 8000.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '22px', fontWeight: '600', marginBottom: '4px' }}>
          Upload Sales Data
        </h1>
        <p style={{ fontSize: '13px', color: 'rgba(255,255,255,0.35)' }}>
          Upload your CSV file to generate a fresh AI demand forecast
        </p>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'minmax(0,1fr) minmax(0,1fr)',
        gap: '20px', alignItems: 'start'
      }}>

        {/* ── Upload Card ───────────────────────────────── */}
        <div className="card">
          <p style={{ fontSize: '14px', fontWeight: '600', marginBottom: '16px' }}>
            Upload CSV File
          </p>

          <div
            onDragOver={onDragOver} onDragLeave={onDragLeave} onDrop={onDrop}
            onClick={() => fileInputRef.current.click()}
            style={{
              border: `1.5px dashed ${dragging ? '#4A9EFF' : file ? '#2ECC71' : 'rgba(255,255,255,0.12)'}`,
              borderRadius: '10px', padding: '40px 20px',
              textAlign: 'center', cursor: 'pointer',
              transition: 'border-color 0.2s', marginBottom: '16px',
              background: dragging ? 'rgba(74,158,255,0.04)' : 'transparent'
            }}
          >
            <div style={{ fontSize: '32px', marginBottom: '12px' }}>
              {file ? '✅' : '📂'}
            </div>
            {file ? (
              <>
                <p style={{ color: '#2ECC71', fontWeight: '500', marginBottom: '4px' }}>{file.name}</p>
                <p style={{ fontSize: '12px', color: 'rgba(255,255,255,0.35)' }}>
                  {(file.size / 1024).toFixed(1)} KB — Click to change
                </p>
              </>
            ) : (
              <>
                <p style={{ color: 'rgba(255,255,255,0.6)', marginBottom: '6px' }}>
                  Drop your sales CSV here
                </p>
                <p style={{ fontSize: '12px', color: 'rgba(255,255,255,0.3)' }}>
                  or click to browse — Superstore format supported
                </p>
              </>
            )}
          </div>

          <input
            type="file" accept=".csv" ref={fileInputRef}
            style={{ display: 'none' }}
            onChange={(e) => handleFile(e.target.files[0])}
          />

          {/* Forecast Period */}
          <div style={{ marginBottom: '16px' }}>
            <label style={{ fontSize: '12px', color: 'rgba(255,255,255,0.4)', display: 'block', marginBottom: '8px' }}>
              Forecast Period
            </label>
            <select
              value={periods} onChange={(e) => setPeriods(Number(e.target.value))}
              style={{
                width: '100%', padding: '10px 12px',
                background: 'rgba(255,255,255,0.05)',
                border: '0.5px solid rgba(255,255,255,0.1)',
                borderRadius: '8px', color: '#fff',
                fontSize: '13px', fontFamily: 'inherit', cursor: 'pointer'
              }}
            >
              <option value={3}>3 months</option>
              <option value={6}>6 months</option>
              <option value={12}>12 months</option>
              <option value={24}>24 months</option>
            </select>
          </div>

          {error && (
            <div style={{
              padding: '10px 14px', borderRadius: '8px', marginBottom: '14px',
              background: 'rgba(226,75,74,0.1)', border: '0.5px solid rgba(226,75,74,0.3)',
              color: '#F09595', fontSize: '13px'
            }}>
              ⚠️ {error}
            </div>
          )}

          <button
            className="btn-primary" onClick={handleUpload}
            disabled={!file || loading}
          >
            {loading ? 'Running forecast...' : '🚀 Upload & Forecast'}
          </button>

          {/* Go to Dashboard button — appears after forecast */}
          {result && (
            <button
              onClick={() => navigate('/')}
              style={{
                width: '100%', marginTop: '10px', padding: '10px',
                background: 'rgba(46,204,113,0.1)',
                border: '0.5px solid rgba(46,204,113,0.3)',
                borderRadius: '8px', color: '#2ECC71',
                fontSize: '13px', fontWeight: '500', cursor: 'pointer'
              }}
            >
              ✅ View Updated Dashboard →
            </button>
          )}
        </div>

        {/* ── Results Card ──────────────────────────────── */}
        <div className="card">
          <p style={{ fontSize: '14px', fontWeight: '600', marginBottom: '16px' }}>
            Forecast Results
          </p>

          {!result && !loading && (
            <div style={{ textAlign: 'center', padding: '40px 20px', color: 'rgba(255,255,255,0.2)' }}>
              <div style={{ fontSize: '40px', marginBottom: '12px' }}>📊</div>
              <p style={{ fontSize: '13px' }}>Upload a CSV file to see forecast results here</p>
            </div>
          )}

          {loading && (
            <div style={{ textAlign: 'center', padding: '40px' }}>
              <div className="spinner" />
              <p style={{ color: 'rgba(255,255,255,0.4)', marginTop: '16px', fontSize: '13px' }}>
                Running AI model...
              </p>
            </div>
          )}

          {result && (
            <>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '20px' }}>
                {[
                  { label: 'Total Forecast',  value: `$${result.summary?.total_forecast?.toLocaleString()}` },
                  { label: 'Monthly Average', value: `$${result.summary?.avg_monthly?.toLocaleString()}` },
                  { label: 'Peak Month',      value: result.summary?.peak_month },
                  { label: 'Peak Value',      value: `$${result.summary?.peak_value?.toLocaleString()}` },
                ].map(item => (
                  <div key={item.label} style={{
                    background: 'rgba(255,255,255,0.04)', borderRadius: '8px', padding: '12px'
                  }}>
                    <p style={{ fontSize: '11px', color: 'rgba(255,255,255,0.35)', marginBottom: '4px' }}>{item.label}</p>
                    <p style={{ fontSize: '16px', fontWeight: '600', color: '#4A9EFF' }}>{item.value}</p>
                  </div>
                ))}
              </div>

              <p style={{ fontSize: '12px', color: 'rgba(255,255,255,0.35)', marginBottom: '10px' }}>
                Month-by-month breakdown
              </p>
              {result.forecast?.map((f, i) => (
                <div key={i} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '10px 0', borderBottom: '0.5px solid rgba(255,255,255,0.05)'
                }}>
                  <span style={{ fontSize: '13px', color: 'rgba(255,255,255,0.6)' }}>{f.month}</span>
                  <div style={{ textAlign: 'right' }}>
                    <span style={{ fontSize: '14px', fontWeight: '500', color: '#4A9EFF' }}>
                      ${f.forecast?.toLocaleString()}
                    </span>
                    <span style={{ fontSize: '11px', color: 'rgba(255,255,255,0.25)', marginLeft: '8px' }}>
                      ${f.lower_bound?.toLocaleString()} – ${f.upper_bound?.toLocaleString()}
                    </span>
                  </div>
                </div>
              ))}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default UploadPage;
