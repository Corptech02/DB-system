#!/usr/bin/env python3
"""
L&I Form Submitter
Properly submit the search form to get results
"""

import requests
import re
from urllib.parse import urlencode
import html

class LIFormSubmitter:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        self.base_url = "https://li-public.fmcsa.dot.gov"
    
    def submit_search(self, usdot):
        """Submit the search form properly"""
        print(f"\n{'='*70}")
        print(f"SUBMITTING SEARCH FORM FOR USDOT: {usdot}")
        print('='*70)
        
        # Step 1: Get the search form page to extract hidden fields
        search_url = f"{self.base_url}/LIVIEW/pkg_carrquery.prc_carrlist"
        
        print("\n1. Getting search form...")
        resp = self.session.get(search_url)
        print(f"   Status: {resp.status_code}")
        
        # Extract the form action URL
        form_action_match = re.search(r'<form[^>]*name="searchform"[^>]*action="([^"]+)"', resp.text, re.IGNORECASE)
        if not form_action_match:
            # Try alternative form patterns
            form_action_match = re.search(r'<form[^>]*action="([^"]+)"[^>]*name="searchform"', resp.text, re.IGNORECASE)
        
        if form_action_match:
            form_action = form_action_match.group(1)
            print(f"   Form action: {form_action}")
        else:
            # Default form action
            form_action = "/LIVIEW/pkg_carrquery.prc_carrlist"
            print(f"   Using default form action: {form_action}")
        
        # Build full action URL
        if form_action.startswith('/'):
            form_action_url = self.base_url + form_action
        else:
            form_action_url = self.base_url + '/LIVIEW/' + form_action
        
        # Extract all hidden fields
        hidden_fields = {}
        hidden_pattern = r'<input[^>]*type=["\']hidden["\'][^>]*>'
        for match in re.finditer(hidden_pattern, resp.text, re.IGNORECASE):
            field_html = match.group(0)
            name_match = re.search(r'name=["\']([^"\']+)["\']', field_html)
            value_match = re.search(r'value=["\']([^"\']*)["\']', field_html)
            if name_match:
                name = name_match.group(1)
                value = value_match.group(1) if value_match else ''
                hidden_fields[name] = value
        
        print(f"   Found {len(hidden_fields)} hidden fields: {list(hidden_fields.keys())}")
        
        # Step 2: Submit the form with POST
        print("\n2. Submitting search with POST...")
        
        # Build form data
        form_data = {
            'n_dotno': str(usdot),
            'n_docketno': '',
            's_legalname': '',
            's_dbaname': '',
            's_state': '~~',
            **hidden_fields  # Include hidden fields
        }
        
        # Add referer header
        self.session.headers['Referer'] = search_url
        
        # Submit the form
        resp = self.session.post(form_action_url, data=form_data)
        print(f"   Status: {resp.status_code}")
        print(f"   Response size: {len(resp.text)} bytes")
        
        # Check if we got results
        if str(usdot) in resp.text and 'carrier details' in resp.text.lower():
            print("   ✅ Got carrier details!")
            
            # Save the response
            with open(f"li_carrier_{usdot}.html", "w") as f:
                f.write(resp.text)
            print(f"   Saved to: li_carrier_{usdot}.html")
            
            # Parse for insurance link
            return self.extract_insurance_url(resp.text, usdot)
        
        # Step 3: Try alternative submission methods
        print("\n3. Trying alternative submission...")
        
        # Method A: Submit to pkg_carrquery.prc_carrlist directly
        alt_url = f"{self.base_url}/LIVIEW/pkg_carrquery.prc_carrlist"
        
        # Minimal form data
        min_data = {
            'n_dotno': str(usdot)
        }
        
        resp = self.session.post(alt_url, data=min_data)
        print(f"   Direct POST status: {resp.status_code}")
        
        if str(usdot) in resp.text:
            print("   Found USDOT in response")
            return self.extract_insurance_url(resp.text, usdot)
        
        # Method B: Try as GET with all parameters
        get_params = {
            'n_dotno': str(usdot),
            'pv_vpath': 'LIVIEW'
        }
        
        get_url = f"{alt_url}?{urlencode(get_params)}"
        resp = self.session.get(get_url)
        print(f"   GET with params status: {resp.status_code}")
        
        if str(usdot) in resp.text:
            print("   Found USDOT in GET response")
            
            with open(f"li_search_get_{usdot}.html", "w") as f:
                f.write(resp.text)
            
            return self.extract_insurance_url(resp.text, usdot)
        
        return None
    
    def extract_insurance_url(self, html_content, usdot):
        """Extract the insurance URL from carrier details"""
        print("\n4. Extracting insurance URL...")
        
        # Look for Active Insurance link
        patterns = [
            # Pattern 1: Direct link
            r'<a[^>]*href=["\']([^"\']*activeinsurance[^"\']*)["\'][^>]*>',
            # Pattern 2: Link with onclick
            r'<a[^>]*onclick=["\']window\.open\(["\']([^"\']*activeinsurance[^"\']*)["\']',
            # Pattern 3: Any activeinsurance URL
            r'["\']([^"\']*pkg_carrquery\.prc_activeinsurance[^"\']*)["\']',
            # Pattern 4: JavaScript navigation
            r'location\.href\s*=\s*["\']([^"\']*activeinsurance[^"\']*)["\']'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            if matches:
                for match in matches:
                    # Clean the URL
                    url = html.unescape(match)
                    
                    # Check if it contains the USDOT
                    if str(usdot) in url or 'pn_dotno' in url:
                        print(f"   ✅ Found insurance URL: {url}")
                        
                        # Build full URL
                        if url.startswith('http'):
                            full_url = url
                        elif url.startswith('/'):
                            full_url = self.base_url + url
                        else:
                            full_url = f"{self.base_url}/LIVIEW/{url}"
                        
                        # Test the URL
                        return self.test_insurance_url(full_url, usdot)
        
        # If no direct link, try to construct it
        print("\n5. Constructing insurance URL...")
        
        # Standard insurance URL format
        insurance_url = f"{self.base_url}/LIVIEW/pkg_carrquery.prc_activeinsurance?pn_dotno={usdot}"
        
        return self.test_insurance_url(insurance_url, usdot)
    
    def test_insurance_url(self, url, usdot):
        """Test if the insurance URL works"""
        print(f"\n6. Testing insurance URL: {url}")
        
        # Add referer from search results
        self.session.headers['Referer'] = f"{self.base_url}/LIVIEW/pkg_carrquery.prc_carrlist"
        
        resp = self.session.get(url)
        print(f"   Status: {resp.status_code}")
        print(f"   Response size: {len(resp.text)} bytes")
        
        if resp.status_code == 200:
            # Check for insurance content
            content_lower = resp.text.lower()
            
            if 'insurance' in content_lower or 'liability' in content_lower:
                print("   ✅ Found insurance content!")
                
                # Save the response
                with open(f"li_insurance_{usdot}.html", "w") as f:
                    f.write(resp.text)
                print(f"   Saved to: li_insurance_{usdot}.html")
                
                # Parse insurance data
                self.parse_insurance_data(resp.text)
                
                return url
            elif str(usdot) in resp.text:
                print("   Found USDOT but no insurance keywords")
                
                # Save anyway for inspection
                with open(f"li_insurance_attempt_{usdot}.html", "w") as f:
                    f.write(resp.text)
                
                return url
        
        return None
    
    def parse_insurance_data(self, html_content):
        """Parse insurance data from the response"""
        print("\n7. Parsing insurance data...")
        
        # Key patterns to look for
        if 'GEICO MARINE INSURANCE COMPANY' in html_content:
            print("   ✅ Found: GEICO MARINE INSURANCE COMPANY")
        
        # Form type
        form_match = re.search(r'\b(91X|BMC-\d+)\b', html_content)
        if form_match:
            print(f"   ✅ Found form: {form_match.group(1)}")
        
        # Policy number
        policy_match = re.search(r'\b(93\d{8}|90\d{8})\b', html_content)
        if policy_match:
            print(f"   ✅ Found policy: {policy_match.group(1)}")
        
        # Coverage amount
        amount_patterns = [
            r'\$\s*1,000,000',
            r'\$\s*1000000',
            r'\$\s*([0-9,]+)'
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, html_content)
            if match:
                print(f"   ✅ Found coverage: {match.group(0)}")
                break
        
        # Dates
        dates = re.findall(r'\b(\d{1,2}/\d{1,2}/\d{4})\b', html_content)
        if dates:
            print(f"   ✅ Found dates: {dates[:3]}")
            
            # Look for effective date
            for date in dates:
                idx = html_content.find(date)
                context = html_content[max(0, idx-50):idx].lower()
                if 'effective' in context or 'eff' in context:
                    print(f"   ✅ Effective date: {date}")
                    break

if __name__ == "__main__":
    submitter = LIFormSubmitter()
    result = submitter.submit_search(905413)
    
    if result:
        print(f"\n{'='*70}")
        print(f"✅ SUCCESS! Working insurance URL: {result}")
        print('='*70)
    else:
        print(f"\n{'='*70}")
        print("❌ Could not find working insurance URL")
        print('='*70)