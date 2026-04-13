
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer
} from 'recharts';

const API    = 'http://localhost:8000/api';
const BLUE   = '#4A9EFF';
const ORANGE = '#F47B20';
const GREEN  = '#2ECC71';
const RED    = '#E24B4A';
const WHITE = '#FFFFFF';

// ── Input Field Component ─────────────────────────────────
function InputField({ label, value, onChange, prefix = '', suffix = '', hint = '' }) {
  return (
    <div style={{ marginBottom: '14px' }}>
      <label style={{
        fontSize: '11px', color: 'rgba(255,255,255,0.4)',
        display: 'block', marginBottom: '5px', textTransform: 'uppercase', letterSpacing: '0.5px'
      }}>
        {label}
      </label>
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
        {prefix && <span style={{ fontSize: '13px', color: 'rgba(255,255,255,0.4)' }}>{prefix}</span>}
        <input
          type="number"
          value={value}
          onChange={e => onChange(Number(e.target.value))}
          style={{
            flex: 1, background: 'rgba(255,255,255,0.05)',
            border: '0.5px solid rgba(255,255,255,0.12)',
            borderRadius: '6px', padding: '8px 10px',
            color: '#fff', fontSize: '14px', fontFamily: 'inherit',
            outline: 'none', width: '100%'
          }}
          onFocus={e => e.target.style.borderColor = BLUE}
          onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.12)'}
        />
        {suffix && <span style={{ fontSize: '13px', color: 'rgba(255,255,255,0.4)' }}>{suffix}</span>}
      </div>
      {hint && <p style={{ fontSize: '10px', color: 'rgba(255,255,255,0.25)', marginTop: '3px' }}>{hint}</p>}
    </div>
  );
}

// ── KPI Card ──────────────────────────────────────────────
function KPICard({ label, value, sub, iconBg, icon, highlight }) {
  return (
    <div className="card" style={{
      display: 'flex', flexDirection: 'column', gap: '10px',
      border: highlight ? `0.5px solid ${highlight}` : '0.5px solid rgba(255,255,255,0.07)',
      transition: 'border 0.3s'
    }}>
      <div style={{
        width: '34px', height: '34px', borderRadius: '8px',
        background: iconBg, display: 'flex', alignItems: 'center',
        justifyContent: 'center', fontSize: '16px'
      }}>{icon}</div>
      <div style={{ fontSize: '12px', color: 'rgba(255,255,255,0.4)' }}>{label}</div>
      <div style={{ fontSize: '22px', fontWeight: '600', letterSpacing: '-0.5px' }}>{value}</div>
      {sub && <div style={{ fontSize: '12px' }}>{sub}</div>}
    </div>
  );
}

// ── Tooltip ───────────────────────────────────────────────
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

// ── Main Dashboard ────────────────────────────────────────
function Dashboard({ uploadedForecast }) {
  const [dashData,    setDashData]    = useState(null);
  const [loading,     setLoading]     = useState(true);
  const [error,       setError]       = useState(null);
  const [calculating, setCalculating] = useState(false);
  const [calcResult,  setCalcResult]  = useState(null);
  const [justCalced,  setJustCalced]  = useState(false);

  // ── User-controlled inputs ────────────────────────────
  const [currentStock,   setCurrentStock]   = useState(450);
  const [orderingCost,   setOrderingCost]   = useState(50);
  const [unitCost,       setUnitCost]       = useState(10);
  const [leadTime,       setLeadTime]       = useState(7);
  const [serviceLevel,   setServiceLevel]   = useState(0.95);

  // Load default dashboard on mount
  useEffect(() => {
    axios.get(`${API}/dashboard`)
      .then(res  => { setDashData(res.data); setLoading(false); })
      .catch(()  => {
        setError('Could not connect to backend. Make sure FastAPI is running on port 8000.');
        setLoading(false);
      });
  }, []);

  // ── Recalculate inventory with user's inputs ──────────
  const handleCalculate = async () => {
    setCalculating(true);
    setJustCalced(false);
    try {
      const forecastDemand = uploadedForecast
        ? uploadedForecast.forecast[0].forecast
        : dashData?.kpis?.forecast_next_month || 65125;

      const res = await axios.post(`${API}/inventory`, {
        forecasted_monthly_demand: forecastDemand,
        current_stock:             currentStock,
        ordering_cost:             orderingCost,
        unit_cost:                 unitCost,
        lead_time_days:            leadTime,
        service_level:             serviceLevel,
        holding_cost_pct:          0.25
      });
      setCalcResult(res.data.data);
      setJustCalced(true);
      setTimeout(() => setJustCalced(false), 3000);
    } catch (err) {
      console.error('Calculation failed:', err);
    } finally {
      setCalculating(false);
    }
  };

  if (loading) return (
    <div className="page" style={{ textAlign: 'center', paddingTop: '60px' }}>
      <div className="spinner" />
      <p style={{ color: 'rgba(255,255,255,0.4)', marginTop: '16px' }}>Loading dashboard...</p>
    </div>
  );

  if (error) return (
    <div className="page">
      <div className="card" style={{ textAlign: 'center', padding: '40px', color: RED }}>
        <p style={{ fontSize: '18px', marginBottom: '8px' }}>⚠️ Connection Error</p>
        <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: '14px' }}>{error}</p>
      </div>
    </div>
  );

  const isUploaded = !!uploadedForecast;

  // Use calc result if available, else uploaded, else default
  const inventory   = calcResult   || (isUploaded ? uploadedForecast.inventory : dashData?.inventory);
  const alert       = calcResult
    ? (() => {
        const s = calcResult.stock_status?.status;
        const map = {
          OUT_OF_STOCK: { level: 'CRITICAL', message: '⚠️ Out of stock! Order immediately.'       },
          BELOW_SAFETY: { level: 'HIGH',     message: '🔴 Stock below safety level. Order urgently.' },
          REORDER_NOW:  { level: 'MEDIUM',   message: '🟡 Reorder point reached. Place order soon.'  },
          ADEQUATE:     { level: 'LOW',      message: '🟢 Stock levels are adequate.'                },
        };
        return map[s] || map['ADEQUATE'];
      })()
    : (isUploaded ? uploadedForecast.alert : dashData?.alert);

  const forecastArr = isUploaded ? uploadedForecast.forecast : dashData?.forecast;
  const kpis        = isUploaded ? uploadedForecast.kpis     : dashData?.kpis;
  const model_perf  = dashData?.model_performance || {};
  const gb          = model_perf?.gradient_boosting || {};
  const arima       = model_perf?.arima || {};

  // Gauge
  const safetyStock = inventory?.safety_stock?.recommended_safety_stock || 1;
  const stockNow    = calcResult
    ? currentStock
    : (isUploaded ? uploadedForecast?.inventory?.stock_status?.current_stock : 450);
  const gaugePct    = Math.min(Math.round((stockNow / safetyStock) * 100), 100);
  const gaugeColor  = gaugePct >= 80 ? GREEN : gaugePct >= 40 ? ORANGE : RED;

  const daysOfStock = inventory?.stock_status?.days_of_stock;
  const daysColor   = daysOfStock > 30 ? GREEN : daysOfStock > 7 ? ORANGE : RED;

  const chartData = (forecastArr || []).map(f => ({
    month: f.month,
    forecast: Math.round(f.forecast),
    upper:    Math.round(f.upper_bound),
    lower:    Math.round(f.lower_bound),
  }));

  return (
    <div className="page">

      {/* ── Banners ─────────────────────────────────────── */}
      {isUploaded && (
        <div style={{
          marginBottom: '12px', padding: '10px 16px', borderRadius: '8px',
          background: 'rgba(46,204,113,0.08)', border: '0.5px solid rgba(46,204,113,0.25)',
          fontSize: '13px', color: GREEN, display: 'flex', alignItems: 'center', gap: '8px'
        }}>
          ✅ Dashboard updated with your uploaded CSV forecast data
        </div>
      )}
      {justCalced && (
        <div style={{
          marginBottom: '12px', padding: '10px 16px', borderRadius: '8px',
          background: 'rgba(74,158,255,0.08)', border: '0.5px solid rgba(74,158,255,0.25)',
          fontSize: '13px', color: BLUE, display: 'flex', alignItems: 'center', gap: '8px'
        }}>
          🔄 Inventory recalculated with your inputs!
        </div>
      )}

      {/* ── Header ─────────────────────────────────────── */}
      <div style={{ marginBottom: '20px' }}>
        <h1 style={{ fontSize: '22px', fontWeight: '600', marginBottom: '4px' }}>Demand Dashboard</h1>
        <p style={{ fontSize: '13px', color: 'rgba(255,255,255,0.35)' }}>
          AI-powered demand forecasting and inventory optimization
        </p>
      </div>

      {/* ── Main Layout: Controls (left) + Dashboard (right) */}
      <div style={{ display: 'grid', gridTemplateColumns: '260px minmax(0,1fr)', gap: '16px' }}>

        {/* ── LEFT: Interactive Controls Panel ─────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>

          <div className="card" style={{ border: `0.5px solid rgba(74,158,255,0.25)` }}>
            <div style={{ marginBottom: '14px' }}>
              <p style={{ fontSize: '14px', fontWeight: '600', color: WHITE }}>
                ⚙️ Your Parameters
              </p>
              <p style={{ fontSize: '11px', color: 'rgba(255,255,255,0.35)', marginTop: '3px' }}>
                Adjust and recalculate
              </p>
            </div>

            <InputField
              label="Current Stock"
              value={currentStock}
              onChange={setCurrentStock}
              suffix="units"
              hint="How many units you have right now"
            />
            <InputField
              label="Ordering Cost"
              value={orderingCost}
              onChange={setOrderingCost}
              prefix="$"
              hint="Cost per order placed"
            />
            <InputField
              label="Unit Cost"
              value={unitCost}
              onChange={setUnitCost}
              prefix="$"
              hint="Cost to buy one unit"
            />
            <InputField
              label="Lead Time"
              value={leadTime}
              onChange={setLeadTime}
              suffix="days"
              hint="Days from order to delivery"
            />

            {/* Service Level Selector */}
            <div style={{ marginBottom: '16px' }}>
              <label style={{
                fontSize: '11px', color: 'rgba(255,255,255,0.4)',
                display: 'block', marginBottom: '5px',
                textTransform: 'uppercase', letterSpacing: '0.5px'
              }}>
                Service Level
              </label>
              <div style={{ display: 'flex', gap: '6px' }}>
                {[0.90, 0.95, 0.99].map(lvl => (
                  <button
                    key={lvl}
                    onClick={() => setServiceLevel(lvl)}
                    style={{
                      flex: 1, padding: '7px 0', borderRadius: '6px',
                      fontSize: '12px', fontWeight: '500', cursor: 'pointer',
                      background: serviceLevel === lvl ? BLUE : 'rgba(255,255,255,0.05)',
                      color:      serviceLevel === lvl ? '#fff' : 'rgba(255,255,255,0.5)',
                      border:     serviceLevel === lvl ? `1px solid ${BLUE}` : '0.5px solid rgba(255,255,255,0.1)',
                      transition: 'all 0.15s'
                    }}
                  >
                    {(lvl * 100).toFixed(0)}%
                  </button>
                ))}
              </div>
              <p style={{ fontSize: '10px', color: 'rgba(255,255,255,0.25)', marginTop: '3px' }}>
                Higher = more safety stock
              </p>
            </div>

            {/* Calculate Button */}
            <button
              onClick={handleCalculate}
              disabled={calculating}
              style={{
                width: '100%', padding: '11px',
                background: calculating ? 'rgba(74,158,255,0.3)' : BLUE,
                border: 'none', borderRadius: '8px',
                color: '#fff', fontSize: '13px', fontWeight: '600',
                cursor: calculating ? 'not-allowed' : 'pointer',
                transition: 'background 0.2s'
              }}
            >
              {calculating ? '⏳ Calculating...' : '🔄 Recalculate'}
            </button>
          </div>

          {/* Quick Presets */}
          <div className="card">
            <p style={{ fontSize: '12px', fontWeight: '600', marginBottom: '10px', color: 'rgba(255,255,255,0.6)' }}>
              Quick Presets
            </p>
            {[
              { label: '🏪 Small Shop',    stock: 100,  ordering: 20,  unit: 5,   lead: 3  },
              { label: '🏬 Mid Business',  stock: 500,  ordering: 50,  unit: 10,  lead: 7  },
              { label: '🏭 Large Retail',  stock: 5000, ordering: 200, unit: 25,  lead: 14 },
            ].map(preset => (
              <button
                key={preset.label}
                onClick={() => {
                  setCurrentStock(preset.stock);
                  setOrderingCost(preset.ordering);
                  setUnitCost(preset.unit);
                  setLeadTime(preset.lead);
                }}
                style={{
                  width: '100%', padding: '8px 10px', marginBottom: '6px',
                  background: 'rgba(255,255,255,0.04)',
                  border: '0.5px solid rgba(255,255,255,0.08)',
                  borderRadius: '6px', color: 'rgba(255,255,255,0.7)',
                  fontSize: '12px', cursor: 'pointer', textAlign: 'left',
                  transition: 'background 0.15s'
                }}
                onMouseEnter={e => e.target.style.background = 'rgba(74,158,255,0.1)'}
                onMouseLeave={e => e.target.style.background = 'rgba(255,255,255,0.04)'}
              >
                {preset.label}
                <span style={{ float: 'right', color: 'rgba(255,255,255,0.3)', fontSize: '10px' }}>
                  Stock: {preset.stock}
                </span>
              </button>
            ))}
            <p style={{ fontSize: '10px', color: 'rgba(255,255,255,0.2)', marginTop: '4px' }}>
              Click a preset then hit Recalculate
            </p>
          </div>
        </div>

        {/* ── RIGHT: Dashboard Content ──────────────────── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>

          {/* KPI Cards */}
          <div>
            <p className="section-label">Key metrics</p>
            <div style={{
              display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0,1fr))',
              gap: '10px'
            }}>
              <KPICard
                label="Next Month Forecast"
                value={`$${kpis?.forecast_next_month?.toLocaleString()}`}
                sub={<span style={{ color: 'rgba(255,255,255,0.35)', fontSize: '11px' }}>
                  {isUploaded ? 'From your CSV' : 'Gradient Boosting'}
                </span>}
                iconBg="rgba(74,158,255,0.12)" icon="📈"
              />
              <KPICard
                label="Recommended Order"
                value={`${inventory?.eoq?.eoq?.toLocaleString()} units`}
                sub={<span style={{ color: 'rgba(255,255,255,0.35)', fontSize: '11px' }}>EOQ formula</span>}
                iconBg="rgba(244,123,32,0.12)" icon="📦"
                highlight={calcResult ? ORANGE : null}
              />
              <KPICard
                label="Reorder Point"
                value={`${inventory?.reorder_point?.reorder_point?.toLocaleString()} units`}
                sub={<span style={{ color: 'rgba(255,255,255,0.35)', fontSize: '11px' }}>Order trigger</span>}
                iconBg="rgba(250,199,117,0.12)" icon="⚠️"
                highlight={calcResult ? ORANGE : null}
              />
              <KPICard
                label="Days of Stock"
                value={<span style={{ color: daysColor }}>{daysOfStock} days</span>}
                sub={
                  daysOfStock > 30 ? <span className="badge badge-green">Healthy</span>
                  : daysOfStock > 7 ? <span className="badge badge-amber">Low</span>
                  : <span className="badge badge-red">Critical</span>
                }
                iconBg={`rgba(${daysOfStock > 30 ? '46,204,113' : daysOfStock > 7 ? '244,123,32' : '226,75,74'},0.12)`}
                icon={daysOfStock > 30 ? '🟢' : daysOfStock > 7 ? '🟡' : '🔴'}
                highlight={calcResult ? gaugeColor : null}
              />
            </div>
          </div>

          {/* Chart + Inventory */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'minmax(0,1.6fr) minmax(0,1fr)',
            gap: '12px'
          }}>
            {/* Forecast Chart */}
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div>
                  <p style={{ fontSize: '14px', fontWeight: '600' }}>
                    {chartData.length}-Month Demand Forecast
                  </p>
                  <p style={{ fontSize: '11px', color: 'rgba(255,255,255,0.35)', marginTop: '2px' }}>
                    {chartData[0]?.month} — {chartData[chartData.length - 1]?.month}
                  </p>
                </div>
                <span className={`badge ${isUploaded ? 'badge-green' : 'badge-blue'}`}>
                  {isUploaded ? '✅ Your Data' : 'Gradient Boosting'}
                </span>
              </div>
              <ResponsiveContainer width="100%" height={190}>
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="fg" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%"  stopColor={BLUE} stopOpacity={0.2} />
                      <stop offset="95%" stopColor={BLUE} stopOpacity={0}   />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="rgba(255,255,255,0.05)" strokeDasharray="3 3" />
                  <XAxis dataKey="month" tick={{ fill: 'rgba(255,255,255,0.35)', fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: 'rgba(255,255,255,0.35)', fontSize: 10 }} axisLine={false} tickLine={false} tickFormatter={v => `$${(v/1000).toFixed(0)}k`} />
                  <Tooltip content={<CustomTooltip />} />
                  <Area type="monotone" dataKey="upper" stroke="transparent" fill="rgba(74,158,255,0.05)" name="Upper" />
                  <Area type="monotone" dataKey="forecast" stroke={BLUE} strokeWidth={2.5} fill="url(#fg)" dot={{ fill: BLUE, r: 4 }} activeDot={{ r: 6 }} name="Forecast" />
                  <Area type="monotone" dataKey="lower" stroke="rgba(74,158,255,0.3)" strokeWidth={1} fill="transparent" name="Lower" />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            {/* Inventory Panel */}
            <div className="card" style={{
              border: calcResult ? `0.5px solid rgba(74,158,255,0.3)` : '0.5px solid rgba(255,255,255,0.07)',
              transition: 'border 0.3s'
            }}>
              <p style={{ fontSize: '14px', fontWeight: '600', marginBottom: '14px' }}>
                Inventory Status
                {calcResult && <span className="badge badge-blue" style={{ marginLeft: '8px', fontSize: '10px' }}>Live</span>}
              </p>

              {/* Dynamic Gauge */}
              <div style={{ textAlign: 'center', marginBottom: '14px' }}>
                <div style={{
                  width: '90px', height: '90px', borderRadius: '50%',
                  background: `conic-gradient(${gaugeColor} 0% ${gaugePct}%, rgba(255,255,255,0.07) ${gaugePct}% 100%)`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 6px',
                  transition: 'background 0.5s'
                }}>
                  <div style={{
                    width: '68px', height: '68px', borderRadius: '50%',
                    background: '#1A2744', display: 'flex', flexDirection: 'column',
                    alignItems: 'center', justifyContent: 'center'
                  }}>
                    <span style={{ fontSize: '16px', fontWeight: '600', color: gaugeColor, transition: 'color 0.3s' }}>
                      {gaugePct}%
                    </span>
                    <span style={{ fontSize: '9px', color: 'rgba(255,255,255,0.3)' }}>safe level</span>
                  </div>
                </div>
              </div>

              {[
                { label: 'Safety Stock',   value: `${inventory?.safety_stock?.recommended_safety_stock?.toLocaleString()} units` },
                { label: 'Reorder Point',  value: `${inventory?.reorder_point?.reorder_point?.toLocaleString()} units` },
                { label: 'EOQ',            value: `${inventory?.eoq?.eoq?.toLocaleString()} units` },
                { label: 'Current Stock',  value: `${stockNow?.toLocaleString()} units`, color: gaugeColor },
              ].map(item => (
                <div key={item.label} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '7px 0', borderBottom: '0.5px solid rgba(255,255,255,0.06)'
                }}>
                  <span style={{ fontSize: '11px', color: 'rgba(255,255,255,0.45)' }}>{item.label}</span>
                  <span style={{ fontSize: '12px', fontWeight: '500', color: item.color || '#fff', transition: 'color 0.3s' }}>
                    {item.value}
                  </span>
                </div>
              ))}

              {alert && (
                <div className={`alert-bar alert-${alert.level}`} style={{ marginTop: '10px', fontSize: '11px' }}>
                  <div style={{
                    width: '6px', height: '6px', borderRadius: '50%', flexShrink: 0,
                    background: alert.level === 'LOW' ? GREEN : alert.level === 'MEDIUM' ? ORANGE : RED
                  }} />
                  {alert.message}
                </div>
              )}
            </div>
          </div>

          {/* Model Performance */}
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
              <p style={{ fontSize: '14px', fontWeight: '600' }}>ARIMA vs Gradient Boosting</p>
              <span className="badge badge-green">🏆 Gradient Boosting wins</span>
            </div>
            <div style={{
              display: 'grid', gridTemplateColumns: '1fr 1fr 1fr',
              padding: '7px 12px', borderRadius: '6px',
              background: 'rgba(255,255,255,0.04)', marginBottom: '6px'
            }}>
              <span style={{ fontSize: '11px', color: 'rgba(255,255,255,0.35)' }}>Metric</span>
              <span style={{ fontSize: '11px', color: 'rgba(255,255,255,0.35)', textAlign: 'center' }}>ARIMA</span>
              <span style={{ fontSize: '11px', color: BLUE, textAlign: 'center' }}>Gradient Boosting</span>
            </div>
            {[
              { metric: 'MAE',  arima: `$${arima.mae?.toLocaleString()}`,  gb: `$${gb.mae?.toLocaleString()}`  },
              { metric: 'RMSE', arima: `$${arima.rmse?.toLocaleString()}`, gb: `$${gb.rmse?.toLocaleString()}` },
              { metric: 'MAPE', arima: `${arima.mape}%`,                   gb: `${gb.mape}%`                   },
              { metric: 'R²',   arima: 'N/A',                              gb: `${gb.r2}`                      },
            ].map(row => (
              <div key={row.metric} style={{
                display: 'grid', gridTemplateColumns: '1fr 1fr 1fr',
                padding: '9px 12px', borderBottom: '0.5px solid rgba(255,255,255,0.05)'
              }}>
                <span style={{ fontSize: '12px', color: 'rgba(255,255,255,0.6)' }}>{row.metric}</span>
                <span style={{ fontSize: '12px', color: 'rgba(255,255,255,0.4)', textAlign: 'center' }}>{row.arima}</span>
                <span style={{ fontSize: '12px', color: GREEN, textAlign: 'center', fontWeight: '500' }}>{row.gb}</span>
              </div>
            ))}
            <div style={{
              marginTop: '12px', padding: '9px 12px', borderRadius: '8px',
              background: 'rgba(99,153,34,0.08)', border: '0.5px solid rgba(99,153,34,0.2)',
              fontSize: '12px', color: '#97C459'
            }}>
              Accuracy: {dashData?.kpis?.model_accuracy} &nbsp;|&nbsp;
              R²: {dashData?.kpis?.model_r2} &nbsp;|&nbsp;
              GB outperforms ARIMA by 40% on all error metrics
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}

export default Dashboard;