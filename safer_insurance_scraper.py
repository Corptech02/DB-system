#!/usr/bin/env python3
"""
SAFER System Insurance Scraper
Using the FMCSA SAFER system which may have different access patterns
"""

import requests
import re
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, Optional

class SAFERInsuranceScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,application/json,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9'
        })
    
    def test_safer_apis(self, usdot):
        """Test various SAFER API endpoints"""
        print(f"\n{'='*70}")
        print(f"TESTING SAFER APIS FOR USDOT: {usdot}")
        print('='*70)
        
        # Known SAFER endpoints
        safer_endpoints = [
            # SAFER Web Service endpoints
            f"https://safer.fmcsa.dot.gov/api/carrier/{usdot}",
            f"https://safer.fmcsa.dot.gov/query.asp?searchtype=ANY&query_type=queryCarrierSnapshot&query_param=USDOT&original_query_param=NAME&query_string={usdot}",
            f"https://safer.fmcsa.dot.gov/api/carrier/{usdot}/insurance",
            f"https://safer.fmcsa.dot.gov/ws/rs/carrier/{usdot}",
            
            # Mobile SAFER endpoints
            f"https://mobile.fmcsa.dot.gov/LIVIEW/carrier/{usdot}",
            f"https://mobile.fmcsa.dot.gov/carrier/{usdot}/insurance",
            
            # AI/ML endpoints (newer)
            f"https://ai.fmcsa.dot.gov/SMS/Carrier/{usdot}/CarrierRegistration.aspx",
            
            # Direct L&I alternative endpoints
            f"https://li-public.fmcsa.dot.gov/LIVIEW/PKG_CARRQUERY.PRC_ACTIVEINSURANCE/{usdot}",
            f"https://li-public.fmcsa.dot.gov/services/carrier/{usdot}/insurance",
            
            # Legacy MCMIS endpoints
            f"https://www.fmcsa.dot.gov/SMS/Carrier/{usdot}",
        ]
        
        for endpoint in safer_endpoints:
            print(f"\nTesting: {endpoint}")
            
            try:
                resp = self.session.get(endpoint, timeout=10, allow_redirects=True)
                print(f"   Status: {resp.status_code}")
                
                if resp.status_code == 200:
                    content_type = resp.headers.get('Content-Type', '')
                    print(f"   Content-Type: {content_type}")
                    print(f"   Response size: {len(resp.content)} bytes")
                    
                    # Check for JSON response
                    if 'json' in content_type:
                        try:
                            data = resp.json()
                            print(f"   ✅ Got JSON response: {list(data.keys())[:5]}")
                            
                            # Look for insurance fields
                            if self.check_json_for_insurance(data):
                                return ('json', data)
                        except:
                            pass
                    
                    # Check for XML response
                    elif 'xml' in content_type:
                        try:
                            root = ET.fromstring(resp.text)
                            print(f"   ✅ Got XML response")
                            
                            # Look for insurance elements
                            if self.check_xml_for_insurance(root):
                                return ('xml', resp.text)
                        except:
                            pass
                    
                    # Check HTML for insurance content
                    elif len(resp.text) > 1000:
                        if self.check_html_for_insurance(resp.text, usdot):
                            print(f"   ✅ Found insurance content in HTML")
                            
                            # Save successful response
                            filename = f"safer_insurance_{usdot}.html"
                            with open(filename, 'w') as f:
                                f.write(resp.text)
                            print(f"   Saved to: {filename}")
                            
                            return ('html', resp.text)
                
            except requests.exceptions.RequestException as e:
                print(f"   Error: {e}")
            except Exception as e:
                print(f"   Unexpected error: {e}")
        
        return None
    
    def check_json_for_insurance(self, data):
        """Check if JSON contains insurance data"""
        insurance_keys = ['insurance', 'liability', 'coverage', 'policy', 'insurer', 'carrier_insurance']
        
        def search_dict(d):
            if isinstance(d, dict):
                for key, value in d.items():
                    if any(ins_key in key.lower() for ins_key in insurance_keys):
                        print(f"      Found insurance field: {key} = {value}")
                        return True
                    if isinstance(value, (dict, list)):
                        if search_dict(value):
                            return True
            elif isinstance(d, list):
                for item in d:
                    if search_dict(item):
                        return True
            return False
        
        return search_dict(data)
    
    def check_xml_for_insurance(self, root):
        """Check if XML contains insurance data"""
        insurance_tags = ['Insurance', 'Liability', 'Coverage', 'Policy', 'Insurer']
        
        for tag in insurance_tags:
            elements = root.findall(f".//{tag}")
            if elements:
                print(f"      Found XML element: {tag}")
                return True
        
        return False
    
    def check_html_for_insurance(self, html, usdot):
        """Check if HTML contains insurance data"""
        insurance_indicators = [
            'insurance',
            'liability',
            'coverage',
            'policy',
            'geico',
            'progressive',
            '91x',
            'bmc-'
        ]
        
        html_lower = html.lower()
        
        # Must contain USDOT and insurance indicators
        if str(usdot) in html:
            for indicator in insurance_indicators:
                if indicator in html_lower:
                    # Look for specific insurance company names
                    if 'GEICO MARINE INSURANCE COMPANY' in html:
                        print("      ✅ Found GEICO MARINE INSURANCE COMPANY")
                        return True
                    elif 'insurance' in html_lower and 'company' in html_lower:
                        return True
        
        return False
    
    def test_safer_query_api(self, usdot):
        """Test the SAFER query API with different parameters"""
        print(f"\n{'='*70}")
        print("TESTING SAFER QUERY API")
        print('='*70)
        
        base_url = "https://safer.fmcsa.dot.gov/query.asp"
        
        # Different query combinations
        queries = [
            {
                'searchtype': 'ANY',
                'query_type': 'queryCarrierSnapshot',
                'query_param': 'USDOT',
                'query_string': str(usdot)
            },
            {
                'searchtype': 'ACTIVE',
                'query_type': 'queryCarrierSnapshot',
                'query_param': 'USDOT',
                'query_string': str(usdot)
            },
            {
                'query_type': 'queryCarrierInsurance',
                'query_param': 'USDOT',
                'query_string': str(usdot)
            }
        ]
        
        for params in queries:
            print(f"\nTrying query: {params}")
            
            resp = self.session.get(base_url, params=params)
            print(f"   Status: {resp.status_code}")
            
            if resp.status_code == 200 and len(resp.text) > 1000:
                # Check for insurance section
                if 'insurance' in resp.text.lower() or 'liability' in resp.text.lower():
                    print("   ✅ Found insurance content")
                    
                    # Parse the insurance data
                    self.parse_safer_insurance(resp.text, usdot)
                    
                    # Save response
                    with open(f"safer_query_{usdot}.html", 'w') as f:
                        f.write(resp.text)
                    
                    return resp.text
        
        return None
    
    def parse_safer_insurance(self, html, usdot):
        """Parse insurance data from SAFER response"""
        print("\n   Parsing SAFER insurance data...")
        
        # Look for insurance table or section
        # SAFER uses specific patterns
        
        # Pattern 1: Insurance company in table
        company_pattern = r'<td[^>]*>([A-Z][A-Z\s&,.\'()-]+(?:INSURANCE|ASSURANCE|INDEMNITY|CASUALTY|MUTUAL)[A-Z\s&,.\'()-]*)</td>'
        companies = re.findall(company_pattern, html, re.IGNORECASE)
        if companies:
            print(f"   Found companies: {companies[:3]}")
        
        # Pattern 2: Policy numbers
        policy_pattern = r'\b([89]\d{9}|[0-9]{10})\b'
        policies = re.findall(policy_pattern, html)
        if policies:
            print(f"   Found policy numbers: {policies[:3]}")
        
        # Pattern 3: Coverage amounts
        amount_pattern = r'\$\s*([0-9,]+(?:,000)?)'
        amounts = re.findall(amount_pattern, html)
        if amounts:
            print(f"   Found coverage amounts: {amounts[:3]}")
        
        # Pattern 4: Dates
        date_pattern = r'(\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})'
        dates = re.findall(date_pattern, html)
        if dates:
            print(f"   Found dates: {dates[:3]}")
    
    def scrape_all_sources(self, usdot):
        """Try all available sources"""
        print(f"\n{'='*80}")
        print(f"COMPREHENSIVE INSURANCE SCRAPING FOR USDOT: {usdot}")
        print('='*80)
        
        # Test SAFER APIs
        result = self.test_safer_apis(usdot)
        if result:
            result_type, data = result
            print(f"\n✅ SUCCESS with SAFER API ({result_type})!")
            return data
        
        # Test SAFER Query API
        result = self.test_safer_query_api(usdot)
        if result:
            print(f"\n✅ SUCCESS with SAFER Query API!")
            return result
        
        print("\n❌ Could not find insurance data in any SAFER endpoint")
        return None

if __name__ == "__main__":
    scraper = SAFERInsuranceScraper()
    result = scraper.scrape_all_sources(905413)
    
    if result:
        print(f"\n{'='*70}")
        print("✅ SUCCESSFULLY FOUND INSURANCE DATA")
        print('='*70)