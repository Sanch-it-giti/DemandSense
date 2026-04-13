

import math


# ── 1. EOQ (Economic Order Quantity) ────────────────────────
def calculate_eoq(annual_demand, ordering_cost, holding_cost_per_unit):
    """
    EOQ = sqrt( 2 × D × S / H )
    D = Annual demand (units)
    S = Cost per order (₹ or $)
    H = Holding cost per unit per year
    """
    eoq = math.sqrt((2 * annual_demand * ordering_cost) / holding_cost_per_unit)

    orders_per_year      = annual_demand / eoq
    total_ordering_cost  = orders_per_year * ordering_cost
    total_holding_cost   = (eoq / 2) * holding_cost_per_unit
    total_cost           = total_ordering_cost + total_holding_cost

    return {
        "eoq":                  round(eoq, 0),
        "orders_per_year":      round(orders_per_year, 1),
        "order_interval_days":  round(365 / orders_per_year, 0),
        "total_ordering_cost":  round(total_ordering_cost, 2),
        "total_holding_cost":   round(total_holding_cost, 2),
        "total_inventory_cost": round(total_cost, 2),
    }


# ── 2. Safety Stock ──────────────────────────────────────────
def calculate_safety_stock(
    avg_daily_demand,
    max_daily_demand,
    avg_lead_time_days,
    max_lead_time_days,
    service_level=0.95
):
    """
    Safety Stock = (Max demand - Avg demand) × Max lead time
    Also calculates a statistical version using Z-score
    """
    # Simple formula
    simple = (max_daily_demand - avg_daily_demand) * max_lead_time_days

    # Statistical formula using Z-score
    z_table = {0.90: 1.28, 0.95: 1.645, 0.99: 2.33}
    z = z_table.get(service_level, 1.645)

    demand_std    = (max_daily_demand - avg_daily_demand) / 3
    lead_time_std = (max_lead_time_days - avg_lead_time_days) / 3

    statistical = z * math.sqrt(
        (avg_lead_time_days * demand_std ** 2) +
        (avg_daily_demand ** 2 * lead_time_std ** 2)
    )

    recommended = max(simple, statistical)

    return {
        "simple_safety_stock":      round(simple, 0),
        "statistical_safety_stock": round(statistical, 0),
        "recommended_safety_stock": round(recommended, 0),
        "service_level":            f"{int(service_level * 100)}%",
    }


# ── 3. Reorder Point ─────────────────────────────────────────
def calculate_reorder_point(avg_daily_demand, avg_lead_time_days, safety_stock):
    """
    ROP = (Avg Daily Demand × Lead Time in Days) + Safety Stock
    When stock hits this number → place a new order immediately
    """
    demand_during_lead = avg_daily_demand * avg_lead_time_days
    rop = demand_during_lead + safety_stock

    return {
        "reorder_point":           round(rop, 0),
        "demand_during_lead_time": round(demand_during_lead, 0),
        "safety_stock":            round(safety_stock, 0),
        "message": f"Place a new order when stock drops to {round(rop, 0):.0f} units"
    }


# ── 4. Full Analysis (calls all 3 above) ─────────────────────
def full_inventory_analysis(
    forecasted_monthly_demand,
    current_stock,
    ordering_cost=50.0,
    holding_cost_pct=0.25,
    unit_cost=10.0,
    lead_time_days=7.0,
    service_level=0.95
):
    """
    Given a demand forecast → return complete inventory recommendations
    This is what the /api/inventory endpoint calls
    """
    annual_demand         = forecasted_monthly_demand * 12
    avg_daily_demand      = forecasted_monthly_demand / 30
    max_daily_demand      = avg_daily_demand * 1.3        # 30% spike
    holding_cost_per_unit = unit_cost * holding_cost_pct

    eoq    = calculate_eoq(annual_demand, ordering_cost, holding_cost_per_unit)
    safety = calculate_safety_stock(
                avg_daily_demand, max_daily_demand,
                lead_time_days,   lead_time_days * 1.5,
                service_level)
    rop    = calculate_reorder_point(
                avg_daily_demand,
                lead_time_days,
                safety["recommended_safety_stock"])

    # Determine stock status
    reorder_point = rop["reorder_point"]
    if current_stock <= 0:
        status = "OUT_OF_STOCK";   alert = "CRITICAL"
    elif current_stock <= safety["recommended_safety_stock"]:
        status = "BELOW_SAFETY";   alert = "HIGH"
    elif current_stock <= reorder_point:
        status = "REORDER_NOW";    alert = "MEDIUM"
    else:
        status = "ADEQUATE";       alert = "LOW"

    days_of_stock = round(current_stock / avg_daily_demand, 1) if avg_daily_demand else 999

    return {
        "eoq":           eoq,
        "safety_stock":  safety,
        "reorder_point": rop,
        "stock_status": {
            "status":         status,
            "alert_level":    alert,
            "current_stock":  current_stock,
            "days_of_stock":  days_of_stock,
            "should_reorder": current_stock <= reorder_point,
        },
        "recommendation": {
            "action":         "Place order now" if current_stock <= reorder_point else "Stock is adequate",
            "order_quantity": eoq["eoq"],
            "urgency":        alert,
        }
    }
