#!/usr/bin/env python3
"""Test script to verify the API is working correctly."""

import requests
import json

# Test the root endpoint
try:
    response = requests.get("http://localhost:8000/")
    print("Root endpoint:", response.status_code)
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error accessing root: {e}")

# Test the search endpoint with empty filters
try:
    response = requests.post(
        "http://localhost:8000/api/search",
        json={"page": 1, "per_page": 5}
    )
    print("\n/api/search endpoint:", response.status_code)
    data = response.json()
    print(f"Total carriers: {data.get('total', 0)}")
    print(f"First carrier: {data.get('carriers', [])[0] if data.get('carriers') else 'None'}")
except Exception as e:
    print(f"Error accessing /api/search: {e}")

# Test search with USDOT number
try:
    response = requests.post(
        "http://localhost:8000/api/search",
        json={"usdot_number": "1000003", "page": 1, "per_page": 5}
    )
    print("\nSearch by USDOT:", response.status_code)
    data = response.json()
    print(f"Found carriers: {data.get('total', 0)}")
except Exception as e:
    print(f"Error searching by USDOT: {e}")

# Test search with state
try:
    response = requests.post(
        "http://localhost:8000/api/search",
        json={"state": "TX", "page": 1, "per_page": 5}
    )
    print("\nSearch by state (TX):", response.status_code)
    data = response.json()
    print(f"Found carriers: {data.get('total', 0)}")
except Exception as e:
    print(f"Error searching by state: {e}")