#!/usr/bin/env python3
"""
Deep L&I Insurance Scraper
Researching different methods to access the L&I system
"""

import requests
import re
import time
from urllib.parse import urlencode, quote
import json

class LIDeepScraper:
    def __init__(self):
        self.session = requests.Session()
        
        # Mimic a real browser completely
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }
        
        self.base_url = "https://li-public.fmcsa.dot.gov"
        
    def test_method_1_direct_url(self, usdot):
        """Method 1: Try direct URL with all possible parameter formats"""
        print(f"\n{'='*60}")
        print(f"Method 1: Direct URL Access for USDOT {usdot}")
        print('='*60)
        
        # Different parameter combinations found in FMCSA sites
        url_patterns = [
            f"/LIVIEW/pkg_carrquery.prc_activeinsurance?pn_dotno={usdot}",
            f"/LIVIEW/pkg_carrquery.prc_activeinsurance?pv_apcant_dot_no={usdot}",
            f"/LIVIEW/pkg_carrquery.prc_activeinsurance?pv_dot_no={usdot}",
            f"/LIVIEW/pkg_carrquery.prc_activeinsurance?p_dot={usdot}",
            f"/LIVIEW/pkg_carrquery.prc_activeinsurance?p_usdot={usdot}",
            f"/LIVIEW/PKG_carrquery.prc_activeinsurance?pn_dotno={usdot}",  # Different case
            f"/LIVIEW/pkg_CARRQUERY.PRC_ACTIVEINSURANCE?pn_dotno={usdot}",  # All caps
        ]
        
        for pattern in url_patterns:
            url = self.base_url + pattern
            print(f"Trying: {url}")
            
            try:
                resp = self.session.get(url, timeout=10, allow_redirects=True)
                print(f"  Status: {resp.status_code}, Length: {len(resp.text)}")
                
                if resp.status_code == 200 and len(resp.text) > 1000:
                    if "GEICO" in resp.text or "insurance" in resp.text.lower():
                        print("  ✅ Found insurance content!")
                        return resp.text
                    if str(usdot) in resp.text:
                        print("  ✅ Found USDOT in response")
                        return resp.text
            except Exception as e:
                print(f"  Error: {e}")
        
        return None
    
    def test_method_2_workflow(self, usdot):
        """Method 2: Follow the complete workflow"""
        print(f"\n{'='*60}")
        print(f"Method 2: Complete Workflow for USDOT {usdot}")
        print('='*60)
        
        # Step 1: Get the main L&I page to establish session
        print("\nStep 1: Getting main L&I page...")
        main_url = f"{self.base_url}/LIVIEW/"
        resp = self.session.get(main_url)
        print(f"  Status: {resp.status_code}")
        
        # Extract any session tokens or hidden fields
        tokens = re.findall(r'name="([^"]*token[^"]*)" value="([^"]*)"', resp.text, re.IGNORECASE)
        if tokens:
            print(f"  Found tokens: {tokens}")
        
        # Step 2: Get the search form
        print("\nStep 2: Getting search form...")
        search_url = f"{self.base_url}/LIVIEW/pkg_carrquery.prc_carrlist"
        resp = self.session.get(search_url)
        print(f"  Status: {resp.status_code}")
        
        # Step 3: Submit search
        print("\nStep 3: Submitting search...")
        
        # Build form data based on actual form fields
        form_data = {
            'n_dotno': str(usdot),
            'pv_vpath': 'LIVIEW',
            'pv_invpath': 'LIVIEW',
            'pv_path': 'LIVIEW',
            'searchtype': 'ANY',
            'query': 'y',
            'searchstring': str(usdot),
            'submit': 'Search'
        }
        
        # Try GET first (some Oracle APEX apps use GET for searches)
        search_with_params = f"{search_url}?{urlencode(form_data)}"
        print(f"  GET: {search_with_params}")
        resp = self.session.get(search_with_params)
        print(f"  Status: {resp.status_code}, Length: {len(resp.text)}")
        
        if resp.status_code == 200 and str(usdot) in resp.text:
            print("  ✅ Found USDOT in search results")
            
            # Look for the activeinsurance link
            insurance_links = re.findall(
                r'href="([^"]*activeinsurance[^"]*)"', 
                resp.text, 
                re.IGNORECASE
            )
            
            if insurance_links:
                print(f"  Found {len(insurance_links)} insurance links")
                for link in insurance_links:
                    if link.startswith('/'):
                        full_url = self.base_url + link
                    elif link.startswith('pkg_'):
                        full_url = f"{self.base_url}/LIVIEW/{link}"
                    else:
                        full_url = link
                    
                    print(f"  Following link: {full_url}")
                    ins_resp = self.session.get(full_url)
                    if ins_resp.status_code == 200:
                        return ins_resp.text
        
        return None
    
    def test_method_3_oracle_apex(self, usdot):
        """Method 3: Try Oracle APEX specific patterns"""
        print(f"\n{'='*60}")
        print(f"Method 3: Oracle APEX Patterns for USDOT {usdot}")
        print('='*60)
        
        # L&I appears to use Oracle APEX, which has specific URL patterns
        apex_patterns = [
            f"/LIVIEW/f?p=LIVIEW:ACTIVEINSURANCE:::::P_USDOT:{usdot}",
            f"/LIVIEW/f?p=100:1:::::P1_USDOT:{usdot}",
            f"/LIVIEW/wwv_flow.show?p_flow_id=LIVIEW&p_page_id=ACTIVEINSURANCE&p_usdot={usdot}",
        ]
        
        for pattern in apex_patterns:
            url = self.base_url + pattern
            print(f"Trying: {url}")
            
            try:
                resp = self.session.get(url, timeout=10)
                print(f"  Status: {resp.status_code}, Length: {len(resp.text)}")
                
                if resp.status_code == 200 and len(resp.text) > 1000:
                    return resp.text
            except Exception as e:
                print(f"  Error: {e}")
        
        return None
    
    def test_method_4_api_endpoints(self, usdot):
        """Method 4: Try hidden API endpoints"""
        print(f"\n{'='*60}")
        print(f"Method 4: Hidden API Endpoints for USDOT {usdot}")
        print('='*60)
        
        # Sometimes there are JSON/XML endpoints
        api_patterns = [
            f"/LIVIEW/api/carriers/{usdot}/insurance",
            f"/LIVIEW/rest/insurance?usdot={usdot}",
            f"/LIVIEW/pkg_carrquery.prc_activeinsurance_json?pn_dotno={usdot}",
            f"/LIVIEW/services/insurance/{usdot}",
            f"/api/li/carrier/{usdot}",
        ]
        
        for pattern in api_patterns:
            url = self.base_url + pattern
            print(f"Trying: {url}")
            
            # Try with JSON headers
            headers = self.session.headers.copy()
            headers['Accept'] = 'application/json, text/plain, */*'
            
            try:
                resp = self.session.get(url, headers=headers, timeout=5)
                print(f"  Status: {resp.status_code}")
                
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        print(f"  ✅ Found JSON response: {data}")
                        return json.dumps(data)
                    except:
                        if len(resp.text) > 100:
                            return resp.text
            except Exception as e:
                print(f"  Error: {e}")
        
        return None
    
    def test_method_5_referer_chain(self, usdot):
        """Method 5: Build proper referer chain"""
        print(f"\n{'='*60}")
        print(f"Method 5: Referer Chain for USDOT {usdot}")
        print('='*60)
        
        # Build the referer chain that a real browser would have
        
        # 1. Main page
        self.session.headers['Referer'] = 'https://www.fmcsa.dot.gov/'
        resp = self.session.get(f"{self.base_url}/LIVIEW/")
        print(f"Step 1 - Main page: {resp.status_code}")
        
        # 2. Search page
        self.session.headers['Referer'] = f"{self.base_url}/LIVIEW/"
        resp = self.session.get(f"{self.base_url}/LIVIEW/pkg_carrquery.prc_carrlist")
        print(f"Step 2 - Search page: {resp.status_code}")
        
        # 3. Submit search with referer
        self.session.headers['Referer'] = f"{self.base_url}/LIVIEW/pkg_carrquery.prc_carrlist"
        
        # Try the activeinsurance with proper referer
        url = f"{self.base_url}/LIVIEW/pkg_carrquery.prc_activeinsurance"
        
        # Add search parameters
        params = {
            'pn_dotno': str(usdot),
            'pv_vpath': 'LIVIEW'
        }
        
        print(f"Step 3 - Insurance page with referer: {url}")
        resp = self.session.get(url, params=params)
        print(f"  Status: {resp.status_code}, Length: {len(resp.text)}")
        
        if resp.status_code == 200 and len(resp.text) > 1000:
            return resp.text
        
        return None
    
    def scrape_insurance(self, usdot):
        """Try all methods to scrape insurance data"""
        print(f"\n{'='*70}")
        print(f"DEEP SCRAPING L&I INSURANCE FOR USDOT: {usdot}")
        print('='*70)
        
        methods = [
            self.test_method_1_direct_url,
            self.test_method_2_workflow,
            self.test_method_3_oracle_apex,
            self.test_method_4_api_endpoints,
            self.test_method_5_referer_chain
        ]
        
        for i, method in enumerate(methods, 1):
            print(f"\n>>> Attempting Method {i}...")
            result = method(usdot)
            
            if result:
                # Save successful result
                filename = f"li_success_{usdot}_method_{i}.html"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(result)
                print(f"\n✅ SUCCESS with Method {i}!")
                print(f"   Saved to: {filename}")
                
                # Check for insurance data
                if "GEICO" in result:
                    print("   ✅ Found GEICO MARINE INSURANCE")
                if "91X" in result:
                    print("   ✅ Found Form 91X")
                if "1,000,000" in result or "1000000" in result:
                    print("   ✅ Found $1,000,000 coverage")
                
                return result
        
        print("\n❌ All methods failed")
        return None


if __name__ == "__main__":
    scraper = LIDeepScraper()
    
    # Test with USDOT 905413
    result = scraper.scrape_insurance(905413)
    
    if not result:
        print("\n" + "="*70)
        print("ANALYSIS: The L&I system requires browser JavaScript execution")
        print("or has anti-scraping measures. Consider using Selenium or Playwright.")
        print("="*70)