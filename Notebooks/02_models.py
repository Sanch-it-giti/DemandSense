# ============================================================
# DemandSense — Phase 2: AI Model Training
# ARIMA (Time Series) + Gradient Boosting (ML)
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import warnings, json, pickle
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
from scipy.stats import norm

warnings.filterwarnings("ignore")

BLUE   = "#1F3F7A"
ORANGE = "#F47B20"
GREEN  = "#2ECC71"
RED    = "#E74C3C"

plt.rcParams.update({
    "figure.facecolor": "#F8F9FA",
    "axes.facecolor":   "#FFFFFF",
    "axes.grid":        True,
    "grid.color":       "#E0E0E0",
})

# ── LOAD FEATURE DATASET ─────────────────────────────────────
df = pd.read_csv("/mnt/user-data/outputs/monthly_features.csv")
df["YearMonth_dt"] = pd.to_datetime(df["YearMonth_dt"])
df = df.sort_values("YearMonth_dt").reset_index(drop=True)

print("=" * 60)
print("  DEMANDSENSE — PHASE 2: AI MODEL TRAINING")
print("=" * 60)
print(f"  Dataset shape : {df.shape}")
print(f"  Date range    : {df['YearMonth_dt'].min().date()} → {df['YearMonth_dt'].max().date()}")
print(f"  Total months  : {len(df)}")


# ════════════════════════════════════════════════════════════
# MODEL 1 — ARIMA (Manual Implementation using scipy)
# ════════════════════════════════════════════════════════════
print("\n" + "─" * 60)
print("  MODEL 1: ARIMA (Time Series Forecasting)")
print("─" * 60)

class SimpleARIMA:
    """
    ARIMA(p,d,q) implementation using numpy/scipy.
    p=2 (autoregressive), d=1 (differencing), q=1 (moving avg)
    """
    def __init__(self, p=2, d=1, q=1):
        self.p = p
        self.d = d
        self.q = q
        self.history = []
        self.residuals = []
        self.ar_coefs = None
        self.ma_coefs = None
        self.mean_diff = 0

    def difference(self, series, d):
        diff = series.copy()
        for _ in range(d):
            diff = np.diff(diff)
        return diff

    def fit(self, series):
        self.original = np.array(series, dtype=float)
        self.last_values = self.original.copy()

        # Differencing
        diff_series = self.difference(self.original, self.d)
        self.mean_diff = np.mean(diff_series)
        diff_series = diff_series - self.mean_diff

        n = len(diff_series)

        # Estimate AR coefficients using Yule-Walker equations
        if self.p > 0:
            autocorr = [np.corrcoef(diff_series[:-k], diff_series[k:])[0,1]
                       if k > 0 else 1.0 for k in range(self.p + 1)]
            R = np.array([[autocorr[abs(i-j)] for j in range(self.p)]
                         for i in range(self.p)])
            r = np.array([autocorr[i+1] for i in range(self.p)])
            try:
                self.ar_coefs = np.linalg.solve(R, r)
            except:
                self.ar_coefs = np.array([0.5] * self.p)
        else:
            self.ar_coefs = np.array([])

        # Compute residuals
        self.residuals = []
        for t in range(max(self.p, self.d), n):
            pred = self.mean_diff
            for i, coef in enumerate(self.ar_coefs):
                if t - i - 1 >= 0:
                    pred += coef * diff_series[t - i - 1]
            self.residuals.append(diff_series[t] - pred)

        self.residuals = np.array(self.residuals)
        self.diff_series = diff_series
        print(f"  ARIMA({self.p},{self.d},{self.q}) fitted on {len(series)} observations")
        return self

    def forecast(self, steps=6):
        forecasts = []
        history = list(self.diff_series)
        residuals = list(self.residuals)

        for _ in range(steps):
            pred = self.mean_diff
            for i, coef in enumerate(self.ar_coefs):
                if len(history) - i - 1 >= 0:
                    pred += coef * history[-(i+1)]
            if len(residuals) > 0 and self.q > 0:
                pred += 0.3 * residuals[-1]
            history.append(pred)
            residuals.append(0)
            forecasts.append(pred)

        # Inverse differencing
        last_val = self.original[-1]
        result = []
        for f in forecasts:
            next_val = last_val + f + self.mean_diff
            result.append(next_val)
            last_val = next_val

        return np.array(result)

    def fitted_values(self):
        """Return in-sample predictions for evaluation"""
        preds = []
        diff = self.diff_series
        for t in range(self.p, len(diff)):
            pred = self.mean_diff
            for i, coef in enumerate(self.ar_coefs):
                if t - i - 1 >= 0:
                    pred += coef * diff[t - i - 1]
            preds.append(pred)

        # Convert back to original scale
        result = []
        base = self.original[self.d + self.p - 1]
        for p in preds:
            val = base + p + self.mean_diff
            result.append(val)
            base = val
        return np.array(result)

# Train ARIMA
sales = df["Total_Sales"].values
train_size = int(len(sales) * 0.8)
train_sales = sales[:train_size]
test_sales  = sales[train_size:]

arima = SimpleARIMA(p=2, d=1, q=1)
arima.fit(train_sales)

# Forecast on test period
arima_test_forecast = arima.forecast(steps=len(test_sales))
arima_future_forecast = arima.forecast(steps=6)  # 6 months ahead

# Metrics
arima_mae  = mean_absolute_error(test_sales, arima_test_forecast)
arima_rmse = np.sqrt(mean_squared_error(test_sales, arima_test_forecast))
arima_mape = np.mean(np.abs((test_sales - arima_test_forecast) / test_sales)) * 100

print(f"  MAE  : ${arima_mae:,.2f}")
print(f"  RMSE : ${arima_rmse:,.2f}")
print(f"  MAPE : {arima_mape:.2f}%")


# ════════════════════════════════════════════════════════════
# MODEL 2 — GRADIENT BOOSTING (ML Forecasting)
# ════════════════════════════════════════════════════════════
print("\n" + "─" * 60)
print("  MODEL 2: Gradient Boosting (ML Forecasting)")
print("─" * 60)

FEATURES = [
    "Sales_Lag_1", "Sales_Lag_2", "Sales_Lag_3",
    "Rolling_3M_Avg", "Rolling_3M_Std",
    "Month_Num", "Year_Num", "Quarter",
    "Num_Orders", "Avg_Discount", "Total_Quantity"
]
TARGET = "Total_Sales"

X = df[FEATURES].values
y = df[TARGET].values

# Train / test split (keep temporal order)
X_train, X_test = X[:train_size], X[train_size:]
y_train, y_test = y[:train_size], y[train_size:]

scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)
X_test_sc  = scaler.transform(X_test)

gb_model = GradientBoostingRegressor(
    n_estimators=200,
    learning_rate=0.05,
    max_depth=3,
    min_samples_leaf=2,
    subsample=0.8,
    random_state=42
)
gb_model.fit(X_train_sc, y_train)

gb_preds = gb_model.predict(X_test_sc)

gb_mae  = mean_absolute_error(y_test, gb_preds)
gb_rmse = np.sqrt(mean_squared_error(y_test, gb_preds))
gb_mape = np.mean(np.abs((y_test - gb_preds) / y_test)) * 100
gb_r2   = r2_score(y_test, gb_preds)

print(f"  MAE  : ${gb_mae:,.2f}")
print(f"  RMSE : ${gb_rmse:,.2f}")
print(f"  MAPE : {gb_mape:.2f}%")
print(f"  R²   : {gb_r2:.4f}")

# ── Future forecast using GB ──────────────────────────────────
# Build future feature rows by extending lag features
last_row = df.iloc[-1].copy()
future_preds = []
future_df = df.copy()

for i in range(6):
    next_month = last_row["Month_Num"] % 12 + 1
    next_year  = last_row["Year_Num"] + (1 if next_month == 1 else 0)
    next_q     = (next_month - 1) // 3 + 1

    new_row = {
        "Sales_Lag_1":    future_df["Total_Sales"].iloc[-1],
        "Sales_Lag_2":    future_df["Total_Sales"].iloc[-2],
        "Sales_Lag_3":    future_df["Total_Sales"].iloc[-3],
        "Rolling_3M_Avg": future_df["Total_Sales"].iloc[-3:].mean(),
        "Rolling_3M_Std": future_df["Total_Sales"].iloc[-3:].std(),
        "Month_Num":      next_month,
        "Year_Num":       next_year,
        "Quarter":        next_q,
        "Num_Orders":     future_df["Num_Orders"].mean(),
        "Avg_Discount":   future_df["Avg_Discount"].mean(),
        "Total_Quantity": future_df["Total_Quantity"].mean(),
        "Total_Sales":    0
    }
    feat_vec = np.array([[new_row[f] for f in FEATURES]])
    feat_sc  = scaler.transform(feat_vec)
    pred     = gb_model.predict(feat_sc)[0]
    future_preds.append(pred)
    new_row["Total_Sales"] = pred
    future_df = pd.concat([future_df, pd.DataFrame([new_row])], ignore_index=True)
    last_row = pd.Series(new_row)

gb_future_forecast = np.array(future_preds)


# ════════════════════════════════════════════════════════════
# VISUALIZATION
# ════════════════════════════════════════════════════════════

dates       = df["YearMonth_dt"].values
train_dates = dates[:train_size]
test_dates  = dates[train_size:]

# Generate future dates
last_date = pd.Timestamp(dates[-1])
future_dates = pd.date_range(start=last_date + pd.offsets.MonthBegin(1),
                             periods=6, freq="MS")

# ── Plot 1: Both Models vs Actual ────────────────────────────
fig, axes = plt.subplots(2, 1, figsize=(14, 10))

for ax, model_preds, model_future, model_name, color in [
    (axes[0], arima_test_forecast, arima_future_forecast, "ARIMA", BLUE),
    (axes[1], gb_preds,            gb_future_forecast,    "Gradient Boosting (ML)", ORANGE)
]:
    # Training data
    ax.plot(train_dates, sales[:train_size],
            color="gray", linewidth=1.5, label="Training Data", alpha=0.7)
    # Actual test
    ax.plot(test_dates, test_sales,
            color=GREEN, linewidth=2, marker="o", markersize=5, label="Actual (Test)")
    # Model predictions
    ax.plot(test_dates, model_preds,
            color=color, linewidth=2, linestyle="--",
            marker="s", markersize=5, label=f"{model_name} Predictions")
    # Future forecast
    ax.plot(future_dates, model_future,
            color=RED, linewidth=2, linestyle=":",
            marker="^", markersize=7, label="Future Forecast (6 months)")
    ax.fill_between(future_dates, model_future * 0.88, model_future * 1.12,
                    alpha=0.15, color=RED, label="Confidence Band (±12%)")

    ax.axvline(x=test_dates[0], color="black", linestyle="--",
               alpha=0.4, linewidth=1)
    ax.text(test_dates[0], ax.get_ylim()[0],
            " Train | Test", fontsize=9, color="gray")
    ax.set_title(f"{model_name} — Sales Forecast",
                 fontsize=13, fontweight="bold", color=BLUE)
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${x:,.0f}"))
    ax.legend(fontsize=9, loc="upper left")
    ax.set_xlabel("Month")
    ax.set_ylabel("Sales ($)")

plt.suptitle("DemandSense — AI Model Forecasts",
             fontsize=15, fontweight="bold", color=BLUE, y=1.01)
plt.tight_layout()
plt.savefig("/mnt/user-data/outputs/07_model_forecasts.png", dpi=150, bbox_inches="tight")
plt.close()
print("\n✓ Saved: 07_model_forecasts.png")

# ── Plot 2: Model Comparison ──────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(14, 4))

metrics    = ["MAE", "RMSE", "MAPE"]
arima_vals = [arima_mae, arima_rmse, arima_mape]
gb_vals    = [gb_mae,    gb_rmse,    gb_mape]
units      = ["$", "$", "%"]

for i, (ax, metric, av, gv, unit) in enumerate(
        zip(axes, metrics, arima_vals, gb_vals, units)):
    bars = ax.bar(["ARIMA", "Gradient\nBoosting"], [av, gv],
                  color=[BLUE, ORANGE], edgecolor="white", linewidth=1.5, width=0.5)
    ax.set_title(metric, fontsize=13, fontweight="bold", color=BLUE)
    winner_idx = np.argmin([av, gv])
    for j, (bar, val) in enumerate(zip(bars, [av, gv])):
        label = f"{unit}{val:,.1f}" if unit == "$" else f"{val:.2f}{unit}"
        ax.text(bar.get_x() + bar.get_width()/2,
                bar.get_height() + max(av, gv) * 0.01,
                label, ha="center", fontsize=11, fontweight="bold")
        if j == winner_idx:
            bar.set_edgecolor(GREEN)
            bar.set_linewidth(3)

plt.suptitle("Model Performance Comparison  (🟢 = Better)",
             fontsize=13, fontweight="bold", color=BLUE)
plt.tight_layout()
plt.savefig("/mnt/user-data/outputs/08_model_comparison.png", dpi=150)
plt.close()
print("✓ Saved: 08_model_comparison.png")

# ── Plot 3: Feature Importance ────────────────────────────────
importances = gb_model.feature_importances_
feat_df = pd.DataFrame({"Feature": FEATURES, "Importance": importances})
feat_df = feat_df.sort_values("Importance", ascending=True)

fig, ax = plt.subplots(figsize=(9, 5))
colors = [ORANGE if v == feat_df["Importance"].max() else BLUE
          for v in feat_df["Importance"]]
ax.barh(feat_df["Feature"], feat_df["Importance"],
        color=colors, edgecolor="white")
ax.set_title("Feature Importance — Gradient Boosting Model",
             fontsize=13, fontweight="bold", color=BLUE)
ax.set_xlabel("Importance Score")
plt.tight_layout()
plt.savefig("/mnt/user-data/outputs/09_feature_importance.png", dpi=150)
plt.close()
print("✓ Saved: 09_feature_importance.png")

# ── Plot 4: Future 6-Month Forecast ──────────────────────────
fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(dates[-12:], sales[-12:], color=BLUE, linewidth=2.5,
        marker="o", markersize=5, label="Historical (Last 12 Months)")
ax.plot(future_dates, gb_future_forecast, color=ORANGE,
        linewidth=2.5, linestyle="--", marker="^",
        markersize=8, label="GB Forecast (Next 6 Months)")
ax.plot(future_dates, arima_future_forecast, color=RED,
        linewidth=2, linestyle=":", marker="s",
        markersize=6, label="ARIMA Forecast (Next 6 Months)")
ax.fill_between(future_dates,
                gb_future_forecast * 0.88,
                gb_future_forecast * 1.12,
                alpha=0.12, color=ORANGE)
ax.axvline(x=future_dates[0], color="gray", linestyle="--", alpha=0.5)
ax.set_title("6-Month Future Demand Forecast",
             fontsize=14, fontweight="bold", color=BLUE)
ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"${x:,.0f}"))
ax.legend(fontsize=10)
ax.set_xlabel("Month")
ax.set_ylabel("Forecasted Sales ($)")
for i, (d, v) in enumerate(zip(future_dates, gb_future_forecast)):
    ax.annotate(f"${v:,.0f}", (d, v),
                textcoords="offset points", xytext=(0, 10),
                ha="center", fontsize=8, color=ORANGE, fontweight="bold")
plt.tight_layout()
plt.savefig("/mnt/user-data/outputs/10_future_forecast.png", dpi=150)
plt.close()
print("✓ Saved: 10_future_forecast.png")


# ════════════════════════════════════════════════════════════
# SAVE MODELS & FORECAST DATA
# ════════════════════════════════════════════════════════════

# Save GB model + scaler
with open("/mnt/user-data/outputs/gb_model.pkl", "wb") as f:
    pickle.dump({"model": gb_model, "scaler": scaler, "features": FEATURES}, f)
print("\n✓ Saved: gb_model.pkl")

# Save forecast results as JSON (for backend API)
forecast_output = {
    "model_performance": {
        "arima": {"mae": round(arima_mae, 2), "rmse": round(arima_rmse, 2),
                  "mape": round(arima_mape, 2)},
        "gradient_boosting": {"mae": round(gb_mae, 2), "rmse": round(gb_rmse, 2),
                               "mape": round(gb_mape, 2), "r2": round(gb_r2, 4)}
    },
    "best_model": "gradient_boosting" if gb_mape < arima_mape else "arima",
    "future_forecast": [
        {
            "month": str(d)[:7],
            "arima_forecast":    round(float(a), 2),
            "gb_forecast":       round(float(g), 2),
            "lower_bound":       round(float(g) * 0.88, 2),
            "upper_bound":       round(float(g) * 1.12, 2),
        }
        for d, a, g in zip(future_dates, arima_future_forecast, gb_future_forecast)
    ]
}

with open("/mnt/user-data/outputs/forecast_results.json", "w") as f:
    json.dump(forecast_output, f, indent=2)
print("✓ Saved: forecast_results.json")


# ════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("  MODEL PERFORMANCE SUMMARY")
print("=" * 60)
print(f"  {'Metric':<12} {'ARIMA':>12} {'Grad. Boost':>14}")
print("  " + "-" * 40)
print(f"  {'MAE':<12} ${arima_mae:>10,.2f} ${gb_mae:>12,.2f}")
print(f"  {'RMSE':<12} ${arima_rmse:>10,.2f} ${gb_rmse:>12,.2f}")
print(f"  {'MAPE':<12} {arima_mape:>10.2f}% {gb_mape:>12.2f}%")
print(f"  {'R²':<12} {'N/A':>12} {gb_r2:>13.4f}")
print("=" * 60)
winner = "Gradient Boosting" if gb_mape < arima_mape else "ARIMA"
print(f"\n  🏆 Best Model: {winner}")
print(f"\n  📅 6-Month Forecast (Gradient Boosting):")
for d, v in zip(future_dates, gb_future_forecast):
    print(f"     {str(d)[:7]}  →  ${v:>10,.2f}")

print("\n✅ Phase 2 Complete! Models trained and saved.")
