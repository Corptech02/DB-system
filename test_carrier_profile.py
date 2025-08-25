#!/usr/bin/env python3
"""Test that carrier profile endpoint returns insurance and inspection data"""

import requests
import json

# First, get some carriers to test
print("Getting carriers list...")
response = requests.post("http://localhost:8000/api/search", json={"per_page": 5})

if response.status_code != 200:
    print(f"Error getting carriers: {response.status_code}")
    print("Make sure the API server is running:")
    print("  cd D:\\context-engineering-intro")
    print("  python demo_real_api.py")
    exit(1)

carriers = response.json().get("carriers", [])
if not carriers:
    print("No carriers found")
    exit(1)

print(f"Found {len(carriers)} carriers")
print("=" * 80)

# Test each carrier's profile endpoint
for carrier in carriers[:3]:  # Test first 3
    usdot = carrier.get("usdot_number")
    print(f"\nTesting carrier USDOT #{usdot}")
    print("-" * 40)
    
    # Get the full profile
    profile_response = requests.get(f"http://localhost:8000/api/carriers/{usdot}")
    
    if profile_response.status_code != 200:
        print(f"  ERROR: Failed to get profile: {profile_response.status_code}")
        continue
    
    profile = profile_response.json()
    
    # Check for insurance data
    print(f"  Name: {profile.get('legal_name', 'N/A')}")
    print(f"  Insurance Company: {profile.get('insurance_company', 'NOT FOUND')}")
    print(f"  Insurance Date: {profile.get('liability_insurance_date', 'NOT FOUND')}")
    print(f"  Insurance Amount: ${profile.get('liability_insurance_amount', 0):,}")
    
    # Check for inspection data
    print(f"  Last Inspection: {profile.get('last_inspection_date', 'NOT FOUND')}")
    print(f"  Total Inspections: {profile.get('total_inspections', 'NOT FOUND')}")
    print(f"  Total Violations: {profile.get('total_violations', 'NOT FOUND')}")
    print(f"  Violation Rate: {profile.get('violation_rate', 'NOT FOUND')}")
    
    # Check for VIN data
    print(f"  Sample VIN: {profile.get('sample_vin', 'NOT FOUND')}")
    print(f"  Total Vehicles: {profile.get('total_vehicles', 'NOT FOUND')}")
    
    # Flag any missing data
    missing = []
    if not profile.get('insurance_company'):
        missing.append('insurance_company')
    if not profile.get('liability_insurance_date'):
        missing.append('liability_insurance_date')
    if not profile.get('last_inspection_date'):
        missing.append('last_inspection_date')
    if profile.get('power_units', 0) > 0 and not profile.get('sample_vin'):
        missing.append('sample_vin')
    
    if missing:
        print(f"  ⚠️ MISSING DATA: {', '.join(missing)}")
    else:
        print(f"  ✅ All data present")

print("\n" + "=" * 80)
print("Test complete")