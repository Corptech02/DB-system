#!/usr/bin/env python3
"""Test POST request to L&I system"""

import requests
import re
import sys

def test_li_post(usdot):
    """Test POST request to search for carrier"""
    
    print(f"\nSearching L&I for USDOT: {usdot}")
    print("="*60)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'https://li-public.fmcsa.dot.gov',
        'Referer': 'https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_carrlist'
    })
    
    # First GET the search page to establish session
    search_page = "https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_carrlist"
    session.get(search_page)
    
    # Now POST the search
    search_url = "https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_carrlist"
    
    # Try different form data combinations
    form_data_options = [
        {
            'n_dotno': str(usdot),
            'pv_vpath': 'LIVIEW',
            'searchtype': 'ANY',
            'submit': 'Search'
        },
        {
            'n_dotno': str(usdot),
            'submit': 'Search'
        },
        {
            'n_dotno': str(usdot),
            'pv_doe_flag': '',
            'pv_vpath': 'LIVIEW'
        }
    ]
    
    for i, form_data in enumerate(form_data_options):
        print(f"\nAttempt {i+1}: {form_data}")
        
        resp = session.post(search_url, data=form_data)
        print(f"Status: {resp.status_code}, Length: {len(resp.text)}")
        
        if resp.status_code == 200 and len(resp.text) > 5000:
            # Save response
            with open(f"li_post_result_{usdot}_{i}.html", "w", encoding="utf-8") as f:
                f.write(resp.text)
            print(f"Saved to li_post_result_{usdot}_{i}.html")
            
            # Check for results
            if "No records found" in resp.text:
                print("❌ No records found message")
            elif str(usdot) in resp.text:
                print(f"✅ Found USDOT {usdot}")
                
                # Look for carrier details link
                detail_pattern = r'<a[^>]*href="([^"]*prc_activeinsurance[^"]*)"[^>]*>'
                detail_links = re.findall(detail_pattern, resp.text, re.IGNORECASE)
                if detail_links:
                    print(f"✅ Found {len(detail_links)} insurance links:")
                    for link in detail_links[:3]:
                        print(f"   {link}")
                        
                        # Try to fetch the insurance page
                        if link.startswith('/'):
                            full_url = f"https://li-public.fmcsa.dot.gov{link}"
                        else:
                            full_url = f"https://li-public.fmcsa.dot.gov/LIVIEW/{link}"
                        
                        print(f"   Fetching: {full_url}")
                        insurance_resp = session.get(full_url)
                        print(f"   Insurance page status: {insurance_resp.status_code}, Length: {len(insurance_resp.text)}")
                        
                        if insurance_resp.status_code == 200:
                            with open(f"li_insurance_{usdot}.html", "w", encoding="utf-8") as f:
                                f.write(insurance_resp.text)
                            print(f"   Saved insurance page to li_insurance_{usdot}.html")
                            
                            # Check for insurance data
                            if "Progressive" in insurance_resp.text or "Nationwide" in insurance_resp.text:
                                print("   ✅ Found insurance company!")
                            
                            return True
                
                # Look for any table with carrier info
                if "<table" in resp.text.lower():
                    tables = resp.text.count("<table")
                    print(f"Found {tables} tables in response")
            
            # Check if it's asking us to search differently
            if "Please enter" in resp.text or "search criteria" in resp.text.lower():
                print("⚠️ Page is asking for search criteria")

if __name__ == "__main__":
    usdot = int(sys.argv[1]) if len(sys.argv) > 1 else 905413
    test_li_post(usdot)