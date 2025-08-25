#!/usr/bin/env python3
"""
Get real FMCSA data from SAFER system using their API endpoint
No web scraping needed - uses their direct data endpoint
"""

import requests
import json
import re
from typing import Dict, Any, Optional
from datetime import datetime

class SAFERDataFetcher:
    """Fetch real carrier data from FMCSA SAFER system"""
    
    def __init__(self):
        # SAFER uses a query endpoint that returns formatted data
        self.base_url = "https://safer.fmcsa.dot.gov"
        self.session = requests.Session()
    
    def get_carrier_by_usdot(self, usdot_number: int) -> Dict[str, Any]:
        """
        Get carrier information from SAFER using USDOT number
        """
        # SAFER query endpoint
        url = f"{self.base_url}/query.asp"
        
        params = {
            'searchtype': 'ANY',
            'query_type': 'queryCarrierSnapshot',
            'query_param': 'USDOT',
            'query_string': str(usdot_number)
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                # Parse the response
                return self._parse_safer_response(response.text, usdot_number)
            else:
                print(f"Error: Status {response.status_code}")
        except Exception as e:
            print(f"Error fetching SAFER data: {e}")
        
        return {}
    
    def _parse_safer_response(self, html_content: str, usdot_number: int) -> Dict[str, Any]:
        """
        Parse SAFER HTML response using regex
        Extract key carrier information
        """
        data = {
            'usdot_number': usdot_number,
            'source': 'FMCSA SAFER System',
            'fetched_at': datetime.now().isoformat()
        }
        
        # Use regex to extract data from HTML
        patterns = {
            'legal_name': r'Legal Name[:\s]*</[^>]+>\s*<[^>]+>([^<]+)',
            'dba_name': r'DBA Name[:\s]*</[^>]+>\s*<[^>]+>([^<]+)',
            'physical_address': r'Physical Address[:\s]*</[^>]+>\s*<[^>]+>([^<]+)',
            'phone': r'Phone[:\s]*</[^>]+>\s*<[^>]+>([^<]+)',
            'power_units': r'Power Units[:\s]*</[^>]+>\s*<[^>]+>([^<]+)',
            'drivers': r'Drivers[:\s]*</[^>]+>\s*<[^>]+>([^<]+)',
            'mcs_150_date': r'MCS-150 Form Date[:\s]*</[^>]+>\s*<[^>]+>([^<]+)',
            'operating_status': r'Operating Status[:\s]*</[^>]+>\s*<[^>]+>([^<]+)',
            'out_of_service_date': r'Out of Service Date[:\s]*</[^>]+>\s*<[^>]+>([^<]+)',
        }
        
        for field, pattern in patterns.items():
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                # Clean up HTML entities
                value = value.replace('&amp;', '&').replace('&nbsp;', ' ')
                if value and value != 'None':
                    data[field] = value
        
        # Check for insurance indicators (SAFER shows if carrier has insurance on file)
        if 'Carrier has cargo and liability insurance on file' in html_content:
            data['insurance_on_file'] = True
        elif 'does not have' in html_content.lower() and 'insurance' in html_content.lower():
            data['insurance_on_file'] = False
        
        # Extract safety rating if present
        rating_match = re.search(r'Safety Rating[:\s]*</[^>]+>\s*<[^>]+>([^<]+)', html_content, re.IGNORECASE)
        if rating_match:
            rating = rating_match.group(1).strip()
            if rating and rating != 'None':
                data['safety_rating'] = rating
        
        return data


def integrate_with_api(usdot_number: int) -> Dict[str, Any]:
    """
    Function to integrate with your existing API
    Returns real data when available, with fallback info
    """
    fetcher = SAFERDataFetcher()
    safer_data = fetcher.get_carrier_by_usdot(usdot_number)
    
    result = {
        'usdot_number': usdot_number,
        'real_data_available': bool(safer_data.get('legal_name')),
        'safer_data': safer_data
    }
    
    # Add insurance status from SAFER
    if safer_data.get('insurance_on_file') is not None:
        result['insurance_status'] = {
            'on_file': safer_data['insurance_on_file'],
            'source': 'FMCSA SAFER',
            'note': 'Detailed insurance carrier and expiration dates require L&I system access'
        }
    
    # For detailed insurance data, you would need:
    # 1. FMCSA WebKey (currently showing 403 error)
    # 2. Web scraping of L&I system (requires more complex parsing)
    # 3. Third-party API subscription
    
    result['insurance_details'] = {
        'available': False,
        'reason': 'Detailed insurance data requires FMCSA API key or L&I system access',
        'alternatives': [
            'Get FMCSA WebKey from https://mobile.fmcsa.dot.gov/QCDevsite/',
            'Use commercial API like CarrierDetails.com',
            'Implement L&I web scraping (complex HTML parsing required)'
        ]
    }
    
    return result


def test_safer():
    """Test SAFER data fetching"""
    
    print("=" * 80)
    print("SAFER System Data Test")
    print("=" * 80)
    
    # Test with known carriers
    test_carriers = {
        80321: "FedEx",
        76830: "UPS",
        65119: "Schneider",
        62978: "J.B. Hunt",
        125604: "Small Carrier Example"
    }
    
    fetcher = SAFERDataFetcher()
    
    for usdot, name in list(test_carriers.items())[:2]:  # Test first 2
        print(f"\n{name} (USDOT: {usdot})")
        print("-" * 40)
        
        data = fetcher.get_carrier_by_usdot(usdot)
        
        if data.get('legal_name'):
            print(f"✓ Found in SAFER")
            for key, value in data.items():
                if key not in ['source', 'fetched_at']:
                    print(f"  {key}: {value}")
        else:
            print("✗ Not found or error occurred")
        
        # Show what real integration would look like
        print("\nIntegration Result:")
        integrated = integrate_with_api(usdot)
        print(f"  Real data available: {integrated['real_data_available']}")
        if integrated.get('insurance_status'):
            print(f"  Insurance on file: {integrated['insurance_status']['on_file']}")
    
    print("\n" + "=" * 80)
    print("Note: This shows SAFER public data. For insurance carrier names")
    print("and expiration dates, you need FMCSA API access or L&I scraping.")
    

if __name__ == "__main__":
    test_safer()