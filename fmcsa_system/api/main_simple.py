"""
Simplified FMCSA API for testing without database dependencies.
This version works without PostgreSQL for initial testing.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import random

# Create FastAPI app
app = FastAPI(
    title="FMCSA Carrier Management API (Demo)",
    description="Simplified demo version without database",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sample data models
class Carrier(BaseModel):
    usdot_number: int
    legal_name: str
    dba_name: Optional[str] = None
    physical_state: str
    physical_city: str
    operating_status: str
    power_units: Optional[int] = None
    drivers: Optional[int] = None
    liability_insurance_date: Optional[str] = None
    safety_rating: Optional[str] = None

class SearchFilters(BaseModel):
    state: Optional[str] = None
    operating_status: Optional[str] = None
    min_power_units: Optional[int] = None
    max_power_units: Optional[int] = None
    text_search: Optional[str] = None
    page: int = 1
    per_page: int = 20

# Generate sample data
def generate_sample_carriers(count: int = 100) -> List[Dict[str, Any]]:
    """Generate sample carrier data for testing."""
    states = ["TX", "CA", "FL", "NY", "IL", "PA", "OH", "GA", "NC", "MI"]
    cities = ["Houston", "Los Angeles", "Miami", "New York", "Chicago", "Philadelphia", "Columbus", "Atlanta", "Charlotte", "Detroit"]
    statuses = ["ACTIVE", "INACTIVE", "OUT_OF_SERVICE"]
    ratings = ["SATISFACTORY", "CONDITIONAL", "UNSATISFACTORY", None]
    
    carriers = []
    for i in range(count):
        state_idx = i % len(states)
        carriers.append({
            "usdot_number": 100000 + i,
            "legal_name": f"Carrier Company {i + 1} LLC",
            "dba_name": f"Carrier Express {i + 1}" if i % 2 == 0 else None,
            "physical_state": states[state_idx],
            "physical_city": cities[state_idx],
            "operating_status": random.choice(statuses),
            "power_units": random.randint(1, 100),
            "drivers": random.randint(1, 150),
            "liability_insurance_date": f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            "safety_rating": random.choice(ratings),
            "telephone": f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            "email": f"info@carrier{i+1}.com"
        })
    return carriers

# Store sample data in memory
SAMPLE_CARRIERS = generate_sample_carriers(500)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "FMCSA API Demo (No Database)",
        "status": "running",
        "docs": "/docs",
        "total_carriers": len(SAMPLE_CARRIERS)
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "mode": "demo",
        "database": "not_connected"
    }

@app.post("/api/search")
async def search_carriers(filters: SearchFilters):
    """Search carriers with filters (demo data)."""
    # Filter the sample data
    results = SAMPLE_CARRIERS.copy()
    
    if filters.state:
        results = [c for c in results if c["physical_state"] == filters.state]
    
    if filters.operating_status:
        results = [c for c in results if c["operating_status"] == filters.operating_status]
    
    if filters.min_power_units:
        results = [c for c in results if c.get("power_units", 0) >= filters.min_power_units]
    
    if filters.max_power_units:
        results = [c for c in results if c.get("power_units", 999) <= filters.max_power_units]
    
    if filters.text_search:
        search_lower = filters.text_search.lower()
        results = [c for c in results if search_lower in c["legal_name"].lower()]
    
    # Pagination
    total = len(results)
    start_idx = (filters.page - 1) * filters.per_page
    end_idx = start_idx + filters.per_page
    paginated_results = results[start_idx:end_idx]
    
    return {
        "carriers": paginated_results,
        "total": total,
        "page": filters.page,
        "per_page": filters.per_page,
        "pages": (total + filters.per_page - 1) // filters.per_page,
        "query_time_ms": random.randint(10, 50)
    }

@app.get("/api/carriers/{usdot_number}")
async def get_carrier(usdot_number: int):
    """Get specific carrier by USDOT number."""
    carrier = next((c for c in SAMPLE_CARRIERS if c["usdot_number"] == usdot_number), None)
    if not carrier:
        raise HTTPException(status_code=404, detail="Carrier not found")
    return carrier

@app.get("/api/stats")
async def get_statistics():
    """Get carrier statistics (demo data)."""
    active = len([c for c in SAMPLE_CARRIERS if c["operating_status"] == "ACTIVE"])
    inactive = len([c for c in SAMPLE_CARRIERS if c["operating_status"] == "INACTIVE"])
    
    # Count by state
    by_state = {}
    for carrier in SAMPLE_CARRIERS:
        state = carrier["physical_state"]
        by_state[state] = by_state.get(state, 0) + 1
    
    return {
        "total_carriers": len(SAMPLE_CARRIERS),
        "active_carriers": active,
        "inactive_carriers": inactive,
        "by_state": by_state,
        "by_entity_type": {
            "CARRIER": len(SAMPLE_CARRIERS) * 0.7,
            "BROKER": len(SAMPLE_CARRIERS) * 0.2,
            "FREIGHT_FORWARDER": len(SAMPLE_CARRIERS) * 0.1
        },
        "by_operating_status": {
            "ACTIVE": active,
            "INACTIVE": inactive,
            "OUT_OF_SERVICE": len(SAMPLE_CARRIERS) - active - inactive
        },
        "insurance_stats": {
            "expired": 50,
            "expiring_30_days": 75,
            "expiring_60_days": 100,
            "expiring_90_days": 125,
            "valid": 150,
            "unknown": 0
        },
        "hazmat_carriers": 45,
        "avg_power_units": 35.5,
        "avg_drivers": 42.3,
        "last_updated": datetime.now().isoformat()
    }

@app.get("/api/stats/summary")
async def get_summary_stats():
    """Get summary statistics."""
    return {
        "total_carriers": len(SAMPLE_CARRIERS),
        "active_carriers": len([c for c in SAMPLE_CARRIERS if c["operating_status"] == "ACTIVE"]),
        "expired_insurance": 50,
        "expiring_soon": 75,
        "hazmat_carriers": 45,
        "states_covered": len(set(c["physical_state"] for c in SAMPLE_CARRIERS))
    }

@app.get("/api/stats/top-states")
async def get_top_states(limit: int = 10):
    """Get top states by carrier count."""
    by_state = {}
    for carrier in SAMPLE_CARRIERS:
        state = carrier["physical_state"]
        if state not in by_state:
            by_state[state] = {"state": state, "total_carriers": 0, "active_carriers": 0}
        by_state[state]["total_carriers"] += 1
        if carrier["operating_status"] == "ACTIVE":
            by_state[state]["active_carriers"] += 1
    
    sorted_states = sorted(by_state.values(), key=lambda x: x["total_carriers"], reverse=True)
    return sorted_states[:limit]

@app.get("/api/leads/expiring-insurance")
async def get_expiring_insurance_leads(days_ahead: int = 90, state: Optional[str] = None, limit: int = 100):
    """Get insurance expiration leads (demo data)."""
    leads = []
    sample_leads = SAMPLE_CARRIERS[:limit]
    
    if state:
        sample_leads = [c for c in sample_leads if c["physical_state"] == state]
    
    for carrier in sample_leads[:limit]:
        leads.append({
            **carrier,
            "days_until_expiration": random.randint(-30, days_ahead),
            "insurance_status": random.choice(["expired", "expiring_soon", "expiring_60_days", "valid"]),
            "lead_score": random.choice(["hot", "warm", "cool", "cold"]),
            "score_value": random.randint(40, 100),
            "score_reasons": ["Insurance expiring soon", "Large fleet"],
            "priority": random.randint(1, 5),
            "best_contact_method": "phone"
        })
    
    return leads

@app.post("/api/export")
async def create_export(format: str = "csv"):
    """Create export (returns mock response)."""
    return {
        "file_id": "export-demo-123",
        "filename": f"carriers_export_demo.{format}",
        "format": format,
        "size_bytes": 1024000,
        "row_count": len(SAMPLE_CARRIERS),
        "download_url": f"/api/export/download/export-demo-123"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)