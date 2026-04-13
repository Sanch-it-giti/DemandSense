

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from utils.ml_engine import process_uploaded_csv, run_forecast
from utils.inventory import full_inventory_analysis
import json
from pathlib import Path

router  = APIRouter()
DEMO    = Path(__file__).parent.parent / "ml_models" / "forecast_results.json"


@router.get("/forecast/demo")
def get_demo_forecast():
    """Return the pre-generated forecast saved during model training"""
    if not DEMO.exists():
        raise HTTPException(status_code=404,
            detail="Demo forecast not found. Make sure forecast_results.json is in ml_models/")
    with open(DEMO) as f:
        data = json.load(f)
    return {"status": "demo", "data": data}


@router.post("/forecast")
async def forecast_from_upload(
    file: UploadFile = File(...),
    periods: int = Query(default=6, ge=1, le=24,
                         description="How many months to forecast"),
    current_stock: float = Query(default=450, ge=0,
                                  description="Current stock level in units"),
    unit_cost: float = Query(default=10.0, gt=0,
                              description="Cost per unit"),
    ordering_cost: float = Query(default=50.0, gt=0,
                                  description="Cost per order placed"),
    lead_time_days: float = Query(default=7.0, gt=0,
                                   description="Lead time in days")
):
    """
    Upload a CSV file → get AI forecast + inventory optimization.
    Now returns BOTH forecast AND inventory so the full dashboard updates.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files accepted.")

    content = await file.read()

    try:
        df       = process_uploaded_csv(content)
        forecast = run_forecast(df, periods=periods)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecast failed: {str(e)}")

    total = sum(f["forecast"] for f in forecast)
    peak  = max(forecast, key=lambda x: x["forecast"])

    # ── Calculate inventory from the NEW forecast ────────────
    first_month_forecast = forecast[0]["forecast"]

    inventory = full_inventory_analysis(
        forecasted_monthly_demand = first_month_forecast,
        current_stock             = current_stock,
        ordering_cost             = ordering_cost,
        unit_cost                 = unit_cost,
        lead_time_days            = lead_time_days,
        service_level             = 0.95
    )

    # Stock alert
    status = inventory["stock_status"]["status"]
    alerts = {
        "OUT_OF_STOCK": {"level": "CRITICAL", "message": "⚠️ Out of stock! Order immediately."},
        "BELOW_SAFETY": {"level": "HIGH",     "message": "🔴 Stock below safety level. Order urgently."},
        "REORDER_NOW":  {"level": "MEDIUM",   "message": "🟡 Reorder point reached. Place order soon."},
        "ADEQUATE":     {"level": "LOW",      "message": "🟢 Stock levels are adequate."},
    }
    alert = alerts.get(status, alerts["ADEQUATE"])

    # Stock gauge percentage
    safety_stock = inventory["safety_stock"]["recommended_safety_stock"]
    gauge_pct = round((current_stock / safety_stock * 100), 1) if safety_stock > 0 else 0
    gauge_pct = min(gauge_pct, 100)

    return {
        "status":   "success",
        "model":    "Gradient Boosting",
        "periods":  periods,
        "forecast": forecast,
        "summary": {
            "total_forecast": round(total, 2),
            "avg_monthly":    round(total / len(forecast), 2),
            "peak_month":     peak["month"],
            "peak_value":     peak["forecast"],
        },
        # ── NEW: inventory data based on uploaded forecast ───
        "inventory":  inventory,
        "alert":      alert,
        "gauge_pct":  gauge_pct,
        "kpis": {
            "forecast_next_month":   round(first_month_forecast, 2),
            "avg_6month_forecast":   round(total / len(forecast), 2),
            "recommended_order_qty": inventory["recommendation"]["order_quantity"],
            "reorder_point":         inventory["reorder_point"]["reorder_point"],
            "safety_stock":          inventory["safety_stock"]["recommended_safety_stock"],
            "days_of_stock":         inventory["stock_status"]["days_of_stock"],
        }
    }