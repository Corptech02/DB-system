#!/usr/bin/env python3
"""Test all statistics endpoints"""

import requests
import json

BASE_URL = "http://localhost:8000"

endpoints = [
    "/api/stats",
    "/api/stats/summary",
    "/api/stats/top-states?limit=10",
    "/api/stats/insurance-expiration-forecast?days=90"
]

print("Testing Statistics API Endpoints")
print("=" * 50)

for endpoint in endpoints:
    print(f"\nTesting: {endpoint}")
    print("-" * 30)
    
    try:
        response = requests.get(f"{BASE_URL}{endpoint}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            
            # Show sample of data
            if isinstance(data, dict):
                for key, value in list(data.items())[:5]:
                    if isinstance(value, dict):
                        print(f"  {key}: {type(value).__name__} with {len(value)} items")
                    elif isinstance(value, list):
                        print(f"  {key}: list with {len(value)} items")
                    else:
                        print(f"  {key}: {value}")
            elif isinstance(data, list):
                print(f"  Returned list with {len(data)} items")
                if data:
                    print(f"  First item keys: {list(data[0].keys())}")
        else:
            print(f"Error response: {response.text[:200]}")
            
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to API server")
        print("Make sure the server is running:")
        print("  cd D:\\context-engineering-intro")
        print("  python demo_real_api.py")
    except Exception as e:
        print(f"ERROR: {e}")

print("\n" + "=" * 50)
print("Test complete")