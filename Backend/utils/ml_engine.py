

import pickle
import numpy as np
import pandas as pd
from pathlib import Path

# Path to the trained model file
MODEL_PATH = Path(__file__).parent.parent / "ml_models" / "gb_model.pkl"

# Cache so we don't reload from disk every single request
_model_cache = None


def load_model():
    """Load the trained model from disk (only loads once, then caches it)"""
    global _model_cache
    if _model_cache is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"❌ Model not found at: {MODEL_PATH}\n"
                "Please copy gb_model.pkl into the ml_models/ folder."
            )
        with open(MODEL_PATH, "rb") as f:
            _model_cache = pickle.load(f)
        print("✅ Model loaded successfully")
    return _model_cache


def run_forecast(df: pd.DataFrame, periods: int = 6) -> list:
    """
    Given a monthly sales dataframe → predict the next N months.

    Steps:
    1. Load the trained model
    2. Build feature rows for each future month
    3. Feed each row into the model → get a prediction
    4. Use that prediction as input for the next month (chain forecasting)
    5. Return list of {month, forecast, lower_bound, upper_bound}
    """
    bundle   = load_model()
    model    = bundle["model"]
    scaler   = bundle["scaler"]
    features = bundle["features"]

    # Make sure data is sorted oldest → newest
    df = df.sort_values("YearMonth_dt").reset_index(drop=True)

    # Add all the features the model needs
    df = _add_features(df)
    df = df.dropna().reset_index(drop=True)

    results   = []
    working   = df.copy()
    last_date = pd.to_datetime(working["YearMonth_dt"].iloc[-1])

    for _ in range(periods):
        # Figure out what the next month is
        next_month = last_date.month % 12 + 1
        next_year  = last_date.year + (1 if next_month == 1 else 0)
        next_date  = pd.Timestamp(year=next_year, month=next_month, day=1)

        # Build the feature row for this future month
        row = {
            "Sales_Lag_1":    working["Total_Sales"].iloc[-1],
            "Sales_Lag_2":    working["Total_Sales"].iloc[-2],
            "Sales_Lag_3":    working["Total_Sales"].iloc[-3],
            "Rolling_3M_Avg": working["Total_Sales"].iloc[-3:].mean(),
            "Rolling_3M_Std": working["Total_Sales"].iloc[-3:].std(),
            "Month_Num":      next_month,
            "Year_Num":       next_year,
            "Quarter":        (next_month - 1) // 3 + 1,
            "Num_Orders":     working["Num_Orders"].mean(),
            "Avg_Discount":   working["Avg_Discount"].mean(),
            "Total_Quantity": working["Total_Quantity"].mean(),
        }

        # Scale features and predict
        X      = np.array([[row[f] for f in features]])
        X_sc   = scaler.transform(X)
        pred   = float(model.predict(X_sc)[0])

        results.append({
            "month":       str(next_date)[:7],        # e.g. "2018-01"
            "forecast":    round(pred, 2),
            "lower_bound": round(pred * 0.88, 2),     # -12% confidence
            "upper_bound": round(pred * 1.12, 2),     # +12% confidence
        })

        # Add this prediction as a real row so the next iteration can use it
        row["Total_Sales"]  = pred
        row["YearMonth_dt"] = str(next_date)
        working = pd.concat([working, pd.DataFrame([row])], ignore_index=True)
        last_date = next_date

    return results


def _add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add lag and rolling features needed by the model"""
    df = df.copy()
    for lag in [1, 2, 3]:
        df[f"Sales_Lag_{lag}"] = df["Total_Sales"].shift(lag)
    df["Rolling_3M_Avg"] = df["Total_Sales"].rolling(3).mean()
    df["Rolling_3M_Std"] = df["Total_Sales"].rolling(3).std()
    df["Month_Num"]      = pd.to_datetime(df["YearMonth_dt"]).dt.month
    df["Year_Num"]       = pd.to_datetime(df["YearMonth_dt"]).dt.year
    df["Quarter"]        = pd.to_datetime(df["YearMonth_dt"]).dt.quarter

    if "Num_Orders"     not in df.columns: df["Num_Orders"]     = df["Total_Sales"] / 100
    if "Avg_Discount"   not in df.columns: df["Avg_Discount"]   = 0.15
    if "Total_Quantity" not in df.columns: df["Total_Quantity"] = df["Total_Sales"] / 50
    return df


def process_uploaded_csv(file_bytes: bytes) -> pd.DataFrame:
    """
    Takes raw CSV bytes from an uploaded file →
    returns a clean monthly sales dataframe ready for forecasting.
    """
    import io
    df = pd.read_csv(io.BytesIO(file_bytes), encoding="latin-1")
    df.columns = [c.strip() for c in df.columns]

    # Validate required columns exist
    for col in ["Order Date", "Sales", "Quantity"]:
        if col not in df.columns:
            raise ValueError(f"Missing required column: '{col}'")

    df["Order Date"] = pd.to_datetime(df["Order Date"], infer_datetime_format=True)
    df["YearMonth"]  = df["Order Date"].dt.to_period("M")

    agg = {"Sales": "sum", "Quantity": "sum"}
    if "Profit"   in df.columns: agg["Profit"]   = "sum"
    if "Discount" in df.columns: agg["Discount"]  = "mean"
    if "Order ID" in df.columns: agg["Order ID"]  = "nunique"

    monthly = df.groupby("YearMonth").agg(agg).reset_index()
    monthly = monthly.rename(columns={
        "Sales":    "Total_Sales",
        "Quantity": "Total_Quantity",
        "Profit":   "Total_Profit",
        "Discount": "Avg_Discount",
        "Order ID": "Num_Orders",
    })
    monthly["YearMonth_dt"] = monthly["YearMonth"].dt.to_timestamp()
    return monthly.sort_values("YearMonth_dt").reset_index(drop=True)
