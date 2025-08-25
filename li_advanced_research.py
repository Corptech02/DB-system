#!/usr/bin/env python3
"""
Advanced L&I System Research
Deep analysis of the FMCSA L&I system architecture
"""

import requests
import re
import time
import hashlib
import base64
from urllib.parse import urlencode, quote, unquote, parse_qs, urlparse

class LIAdvancedResearch:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
    def analyze_oracle_patterns(self):
        """Oracle APEX/PL/SQL patterns research"""
        print("\n" + "="*70)
        print("ORACLE APEX/PL/SQL GATEWAY ANALYSIS")
        print("="*70)
        
        # Oracle PL/SQL gateway uses specific URL patterns
        # Format: /DAD/package.procedure?param=value
        # Where DAD = Database Access Descriptor (LIVIEW)
        
        base = "https://li-public.fmcsa.dot.gov"
        
        # Test 1: Check if it's Oracle Portal/APEX
        print("\n1. Testing Oracle Portal patterns...")
        oracle_tests = [
            "/pls/apex",
            "/pls/LIVIEW",
            "/apex",
            "/LIVIEW/apex",
            "/LIVIEW/wwv_flow.show",
            "/LIVIEW/f",
            "/LIVIEW/pls"
        ]
        
        for path in oracle_tests:
            url = base + path
            print(f"   Testing: {url}")
            try:
                resp = self.session.get(url, timeout=5, allow_redirects=False)
                print(f"   Status: {resp.status_code}")
                if resp.status_code != 404:
                    print(f"   ✅ Found valid Oracle endpoint!")
                    if resp.headers:
                        print(f"   Headers: {dict(resp.headers)}")
            except:
                pass
        
        # Test 2: Direct package access without parameters might fail
        print("\n2. Testing direct package access...")
        url = f"{base}/LIVIEW/pkg_carrquery"
        resp = self.session.get(url)
        print(f"   Status: {resp.status_code}")
        print(f"   Info: Package without procedure typically returns error")
        
        # Test 3: Check for Oracle error messages
        print("\n3. Analyzing error patterns...")
        test_urls = [
            f"{base}/LIVIEW/pkg_carrquery.invalid_proc",
            f"{base}/LIVIEW/invalid_package.test"
        ]
        
        for url in test_urls:
            resp = self.session.get(url)
            if "ORA-" in resp.text or "oracle" in resp.text.lower():
                print(f"   ✅ Oracle error detected - confirms Oracle backend")
                
    def research_session_flow(self, usdot=905413):
        """Research the actual session flow"""
        print("\n" + "="*70)
        print("SESSION FLOW RESEARCH")
        print("="*70)
        
        base = "https://li-public.fmcsa.dot.gov"
        
        # Step 1: Initial connection
        print("\n1. Initial connection to establish session...")
        root_url = f"{base}/LIVIEW/"
        resp = self.session.get(root_url)
        print(f"   Status: {resp.status_code}")
        print(f"   Cookies received: {list(self.session.cookies.keys())}")
        
        # Look for session establishment patterns
        if resp.text:
            # Check for JavaScript redirects
            js_redirects = re.findall(r'window\.location[.\s]*=[.\s]*["\']([^"\']+)["\']', resp.text)
            if js_redirects:
                print(f"   Found JS redirect: {js_redirects}")
            
            # Check for meta redirects
            meta_redirects = re.findall(r'<meta[^>]*http-equiv=["\']refresh["\'][^>]*content=["\'][^;]*;\s*url=([^"\']+)["\']', resp.text, re.IGNORECASE)
            if meta_redirects:
                print(f"   Found meta redirect: {meta_redirects}")
        
        # Step 2: Get the search form
        print("\n2. Accessing search form...")
        search_url = f"{base}/LIVIEW/pkg_carrquery.prc_carrlist"
        resp = self.session.get(search_url)
        print(f"   Status: {resp.status_code}")
        
        if resp.status_code == 200:
            # Extract ALL form elements
            print("\n   Analyzing form structure...")
            
            # Find form action
            form_action = re.search(r'<form[^>]*action=["\']([^"\']+)["\']', resp.text, re.IGNORECASE)
            if form_action:
                print(f"   Form action: {form_action.group(1)}")
            
            # Find all input fields
            inputs = re.findall(r'<input[^>]*name=["\']([^"\']+)["\'][^>]*>', resp.text, re.IGNORECASE)
            print(f"   Found {len(inputs)} input fields: {inputs[:5]}...")
            
            # Find all hidden fields with values
            hidden_fields = {}
            hidden_pattern = r'<input[^>]*type=["\']hidden["\'][^>]*>'
            for hidden in re.findall(hidden_pattern, resp.text, re.IGNORECASE):
                name_match = re.search(r'name=["\']([^"\']+)["\']', hidden)
                value_match = re.search(r'value=["\']([^"\']*)["\']', hidden)
                if name_match:
                    name = name_match.group(1)
                    value = value_match.group(1) if value_match else ''
                    hidden_fields[name] = value
            
            print(f"   Hidden fields: {list(hidden_fields.keys())}")
            
            return hidden_fields
        
        return {}
    
    def test_parameter_variations(self, usdot=905413):
        """Test all possible parameter name variations"""
        print("\n" + "="*70)
        print("PARAMETER VARIATION TESTING")
        print("="*70)
        
        base_url = "https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_activeinsurance"
        
        # Common Oracle parameter prefixes
        param_variations = [
            f"pn_dotno={usdot}",
            f"pv_dotno={usdot}",
            f"p_dotno={usdot}",
            f"n_dotno={usdot}",
            f"v_dotno={usdot}",
            f"in_dotno={usdot}",
            f"pn_dot_no={usdot}",
            f"pn_usdot={usdot}",
            f"pn_usdotno={usdot}",
            f"p_usdot_no={usdot}",
            f"p_id={usdot}",
            f"id={usdot}",
            f"dotno={usdot}",
            f"usdot={usdot}",
            f"carrier={usdot}",
            f"pn_carrier_id={usdot}",
            f"P1_DOTNO={usdot}",  # APEX style
            f"P2_DOTNO={usdot}",
            f"P100_DOTNO={usdot}"
        ]
        
        for params in param_variations:
            url = f"{base_url}?{params}"
            print(f"\nTesting: {params}")
            
            resp = self.session.get(url, allow_redirects=True)
            print(f"   Status: {resp.status_code}, Size: {len(resp.text)}")
            
            if resp.status_code == 200 and len(resp.text) > 1000:
                # Check for insurance indicators
                if any(word in resp.text.upper() for word in ['INSURANCE', 'GEICO', 'LIABILITY', '91X']):
                    print(f"   ✅ FOUND INSURANCE DATA!")
                    return resp.text
                elif str(usdot) in resp.text:
                    print(f"   ✅ Found USDOT in response")
                    return resp.text
        
        return None
    
    def analyze_working_search(self, usdot=905413):
        """Analyze the working search form submission"""
        print("\n" + "="*70)
        print("ANALYZING WORKING SEARCH FLOW")
        print("="*70)
        
        base = "https://li-public.fmcsa.dot.gov"
        
        # Get search page with hidden fields
        search_url = f"{base}/LIVIEW/pkg_carrquery.prc_carrlist"
        resp = self.session.get(search_url)
        
        if resp.status_code == 200:
            # Method 1: Try as GET with just the USDOT
            print("\n1. Simple GET search...")
            simple_url = f"{search_url}?n_dotno={usdot}"
            resp = self.session.get(simple_url)
            print(f"   Status: {resp.status_code}, Size: {len(resp.text)}")
            
            if str(usdot) in resp.text:
                print("   ✅ Found USDOT in results")
                
                # Extract the activeinsurance URL
                # Pattern 1: Direct href
                pattern1 = rf'href=["\']([^"\']*prc_activeinsurance[^"\']*{usdot}[^"\']*)["\']'
                # Pattern 2: onclick or JavaScript
                pattern2 = rf'(?:onclick|href)=["\'][^"\']*prc_activeinsurance[^"\']*["\']'
                # Pattern 3: Any activeinsurance mention
                pattern3 = r'prc_activeinsurance[^"\'>]*'
                
                for pattern in [pattern1, pattern2, pattern3]:
                    matches = re.findall(pattern, resp.text, re.IGNORECASE)
                    if matches:
                        print(f"   Found insurance links: {matches[:2]}")
                        
                        for match in matches:
                            # Clean and build URL
                            if 'prc_activeinsurance' in match:
                                if match.startswith('http'):
                                    ins_url = match
                                elif match.startswith('/'):
                                    ins_url = base + match
                                else:
                                    ins_url = f"{base}/LIVIEW/{match}"
                                
                                # Clean HTML entities
                                ins_url = ins_url.replace('&amp;', '&')
                                
                                print(f"\n   Testing insurance URL: {ins_url}")
                                ins_resp = self.session.get(ins_url)
                                print(f"   Status: {ins_resp.status_code}, Size: {len(ins_resp.text)}")
                                
                                if ins_resp.status_code == 200 and len(ins_resp.text) > 1000:
                                    return ins_resp.text
            
            # Method 2: POST with form data
            print("\n2. POST search with form data...")
            form_data = {
                'n_dotno': str(usdot),
                'pv_vpath': 'LIVIEW',
                'submit': 'Search'
            }
            
            resp = self.session.post(search_url, data=form_data)
            print(f"   Status: {resp.status_code}, Size: {len(resp.text)}")
            
            if str(usdot) in resp.text:
                print("   ✅ Found USDOT in POST results")
        
        return None
    
    def test_direct_procedures(self, usdot=905413):
        """Test calling Oracle procedures directly"""
        print("\n" + "="*70)
        print("DIRECT ORACLE PROCEDURE TESTING")
        print("="*70)
        
        base = "https://li-public.fmcsa.dot.gov/LIVIEW"
        
        # Common Oracle package.procedure patterns for insurance
        procedures = [
            "pkg_carrquery.prc_activeinsurance",
            "pkg_carrquery.proc_activeinsurance",
            "pkg_carrquery.get_activeinsurance",
            "pkg_carrquery.active_insurance",
            "pkg_carrquery.insurance",
            "pkg_carrier.prc_insurance",
            "pkg_insurance.prc_getactive",
            "pkg_li.prc_getinsurance",
            "pkg_reports.prc_insurance"
        ]
        
        # Test each procedure with different parameter styles
        for proc in procedures:
            url = f"{base}/{proc}"
            print(f"\nTesting procedure: {proc}")
            
            # Test 1: With standard parameter
            test_url = f"{url}?pn_dotno={usdot}"
            resp = self.session.get(test_url)
            print(f"   GET with pn_dotno: {resp.status_code}")
            if resp.status_code == 200 and len(resp.text) > 500:
                print(f"   ✅ Got response: {len(resp.text)} bytes")
                if 'GEICO' in resp.text or 'insurance' in resp.text.lower():
                    return resp.text
            
            # Test 2: With POST
            resp = self.session.post(url, data={'pn_dotno': str(usdot)})
            print(f"   POST with pn_dotno: {resp.status_code}")
            if resp.status_code == 200 and len(resp.text) > 500:
                print(f"   ✅ Got response: {len(resp.text)} bytes")
                if 'GEICO' in resp.text or 'insurance' in resp.text.lower():
                    return resp.text
        
        return None
    
    def research_all(self, usdot=905413):
        """Run all research methods"""
        print("\n" + "="*80)
        print("COMPREHENSIVE L&I SYSTEM RESEARCH")
        print("="*80)
        
        # 1. Analyze Oracle patterns
        self.analyze_oracle_patterns()
        
        # 2. Research session flow
        hidden_fields = self.research_session_flow(usdot)
        
        # 3. Test parameter variations
        result = self.test_parameter_variations(usdot)
        if result:
            self.save_result(result, "param_variation", usdot)
            return result
        
        # 4. Analyze working search
        result = self.analyze_working_search(usdot)
        if result:
            self.save_result(result, "search_flow", usdot)
            return result
        
        # 5. Test direct procedures
        result = self.test_direct_procedures(usdot)
        if result:
            self.save_result(result, "direct_proc", usdot)
            return result
        
        print("\n" + "="*80)
        print("RESEARCH COMPLETE")
        print("="*80)
        return None
    
    def save_result(self, html, method, usdot):
        """Save successful result"""
        filename = f"li_research_{method}_{usdot}.html"
        with open(filename, 'w') as f:
            f.write(html)
        print(f"\n✅ SUCCESS! Saved to {filename}")
        
        # Quick parse
        if 'GEICO' in html:
            print("   Found: GEICO MARINE INSURANCE COMPANY")
        if '91X' in html:
            print("   Found: Form 91X")
        if '1,000,000' in html or '1000000' in html:
            print("   Found: $1,000,000 coverage")

if __name__ == "__main__":
    researcher = LIAdvancedResearch()
    result = researcher.research_all(905413)