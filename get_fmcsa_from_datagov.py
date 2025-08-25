#!/usr/bin/env python3
"""
Get FMCSA data through data.gov CKAN API
This API is accessible and provides links to FMCSA datasets
"""

import requests
import json
from typing import Dict, List, Any

def search_fmcsa_datasets():
    """Search for FMCSA datasets on data.gov"""
    
    print("=" * 80)
    print("Searching for FMCSA Insurance & Carrier Data on data.gov")
    print("=" * 80)
    
    # data.gov CKAN API endpoint
    search_url = "https://catalog.data.gov/api/3/action/package_search"
    
    # Search for FMCSA insurance and licensing data
    search_queries = [
        "FMCSA insurance",
        "FMCSA licensing",
        "motor carrier census",
        "SAFER snapshot",
        "DOT carrier"
    ]
    
    all_datasets = []
    
    for query in search_queries:
        print(f"\nSearching for: {query}")
        print("-" * 40)
        
        params = {
            "q": query,
            "rows": 10,
            "fq": "organization:dot-gov"  # Filter for DOT datasets
        }
        
        try:
            response = requests.get(search_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    results = data.get("result", {}).get("results", [])
                    print(f"Found {len(results)} datasets")
                    
                    for dataset in results:
                        title = dataset.get('title', 'No title')
                        dataset_id = dataset.get('id', '')
                        org = dataset.get('organization', {}).get('title', 'N/A')
                        
                        # Look for downloadable resources
                        resources = dataset.get('resources', [])
                        downloadable = []
                        
                        for resource in resources:
                            format_type = resource.get('format', '').upper()
                            if format_type in ['CSV', 'JSON', 'XML', 'API']:
                                downloadable.append({
                                    'format': format_type,
                                    'name': resource.get('name', 'Unnamed'),
                                    'url': resource.get('url', ''),
                                    'description': resource.get('description', '')
                                })
                        
                        if downloadable:
                            dataset_info = {
                                'title': title,
                                'id': dataset_id,
                                'organization': org,
                                'resources': downloadable,
                                'notes': dataset.get('notes', '')[:200]
                            }
                            all_datasets.append(dataset_info)
                            
                            print(f"\n✅ {title}")
                            print(f"   Organization: {org}")
                            for resource in downloadable[:2]:  # Show first 2 resources
                                print(f"   📊 {resource['format']}: {resource['name'][:50]}")
                    
        except Exception as e:
            print(f"Error: {e}")
    
    return all_datasets


def get_dataset_details(dataset_id: str):
    """Get detailed information about a specific dataset"""
    
    url = "https://catalog.data.gov/api/3/action/package_show"
    params = {"id": dataset_id}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data.get("result")
    except Exception as e:
        print(f"Error getting dataset details: {e}")
    
    return None


def find_best_insurance_dataset(datasets: List[Dict]):
    """Find the most relevant dataset for insurance information"""
    
    print("\n" + "=" * 80)
    print("Analyzing Datasets for Insurance Information")
    print("=" * 80)
    
    # Score datasets based on relevance
    scored = []
    
    for dataset in datasets:
        score = 0
        title_lower = dataset['title'].lower()
        notes_lower = dataset.get('notes', '').lower()
        
        # Score based on keywords
        if 'insurance' in title_lower or 'insurance' in notes_lower:
            score += 10
        if 'licensing' in title_lower or 'licensing' in notes_lower:
            score += 8
        if 'safer' in title_lower:
            score += 7
        if 'census' in title_lower:
            score += 5
        if 'snapshot' in title_lower:
            score += 6
        
        # Prefer CSV or JSON formats
        for resource in dataset['resources']:
            if resource['format'] in ['CSV', 'JSON']:
                score += 3
            if resource['format'] == 'API':
                score += 5
        
        scored.append((score, dataset))
    
    # Sort by score
    scored.sort(key=lambda x: x[0], reverse=True)
    
    print("\nTop datasets for insurance/carrier data:")
    for score, dataset in scored[:5]:
        print(f"\nScore: {score} - {dataset['title']}")
        print(f"Resources: {[r['format'] for r in dataset['resources']]}")
        
        # Get more details about the top dataset
        if score == scored[0][0]:  # If this is the highest scoring
            print("\n🏆 BEST MATCH - Getting details...")
            details = get_dataset_details(dataset['id'])
            if details:
                print(f"Dataset ID: {dataset['id']}")
                print(f"Last Modified: {details.get('metadata_modified', 'N/A')}")
                print(f"License: {details.get('license_title', 'N/A')}")
                
                print("\nAvailable Downloads:")
                for resource in dataset['resources']:
                    print(f"\n  Format: {resource['format']}")
                    print(f"  Name: {resource['name']}")
                    print(f"  URL: {resource['url']}")
                    
                    # If it's a direct download link, we could fetch it
                    if resource['format'] == 'CSV' and '.csv' in resource['url'].lower():
                        print(f"  💡 This appears to be a direct CSV download!")
                    elif resource['format'] == 'API':
                        print(f"  💡 This is an API endpoint!")
    
    return scored[0][1] if scored else None


def test_direct_download(url: str, limit: int = 5):
    """Test if we can directly download data from a URL"""
    
    print(f"\nTesting direct access to: {url[:80]}...")
    
    try:
        # Try to get just headers first
        response = requests.head(url, timeout=5, allow_redirects=True)
        print(f"Header Status: {response.status_code}")
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            content_length = response.headers.get('Content-Length', 'Unknown')
            print(f"Content-Type: {content_type}")
            print(f"Content-Length: {content_length}")
            
            # If it's CSV or JSON, try to get a sample
            if 'csv' in content_type.lower() or 'json' in content_type.lower():
                print("\n✅ This resource appears to be directly accessible!")
                return True
        elif response.status_code == 403:
            print("❌ Access forbidden (403)")
        else:
            print(f"❌ Status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return False


def main():
    """Main function to find and access FMCSA data"""
    
    # Search for datasets
    datasets = search_fmcsa_datasets()
    
    if datasets:
        # Find the best dataset for insurance info
        best_dataset = find_best_insurance_dataset(datasets)
        
        if best_dataset:
            print("\n" + "=" * 80)
            print("Testing Access to Best Dataset")
            print("=" * 80)
            
            # Test each resource URL
            for resource in best_dataset['resources'][:3]:  # Test first 3
                test_direct_download(resource['url'])
    
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print("""
✅ data.gov CKAN API is accessible
✅ Found FMCSA datasets with metadata

❌ Direct downloads may still be blocked (403)

Options:
1. Use the dataset URLs in a browser on Windows
2. Contact data.gov for API access to specific datasets  
3. Use commercial APIs that aggregate this data
4. Continue with your existing 2.2M carrier dataset
""")


if __name__ == "__main__":
    main()