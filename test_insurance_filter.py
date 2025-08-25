#!/usr/bin/env python3
"""Test the insurance company filter functionality"""

import requests
import json

# Test the search endpoint with insurance company filter
print("Testing insurance company filter...")
print("="*50)

# First, get some carriers without filter to see available companies
print("\n1. Getting carriers to see insurance companies...")
payload = {
    "operating_status": "ACTIVE",
    "insurance_expiring_days": 90,
    "page": 1,
    "per_page": 50
}

try:
    response = requests.post(
        "http://localhost:8000/api/search",
        json=payload
    )
    
    if response.status_code == 200:
        data = response.json()
        carriers = data.get('carriers', [])
        
        # Collect unique insurance companies
        companies = set()
        for carrier in carriers:
            if carrier.get('insurance_company'):
                companies.add(carrier['insurance_company'])
        
        print(f"Found {len(companies)} unique insurance companies in first 50 results:")
        for company in sorted(companies)[:10]:
            print(f"  - {company}")
        
        # Test filtering by specific companies
        test_companies = list(companies)[:3]  # Pick first 3 companies
        
        print(f"\n2. Testing filter with companies: {test_companies}")
        print("-"*50)
        
        filter_payload = {
            "operating_status": "ACTIVE",
            "insurance_expiring_days": 90,
            "insurance_companies": test_companies,
            "page": 1,
            "per_page": 20
        }
        
        response2 = requests.post(
            "http://localhost:8000/api/search",
            json=filter_payload
        )
        
        if response2.status_code == 200:
            filtered_data = response2.json()
            filtered_carriers = filtered_data.get('carriers', [])
            
            print(f"Total carriers found: {filtered_data.get('total', 0)}")
            print(f"Carriers returned: {len(filtered_carriers)}")
            
            # Verify all carriers have the correct insurance companies
            wrong_company = False
            for carrier in filtered_carriers:
                company = carrier.get('insurance_company')
                if company not in test_companies:
                    print(f"ERROR: Carrier {carrier.get('usdot_number')} has company '{company}' not in filter!")
                    wrong_company = True
            
            if not wrong_company:
                print("✓ All carriers have correct insurance companies")
            
            # Show some results
            print("\nFirst 3 carriers:")
            for carrier in filtered_carriers[:3]:
                print(f"  USDOT: {carrier.get('usdot_number')}")
                print(f"  Name: {carrier.get('legal_name')}")
                print(f"  Insurance Company: {carrier.get('insurance_company')}")
                print(f"  Insurance Date: {carrier.get('liability_insurance_date')}")
                print()
        else:
            print(f"Error in filtered request: {response2.text}")
            
    else:
        print(f"Error in initial request: {response.text}")
        
except Exception as e:
    print(f"Connection error: {e}")
    print("\nMake sure the API server is running:")
    print("  cd D:\\context-engineering-intro")
    print("  python demo_real_api.py")

# Test with single insurance company
print("\n3. Testing with single insurance company...")
print("-"*50)

single_company_payload = {
    "operating_status": "ACTIVE",
    "insurance_expiring_days": 30,
    "insurance_companies": ["Progressive Commercial"],
    "page": 1,
    "per_page": 10
}

try:
    response3 = requests.post(
        "http://localhost:8000/api/search",
        json=single_company_payload
    )
    
    if response3.status_code == 200:
        single_data = response3.json()
        print(f"Carriers with Progressive Commercial expiring in 30 days: {single_data.get('total', 0)}")
        
        for carrier in single_data.get('carriers', [])[:3]:
            print(f"  - {carrier.get('legal_name')} (USDOT: {carrier.get('usdot_number')})")
            
except Exception as e:
    print(f"Error: {e}")

print("\n✅ Insurance company filter test complete")