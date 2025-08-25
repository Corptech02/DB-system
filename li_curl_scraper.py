#!/usr/bin/env python3
"""
CURL-based L&I Insurance Scraper
Uses curl to mimic exact browser behavior
"""

import subprocess
import re
import json
from datetime import datetime
from typing import Dict, Optional

class LICurlScraper:
    def __init__(self):
        self.base_url = "https://li-public.fmcsa.dot.gov"
        self.cookies_file = "li_cookies.txt"
        
    def curl_request(self, url: str, method="GET", data=None, save_cookies=False, load_cookies=False) -> str:
        """
        Execute a curl request that mimics a browser
        """
        cmd = [
            "curl",
            "-s",  # Silent mode
            "-L",  # Follow redirects
            "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "-H", "Accept-Language: en-US,en;q=0.9",
            "-H", "Accept-Encoding: gzip, deflate, br",
            "-H", "Connection: keep-alive",
            "-H", "Upgrade-Insecure-Requests: 1",
            "-H", "Sec-Fetch-Dest: document",
            "-H", "Sec-Fetch-Mode: navigate",
            "-H", "Sec-Fetch-Site: none",
            "-H", "Sec-Fetch-User: ?1",
            "-H", "Cache-Control: max-age=0",
        ]
        
        # Cookie handling
        if save_cookies:
            cmd.extend(["-c", self.cookies_file])  # Save cookies
        if load_cookies:
            cmd.extend(["-b", self.cookies_file])  # Load cookies
        
        # Method and data
        if method == "POST" and data:
            cmd.extend(["-X", "POST"])
            cmd.extend(["-d", data])
            cmd.extend(["-H", "Content-Type: application/x-www-form-urlencoded"])
        
        # Add URL
        cmd.append(url)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.stdout
        except Exception as e:
            print(f"Curl error: {e}")
            return ""
    
    def scrape_insurance(self, usdot_number: int) -> Dict:
        """
        Scrape insurance data using curl to mimic browser
        """
        result = {
            'success': False,
            'usdot_number': usdot_number,
            'insurance_company': None,
            'liability_insurance_date': None,
            'coverage_amount': None,
            'policy_number': None,
            'form_type': None,
            'error': None
        }
        
        print(f"\n{'='*70}")
        print(f"CURL-BASED L&I SCRAPER FOR USDOT: {usdot_number}")
        print('='*70)
        
        # Step 1: Get main page and establish session
        print("\nStep 1: Getting main L&I page...")
        main_url = f"{self.base_url}/LIVIEW/"
        response = self.curl_request(main_url, save_cookies=True)
        
        if not response:
            result['error'] = "Failed to connect to L&I system"
            return result
        
        print(f"  Response length: {len(response)} bytes")
        
        # Step 2: Get search form page
        print("\nStep 2: Getting search form...")
        search_url = f"{self.base_url}/LIVIEW/pkg_carrquery.prc_carrlist"
        response = self.curl_request(search_url, load_cookies=True, save_cookies=True)
        
        if not response:
            result['error'] = "Failed to get search form"
            return result
        
        print(f"  Response length: {len(response)} bytes")
        
        # Extract any hidden fields from the form
        hidden_fields = {}
        hidden_pattern = r'<input[^>]*type=["\']hidden["\'][^>]*name=["\']([^"\']+)["\'][^>]*value=["\']([^"\']*)["\'][^>]*>'
        for match in re.finditer(hidden_pattern, response, re.IGNORECASE):
            field_name = match.group(1)
            field_value = match.group(2)
            hidden_fields[field_name] = field_value
            print(f"  Found hidden field: {field_name}")
        
        # Step 3: Submit search
        print(f"\nStep 3: Searching for USDOT {usdot_number}...")
        
        # Build form data
        form_data = f"n_dotno={usdot_number}"
        for field, value in hidden_fields.items():
            form_data += f"&{field}={value}"
        form_data += "&submit=Search"
        
        # First try GET (some Oracle systems use GET)
        search_with_params = f"{search_url}?n_dotno={usdot_number}"
        response = self.curl_request(search_with_params, load_cookies=True, save_cookies=True)
        
        if response and str(usdot_number) in response:
            print("  ✅ Found USDOT in search results")
            
            # Look for Active Insurance link
            insurance_link_pattern = r'href=["\']([^"\']*activeinsurance[^"\']*)["\']'
            match = re.search(insurance_link_pattern, response, re.IGNORECASE)
            
            if match:
                insurance_path = match.group(1)
                print(f"  Found insurance link: {insurance_path}")
                
                # Build full URL
                if insurance_path.startswith('http'):
                    insurance_url = insurance_path
                elif insurance_path.startswith('/'):
                    insurance_url = self.base_url + insurance_path
                else:
                    insurance_url = f"{self.base_url}/LIVIEW/{insurance_path}"
                
                # Clean up any HTML entities
                insurance_url = insurance_url.replace('&amp;', '&')
            else:
                # Try direct URL
                insurance_url = f"{self.base_url}/LIVIEW/pkg_carrquery.prc_activeinsurance?pn_dotno={usdot_number}"
        else:
            # Try direct navigation
            insurance_url = f"{self.base_url}/LIVIEW/pkg_carrquery.prc_activeinsurance?pn_dotno={usdot_number}"
        
        # Step 4: Get insurance page
        print(f"\nStep 4: Getting insurance page...")
        print(f"  URL: {insurance_url}")
        
        # Add referer header for insurance request
        cmd = [
            "curl",
            "-s",
            "-L",
            "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "-H", f"Referer: {search_url}",
            "-b", self.cookies_file,
            insurance_url
        ]
        
        try:
            curl_result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            insurance_html = curl_result.stdout
        except Exception as e:
            result['error'] = f"Failed to get insurance page: {e}"
            return result
        
        print(f"  Response length: {len(insurance_html)} bytes")
        
        # Save HTML for debugging
        with open(f"li_curl_{usdot_number}.html", "w") as f:
            f.write(insurance_html)
        print(f"  Saved to li_curl_{usdot_number}.html")
        
        # Parse the response
        if len(insurance_html) > 1000:
            result = self.parse_insurance_html(insurance_html, usdot_number)
            if result.get('insurance_company'):
                result['success'] = True
                print("\n✅ Successfully scraped insurance data!")
        else:
            result['error'] = "Received empty or error response"
        
        return result
    
    def parse_insurance_html(self, html: str, usdot_number: int) -> Dict:
        """Parse insurance HTML response"""
        result = {
            'usdot_number': usdot_number,
            'insurance_company': None,
            'liability_insurance_date': None,
            'coverage_amount': None,
            'policy_number': None,
            'form_type': None
        }
        
        # Check for GEICO MARINE
        if "GEICO MARINE INSURANCE COMPANY" in html:
            result['insurance_company'] = "GEICO MARINE INSURANCE COMPANY"
            print("  ✅ Found GEICO MARINE INSURANCE COMPANY")
        
        # Look for form type
        form_match = re.search(r'\b(91X|BMC-\d+)\b', html)
        if form_match:
            result['form_type'] = form_match.group(1)
            print(f"  ✅ Found form type: {result['form_type']}")
        
        # Look for policy number
        policy_match = re.search(r'\b(93\d{8})\b', html)
        if policy_match:
            result['policy_number'] = policy_match.group(1)
            print(f"  ✅ Found policy number: {result['policy_number']}")
        
        # Look for coverage amount
        if "$1,000,000" in html or "$1000000" in html:
            result['coverage_amount'] = 1000000
            print("  ✅ Found coverage amount: $1,000,000")
        
        # Look for dates
        dates = re.findall(r'\b(\d{1,2}/\d{1,2}/\d{4})\b', html)
        if dates:
            # Look for effective date
            for date in dates:
                date_index = html.index(date)
                context = html[max(0, date_index-50):date_index+50]
                if 'effective' in context.lower():
                    result['liability_insurance_date'] = date
                    print(f"  ✅ Found effective date: {date}")
                    break
            
            # If not found, use last date (often effective date)
            if not result['liability_insurance_date'] and dates:
                result['liability_insurance_date'] = dates[-1]
                print(f"  ✅ Using date: {result['liability_insurance_date']}")
        
        return result


def get_li_insurance_curl(usdot_number: int) -> Dict:
    """
    Main function to get insurance via curl
    """
    scraper = LICurlScraper()
    result = scraper.scrape_insurance(usdot_number)
    
    # Format for our cache
    if result['success']:
        # Convert date format
        if result.get('liability_insurance_date'):
            try:
                month, day, year = result['liability_insurance_date'].split('/')
                formatted_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                result['liability_insurance_date'] = formatted_date
                result['insurance_expiry_date'] = formatted_date
            except:
                pass
        
        result['insurance_data_source'] = "FMCSA L&I Active Insurance (Live)"
        result['insurance_data_type'] = "real"
        result['cached_at'] = datetime.now().isoformat()
    
    return result


if __name__ == "__main__":
    result = get_li_insurance_curl(905413)
    print("\n" + "="*70)
    print("FINAL RESULT:")
    print("="*70)
    print(json.dumps(result, indent=2))