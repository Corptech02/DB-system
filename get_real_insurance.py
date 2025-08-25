#!/usr/bin/env python3
"""
Get real FMCSA insurance data from public sources
Uses SAFER Company Snapshot and L&I public search
"""

import requests
from bs4 import BeautifulSoup
import re
import json
from typing import Dict, Any, Optional
from datetime import datetime

class FMCSAPublicDataScraper:
    """Scrape real insurance data from FMCSA public websites"""
    
    def __init__(self):
        self.safer_base_url = "https://safer.fmcsa.dot.gov"
        self.li_base_url = "https://li-public.fmcsa.dot.gov"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_safer_snapshot(self, usdot_number: int) -> Dict[str, Any]:
        """
        Get company snapshot from SAFER system
        This includes basic insurance status but not detailed info
        """
        url = f"{self.safer_base_url}/query.asp"
        
        # First, get the search page to get any required tokens
        search_page = self.session.get(f"{self.safer_base_url}/CompanySnapshot.aspx")
        
        # Submit search
        params = {
            'searchtype': 'ANY',
            'query_type': 'queryCarrierSnapshot',
            'query_param': 'USDOT',
            'query_string': str(usdot_number)
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return self._parse_safer_snapshot(response.text)
        except Exception as e:
            print(f"Error fetching SAFER snapshot: {e}")
        
        return {}
    
    def get_li_insurance_data(self, usdot_number: int) -> Dict[str, Any]:
        """
        Get detailed insurance data from L&I public system
        This has actual insurance carrier names and dates
        """
        # Search URL
        search_url = f"{self.li_base_url}/LIVIEW/pkg_carrquery.prc_carrlist"
        
        # Search parameters
        data = {
            'n_dotno': str(usdot_number),
            'pv_vpath': 'LIVIEW'
        }
        
        try:
            # Perform search
            response = self.session.post(search_url, data=data, timeout=10)
            
            if response.status_code == 200:
                # Extract carrier details link
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Look for the carrier link in results
                carrier_link = None
                for link in soup.find_all('a'):
                    if 'prc_carrdetails' in str(link.get('href', '')):
                        carrier_link = link.get('href')
                        break
                
                if carrier_link:
                    # Get detailed carrier page
                    if not carrier_link.startswith('http'):
                        carrier_link = f"{self.li_base_url}{carrier_link}"
                    
                    detail_response = self.session.get(carrier_link, timeout=10)
                    if detail_response.status_code == 200:
                        return self._parse_li_insurance(detail_response.text)
        
        except Exception as e:
            print(f"Error fetching L&I data: {e}")
        
        return {}
    
    def _parse_safer_snapshot(self, html: str) -> Dict[str, Any]:
        """Parse SAFER company snapshot HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        data = {}
        
        # Extract basic info
        for row in soup.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) >= 2:
                label = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                
                if 'Legal Name' in label:
                    data['legal_name'] = value
                elif 'DBA Name' in label:
                    data['dba_name'] = value
                elif 'DOT' in label and 'Number' in label:
                    data['usdot_number'] = value
                elif 'Power Units' in label:
                    data['power_units'] = value
                elif 'Drivers' in label:
                    data['drivers'] = value
                elif 'MCS-150 Form Date' in label:
                    data['mcs150_date'] = value
        
        return data
    
    def _parse_li_insurance(self, html: str) -> Dict[str, Any]:
        """Parse L&I insurance details HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        data = {
            'insurance_records': [],
            'current_insurance': {}
        }
        
        # Look for insurance tables
        tables = soup.find_all('table')
        
        for table in tables:
            # Check if this is an insurance table
            headers = [th.get_text(strip=True) for th in table.find_all('th')]
            
            if any('Insurance' in h or 'Policy' in h for h in headers):
                rows = table.find_all('tr')[1:]  # Skip header row
                
                for row in rows:
                    cells = row.find_all('td')
                    if cells:
                        record = {}
                        
                        # Map cells to fields based on position
                        if len(cells) > 0:
                            record['form_type'] = cells[0].get_text(strip=True)
                        if len(cells) > 1:
                            record['type'] = cells[1].get_text(strip=True)
                        if len(cells) > 2:
                            record['insurance_carrier'] = cells[2].get_text(strip=True)
                        if len(cells) > 3:
                            record['policy_number'] = cells[3].get_text(strip=True)
                        if len(cells) > 4:
                            record['posted_date'] = cells[4].get_text(strip=True)
                        if len(cells) > 5:
                            record['coverage_from'] = cells[5].get_text(strip=True)
                        if len(cells) > 6:
                            record['coverage_to'] = cells[6].get_text(strip=True)
                        if len(cells) > 7:
                            record['effective_date'] = cells[7].get_text(strip=True)
                        if len(cells) > 8:
                            record['cancellation_date'] = cells[8].get_text(strip=True)
                        
                        # Add to records
                        if record.get('insurance_carrier'):
                            data['insurance_records'].append(record)
                            
                            # Set as current if no cancellation date
                            if not record.get('cancellation_date'):
                                data['current_insurance'] = record
        
        return data
    
    def get_real_insurance_data(self, usdot_number: int) -> Dict[str, Any]:
        """
        Get all available real insurance data for a carrier
        Combines SAFER and L&I data
        """
        print(f"Fetching real insurance data for USDOT {usdot_number}...")
        
        result = {
            'usdot_number': usdot_number,
            'fetched_at': datetime.now().isoformat(),
            'safer_data': {},
            'insurance_data': {},
            'success': False
        }
        
        # Get SAFER snapshot
        print("  - Fetching SAFER company snapshot...")
        safer_data = self.get_safer_snapshot(usdot_number)
        if safer_data:
            result['safer_data'] = safer_data
            print(f"    ✓ Found: {safer_data.get('legal_name', 'Unknown')}")
        
        # Get L&I insurance details
        print("  - Fetching L&I insurance details...")
        insurance_data = self.get_li_insurance_data(usdot_number)
        if insurance_data:
            result['insurance_data'] = insurance_data
            if insurance_data.get('current_insurance'):
                carrier = insurance_data['current_insurance'].get('insurance_carrier')
                print(f"    ✓ Insurance Carrier: {carrier}")
                result['success'] = True
        
        return result


def test_real_data():
    """Test with known carriers"""
    
    scraper = FMCSAPublicDataScraper()
    
    # Test carriers
    test_carriers = [
        80321,   # FedEx
        76830,   # UPS  
        65119,   # Schneider
        2350588, # Small carrier (easier to test)
    ]
    
    print("=" * 80)
    print("FMCSA Real Insurance Data Test")
    print("=" * 80)
    
    for usdot in test_carriers[:1]:  # Test first one
        print(f"\nTesting USDOT: {usdot}")
        print("-" * 40)
        
        data = scraper.get_real_insurance_data(usdot)
        
        # Display results
        if data['safer_data']:
            print("\nSAFER Data:")
            for key, value in data['safer_data'].items():
                print(f"  {key}: {value}")
        
        if data['insurance_data'].get('current_insurance'):
            print("\nCurrent Insurance:")
            insurance = data['insurance_data']['current_insurance']
            for key, value in insurance.items():
                if value:
                    print(f"  {key}: {value}")
        
        if data['insurance_data'].get('insurance_records'):
            print(f"\nTotal Insurance Records: {len(data['insurance_data']['insurance_records'])}")
    
    print("\n" + "=" * 80)
    print("Note: For production use, implement caching to avoid excessive requests")
    

if __name__ == "__main__":
    # Test direct SAFER access first
    print("Testing direct SAFER access...")
    response = requests.get("https://safer.fmcsa.dot.gov/CompanySnapshot.aspx", timeout=5)
    print(f"SAFER Status: {response.status_code}")
    
    # Test L&I access
    print("Testing L&I public access...")
    response = requests.get("https://li-public.fmcsa.dot.gov/", timeout=5)
    print(f"L&I Status: {response.status_code}")
    
    print("\n")
    test_real_data()