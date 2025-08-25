#!/usr/bin/env python3
"""
Find working sources for FMCSA data
Try various alternatives including archives, mirrors, and aggregators
"""

import requests
import json
from datetime import datetime

def test_sources():
    """Test various alternative data sources"""
    
    sources = [
        {
            "name": "Transportation.gov Open Data",
            "url": "https://www.transportation.gov/data",
            "api": "https://api.transportation.gov/",
            "description": "Main DOT data portal"
        },
        {
            "name": "Data.gov Direct Dataset",
            "url": "https://catalog.data.gov/dataset/motor-carrier-registrations-census-files",
            "api": "https://catalog.data.gov/api/3/action/resource_show?id=0af23347-261b-4c6a-8bfc-eba51ec105a7",
            "description": "Motor Carrier Census via Data.gov"
        },
        {
            "name": "Internet Archive Wayback Machine",
            "url": "https://web.archive.org/web/20240101000000*/ai.fmcsa.dot.gov/SMS/Tools/Downloads.aspx",
            "api": "https://archive.org/wayback/available?url=ai.fmcsa.dot.gov",
            "description": "Archived FMCSA data"
        },
        {
            "name": "GitHub - FMCSA Data Projects",
            "url": "https://api.github.com/search/repositories?q=fmcsa+data+csv",
            "api": "https://api.github.com/search/code?q=fmcsa+extension:csv",
            "description": "GitHub repositories with FMCSA data"
        },
        {
            "name": "Kaggle Datasets",
            "url": "https://www.kaggle.com/datasets?search=truck+carrier+fmcsa",
            "api": None,
            "description": "Kaggle transportation datasets"
        },
        {
            "name": "OpenDataSoft",
            "url": "https://data.opendatasoft.com/explore/?q=transportation",
            "api": "https://data.opendatasoft.com/api/v2/catalog/datasets",
            "description": "Open data aggregator"
        }
    ]
    
    print("=" * 80)
    print("Testing Alternative FMCSA Data Sources")
    print("=" * 80)
    
    working_sources = []
    
    for source in sources:
        print(f"\n{source['name']}")
        print("-" * 40)
        
        # Test API endpoint if available
        if source['api']:
            try:
                response = requests.get(source['api'], timeout=5)
                print(f"API Status: {response.status_code}")
                
                if response.status_code == 200:
                    print("✅ API is accessible!")
                    working_sources.append(source)
                    
                    # For GitHub, show repositories found
                    if 'github' in source['api']:
                        data = response.json()
                        if 'items' in data:
                            print(f"Found {data['total_count']} repositories")
                            for repo in data['items'][:3]:
                                print(f"  - {repo['full_name']}: {repo['description'][:50] if repo['description'] else 'No description'}...")
                    
                    # For Data.gov, show resource info
                    elif 'catalog.data.gov' in source['api']:
                        data = response.json()
                        if data.get('success'):
                            result = data.get('result', {})
                            print(f"  Resource: {result.get('name', 'Unknown')}")
                            print(f"  Format: {result.get('format', 'Unknown')}")
                            print(f"  URL: {result.get('url', 'No URL')[:80]}")
                            
                elif response.status_code == 403:
                    print("❌ Access forbidden")
                else:
                    print(f"❌ Status: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ Error: {str(e)[:50]}")
        else:
            print("ℹ️ No API endpoint to test")
    
    return working_sources


def test_github_data():
    """Search GitHub for FMCSA CSV data files"""
    
    print("\n" + "=" * 80)
    print("Searching GitHub for FMCSA Data Files")
    print("=" * 80)
    
    # Search for CSV files containing FMCSA data
    search_url = "https://api.github.com/search/code"
    params = {
        "q": "USDOT carrier extension:csv size:>1000",
        "per_page": 10
    }
    
    headers = {
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        response = requests.get(search_url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            
            print(f"Found {len(items)} potential CSV files with carrier data:")
            
            for item in items[:5]:
                print(f"\n📁 File: {item['name']}")
                print(f"   Repo: {item['repository']['full_name']}")
                print(f"   Path: {item['path']}")
                print(f"   URL: {item['html_url']}")
                
                # Get raw URL for downloading
                raw_url = item['html_url'].replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
                print(f"   Raw: {raw_url}")
                
                # Test if we can access the raw file
                try:
                    head_response = requests.head(raw_url, timeout=3)
                    if head_response.status_code == 200:
                        size = head_response.headers.get('Content-Length', 'Unknown')
                        print(f"   ✅ Accessible! Size: {size} bytes")
                except:
                    print(f"   ❌ Cannot access raw file")
                    
        else:
            print(f"GitHub search failed: {response.status_code}")
            if response.status_code == 403:
                print("Rate limited - GitHub API has usage limits")
                
    except Exception as e:
        print(f"Error searching GitHub: {e}")


def test_wayback_machine():
    """Check if FMCSA data is available in Internet Archive"""
    
    print("\n" + "=" * 80)
    print("Checking Internet Archive for FMCSA Data")
    print("=" * 80)
    
    # Check if FMCSA downloads page is archived
    wayback_api = "https://archive.org/wayback/available"
    
    urls_to_check = [
        "ai.fmcsa.dot.gov/SMS/Tools/Downloads.aspx",
        "safer.fmcsa.dot.gov/CompanySnapshot.aspx",
        "li-public.fmcsa.dot.gov"
    ]
    
    for url in urls_to_check:
        print(f"\nChecking archive for: {url}")
        
        params = {"url": url}
        try:
            response = requests.get(wayback_api, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                snapshots = data.get('archived_snapshots', {})
                
                if snapshots.get('closest'):
                    snapshot = snapshots['closest']
                    print(f"✅ Found snapshot from: {snapshot['timestamp']}")
                    print(f"   Status: {snapshot['status']}")
                    print(f"   URL: {snapshot['url']}")
                else:
                    print("❌ No snapshots found")
        except Exception as e:
            print(f"Error: {e}")


def main():
    # Test various sources
    working = test_sources()
    
    # Search GitHub for data
    test_github_data()
    
    # Check Wayback Machine
    test_wayback_machine()
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    if working:
        print(f"\n✅ Found {len(working)} working sources:")
        for source in working:
            print(f"  - {source['name']}")
    
    print("""
Next Steps:
1. Check GitHub repositories for shared FMCSA data
2. Try Internet Archive snapshots
3. Use data.gov API to get metadata (even if downloads are blocked)
4. Consider using your existing 2.2M carrier dataset
5. Set up a US-based proxy or VPN service
""")


if __name__ == "__main__":
    main()