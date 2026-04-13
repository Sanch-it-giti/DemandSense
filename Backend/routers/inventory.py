

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from utils.inventory import full_inventory_analysis

router = APIRouter()


# ── Request model (defines what the frontend must send) ──────
class InventoryRequest(BaseModel):
    forecasted_monthly_demand: float = Field(...,  gt=0, example=65125)
    current_stock:             float = Field(...,  ge=0, example=450)
    ordering_cost:             float = Field(50.0, gt=0, description="Cost per order placed")
    holding_cost_pct:          float = Field(0.25, gt=0, description="Annual holding cost as % of unit cost")
    unit_cost:                 float = Field(10.0, gt=0, description="Cost per unit")
    lead_time_days:            float = Field(7.0,  gt=0, description="Days between placing and receiving order")
    service_level:             float = Field(0.95, gt=0, le=1, description="Desired service level (0.90, 0.95, 0.99)")


# ── Endpoints ─────────────────────────────────────────────────
@router.post("/inventory")
def get_inventory_optimization(req: InventoryRequest):
    """Calculate full inventory optimization from a demand forecast"""
    try:
        result = full_inventory_analysis(
            forecasted_monthly_demand = req.forecasted_monthly_demand,
            current_stock             = req.current_stock,
            ordering_cost             = req.ordering_cost,
            holding_cost_pct          = req.holding_cost_pct,
            unit_cost                 = req.unit_cost,
            lead_time_days            = req.lead_time_days,
            service_level             = req.service_level,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "success", "data": result}


@router.get("/inventory/demo")
def demo_inventory():
    """Demo using Jan 2018 forecast values and default cost parameters"""
    result = full_inventory_analysis(
        forecasted_monthly_demand = 65125.42,
        current_stock             = 450,
        ordering_cost             = 50,
        holding_cost_pct          = 0.25,
        unit_cost                 = 10,
        lead_time_days            = 7,
        service_level             = 0.95
    )
    return {"status": "demo", "data": result}
