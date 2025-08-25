#!/usr/bin/env python3
"""
L&I Search Results Parser
Parse the search results to find the correct insurance URL pattern
"""

import requests
import re
from urllib.parse import urlencode, unquote
import html

class LISearchParser:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9'
        })
        
    def get_search_results(self, usdot):
        """Get search results page"""
        print(f"\n{'='*70}")
        print(f"GETTING SEARCH RESULTS FOR USDOT: {usdot}")
        print('='*70)
        
        # The search URL that works
        search_url = f"https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_carrlist?n_dotno={usdot}"
        
        print(f"\nFetching: {search_url}")
        resp = self.session.get(search_url)
        
        print(f"Status: {resp.status_code}")
        print(f"Response size: {len(resp.text)} bytes")
        
        if resp.status_code == 200:
            # Save the search results
            with open(f"li_search_{usdot}.html", "w") as f:
                f.write(resp.text)
            print(f"Saved to: li_search_{usdot}.html")
            
            return resp.text
        
        return None
    
    def parse_insurance_links(self, html_content, usdot):
        """Parse all possible insurance link patterns"""
        print(f"\n{'='*70}")
        print("PARSING INSURANCE LINKS")
        print('='*70)
        
        if not html_content:
            return []
        
        links = []
        
        # Pattern 1: Look for "Active Insurance" text and nearby links
        print("\n1. Looking for 'Active Insurance' links...")
        
        # Find all anchor tags
        anchor_pattern = r'<a[^>]*>(.*?)</a>'
        anchors = re.findall(anchor_pattern, html_content, re.IGNORECASE | re.DOTALL)
        
        for i, anchor_text in enumerate(anchors):
            if 'active insurance' in anchor_text.lower():
                print(f"   Found 'Active Insurance' anchor text")
                
                # Get the full anchor tag
                start = html_content.lower().find('<a', html_content.lower().find(anchor_text.lower()) - 200)
                end = html_content.find('</a>', start) + 4
                full_anchor = html_content[start:end]
                
                # Extract href
                href_match = re.search(r'href=["\']([^"\']+)["\']', full_anchor, re.IGNORECASE)
                if href_match:
                    href = href_match.group(1)
                    # Unescape HTML entities
                    href = html.unescape(href)
                    links.append(('href', href))
                    print(f"   Extracted href: {href}")
                
                # Extract onclick
                onclick_match = re.search(r'onclick=["\']([^"\']+)["\']', full_anchor, re.IGNORECASE)
                if onclick_match:
                    onclick = onclick_match.group(1)
                    onclick = html.unescape(onclick)
                    links.append(('onclick', onclick))
                    print(f"   Extracted onclick: {onclick}")
        
        # Pattern 2: Look for pkg_carrquery.prc_activeinsurance references
        print("\n2. Looking for prc_activeinsurance references...")
        
        active_patterns = [
            r'pkg_carrquery\.prc_activeinsurance[^"\'\s>]*',
            r'prc_activeinsurance[^"\'\s>]*',
            r'["\']([^"\']*activeinsurance[^"\']*)["\']'
        ]
        
        for pattern in active_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                if match and 'prc_activeinsurance' in match.lower():
                    match = html.unescape(match)
                    links.append(('pattern', match))
                    print(f"   Found pattern: {match[:100]}")
        
        # Pattern 3: JavaScript function calls
        print("\n3. Looking for JavaScript navigation...")
        
        js_patterns = [
            r'window\.location[.\s]*=[.\s]*["\']([^"\']+activeinsurance[^"\']+)["\']',
            r'document\.location[.\s]*=[.\s]*["\']([^"\']+activeinsurance[^"\']+)["\']',
            r'location\.href[.\s]*=[.\s]*["\']([^"\']+activeinsurance[^"\']+)["\']',
            r'navigate\(["\']([^"\']+activeinsurance[^"\']+)["\']',
            r'open\(["\']([^"\']+activeinsurance[^"\']+)["\']'
        ]
        
        for pattern in js_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                match = html.unescape(match)
                links.append(('javascript', match))
                print(f"   Found JS navigation: {match}")
        
        # Pattern 4: Form submissions
        print("\n4. Looking for form submissions...")
        
        form_pattern = r'<form[^>]*action=["\']([^"\']*activeinsurance[^"\']*)["\']'
        matches = re.findall(form_pattern, html_content, re.IGNORECASE)
        for match in matches:
            match = html.unescape(match)
            links.append(('form', match))
            print(f"   Found form action: {match}")
        
        # Pattern 5: Look specifically around the USDOT number
        print(f"\n5. Looking for links near USDOT {usdot}...")
        
        usdot_index = html_content.find(str(usdot))
        if usdot_index > -1:
            # Get 500 chars before and after
            context = html_content[max(0, usdot_index-500):usdot_index+500]
            
            # Look for any URL-like patterns
            url_patterns = [
                r'href=["\']([^"\']+)["\']',
                r'onclick=["\']([^"\']+)["\']',
                r'action=["\']([^"\']+)["\']'
            ]
            
            for pattern in url_patterns:
                matches = re.findall(pattern, context, re.IGNORECASE)
                for match in matches:
                    if 'insurance' in match.lower() or 'prc_' in match.lower():
                        match = html.unescape(match)
                        links.append(('near_usdot', match))
                        print(f"   Found near USDOT: {match[:100]}")
        
        return links
    
    def test_insurance_urls(self, links, usdot):
        """Test each found link to see if it works"""
        print(f"\n{'='*70}")
        print("TESTING INSURANCE URLS")
        print('='*70)
        
        base_url = "https://li-public.fmcsa.dot.gov"
        tested = set()
        
        for link_type, link_value in links:
            # Build full URL
            if 'pkg_carrquery.prc_activeinsurance' in link_value:
                # It's a procedure call
                if link_value.startswith('http'):
                    test_url = link_value
                elif link_value.startswith('/'):
                    test_url = base_url + link_value
                else:
                    test_url = f"{base_url}/LIVIEW/{link_value}"
            elif link_value.startswith('javascript:'):
                # Extract URL from JavaScript
                continue
            else:
                continue
            
            # Clean URL
            test_url = test_url.replace('&amp;', '&')
            
            # Skip if already tested
            if test_url in tested:
                continue
            tested.add(test_url)
            
            print(f"\nTesting: {test_url}")
            
            try:
                resp = self.session.get(test_url, timeout=10)
                print(f"   Status: {resp.status_code}, Size: {len(resp.text)}")
                
                if resp.status_code == 200:
                    # Check for insurance content
                    content_lower = resp.text.lower()
                    if any(term in content_lower for term in ['insurance', 'liability', 'coverage', 'policy']):
                        print("   ✅ Found insurance content!")
                        
                        # Save successful response
                        with open(f"li_insurance_{usdot}_success.html", "w") as f:
                            f.write(resp.text)
                        print(f"   Saved to: li_insurance_{usdot}_success.html")
                        
                        # Parse insurance data
                        self.parse_insurance_data(resp.text)
                        return test_url
                    elif str(usdot) in resp.text:
                        print("   Found USDOT in response")
                    else:
                        print("   No insurance content found")
            except Exception as e:
                print(f"   Error: {e}")
        
        return None
    
    def parse_insurance_data(self, html_content):
        """Parse insurance data from successful response"""
        print("\n   Parsing insurance data...")
        
        # Look for key insurance information
        if 'GEICO MARINE INSURANCE COMPANY' in html_content:
            print("   ✅ Found: GEICO MARINE INSURANCE COMPANY")
        
        # Look for form types
        form_match = re.search(r'\b(91X|BMC-\d+)\b', html_content)
        if form_match:
            print(f"   ✅ Found form: {form_match.group(1)}")
        
        # Look for policy numbers
        policy_match = re.search(r'\b(93\d{8})\b', html_content)
        if policy_match:
            print(f"   ✅ Found policy: {policy_match.group(1)}")
        
        # Look for amounts
        amount_match = re.search(r'\$([0-9,]+)', html_content)
        if amount_match:
            print(f"   ✅ Found amount: ${amount_match.group(1)}")
        
        # Look for dates
        dates = re.findall(r'\b(\d{1,2}/\d{1,2}/\d{4})\b', html_content)
        if dates:
            print(f"   ✅ Found dates: {dates[:3]}")
    
    def analyze_search(self, usdot=905413):
        """Full analysis of search results"""
        # Get search results
        html_content = self.get_search_results(usdot)
        
        if html_content:
            # Parse insurance links
            links = self.parse_insurance_links(html_content, usdot)
            
            print(f"\nFound {len(links)} potential insurance links")
            
            # Test each link
            if links:
                working_url = self.test_insurance_urls(links, usdot)
                if working_url:
                    print(f"\n✅ SUCCESS! Working URL: {working_url}")
                    return working_url
            
            # If no links found, analyze the HTML structure
            print("\n" + "="*70)
            print("ANALYZING HTML STRUCTURE")
            print("="*70)
            
            # Check if it's a single result that goes directly to detail
            if 'carrier details' in html_content.lower():
                print("   Page shows carrier details directly")
            
            # Check for frames or iframes
            if '<iframe' in html_content.lower() or '<frame' in html_content.lower():
                print("   Page uses frames/iframes")
            
            # Check for AJAX indicators
            if 'xmlhttprequest' in html_content.lower() or 'ajax' in html_content.lower():
                print("   Page uses AJAX for loading")
            
            # Extract visible text around "Active Insurance"
            if 'active insurance' in html_content.lower():
                idx = html_content.lower().find('active insurance')
                context = html_content[max(0, idx-200):idx+200]
                # Remove HTML tags for readability
                text = re.sub(r'<[^>]+>', ' ', context)
                text = ' '.join(text.split())
                print(f"\n   Context around 'Active Insurance':\n   {text}")
        
        return None

if __name__ == "__main__":
    parser = LISearchParser()
    result = parser.analyze_search(905413)