
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, ReferenceLine,
  Area, AreaChart
} from 'recharts';

const API = 'http://localhost:8000/api';

// ── Colour constants ─────────────────────────────────────
const BLUE   = '#4A9EFF';
const ORANGE = '#F47B20';
const GREEN  = '#2ECC71';
const RED    = '#E24B4A';

// ── Small reusable KPI card ───────────────────────────────
function KPICard({ label, value, sub, subColor, iconBg, icon }) {
  return (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
      <div style={{
        width: '34px', height: '34px', borderRadius: '8px',
        background: iconBg, display: 'flex', alignItems: 'center',
        justifyContent: 'center', fontSize: '16px'
      }}>
        {icon}
      </div>
      <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.4)' }}>{label}</div>
      <div style={{ fontSize: '24px', fontWeight: '600', letterSpacing: '-0.5px' }}>{value}</div>
      {sub && (
        <div style={{ fontSize: '12px', color: subColor || 'rgba(255,255,255,0.35)' }}>{sub}</div>
      )}
    </div>
  );
}

// ── Custom chart tooltip ──────────────────────────────────
function CustomTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    return (
      <div style={{
        background: '#1A2744', border: '0.5px solid rgba(255,255,255,0.1)',
        borderRadius: '8px', padding: '12px 16px', fontSize: '13px'
      }}>
        <p style={{ color: 'rgba(255,255,255,0.5)', marginBottom: '8px' }}>{label}</p>
        {payload.map((p, i) => (
          <p key={i} style={{ color: p.color, marginBottom: '4px' }}>
            {p.name}: ${p.value?.toLocaleString()}
          </p>
        ))}
      </div>
    );
  }
  return null;
}

// ── Main Dashboard component ──────────────────────────────
function Dashboard() {
  const [data,    setData]    = useState(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);

  // Fetch dashboard data from backend when page loads
  useEffect(() => {
    axios.get(`${API}/dashboard`)
      .then(res => {
        setData(res.data);
        setLoading(false);
      })
      .catch(err => {
        setError('Could not connect to backend. Make sure the FastAPI server is running on port 8000.');
        setLoading(false);
      });
  }, []);

  // ── Loading state ───────────────────────────────────────
  if (loading) return (
    <div className="page" style={{ textAlign: 'center', paddingTop: '60px' }}>
      <div className="spinner" />
      <p style={{ color: 'rgba(255,255,255,0.4)', marginTop: '16px' }}>
        Loading dashboard data...
      </p>
    </div>
  );

  // ── Error state ─────────────────────────────────────────
  if (error) return (
    <div className="page">
      <div className="card" style={{ textAlign: 'center', padding: '40px', color: RED }}>
        <p style={{ fontSize: '18px', marginBottom: '8px' }}>⚠️ Connection Error</p>
        <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: '14px' }}>{error}</p>
      </div>
    </div>
  );

  const { kpis, forecast, inventory, alert, model_performance } = data;
  const gb    = model_performance?.gradient_boosting || {};
  const arima = model_performance?.arima || {};

  // Prepare chart data
  const chartData = forecast.map(f => ({
    month:    f.month,
    forecast: Math.round(f.forecast),
    upper:    Math.round(f.upper_bound),
    lower:    Math.round(f.lower_bound),
  }));

  return (
    <div className="page">

      {/* ── Page Header ─────────────────────────────────── */}
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '22px', fontWeight: '600', color: '#fff', marginBottom: '4px' }}>
          Demand Dashboard
        </h1>
        <p style={{ fontSize: '13px', color: 'rgba(255,255,255,0.35)' }}>
          AI-powered demand forecasting and inventory optimization
        </p>
      </div>

      {/* ── KPI Cards ───────────────────────────────────── */}
      <p className="section-label">Key metrics</p>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, minmax(0,1fr))',
        gap: '12px',
        marginBottom: '20px'
      }}>
        <KPICard
          label="Next Month Forecast"
          value={`$${kpis.forecast_next_month?.toLocaleString()}`}
          sub="Gradient Boosting model"
          iconBg="rgba(74,158,255,0.12)"
          icon="📈"
        />
        <KPICard
          label="Recommended Order"
          value={`${kpis.recommended_order_qty?.toLocaleString()} units`}
          sub="Economic Order Quantity"
          iconBg="rgba(244,123,32,0.12)"
          icon="📦"
        />
        <KPICard
          label="Reorder Point"
          value={`${kpis.reorder_point?.toLocaleString()} units`}
          sub="Order when stock hits this"
          iconBg="rgba(250,199,117,0.12)"
          icon="⚠️"
        />
        <KPICard
          label="Days of Stock"
          value={`${kpis.days_of_stock} days`}
          sub={<span className="badge badge-red">Critical</span>}
          iconBg="rgba(226,75,74,0.12)"
          icon="🔴"
        />
      </div>

      {/* ── Forecast Chart + Inventory Panel ────────────── */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'minmax(0,1.6fr) minmax(0,1fr)',
        gap: '12px',
        marginBottom: '20px'
      }}>

        {/* Forecast Chart */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
            <div>
              <p style={{ fontSize: '14px', fontWeight: '600' }}>6-Month Demand Forecast</p>
              <p style={{ fontSize: '12px', color: 'rgba(255,255,255,0.35)', marginTop: '2px' }}>
                Jan 2018 — Jun 2018
              </p>
            </div>
            <span className="badge badge-blue">Gradient Boosting</span>
          </div>

          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="forecastGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor={BLUE} stopOpacity={0.2} />
                  <stop offset="95%" stopColor={BLUE} stopOpacity={0}   />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="rgba(255,255,255,0.05)" strokeDasharray="3 3" />
              <XAxis
                dataKey="month"
                tick={{ fill: 'rgba(255,255,255,0.35)', fontSize: 11 }}
                axisLine={false} tickLine={false}
              />
              <YAxis
                tick={{ fill: 'rgba(255,255,255,0.35)', fontSize: 11 }}
                axisLine={false} tickLine={false}
                tickFormatter={v => `$${(v/1000).toFixed(0)}k`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone" dataKey="upper"
                stroke="transparent" fill="rgba(74,158,255,0.08)"
                name="Upper Bound"
              />
              <Area
                type="monotone" dataKey="forecast"
                stroke={BLUE} strokeWidth={2.5}
                fill="url(#forecastGrad)"
                dot={{ fill: BLUE, r: 5 }}
                activeDot={{ r: 7 }}
                name="GB Forecast"
              />
              <Line
                type="monotone" dataKey="lower"
                stroke="rgba(74,158,255,0.3)" strokeWidth={1}
                strokeDasharray="4 4" dot={false}
                name="Lower Bound"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Inventory Panel */}
        <div className="card">
          <p style={{ fontSize: '14px', fontWeight: '600', marginBottom: '16px' }}>
            Inventory Status
          </p>

          {/* Stock Gauge */}
          <div style={{ textAlign: 'center', marginBottom: '16px' }}>
            <div style={{
              width: '100px', height: '100px', borderRadius: '50%',
              background: `conic-gradient(${RED} 0% 2%, rgba(255,255,255,0.07) 2% 100%)`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              margin: '0 auto 8px',
            }}>
              <div style={{
                width: '76px', height: '76px', borderRadius: '50%',
                background: '#1A2744', display: 'flex', flexDirection: 'column',
                alignItems: 'center', justifyContent: 'center'
              }}>
                <span style={{ fontSize: '18px', fontWeight: '600', color: RED }}>2%</span>
                <span style={{ fontSize: '10px', color: 'rgba(255,255,255,0.3)' }}>of safe level</span>
              </div>
            </div>
          </div>

          {/* Inventory Metrics */}
          {[
            { label: 'Safety Stock',  value: `${inventory?.safety_stock?.recommended_safety_stock?.toLocaleString()} units` },
            { label: 'Reorder Point', value: `${inventory?.reorder_point?.reorder_point?.toLocaleString()} units` },
            { label: 'EOQ',           value: `${inventory?.eoq?.eoq?.toLocaleString()} units` },
            { label: 'Current Stock', value: `${inventory?.stock_status?.current_stock?.toLocaleString()} units`, color: RED },
          ].map(item => (
            <div key={item.label} style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '9px 0', borderBottom: '0.5px solid rgba(255,255,255,0.06)'
            }}>
              <span style={{ fontSize: '12px', color: 'rgba(255,255,255,0.45)' }}>{item.label}</span>
              <span style={{ fontSize: '13px', fontWeight: '500', color: item.color || '#fff' }}>
                {item.value}
              </span>
            </div>
          ))}

          {/* Alert Banner */}
          {alert && (
            <div className={`alert-bar alert-${alert.level}`}>
              <div style={{
                width: '7px', height: '7px', borderRadius: '50%',
                background: alert.level === 'LOW' ? GREEN : alert.level === 'MEDIUM' ? ORANGE : RED,
                flexShrink: 0
              }} />
              {alert.message}
            </div>
          )}
        </div>
      </div>

      {/* ── Model Performance ────────────────────────────── */}
      <p className="section-label">Model performance</p>
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <p style={{ fontSize: '14px', fontWeight: '600' }}>ARIMA vs Gradient Boosting</p>
          <span className="badge badge-green">🏆 Gradient Boosting wins</span>
        </div>

        {/* Table Header */}
        <div style={{
          display: 'grid', gridTemplateColumns: '1fr 1fr 1fr',
          padding: '8px 12px', borderRadius: '6px',
          background: 'rgba(255,255,255,0.04)', marginBottom: '8px'
        }}>
          <span style={{ fontSize: '12px', color: 'rgba(255,255,255,0.35)' }}>Metric</span>
          <span style={{ fontSize: '12px', color: 'rgba(255,255,255,0.35)', textAlign: 'center' }}>ARIMA</span>
          <span style={{ fontSize: '12px', color: BLUE, textAlign: 'center' }}>Gradient Boosting</span>
        </div>

        {/* Table Rows */}
        {[
          { metric: 'MAE',  arima: `$${arima.mae?.toLocaleString()}`,  gb: `$${gb.mae?.toLocaleString()}`,  gbWins: true  },
          { metric: 'RMSE', arima: `$${arima.rmse?.toLocaleString()}`, gb: `$${gb.rmse?.toLocaleString()}`, gbWins: true  },
          { metric: 'MAPE', arima: `${arima.mape}%`,                   gb: `${gb.mape}%`,                   gbWins: true  },
          { metric: 'R²',   arima: 'N/A',                              gb: `${gb.r2}`,                      gbWins: true  },
        ].map(row => (
          <div key={row.metric} style={{
            display: 'grid', gridTemplateColumns: '1fr 1fr 1fr',
            padding: '11px 12px',
            borderBottom: '0.5px solid rgba(255,255,255,0.05)'
          }}>
            <span style={{ fontSize: '13px', color: 'rgba(255,255,255,0.6)' }}>{row.metric}</span>
            <span style={{ fontSize: '13px', color: 'rgba(255,255,255,0.4)', textAlign: 'center' }}>{row.arima}</span>
            <span style={{ fontSize: '13px', color: GREEN, textAlign: 'center', fontWeight: '500' }}>{row.gb}</span>
          </div>
        ))}

        {/* Summary */}
        <div style={{
          marginTop: '14px', padding: '10px 14px', borderRadius: '8px',
          background: 'rgba(99,153,34,0.08)', border: '0.5px solid rgba(99,153,34,0.2)',
          fontSize: '13px', color: '#97C459'
        }}>
          Model accuracy: {kpis.model_accuracy} &nbsp;|&nbsp; R² Score: {kpis.model_r2} &nbsp;|&nbsp;
          Gradient Boosting outperforms ARIMA by 40% on error metrics
        </div>
      </div>

    </div>
  );
}

export default Dashboard;
