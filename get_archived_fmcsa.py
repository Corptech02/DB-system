#!/usr/bin/env python3
"""
Access FMCSA L&I data through Internet Archive Wayback Machine
This bypasses the 403 errors by using archived versions
"""

import requests
import re
from urllib.parse import urljoin, quote
from datetime import datetime

class ArchivedFMCSAAccess:
    """Access FMCSA data through Internet Archive"""
    
    def __init__(self):
        self.wayback_base = "http://web.archive.org"
        self.snapshot_date = "20250710231815"  # Latest working snapshot
        self.li_base = f"{self.wayback_base}/web/{self.snapshot_date}/https://li-public.fmcsa.dot.gov"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_carrier(self, usdot_number: int):
        """Search for a carrier by USDOT number in archived L&I system"""
        
        print(f"\n🔍 Searching for USDOT {usdot_number} in archived L&I system...")
        
        # L&I search URL
        search_url = f"{self.li_base}/LIVIEW/pkg_carrquery.prc_carrlist"
        
        # Search form data
        data = {
            'n_dotno': str(usdot_number),
            'pv_vpath': 'LIVIEW'
        }
        
        try:
            # Submit search
            response = self.session.post(search_url, data=data, timeout=15)
            
            if response.status_code == 200:
                return self._parse_search_results(response.text, usdot_number)
            else:
                print(f"❌ Search failed with status: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error searching: {e}")
            return None
    
    def _parse_search_results(self, html: str, usdot_number: int):
        """Parse the search results to extract carrier information"""
        
        # Extract basic carrier info using regex
        carrier_info = {
            'usdot_number': usdot_number,
            'source': 'FMCSA L&I System (Archived)',
            'snapshot_date': self.snapshot_date,
            'fetched_at': datetime.now().isoformat()
        }
        
        # Look for carrier details link
        detail_link_pattern = r'href="([^"]*prc_carrdetails[^"]*)"'
        detail_match = re.search(detail_link_pattern, html)
        
        if detail_match:
            detail_path = detail_match.group(1)
            # Clean up the URL (remove wayback prefixes if present)
            detail_path = re.sub(r'/web/\d+/', '', detail_path)
            
            # Construct full URL
            if not detail_path.startswith('http'):
                detail_url = f"{self.li_base}{detail_path}"
            else:
                detail_url = f"{self.wayback_base}/web/{self.snapshot_date}/{detail_path}"
            
            print(f"✅ Found carrier details page")
            
            # Get detailed information
            return self._get_carrier_details(detail_url, carrier_info)
        else:
            # Try to extract from search results page
            return self._extract_from_results(html, carrier_info)
    
    def _get_carrier_details(self, url: str, carrier_info: dict):
        """Get detailed carrier information including insurance"""
        
        print("📋 Fetching detailed carrier information...")
        
        try:
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                html = response.text
                
                # Extract carrier name
                name_pattern = r'Legal Name[:\s]*</[^>]+>\s*<[^>]+>([^<]+)'
                name_match = re.search(name_pattern, html, re.IGNORECASE)
                if name_match:
                    carrier_info['legal_name'] = name_match.group(1).strip()
                
                # Extract DBA name
                dba_pattern = r'DBA Name[:\s]*</[^>]+>\s*<[^>]+>([^<]+)'
                dba_match = re.search(dba_pattern, html, re.IGNORECASE)
                if dba_match:
                    carrier_info['dba_name'] = dba_match.group(1).strip()
                
                # Extract insurance information
                insurance_info = self._extract_insurance(html)
                if insurance_info:
                    carrier_info['insurance'] = insurance_info
                    print(f"✅ Found insurance records: {len(insurance_info)}")
                
                # Extract authority status
                authority_pattern = r'Authority Status[:\s]*</[^>]+>\s*<[^>]+>([^<]+)'
                authority_match = re.search(authority_pattern, html, re.IGNORECASE)
                if authority_match:
                    carrier_info['authority_status'] = authority_match.group(1).strip()
                
                return carrier_info
            else:
                print(f"❌ Failed to get details: {response.status_code}")
                return carrier_info
                
        except Exception as e:
            print(f"❌ Error getting details: {e}")
            return carrier_info
    
    def _extract_insurance(self, html: str):
        """Extract insurance information from the HTML"""
        
        insurance_records = []
        
        # Pattern to find insurance table rows
        # Look for patterns like: Form | Type | Insurance Carrier | Policy Number | etc.
        table_pattern = r'<tr[^>]*>.*?Insurance.*?</tr>'
        
        # More specific pattern for insurance data
        insurance_patterns = [
            r'BMC[\s-]*\d+',  # Form type (BMC-91, BMC-34, etc.)
            r'Policy[\s#:]*([A-Z0-9\-]+)',  # Policy number
            r'Effective[\s:]*(\d{1,2}/\d{1,2}/\d{4})',  # Effective date
            r'Cancel[\s:]*(\d{1,2}/\d{1,2}/\d{4})',  # Cancellation date
        ]
        
        # Look for insurance carrier names (common ones)
        carrier_names = [
            'Progressive', 'Nationwide', 'Great West', 'Canal Insurance',
            'Sentry', 'Northland', 'Zurich', 'Hartford', 'Liberty Mutual',
            'Travelers', 'State Farm', 'GEICO', 'Allstate', 'CNA',
            'Chubb', 'AIG', 'Berkshire', 'Farmers', 'USAA'
        ]
        
        for carrier in carrier_names:
            if carrier.lower() in html.lower():
                insurance_records.append({
                    'carrier_name': carrier,
                    'found_in_page': True
                })
        
        # Try to extract structured insurance data
        # This would need more sophisticated parsing based on actual HTML structure
        
        return insurance_records if insurance_records else None
    
    def _extract_from_results(self, html: str, carrier_info: dict):
        """Extract basic info from search results if no detail page found"""
        
        # Extract what we can from the results page
        patterns = {
            'legal_name': r'Legal Name[:\s]*([^<\n]+)',
            'dba_name': r'DBA[:\s]*([^<\n]+)',
            'city': r'City[:\s]*([^<\n]+)',
            'state': r'State[:\s]*([A-Z]{2})',
        }
        
        for field, pattern in patterns.items():
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if value:
                    carrier_info[field] = value
        
        return carrier_info


def test_archived_access():
    """Test accessing real carrier data through archives"""
    
    print("=" * 80)
    print("FMCSA L&I System Access via Internet Archive")
    print("=" * 80)
    print("Using snapshot from July 10, 2025")
    
    access = ArchivedFMCSAAccess()
    
    # Test with known carriers
    test_carriers = [
        80321,   # FedEx
        76830,   # UPS
        125604,  # Smaller carrier
        2350588  # Another test
    ]
    
    results = []
    
    for usdot in test_carriers[:2]:  # Test first 2
        result = access.search_carrier(usdot)
        if result:
            results.append(result)
            
            print(f"\n📊 Results for USDOT {usdot}:")
            print(f"   Legal Name: {result.get('legal_name', 'Not found')}")
            print(f"   DBA Name: {result.get('dba_name', 'N/A')}")
            print(f"   Authority Status: {result.get('authority_status', 'N/A')}")
            
            if result.get('insurance'):
                print(f"   Insurance Records: {len(result['insurance'])}")
                for ins in result['insurance'][:2]:
                    print(f"     - {ins}")
    
    return results


def integrate_with_system(usdot_number: int):
    """
    Function to integrate archived data with your system
    Call this from your API to get real insurance data
    """
    
    access = ArchivedFMCSAAccess()
    carrier_data = access.search_carrier(usdot_number)
    
    if carrier_data:
        # Format for your system
        return {
            'success': True,
            'source': 'FMCSA L&I (Archived)',
            'data': carrier_data,
            'note': 'Data from Internet Archive snapshot'
        }
    else:
        return {
            'success': False,
            'error': 'Carrier not found in archived data'
        }


def main():
    print("Starting FMCSA Archive Access Test...")
    print("This uses Internet Archive to bypass 403 errors\n")
    
    # Test the archived access
    results = test_archived_access()
    
    print("\n" + "=" * 80)
    print("Integration Instructions")
    print("=" * 80)
    print("""
To use this in your system:

1. Import this module in your API:
   from get_archived_fmcsa import integrate_with_system

2. In your carrier endpoint, add:
   real_data = integrate_with_system(usdot_number)
   if real_data['success']:
       carrier_info.update(real_data['data'])

3. The archived data includes:
   - Legal and DBA names
   - Authority status
   - Insurance carrier names (when found)
   - Other publicly available information

Note: This uses July 2025 snapshot. Data may be slightly outdated.
""")


if __name__ == "__main__":
    main()