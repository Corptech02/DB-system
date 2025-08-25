#!/usr/bin/env python3
"""
Final L&I Scraping Attempt
Testing mobile interfaces, REST APIs, and alternative access methods
"""

import requests
import json
import re
from datetime import datetime

class LIFinalAttempt:
    def __init__(self):
        self.session = requests.Session()
        
    def test_mobile_interface(self, usdot):
        """Test mobile-optimized interfaces"""
        print(f"\n{'='*70}")
        print("TESTING MOBILE INTERFACES")
        print('='*70)
        
        mobile_headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        }
        
        mobile_urls = [
            f"https://li-public.fmcsa.dot.gov/m/carrier/{usdot}",
            f"https://li-public.fmcsa.dot.gov/mobile/carrier/{usdot}",
            f"https://m.fmcsa.dot.gov/li/carrier/{usdot}",
            f"https://mobile.fmcsa.dot.gov/LIVIEW/carrier/{usdot}/insurance",
            f"https://li-public.fmcsa.dot.gov/api/v1/carrier/{usdot}/insurance",
            f"https://li-public.fmcsa.dot.gov/rest/carrier/{usdot}",
            f"https://li-public.fmcsa.dot.gov/LIVIEW/m/pkg_carrquery.prc_activeinsurance?pn_dotno={usdot}"
        ]
        
        for url in mobile_urls:
            print(f"\nTesting: {url}")
            resp = requests.get(url, headers=mobile_headers, timeout=5, allow_redirects=True)
            print(f"   Status: {resp.status_code}")
            
            if resp.status_code == 200 and len(resp.text) > 500:
                print(f"   ✅ Got response: {len(resp.text)} bytes")
                return resp.text
        
        return None
    
    def test_data_endpoints(self, usdot):
        """Test data-specific endpoints"""
        print(f"\n{'='*70}")
        print("TESTING DATA ENDPOINTS")
        print('='*70)
        
        # Try different data formats
        endpoints = [
            (f"https://li-public.fmcsa.dot.gov/LIVIEW/data/carrier/{usdot}", "json"),
            (f"https://li-public.fmcsa.dot.gov/LIVIEW/xml/carrier/{usdot}", "xml"),
            (f"https://li-public.fmcsa.dot.gov/LIVIEW/csv/carrier/{usdot}", "csv"),
            (f"https://li-public.fmcsa.dot.gov/services/insuranceService/getActiveInsurance?usdot={usdot}", "json"),
            (f"https://li-public.fmcsa.dot.gov/api/insurance?carrier={usdot}", "json")
        ]
        
        for url, expected_type in endpoints:
            print(f"\nTesting {expected_type}: {url}")
            
            headers = self.session.headers.copy()
            if expected_type == "json":
                headers['Accept'] = 'application/json'
            elif expected_type == "xml":
                headers['Accept'] = 'application/xml'
            
            resp = self.session.get(url, headers=headers, timeout=5)
            print(f"   Status: {resp.status_code}")
            
            if resp.status_code == 200:
                if expected_type == "json":
                    try:
                        data = resp.json()
                        print(f"   ✅ Got JSON: {data}")
                        return data
                    except:
                        pass
                elif len(resp.text) > 100:
                    print(f"   Got response: {len(resp.text)} bytes")
                    return resp.text
        
        return None
    
    def test_websocket_endpoints(self, usdot):
        """Check for WebSocket or Server-Sent Events endpoints"""
        print(f"\n{'='*70}")
        print("CHECKING FOR WEBSOCKET/SSE ENDPOINTS")
        print('='*70)
        
        # Get the main page and look for WebSocket connections
        main_url = "https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_carrlist"
        resp = self.session.get(main_url)
        
        if resp.status_code == 200:
            # Look for WebSocket URLs
            ws_patterns = [
                r'wss?://[^"\'\s]+',
                r'new WebSocket\(["\']([^"\']+)["\']',
                r'EventSource\(["\']([^"\']+)["\']'
            ]
            
            for pattern in ws_patterns:
                matches = re.findall(pattern, resp.text)
                if matches:
                    print(f"   Found WebSocket/SSE: {matches}")
                    return matches
        
        return None
    
    def analyze_javascript_requirements(self, usdot):
        """Analyze what JavaScript is doing"""
        print(f"\n{'='*70}")
        print("ANALYZING JAVASCRIPT REQUIREMENTS")
        print('='*70)
        
        # Get the search page
        search_url = "https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_carrlist"
        resp = self.session.get(search_url)
        
        if resp.status_code == 200:
            # Look for JavaScript that builds URLs
            js_patterns = [
                r'function\s+\w+\s*\([^)]*\)\s*{[^}]*activeinsurance[^}]*}',
                r'var\s+\w+\s*=\s*["\'][^"\']*activeinsurance[^"\']*["\']',
                r'\.href\s*=\s*["\'][^"\']*activeinsurance[^"\']*["\']'
            ]
            
            for pattern in js_patterns:
                matches = re.findall(pattern, resp.text, re.IGNORECASE | re.DOTALL)
                if matches:
                    print(f"   Found JS building insurance URL:")
                    for match in matches[:2]:
                        print(f"   {match[:200]}")
            
            # Look for AJAX calls
            ajax_patterns = [
                r'\.ajax\({[^}]*url[^}]*}',
                r'fetch\([^)]+\)',
                r'XMLHttpRequest'
            ]
            
            for pattern in ajax_patterns:
                if re.search(pattern, resp.text):
                    print(f"   Found AJAX pattern: {pattern}")
            
            # Look for form submission handlers
            form_patterns = [
                r'onsubmit\s*=\s*["\']([^"\']+)["\']',
                r'\.submit\s*\(\s*function',
                r'addEventListener\(["\']submit["\']'
            ]
            
            for pattern in form_patterns:
                matches = re.findall(pattern, resp.text)
                if matches:
                    print(f"   Found form handler: {matches[:2]}")
    
    def brute_force_parameters(self, usdot):
        """Try every possible parameter combination"""
        print(f"\n{'='*70}")
        print("BRUTE FORCE PARAMETER TESTING")
        print('='*70)
        
        base_url = "https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_activeinsurance"
        
        # All possible parameter combinations
        param_names = ['pn_dotno', 'pv_dotno', 'p_dotno', 'n_dotno', 'dotno', 'usdot', 'id']
        extra_params = [
            {},
            {'pv_vpath': 'LIVIEW'},
            {'vpath': 'LIVIEW'},
            {'path': 'LIVIEW'},
            {'p_session': '1234567890'},
            {'session_id': '1234567890'},
            {'csrf_token': 'test'},
            {'ajax': '1'},
            {'json': '1'},
            {'format': 'json'}
        ]
        
        for param in param_names:
            for extra in extra_params:
                params = {param: str(usdot), **extra}
                
                # Try both GET and POST
                for method in ['GET', 'POST']:
                    if method == 'GET':
                        resp = self.session.get(base_url, params=params, timeout=5)
                    else:
                        resp = self.session.post(base_url, data=params, timeout=5)
                    
                    if resp.status_code == 200 and len(resp.text) > 1000:
                        print(f"\n   ✅ SUCCESS with {method} {param}: {params}")
                        print(f"   Response size: {len(resp.text)}")
                        
                        # Check for insurance content
                        if 'insurance' in resp.text.lower() or 'geico' in resp.text.lower():
                            print(f"   ✅ FOUND INSURANCE DATA!")
                            
                            with open(f"li_bruteforce_{usdot}.html", 'w') as f:
                                f.write(resp.text)
                            
                            return resp.text
        
        return None
    
    def final_comprehensive_test(self, usdot):
        """Run all final tests"""
        print(f"\n{'='*80}")
        print(f"FINAL COMPREHENSIVE L&I TEST FOR USDOT: {usdot}")
        print('='*80)
        
        # Test mobile interfaces
        result = self.test_mobile_interface(usdot)
        if result:
            print("\n✅ SUCCESS with mobile interface!")
            return result
        
        # Test data endpoints
        result = self.test_data_endpoints(usdot)
        if result:
            print("\n✅ SUCCESS with data endpoint!")
            return result
        
        # Check for WebSocket/SSE
        self.test_websocket_endpoints(usdot)
        
        # Analyze JavaScript
        self.analyze_javascript_requirements(usdot)
        
        # Brute force parameters
        result = self.brute_force_parameters(usdot)
        if result:
            print("\n✅ SUCCESS with brute force!")
            return result
        
        print(f"\n{'='*80}")
        print("CONCLUSION: L&I system absolutely requires JavaScript execution")
        print("The system cannot be scraped without a full browser environment")
        print('='*80)
        
        return None

if __name__ == "__main__":
    tester = LIFinalAttempt()
    result = tester.final_comprehensive_test(905413)