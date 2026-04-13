

from fastapi import APIRouter
from utils.inventory import full_inventory_analysis
import json
from pathlib import Path

router    = APIRouter()
DEMO_PATH = Path(__file__).parent.parent / "ml_models" / "forecast_results.json"


@router.get("/dashboard")
def get_dashboard():
    """Return all data needed to render the full dashboard in one call"""

    # ── Load saved forecast from Phase 2 ─────────────────────
    forecast_data = {}
    if DEMO_PATH.exists():
        with open(DEMO_PATH) as f:
            forecast_data = json.load(f)

    future               = forecast_data.get("future_forecast", [])
    first_month_forecast = future[0]["gb_forecast"] if future else 65125.42
    avg_forecast         = (
        sum(m["gb_forecast"] for m in future) / len(future) if future else 60000
    )

    # ── Run inventory optimization ───────────────────────────
    inventory = full_inventory_analysis(
        forecasted_monthly_demand = first_month_forecast,
        current_stock             = 450,
        ordering_cost             = 50,
        holding_cost_pct          = 0.25,
        unit_cost                 = 10,
        lead_time_days            = 7,
        service_level             = 0.95
    )

    # ── Build alert messages ──────────────────────────────────
    status = inventory["stock_status"]["status"]
    alerts = {
        "OUT_OF_STOCK":   {"level": "CRITICAL", "message": "⚠️ Out of stock! Order immediately."},
        "BELOW_SAFETY":   {"level": "HIGH",     "message": "🔴 Stock below safety level. Order urgently."},
        "REORDER_NOW":    {"level": "MEDIUM",   "message": "🟡 Reorder point reached. Place order soon."},
        "ADEQUATE":       {"level": "LOW",      "message": "🟢 Stock levels are adequate."},
    }
    alert = alerts.get(status, alerts["ADEQUATE"])

    # ── Model performance ─────────────────────────────────────
    model_perf = forecast_data.get("model_performance", {})
    gb         = model_perf.get("gradient_boosting", {})

    # ── Build and return full dashboard payload ───────────────
    return {
        "status": "success",

        # Top KPI cards shown on the dashboard
        "kpis": {
            "forecast_next_month":   round(first_month_forecast, 2),
            "avg_6month_forecast":   round(avg_forecast, 2),
            "recommended_order_qty": inventory["recommendation"]["order_quantity"],
            "reorder_point":         inventory["reorder_point"]["reorder_point"],
            "safety_stock":          inventory["safety_stock"]["recommended_safety_stock"],
            "days_of_stock":         inventory["stock_status"]["days_of_stock"],
            "model_accuracy":        f"{round(100 - gb.get('mape', 20), 1)}%",
            "model_r2":              gb.get("r2"),
        },

        # Chart data — 6 month forecast
        "forecast": [
            {
                "month":       m["month"],
                "forecast":    m["gb_forecast"],
                "lower_bound": m["lower_bound"],
                "upper_bound": m["upper_bound"],
            }
            for m in future
        ],

        # Full inventory analysis
        "inventory":         inventory,

        # Alert banner for the dashboard
        "alert":             alert,

        # Model comparison data
        "model_performance": model_perf,
        "best_model":        forecast_data.get("best_model", "gradient_boosting"),
    }
