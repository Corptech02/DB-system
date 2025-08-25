#!/usr/bin/env python3
"""
Access FMCSA L&I Insurance data using the correct workflow
The L&I system requires specific parameters and proper session handling
"""

import requests
import re
from datetime import datetime
import json
from typing import Dict, Optional, List
from urllib.parse import urlencode

class LIInsuranceFetcher:
    """Fetch insurance data from FMCSA L&I system"""
    
    def __init__(self):
        self.base_url = "https://li-public.fmcsa.dot.gov"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def get_carrier_insurance(self, usdot_number: int) -> Optional[Dict]:
        """
        Get insurance information for a carrier by USDOT number
        Uses the direct insurance query endpoint
        """
        
        print(f"\n🔍 Fetching insurance for USDOT {usdot_number}...")
        
        # The active insurance endpoint format
        # Based on the URL you found: https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_activeinsurance
        
        # Try different parameter combinations
        attempts = [
            # Method 1: Direct USDOT parameter
            {
                'url': f"{self.base_url}/LIVIEW/pkg_carrquery.prc_activeinsurance",
                'params': {'n_dotno': str(usdot_number)}
            },
            # Method 2: With docket number format
            {
                'url': f"{self.base_url}/LIVIEW/pkg_carrquery.prc_activeinsurance",
                'params': {'pv_apcant_docket': f'MC-{usdot_number}'}
            },
            # Method 3: Try without parameters (might show a form)
            {
                'url': f"{self.base_url}/LIVIEW/pkg_carrquery.prc_activeinsurance",
                'params': {}
            }
        ]
        
        for i, attempt in enumerate(attempts, 1):
            print(f"\nAttempt {i}: {attempt['params']}")
            
            try:
                response = self.session.get(
                    attempt['url'],
                    params=attempt['params'],
                    timeout=15,
                    allow_redirects=True
                )
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    # Parse the response
                    result = self._parse_insurance_page(response.text, usdot_number)
                    if result and (result.get('carrier_found') or result.get('insurance_records')):
                        return result
                    
            except Exception as e:
                print(f"Error: {e}")
        
        # If direct access doesn't work, try the search workflow
        return self._search_and_get_insurance(usdot_number)
    
    def _search_and_get_insurance(self, usdot_number: int) -> Optional[Dict]:
        """
        Use the search workflow: search first, then navigate to insurance
        """
        
        print(f"\n📋 Using search workflow for USDOT {usdot_number}...")
        
        # Step 1: Search for the carrier
        search_url = f"{self.base_url}/LIVIEW/pkg_carrquery.prc_carrlist"
        
        search_data = {
            'n_dotno': str(usdot_number),
            'pv_vpath': 'LIVIEW'
        }
        
        try:
            # Submit search
            print("Submitting carrier search...")
            response = self.session.post(search_url, data=search_data, timeout=15)
            
            if response.status_code != 200:
                print(f"Search failed: {response.status_code}")
                return None
            
            # Parse search results
            html = response.text
            
            # Look for the carrier details link
            # Pattern: href="/LIVIEW/pkg_carrquery.prc_carrdetails?pv_apcant_docket=..."
            detail_pattern = r'href="([^"]*pkg_carrquery\.prc_carrdetails[^"]*)"'
            detail_match = re.search(detail_pattern, html, re.IGNORECASE)
            
            if detail_match:
                detail_path = detail_match.group(1)
                print(f"Found carrier details link: {detail_path}")
                
                # Get the carrier details page
                if not detail_path.startswith('http'):
                    detail_url = f"{self.base_url}{detail_path}"
                else:
                    detail_url = detail_path
                
                detail_response = self.session.get(detail_url, timeout=15)
                
                if detail_response.status_code == 200:
                    # Look for insurance link on the details page
                    insurance_pattern = r'href="([^"]*prc_activeinsurance[^"]*)"'
                    insurance_match = re.search(insurance_pattern, detail_response.text, re.IGNORECASE)
                    
                    if insurance_match:
                        insurance_path = insurance_match.group(1)
                        print(f"Found insurance link: {insurance_path}")
                        
                        if not insurance_path.startswith('http'):
                            insurance_url = f"{self.base_url}{insurance_path}"
                        else:
                            insurance_url = insurance_path
                        
                        # Get the insurance page
                        insurance_response = self.session.get(insurance_url, timeout=15)
                        
                        if insurance_response.status_code == 200:
                            return self._parse_insurance_page(insurance_response.text, usdot_number)
            
            # If we can't find links, try to parse the search results directly
            return self._parse_insurance_page(html, usdot_number)
            
        except Exception as e:
            print(f"Search workflow error: {e}")
            return None
    
    def _parse_insurance_page(self, html: str, usdot_number: int) -> Dict:
        """
        Parse the insurance page HTML to extract insurance information
        """
        
        result = {
            'usdot_number': usdot_number,
            'source': 'FMCSA L&I System',
            'fetched_at': datetime.now().isoformat(),
            'carrier_found': False,
            'insurance_records': []
        }
        
        # Check if this is an actual carrier page
        if str(usdot_number) in html:
            result['carrier_found'] = True
            print(f"✅ USDOT {usdot_number} found in page")
        
        # Extract carrier name
        name_patterns = [
            r'Legal Name[:\s]*</[^>]+>\s*([^<]+)',
            r'Carrier Name[:\s]*</[^>]+>\s*([^<]+)',
            r'Name[:\s]*</[^>]+>\s*<[^>]+>([^<]+)'
        ]
        
        for pattern in name_patterns:
            name_match = re.search(pattern, html, re.IGNORECASE)
            if name_match:
                result['carrier_name'] = name_match.group(1).strip()
                print(f"Found carrier name: {result['carrier_name']}")
                break
        
        # Look for insurance information
        # Common insurance company names to search for
        insurance_companies = [
            'Progressive', 'Nationwide', 'Great West', 'Canal',
            'Sentry', 'Northland', 'Zurich', 'Hartford',
            'Liberty Mutual', 'Travelers', 'State Farm', 'GEICO',
            'Allstate', 'CNA', 'Chubb', 'AIG', 'Berkshire',
            'Farmers', 'USAA', 'Tokio Marine', 'Hanover'
        ]
        
        for company in insurance_companies:
            if company.lower() in html.lower():
                # Found an insurance company, try to extract details
                # Look for dates near the company name
                pattern = f"{company}.*?(\\d{{1,2}}/\\d{{1,2}}/\\d{{4}})"
                match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
                
                if match:
                    record = {
                        'insurance_carrier': company,
                        'date_found': match.group(1),
                        'type': 'Liability'  # Default assumption
                    }
                    result['insurance_records'].append(record)
                    print(f"Found insurance: {company} - {match.group(1)}")
        
        # Look for BMC forms (BMC-91, BMC-34, etc.)
        bmc_pattern = r'BMC[\s-]*(\d+)'
        bmc_matches = re.findall(bmc_pattern, html, re.IGNORECASE)
        for bmc_num in bmc_matches:
            result['bmc_forms'] = result.get('bmc_forms', [])
            result['bmc_forms'].append(f'BMC-{bmc_num}')
        
        # Extract dates (insurance effective/expiration dates)
        date_pattern = r'(\d{1,2}/\d{1,2}/\d{4})'
        dates = re.findall(date_pattern, html)
        
        if dates:
            result['dates_found'] = dates[:10]  # First 10 dates
            print(f"Found {len(dates)} dates in page")
        
        # Look for specific insurance table structure
        # Try to find insurance in table rows
        table_rows = re.findall(r'<tr[^>]*>(.*?)</tr>', html, re.IGNORECASE | re.DOTALL)
        
        for row in table_rows:
            # Check if this row contains insurance information
            if any(term in row.lower() for term in ['insurance', 'liability', 'cargo', 'policy']):
                # Try to extract structured data from the row
                cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.IGNORECASE | re.DOTALL)
                if len(cells) >= 2:
                    # Clean up cell content
                    clean_cells = [re.sub(r'<[^>]+>', '', cell).strip() for cell in cells]
                    
                    # Look for insurance company names in cells
                    for cell in clean_cells:
                        for company in insurance_companies:
                            if company.lower() in cell.lower():
                                # Found insurance company in table
                                record = {
                                    'insurance_carrier': company,
                                    'row_data': clean_cells,
                                    'source': 'table'
                                }
                                
                                # Try to find associated dates
                                for other_cell in clean_cells:
                                    date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', other_cell)
                                    if date_match:
                                        record['date'] = date_match.group(1)
                                        break
                                
                                if record not in result['insurance_records']:
                                    result['insurance_records'].append(record)
        
        return result


def test_li_fetcher():
    """Test the L&I insurance fetcher with known carriers"""
    
    print("=" * 80)
    print("FMCSA L&I Insurance Data Fetcher")
    print("=" * 80)
    
    fetcher = LIInsuranceFetcher()
    
    # Test carriers
    test_carriers = [
        (80321, "FedEx"),
        (76830, "UPS"),
        (125604, "Small Carrier"),
        (660531, "Swift Transportation")
    ]
    
    results = []
    
    for usdot, name in test_carriers[:2]:  # Test first 2
        print(f"\n{'=' * 40}")
        print(f"Testing: {name} (USDOT: {usdot})")
        print('=' * 40)
        
        result = fetcher.get_carrier_insurance(usdot)
        
        if result:
            results.append(result)
            
            print(f"\n📊 Results for {name}:")
            print(f"   Carrier Found: {result.get('carrier_found', False)}")
            print(f"   Carrier Name: {result.get('carrier_name', 'Not found')}")
            
            if result.get('insurance_records'):
                print(f"   Insurance Records: {len(result['insurance_records'])}")
                for record in result['insurance_records'][:2]:
                    print(f"     - {record}")
            
            if result.get('dates_found'):
                print(f"   Dates Found: {result['dates_found'][:3]}")
            
            if result.get('bmc_forms'):
                print(f"   BMC Forms: {result['bmc_forms']}")
        else:
            print(f"   ❌ No data retrieved")
    
    return results


def integrate_with_api(usdot_number: int) -> Dict:
    """
    Integration function for your API
    Returns real insurance data from L&I system
    """
    
    fetcher = LIInsuranceFetcher()
    result = fetcher.get_carrier_insurance(usdot_number)
    
    if result and result.get('insurance_records'):
        # Format for API response
        insurance = result['insurance_records'][0] if result['insurance_records'] else {}
        
        return {
            'success': True,
            'carrier_name': result.get('carrier_name', ''),
            'insurance_company': insurance.get('insurance_carrier', ''),
            'insurance_date': insurance.get('date', insurance.get('date_found', '')),
            'bmc_forms': result.get('bmc_forms', []),
            'source': 'FMCSA L&I System',
            'fetched_at': result['fetched_at']
        }
    
    return {
        'success': False,
        'error': 'Unable to retrieve insurance data',
        'usdot': usdot_number
    }


if __name__ == "__main__":
    # Test the fetcher
    results = test_li_fetcher()
    
    print("\n" + "=" * 80)
    print("Integration Instructions")
    print("=" * 80)
    print("""
To integrate this into your system:

1. Import in your API:
   from get_li_insurance_fixed import integrate_with_api

2. In your carrier endpoint, replace simulated insurance with:
   real_insurance = integrate_with_api(usdot_number)
   if real_insurance['success']:
       carrier['insurance_company'] = real_insurance['insurance_company']
       carrier['liability_insurance_date'] = real_insurance['insurance_date']

3. This fetches REAL data from the L&I system you found.

Note: Add caching to avoid hitting the server too frequently!
""")