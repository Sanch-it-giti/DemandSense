

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import all our routers (each router handles one area)
from routers import forecast, inventory, dashboard, upload

# ── Create the FastAPI app ───────────────────────────────────
app = FastAPI(
    title="DemandSense API",
    description="Demand Forecasting & Inventory Optimization System",
    version="1.0.0"
)

# ── CORS Setup ───────────────────────────────────────────────
# This allows the React frontend (running on port 3000)
# to send requests to this backend (running on port 8000)
# Without this, the browser would block all requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register Routers ─────────────────────────────────────────
# Each router is a group of related endpoints
# prefix="/api" means all URLs start with /api/...
app.include_router(upload.router,    prefix="/api", tags=["Upload"])
app.include_router(forecast.router,  prefix="/api", tags=["Forecast"])
app.include_router(inventory.router, prefix="/api", tags=["Inventory"])
app.include_router(dashboard.router, prefix="/api", tags=["Dashboard"])

# ── Root endpoint ────────────────────────────────────────────
# Visit http://localhost:8000 to see this
@app.get("/")
def root():
    return {
        "app":    "DemandSense API",
        "status": "running ✅",
        "docs":   "Visit /docs to test all endpoints"
    }

# ── Health check ─────────────────────────────────────────────
# Used to confirm the server is alive
@app.get("/health")
def health():
    return {"status": "healthy"}
