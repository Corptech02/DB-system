#!/usr/bin/env python3
"""
Reverse engineering the L&I system
Let's find exactly how the browser accesses it
"""

import requests
import re
import base64
import hashlib
import time
from urllib.parse import urlencode, quote, unquote

class LIReverseEngineer:
    def __init__(self):
        self.session = requests.Session()
        
        # Exact Chrome headers from DevTools
        self.session.headers = {
            'Host': 'li-public.fmcsa.dot.gov',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-User': '?1',
            'Sec-Fetch-Dest': 'document',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
        }
    
    def test_oracle_forms(self, usdot):
        """Oracle Forms uses special protocols"""
        print("\n" + "="*60)
        print("Testing Oracle Forms Protocol")
        print("="*60)
        
        base_url = "https://li-public.fmcsa.dot.gov"
        
        # Oracle Forms endpoints
        endpoints = [
            "/forms/frmservlet",
            "/forms/lservlet",
            "/forms90/f90servlet",
            "/LIVIEW/forms/frmservlet"
        ]
        
        for endpoint in endpoints:
            url = base_url + endpoint
            print(f"Testing: {url}")
            
            # Oracle Forms specific parameters
            params = {
                'config': 'liview',
                'form': 'carrquery',
                'userid': '',
                'parameters': f'dotno={usdot}'
            }
            
            try:
                resp = self.session.get(url, params=params, timeout=5)
                print(f"  Status: {resp.status_code}")
                if resp.status_code == 200:
                    print(f"  Content-Type: {resp.headers.get('Content-Type', 'N/A')}")
                    if len(resp.content) > 100:
                        print(f"  ✅ Got response: {len(resp.content)} bytes")
                        return resp.content
            except Exception as e:
                print(f"  Error: {e}")
        
        return None
    
    def test_soap_endpoint(self, usdot):
        """Some Oracle systems use SOAP"""
        print("\n" + "="*60)
        print("Testing SOAP/XML Endpoints")
        print("="*60)
        
        soap_envelope = f"""<?xml version="1.0" encoding="utf-8"?>
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Body>
                <GetActiveInsurance xmlns="http://li-public.fmcsa.dot.gov/">
                    <usdot>{usdot}</usdot>
                </GetActiveInsurance>
            </soap:Body>
        </soap:Envelope>"""
        
        urls = [
            "https://li-public.fmcsa.dot.gov/LIVIEW/services",
            "https://li-public.fmcsa.dot.gov/services/LIService",
            "https://li-public.fmcsa.dot.gov/ws/carrier"
        ]
        
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': 'GetActiveInsurance'
        }
        
        for url in urls:
            print(f"Testing: {url}")
            try:
                resp = self.session.post(url, data=soap_envelope, headers=headers, timeout=5)
                print(f"  Status: {resp.status_code}")
                if resp.status_code == 200:
                    print(f"  ✅ Got SOAP response")
                    return resp.text
            except Exception as e:
                print(f"  Error: {e}")
        
        return None
    
    def test_hidden_form_submission(self, usdot):
        """Test hidden form field requirements"""
        print("\n" + "="*60)
        print("Testing Hidden Form Fields")
        print("="*60)
        
        # First, get the search page to extract hidden fields
        search_url = "https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_carrlist"
        
        print("Step 1: Getting search form...")
        resp = self.session.get(search_url)
        
        if resp.status_code == 200:
            # Extract all hidden fields
            hidden_fields = re.findall(r'<input[^>]*type=["\']hidden["\'][^>]*>', resp.text, re.IGNORECASE)
            print(f"Found {len(hidden_fields)} hidden fields")
            
            form_data = {}
            for field in hidden_fields:
                name_match = re.search(r'name=["\']([^"\']+)["\']', field)
                value_match = re.search(r'value=["\']([^"\']*)["\']', field)
                if name_match:
                    name = name_match.group(1)
                    value = value_match.group(1) if value_match else ''
                    form_data[name] = value
                    print(f"  {name}: {value[:50]}...")
            
            # Add the USDOT search
            form_data['n_dotno'] = str(usdot)
            form_data['submit'] = 'Search'
            
            print("\nStep 2: Submitting with all fields...")
            resp = self.session.post(search_url, data=form_data)
            print(f"  Status: {resp.status_code}, Length: {len(resp.text)}")
            
            if resp.status_code == 200 and str(usdot) in resp.text:
                print("  ✅ Found USDOT in response")
                
                # Save for analysis
                with open(f"li_hidden_form_{usdot}.html", "w") as f:
                    f.write(resp.text)
                
                return resp.text
        
        return None
    
    def test_base64_encoding(self, usdot):
        """Some systems encode parameters"""
        print("\n" + "="*60)
        print("Testing Base64 Encoded Parameters")
        print("="*60)
        
        # Encode the USDOT
        encoded_usdot = base64.b64encode(str(usdot).encode()).decode()
        
        urls = [
            f"https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_activeinsurance?data={encoded_usdot}",
            f"https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_activeinsurance?q={encoded_usdot}",
            f"https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_activeinsurance?p={encoded_usdot}"
        ]
        
        for url in urls:
            print(f"Testing: {url}")
            resp = self.session.get(url)
            print(f"  Status: {resp.status_code}")
            if resp.status_code == 200 and len(resp.text) > 1000:
                return resp.text
        
        return None
    
    def test_cookie_requirements(self, usdot):
        """Test if specific cookies enable access"""
        print("\n" + "="*60)
        print("Testing Cookie Requirements")
        print("="*60)
        
        # Common Oracle/APEX cookies
        cookies = {
            'ORA_WWV_APP_100': 'ORA_WWV-1234567890',
            'JSESSIONID': hashlib.md5(str(usdot).encode()).hexdigest(),
            'TS01234567': str(int(time.time())),
            '__Secure-LI-Session': base64.b64encode(f"usdot={usdot}".encode()).decode()
        }
        
        for cookie_name, cookie_value in cookies.items():
            self.session.cookies.set(cookie_name, cookie_value)
        
        url = f"https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_activeinsurance"
        params = {'pn_dotno': str(usdot)}
        
        print(f"Testing with cookies: {list(cookies.keys())}")
        resp = self.session.get(url, params=params)
        print(f"  Status: {resp.status_code}, Length: {len(resp.text)}")
        
        if resp.status_code == 200 and len(resp.text) > 1000:
            return resp.text
        
        return None
    
    def test_ajax_json(self, usdot):
        """Test AJAX/JSON endpoints"""
        print("\n" + "="*60)
        print("Testing AJAX/JSON Endpoints")
        print("="*60)
        
        # AJAX headers
        ajax_headers = {
            'X-Requested-With': 'XMLHttpRequest',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }
        
        endpoints = [
            "/LIVIEW/ajax/get_insurance",
            "/LIVIEW/api/insurance",
            "/LIVIEW/json/carrier_insurance",
            "/LIVIEW/pkg_carrquery.ajax_activeinsurance"
        ]
        
        for endpoint in endpoints:
            url = f"https://li-public.fmcsa.dot.gov{endpoint}"
            print(f"Testing: {url}")
            
            data = {'usdot': str(usdot), 'dotno': str(usdot), 'pn_dotno': str(usdot)}
            
            try:
                resp = self.session.post(url, data=data, headers=ajax_headers, timeout=5)
                print(f"  Status: {resp.status_code}")
                
                if resp.status_code == 200:
                    try:
                        json_data = resp.json()
                        print(f"  ✅ Got JSON: {json_data}")
                        return json_data
                    except:
                        if len(resp.text) > 100:
                            return resp.text
            except Exception as e:
                print(f"  Error: {e}")
        
        return None
    
    def test_post_with_tokens(self, usdot):
        """Test POST with CSRF tokens"""
        print("\n" + "="*60)
        print("Testing POST with CSRF Tokens")
        print("="*60)
        
        # Get initial page to extract tokens
        search_url = "https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_carrlist"
        resp = self.session.get(search_url)
        
        if resp.status_code == 200:
            # Look for CSRF tokens
            csrf_patterns = [
                r'name="csrf_token" value="([^"]+)"',
                r'name="_token" value="([^"]+)"',
                r'name="authenticity_token" value="([^"]+)"',
                r'name="p_session_id" value="([^"]+)"',
                r'name="p_instance" value="([^"]+)"'
            ]
            
            tokens = {}
            for pattern in csrf_patterns:
                match = re.search(pattern, resp.text)
                if match:
                    token_name = pattern.split('"')[1]
                    tokens[token_name] = match.group(1)
                    print(f"Found token: {token_name} = {match.group(1)[:20]}...")
            
            # Build form data with tokens
            form_data = {
                'n_dotno': str(usdot),
                'submit': 'Search',
                **tokens
            }
            
            print(f"\nSubmitting with {len(tokens)} tokens...")
            resp = self.session.post(search_url, data=form_data)
            print(f"  Status: {resp.status_code}, Length: {len(resp.text)}")
            
            if resp.status_code == 200 and str(usdot) in resp.text:
                print("  ✅ Success!")
                return resp.text
        
        return None
    
    def reverse_engineer(self, usdot):
        """Try all reverse engineering methods"""
        print("\n" + "="*70)
        print(f"REVERSE ENGINEERING L&I FOR USDOT: {usdot}")
        print("="*70)
        
        methods = [
            ("Oracle Forms", self.test_oracle_forms),
            ("SOAP/XML", self.test_soap_endpoint),
            ("Hidden Form Fields", self.test_hidden_form_submission),
            ("Base64 Encoding", self.test_base64_encoding),
            ("Cookie Requirements", self.test_cookie_requirements),
            ("AJAX/JSON", self.test_ajax_json),
            ("POST with Tokens", self.test_post_with_tokens)
        ]
        
        for name, method in methods:
            print(f"\n>>> Testing: {name}")
            result = method(usdot)
            
            if result:
                print(f"\n✅ SUCCESS with {name}!")
                
                # Save result
                if isinstance(result, bytes):
                    filename = f"li_success_{usdot}_{name.replace('/', '_')}.bin"
                    with open(filename, 'wb') as f:
                        f.write(result)
                else:
                    filename = f"li_success_{usdot}_{name.replace('/', '_')}.html"
                    with open(filename, 'w') as f:
                        f.write(str(result))
                
                print(f"Saved to: {filename}")
                
                # Check for insurance data
                result_str = str(result)
                if "GEICO" in result_str:
                    print("✅ Found GEICO MARINE!")
                if "905413" in result_str:
                    print("✅ Found USDOT!")
                
                return result
        
        print("\n❌ All methods failed")
        return None


if __name__ == "__main__":
    engineer = LIReverseEngineer()
    result = engineer.reverse_engineer(905413)
    
    if not result:
        print("\n" + "="*70)
        print("ANALYSIS: L&I system likely requires:")
        print("1. JavaScript execution for token generation")
        print("2. WebSocket or Server-Sent Events")
        print("3. Complex session management")
        print("="*70)