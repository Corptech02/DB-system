#!/usr/bin/env python3
"""
Test alternative FMCSA data sources that might not be blocked
"""

import requests
import json

def test_endpoints():
    """Test various FMCSA-related endpoints"""
    
    endpoints = [
        {
            "name": "NHTSA Recalls API (includes commercial vehicles)",
            "url": "https://api.nhtsa.gov/products/vehicle/makes?issueType=r",
            "description": "NHTSA API - might have carrier data"
        },
        {
            "name": "DOT Data Hub API",
            "url": "https://data.transportation.gov/api/views/metadata/v1",
            "description": "DOT open data portal metadata"
        },
        {
            "name": "Census Bureau API (has business data)",
            "url": "https://api.census.gov/data/2021/cbp?get=NAICS2017,EMP&for=state:*",
            "description": "Census business patterns - includes trucking"
        },
        {
            "name": "data.gov CKAN API",
            "url": "https://catalog.data.gov/api/3/action/package_list",
            "description": "Data.gov catalog API"
        },
        {
            "name": "OpenFEMA API",
            "url": "https://www.fema.gov/api/open/v1/OpenFemaDataSets",
            "description": "FEMA open data - might have carrier info"
        }
    ]
    
    print("=" * 80)
    print("Testing Alternative Data Sources")
    print("=" * 80)
    
    working_endpoints = []
    
    for endpoint in endpoints:
        print(f"\n{endpoint['name']}")
        print("-" * 40)
        print(f"URL: {endpoint['url']}")
        
        try:
            response = requests.get(endpoint['url'], timeout=5)
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ WORKING - This endpoint is accessible!")
                working_endpoints.append(endpoint)
                
                # Show sample of response
                try:
                    data = response.json()
                    if isinstance(data, list):
                        print(f"Response: List with {len(data)} items")
                    elif isinstance(data, dict):
                        print(f"Response: Dict with keys: {list(data.keys())[:5]}")
                except:
                    print("Response: Non-JSON data")
            else:
                print(f"❌ Not accessible - Status {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if working_endpoints:
        print(f"\n✅ Found {len(working_endpoints)} working endpoints:")
        for ep in working_endpoints:
            print(f"  - {ep['name']}")
    else:
        print("\n❌ No working endpoints found")
    
    # Test searching data.gov for FMCSA datasets
    print("\n" + "=" * 80)
    print("Searching data.gov for FMCSA datasets...")
    print("=" * 80)
    
    try:
        search_url = "https://catalog.data.gov/api/3/action/package_search"
        params = {
            "q": "FMCSA motor carrier",
            "rows": 5
        }
        
        response = requests.get(search_url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                results = data.get("result", {}).get("results", [])
                print(f"\nFound {len(results)} FMCSA-related datasets:")
                
                for dataset in results:
                    print(f"\n- {dataset.get('title', 'No title')}")
                    print(f"  Organization: {dataset.get('organization', {}).get('title', 'N/A')}")
                    
                    # Check for downloadable resources
                    resources = dataset.get('resources', [])
                    for resource in resources:
                        if resource.get('format', '').upper() in ['CSV', 'JSON', 'XML']:
                            print(f"  📊 {resource.get('format')} available: {resource.get('name', 'Unnamed')}")
                            url = resource.get('url', '')
                            if url:
                                print(f"     URL: {url[:80]}...")
        else:
            print(f"Search failed: {response.status_code}")
            
    except Exception as e:
        print(f"Error searching data.gov: {e}")
    
    return working_endpoints


def test_dot_socrata():
    """Test DOT's Socrata API endpoints"""
    print("\n" + "=" * 80)
    print("Testing DOT Socrata API")
    print("=" * 80)
    
    # Try different Socrata endpoints
    endpoints = [
        "https://data.transportation.gov/api/views.json",
        "https://data.transportation.gov/resource/a7qi-9vxj.json?$limit=1",  # Try a specific dataset
        "https://opendata.socrata.com/resource/7xzn-4j4j.json?$limit=1"
    ]
    
    for url in endpoints:
        print(f"\nTrying: {url}")
        try:
            response = requests.get(url, timeout=5)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print("✅ WORKING!")
                data = response.json()
                if isinstance(data, list):
                    print(f"Got {len(data)} records")
                return True
        except Exception as e:
            print(f"Error: {e}")
    
    return False


if __name__ == "__main__":
    # Test various endpoints
    working = test_endpoints()
    
    # Test Socrata specifically
    test_dot_socrata()
    
    print("\n" + "=" * 80)
    print("Next Steps:")
    print("=" * 80)
    print("""
If none of these work, you can:
1. Use the browser on Windows to manually access FMCSA sites
2. Set up a proxy server in the US
3. Use a commercial API service
4. Work with the existing 2.2M carrier dataset you already have
""")