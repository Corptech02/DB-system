"""
Standalone FMCSA Demo API - No dependencies on other modules
Run this file directly: python demo_api.py
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import random
import uvicorn

# Create FastAPI app
app = FastAPI(
    title="FMCSA Carrier Management API (Demo)",
    description="Standalone demo version - no database required",
    version="1.0.0"
)

# Enable CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class SearchFilters(BaseModel):
    state: Optional[str] = None
    operating_status: Optional[str] = None
    min_power_units: Optional[int] = None
    max_power_units: Optional[int] = None
    text_search: Optional[str] = None
    insurance_expiring_days: Optional[int] = None
    hazmat_only: Optional[bool] = False
    page: int = 1
    per_page: int = 20

# Generate sample data
def generate_sample_carriers(count: int = 2000) -> List[Dict[str, Any]]:
    """Generate sample carrier data for testing."""
    # All US states for more realistic distribution
    states = [
        "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
        "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
        "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
        "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
        "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
    ]
    
    # Major cities by state (simplified)
    state_cities = {
        "TX": ["Houston", "Dallas", "Austin", "San Antonio", "Fort Worth"],
        "CA": ["Los Angeles", "San Francisco", "San Diego", "Sacramento", "San Jose"],
        "FL": ["Miami", "Orlando", "Tampa", "Jacksonville", "Fort Lauderdale"],
        "NY": ["New York", "Buffalo", "Rochester", "Albany", "Syracuse"],
        "IL": ["Chicago", "Aurora", "Rockford", "Joliet", "Naperville"],
        "PA": ["Philadelphia", "Pittsburgh", "Allentown", "Erie", "Reading"],
        "OH": ["Columbus", "Cleveland", "Cincinnati", "Toledo", "Akron"],
        "GA": ["Atlanta", "Augusta", "Columbus", "Savannah", "Athens"],
        "NC": ["Charlotte", "Raleigh", "Greensboro", "Durham", "Winston-Salem"],
        "MI": ["Detroit", "Grand Rapids", "Warren", "Sterling Heights", "Lansing"]
    }
    
    company_types = ["Transport", "Logistics", "Freight", "Shipping", "Express", "Carriers", "Trucking", "Delivery", "Lines", "Services"]
    company_prefixes = ["National", "American", "United", "Global", "Premier", "Elite", "Superior", "Professional", "Reliable", "Quality"]
    
    statuses = ["ACTIVE", "INACTIVE", "OUT_OF_SERVICE"]
    ratings = ["SATISFACTORY", "CONDITIONAL", "UNSATISFACTORY", None]
    entity_types = ["CARRIER", "BROKER", "FREIGHT_FORWARDER", "SHIPPER"]
    
    carriers = []
    for i in range(count):
        # Random state selection for more realistic distribution
        state = random.choice(states)
        
        # Get cities for the state, or use default
        cities = state_cities.get(state, ["City Center", "Downtown", "Metro Area", "Industrial District", "Business Park"])
        city = random.choice(cities)
        
        # Generate more realistic USDOT numbers (random 6-7 digit numbers)
        usdot = random.randint(100000, 9999999)
        
        # Generate more realistic company names
        company_name = f"{random.choice(company_prefixes)} {random.choice(company_types)} {random.choice(['LLC', 'Inc', 'Corp', 'Company', 'Group'])}"
        
        carriers.append({
            "usdot_number": usdot,
            "legal_name": company_name,
            "dba_name": f"{random.choice(company_prefixes)} {random.choice(['Express', 'Transport', 'Freight'])}" if i % 3 == 0 else None,
            "physical_state": state,
            "physical_city": city,
            "physical_address": f"{random.randint(100, 9999)} Main Street",
            "physical_zip": f"{random.randint(10000, 99999)}",
            "operating_status": random.choice(statuses),
            "entity_type": random.choice(entity_types),
            "power_units": random.randint(1, 100),
            "drivers": random.randint(1, 150),
            "hazmat_flag": random.choice([True, False]),
            "liability_insurance_date": f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
            "liability_insurance_amount": random.randint(500000, 2000000),
            "safety_rating": random.choice(ratings),
            "telephone": f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            "email": f"info@carrier{i+1}.com",
            "mcs_150_date": f"2024-0{random.randint(1, 9)}-{random.randint(1, 28):02d}",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        })
    return carriers

# Store sample data - 2000 carriers across all 50 states
SAMPLE_CARRIERS = generate_sample_carriers(2000)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "FMCSA API Demo (Standalone)",
        "status": "running",
        "docs_url": "/docs",
        "total_carriers": len(SAMPLE_CARRIERS),
        "endpoints": {
            "search": "/api/search",
            "stats": "/api/stats",
            "health": "/api/health"
        }
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "mode": "demo_standalone"
    }

@app.post("/api/search")
async def search_carriers(filters: SearchFilters):
    """Search carriers with filters."""
    results = SAMPLE_CARRIERS.copy()
    
    # Apply filters
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
    
    if filters.hazmat_only:
        results = [c for c in results if c.get("hazmat_flag", False)]
    
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
        "pages": max(1, (total + filters.per_page - 1) // filters.per_page),
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
    """Get carrier statistics."""
    active = len([c for c in SAMPLE_CARRIERS if c["operating_status"] == "ACTIVE"])
    inactive = len([c for c in SAMPLE_CARRIERS if c["operating_status"] == "INACTIVE"])
    
    by_state = {}
    for carrier in SAMPLE_CARRIERS:
        state = carrier["physical_state"]
        by_state[state] = by_state.get(state, 0) + 1
    
    by_entity = {}
    for carrier in SAMPLE_CARRIERS:
        entity = carrier.get("entity_type", "UNKNOWN")
        by_entity[entity] = by_entity.get(entity, 0) + 1
    
    return {
        "total_carriers": len(SAMPLE_CARRIERS),
        "active_carriers": active,
        "inactive_carriers": inactive,
        "by_state": by_state,
        "by_entity_type": by_entity,
        "by_operating_status": {
            "ACTIVE": active,
            "INACTIVE": inactive,
            "OUT_OF_SERVICE": len(SAMPLE_CARRIERS) - active - inactive
        },
        "insurance_stats": {
            "expired": random.randint(40, 60),
            "expiring_30_days": random.randint(60, 80),
            "expiring_60_days": random.randint(80, 100),
            "expiring_90_days": random.randint(100, 120),
            "valid": random.randint(200, 250),
            "unknown": random.randint(0, 10)
        },
        "hazmat_carriers": len([c for c in SAMPLE_CARRIERS if c.get("hazmat_flag", False)]),
        "avg_power_units": sum(c.get("power_units", 0) for c in SAMPLE_CARRIERS) / len(SAMPLE_CARRIERS),
        "avg_drivers": sum(c.get("drivers", 0) for c in SAMPLE_CARRIERS) / len(SAMPLE_CARRIERS),
        "last_updated": datetime.now().isoformat()
    }

@app.get("/api/stats/summary")
async def get_summary_stats():
    """Get summary statistics."""
    active_count = len([c for c in SAMPLE_CARRIERS if c["operating_status"] == "ACTIVE"])
    hazmat_count = len([c for c in SAMPLE_CARRIERS if c.get("hazmat_flag", False)])
    states = set(c["physical_state"] for c in SAMPLE_CARRIERS)
    
    return {
        "total_carriers": len(SAMPLE_CARRIERS),
        "active_carriers": active_count,
        "expired_insurance": random.randint(40, 60),
        "expiring_soon": random.randint(60, 80),
        "hazmat_carriers": hazmat_count,
        "states_covered": len(states)
    }

@app.get("/api/stats/top-states")
async def get_top_states(limit: int = 10):
    """Get top states by carrier count."""
    by_state = {}
    for carrier in SAMPLE_CARRIERS:
        state = carrier["physical_state"]
        if state not in by_state:
            by_state[state] = {
                "state": state,
                "total_carriers": 0,
                "active_carriers": 0,
                "avg_fleet_size": 0
            }
        by_state[state]["total_carriers"] += 1
        if carrier["operating_status"] == "ACTIVE":
            by_state[state]["active_carriers"] += 1
    
    # Calculate average fleet size
    for state_data in by_state.values():
        state_carriers = [c for c in SAMPLE_CARRIERS if c["physical_state"] == state_data["state"]]
        if state_carriers:
            state_data["avg_fleet_size"] = sum(c.get("power_units", 0) for c in state_carriers) / len(state_carriers)
    
    sorted_states = sorted(by_state.values(), key=lambda x: x["total_carriers"], reverse=True)
    return sorted_states[:limit]

@app.get("/api/stats/insurance-expiration-forecast")
async def get_insurance_forecast(days: int = 90):
    """Get insurance expiration forecast."""
    return {
        "forecast_days": days,
        "expiring_week_1": random.randint(15, 25),
        "expiring_week_2": random.randint(20, 30),
        "expiring_month_1": random.randint(40, 60),
        "expiring_month_2": random.randint(50, 70),
        "expiring_month_3": random.randint(60, 80),
        "expiring_beyond_90": random.randint(100, 150)
    }

@app.get("/api/leads/expiring-insurance")
async def get_expiring_insurance_leads(
    days_ahead: int = 90,
    state: Optional[str] = None,
    min_power_units: Optional[int] = None,
    limit: int = 100
):
    """Get insurance expiration leads."""
    leads = []
    sample_leads = SAMPLE_CARRIERS[:limit]
    
    if state:
        sample_leads = [c for c in sample_leads if c["physical_state"] == state]
    
    if min_power_units:
        sample_leads = [c for c in sample_leads if c.get("power_units", 0) >= min_power_units]
    
    for carrier in sample_leads[:limit]:
        days_until = random.randint(-30, days_ahead)
        if days_until < 0:
            insurance_status = "expired"
            lead_score = "hot"
        elif days_until <= 30:
            insurance_status = "expiring_soon"
            lead_score = "hot"
        elif days_until <= 60:
            insurance_status = "expiring_60_days"
            lead_score = "warm"
        elif days_until <= 90:
            insurance_status = "expiring_90_days"
            lead_score = "cool"
        else:
            insurance_status = "valid"
            lead_score = "cold"
        
        leads.append({
            **carrier,
            "days_until_expiration": days_until,
            "insurance_status": insurance_status,
            "lead_score": lead_score,
            "score_value": random.randint(40, 100),
            "score_reasons": [
                "Insurance expiring soon" if days_until <= 30 else "Insurance status tracked",
                "Fleet size: " + str(carrier.get("power_units", 0)) + " units"
            ],
            "priority": 1 if lead_score == "hot" else (2 if lead_score == "warm" else 3),
            "best_contact_method": "phone" if carrier.get("telephone") else "email"
        })
    
    return sorted(leads, key=lambda x: x["priority"])

@app.post("/api/export")
async def create_export(request: Dict[str, Any]):
    """Create export (mock)."""
    return {
        "file_id": f"export-{random.randint(1000, 9999)}",
        "filename": f"carriers_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        "format": request.get("format", "csv"),
        "size_bytes": random.randint(100000, 1000000),
        "row_count": len(SAMPLE_CARRIERS),
        "download_url": f"/api/export/download/export-demo"
    }

if __name__ == "__main__":
    print("=" * 50)
    print("FMCSA Demo API Server")
    print("=" * 50)
    print("")
    print("Starting server on http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("")
    print("Press CTRL+C to stop")
    print("-" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)