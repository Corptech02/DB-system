#!/usr/bin/env python3
"""Test the leads API endpoint"""

import requests
import json

# Test the search endpoint with insurance filter
print("Testing leads generation...")

# Test with insurance expiring in 90 days
payload = {
    "insurance_expiring_days": 90,
    "operating_status": "ACTIVE",
    "page": 1,
    "per_page": 20
}

try:
    response = requests.post(
        "http://localhost:8000/api/search",
        json=payload
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Total carriers found: {data.get('total', 0)}")
        print(f"Number of carriers returned: {len(data.get('carriers', []))}")
        
        if data.get('carriers'):
            # Check first carrier
            carrier = data['carriers'][0]
            print("\nFirst carrier:")
            print(f"  Name: {carrier.get('legal_name')}")
            print(f"  USDOT: {carrier.get('usdot_number')}")
            print(f"  Insurance Date: {carrier.get('liability_insurance_date')}")
            print(f"  Power Units: {carrier.get('power_units')}")
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Connection error: {e}")
    print("\nMake sure the API server is running:")
    print("  cd D:\\context-engineering-intro")
    print("  python demo_real_api.py")

# Test without insurance filter
print("\n" + "="*50)
print("Testing without insurance filter...")

payload2 = {
    "operating_status": "ACTIVE",
    "page": 1,
    "per_page": 10
}

try:
    response = requests.post(
        "http://localhost:8000/api/search",
        json=payload2
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"Total carriers found: {data.get('total', 0)}")
        print(f"Carriers have insurance dates: {sum(1 for c in data.get('carriers', []) if c.get('liability_insurance_date'))}/{len(data.get('carriers', []))}")
except Exception as e:
    print(f"Error: {e}")