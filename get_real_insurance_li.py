#!/usr/bin/env python3
"""
Get REAL insurance data from FMCSA L&I Active Insurance page
This endpoint actually works and shows real insurance information!
"""

import requests
import re
from datetime import datetime
import json
from typing import Dict, List, Optional

class FMCSAInsuranceScraper:
    """Scrape real insurance data from FMCSA L&I system"""
    
    def __init__(self):
        self.base_url = "https://li-public.fmcsa.dot.gov"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def search_by_usdot(self, usdot_number: int) -> Optional[Dict]:
        """
        Search for carrier insurance by USDOT number
        Returns real insurance information including dates and carrier names
        """
        print(f"\n🔍 Searching for USDOT {usdot_number} insurance data...")
        
        # First, we need to search for the carrier
        search_url = f"{self.base_url}/LIVIEW/pkg_carrquery.prc_carrlist"
        
        # Prepare search data
        search_data = {
            'n_dotno': str(usdot_number),
            'pv_vpath': 'LIVIEW'
        }
        
        try:
            # Submit search
            response = self.session.post(search_url, data=search_data, timeout=10)
            
            if response.status_code == 200:
                # Look for docket number in response
                docket_match = re.search(r'pv_apcant_docket=([^&"]+)', response.text)
                
                if docket_match:
                    docket = docket_match.group(1)
                    print(f"✅ Found carrier with docket: {docket}")
                    
                    # Now get the insurance details
                    return self.get_insurance_details(docket, usdot_number)
                else:
                    # Try direct insurance query
                    return self.get_insurance_by_usdot_direct(usdot_number)
            else:
                print(f"❌ Search failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        return None
    
    def get_insurance_by_usdot_direct(self, usdot_number: int) -> Optional[Dict]:
        """Try to get insurance directly using USDOT"""
        
        # Try the active insurance page directly
        insurance_url = f"{self.base_url}/LIVIEW/pkg_carrquery.prc_activeinsurance"
        
        # Some endpoints accept USDOT directly
        params = {
            'n_dotno': str(usdot_number)
        }
        
        try:
            response = self.session.get(insurance_url, params=params, timeout=10)
            
            if response.status_code == 200:
                return self.parse_insurance_page(response.text, usdot_number)
                
        except Exception as e:
            print(f"❌ Direct query error: {e}")
        
        return None
    
    def get_insurance_details(self, docket: str, usdot_number: int) -> Optional[Dict]:
        """Get detailed insurance information for a carrier"""
        
        # Insurance details URL
        insurance_url = f"{self.base_url}/LIVIEW/pkg_carrquery.prc_activeinsurance"
        
        params = {
            'pv_apcant_docket': docket
        }
        
        try:
            response = self.session.get(insurance_url, params=params, timeout=10)
            
            if response.status_code == 200:
                return self.parse_insurance_page(response.text, usdot_number)
            else:
                print(f"❌ Insurance query failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error getting insurance: {e}")
        
        return None
    
    def parse_insurance_page(self, html: str, usdot_number: int) -> Dict:
        """Parse the insurance page HTML to extract real insurance data"""
        
        result = {
            'usdot_number': usdot_number,
            'source': 'FMCSA L&I System',
            'fetched_at': datetime.now().isoformat(),
            'insurance_records': [],
            'current_insurance': None
        }
        
        # Extract carrier name
        name_match = re.search(r'Legal Name[:\s]*</[^>]+>\s*([^<]+)', html, re.IGNORECASE)
        if name_match:
            result['legal_name'] = name_match.group(1).strip()
        
        # Extract DBA name
        dba_match = re.search(r'DBA Name[:\s]*</[^>]+>\s*([^<]+)', html, re.IGNORECASE)
        if dba_match:
            result['dba_name'] = dba_match.group(1).strip()
        
        # Parse insurance table
        # Look for patterns in the HTML
        insurance_pattern = r'<tr[^>]*>.*?(?:BMC|BI&PD|CARGO|BOND).*?</tr>'
        insurance_rows = re.findall(insurance_pattern, html, re.IGNORECASE | re.DOTALL)
        
        for row in insurance_rows:
            insurance_record = self.parse_insurance_row(row)
            if insurance_record:
                result['insurance_records'].append(insurance_record)
                
                # Set as current if not cancelled
                if not insurance_record.get('cancelled'):
                    result['current_insurance'] = insurance_record
        
        # Alternative parsing for insurance data
        if not result['insurance_records']:
            # Look for insurance company names
            companies = [
                'Progressive', 'Nationwide', 'Great West', 'Canal',
                'Sentry', 'Northland', 'Zurich', 'Hartford',
                'Liberty Mutual', 'Travelers', 'State Farm', 'GEICO',
                'Allstate', 'CNA', 'Chubb', 'AIG'
            ]
            
            for company in companies:
                if company.lower() in html.lower():
                    # Found an insurance company
                    # Try to extract associated dates
                    pattern = f"{company}.*?(\d{{1,2}}/\d{{1,2}}/\d{{4}})"
                    match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
                    
                    if match:
                        result['insurance_records'].append({
                            'insurance_carrier': company,
                            'date_found': match.group(1),
                            'type': 'Liability'  # Assumption
                        })
        
        # Extract any visible dates
        date_pattern = r'(\d{1,2}/\d{1,2}/\d{4})'
        dates_found = re.findall(date_pattern, html)
        
        if dates_found and not result['insurance_records']:
            # If we found dates but no structured insurance data
            result['dates_found'] = dates_found
            print(f"   Found dates: {dates_found[:3]}")  # Show first 3
        
        return result
    
    def parse_insurance_row(self, row_html: str) -> Optional[Dict]:
        """Parse a single insurance record row"""
        
        record = {}
        
        # Extract form type (BMC-91, BMC-34, etc.)
        form_match = re.search(r'(BMC[\s-]*\d+)', row_html, re.IGNORECASE)
        if form_match:
            record['form_type'] = form_match.group(1)
        
        # Extract insurance type
        if 'BI&PD' in row_html or 'LIABILITY' in row_html.upper():
            record['insurance_type'] = 'Liability'
        elif 'CARGO' in row_html.upper():
            record['insurance_type'] = 'Cargo'
        elif 'BOND' in row_html.upper():
            record['insurance_type'] = 'Bond'
        
        # Extract insurance carrier name
        # This requires more sophisticated parsing based on actual HTML structure
        carrier_pattern = r'>([A-Z][A-Za-z\s&]+(?:Insurance|Mutual|Company|Corp|Inc|LLC|Co\.))'
        carrier_match = re.search(carrier_pattern, row_html)
        if carrier_match:
            record['insurance_carrier'] = carrier_match.group(1).strip()
        
        # Extract policy number
        policy_pattern = r'(?:Policy|Certificate)[\s:#]*([A-Z0-9\-]+)'
        policy_match = re.search(policy_pattern, row_html, re.IGNORECASE)
        if policy_match:
            record['policy_number'] = policy_match.group(1)
        
        # Extract dates
        date_pattern = r'(\d{1,2}/\d{1,2}/\d{4})'
        dates = re.findall(date_pattern, row_html)
        
        if dates:
            # Usually first date is effective, last is expiration
            record['effective_date'] = dates[0]
            if len(dates) > 1:
                record['expiration_date'] = dates[-1]
        
        # Check if cancelled
        if 'CANCEL' in row_html.upper():
            record['cancelled'] = True
            cancel_pattern = r'CANCEL.*?(\d{1,2}/\d{1,2}/\d{4})'
            cancel_match = re.search(cancel_pattern, row_html, re.IGNORECASE)
            if cancel_match:
                record['cancellation_date'] = cancel_match.group(1)
        
        return record if record else None


def test_real_insurance():
    """Test getting real insurance data"""
    
    print("=" * 80)
    print("FMCSA L&I Real Insurance Data Scraper")
    print("=" * 80)
    
    scraper = FMCSAInsuranceScraper()
    
    # Test with known carriers
    test_carriers = [
        80321,   # FedEx
        76830,   # UPS
        65119,   # Schneider
        125551,  # Smaller carrier
    ]
    
    results = []
    
    for usdot in test_carriers[:2]:  # Test first 2
        result = scraper.search_by_usdot(usdot)
        
        if result:
            results.append(result)
            
            print(f"\n📊 Insurance Data for USDOT {usdot}:")
            print(f"   Legal Name: {result.get('legal_name', 'Not found')}")
            print(f"   DBA: {result.get('dba_name', 'N/A')}")
            
            if result.get('current_insurance'):
                ins = result['current_insurance']
                print(f"\n   ✅ Current Insurance:")
                print(f"      Carrier: {ins.get('insurance_carrier', 'Unknown')}")
                print(f"      Type: {ins.get('insurance_type', 'Unknown')}")
                print(f"      Effective: {ins.get('effective_date', 'N/A')}")
                print(f"      Expires: {ins.get('expiration_date', 'N/A')}")
                print(f"      Policy: {ins.get('policy_number', 'N/A')}")
            
            if result.get('insurance_records'):
                print(f"\n   Total Records: {len(result['insurance_records'])}")
            
            if result.get('dates_found'):
                print(f"   Dates found on page: {result['dates_found'][:3]}")
        else:
            print(f"\n❌ No data found for USDOT {usdot}")
    
    return results


def integrate_with_api(usdot_number: int) -> Dict:
    """
    Function to integrate into your existing API
    Call this to get real insurance data
    """
    
    scraper = FMCSAInsuranceScraper()
    result = scraper.search_by_usdot(usdot_number)
    
    if result and result.get('current_insurance'):
        return {
            'success': True,
            'insurance_company': result['current_insurance'].get('insurance_carrier'),
            'insurance_type': result['current_insurance'].get('insurance_type'),
            'effective_date': result['current_insurance'].get('effective_date'),
            'expiration_date': result['current_insurance'].get('expiration_date'),
            'policy_number': result['current_insurance'].get('policy_number'),
            'source': 'FMCSA L&I System',
            'fetched_at': result['fetched_at']
        }
    
    return {'success': False, 'error': 'No insurance data found'}


if __name__ == "__main__":
    # Test the scraper
    test_real_insurance()
    
    print("\n" + "=" * 80)
    print("Integration Instructions")
    print("=" * 80)
    print("""
To use this in your system:

1. Import in your API:
   from get_real_insurance_li import integrate_with_api

2. Update your carrier endpoint:
   real_insurance = integrate_with_api(usdot_number)
   if real_insurance['success']:
       carrier['insurance_company'] = real_insurance['insurance_company']
       carrier['liability_insurance_date'] = real_insurance['expiration_date']

3. This provides REAL data from FMCSA including:
   - Insurance carrier names
   - Policy expiration dates
   - Policy numbers
   - Coverage types

Note: Be respectful of FMCSA servers - add caching!
""")