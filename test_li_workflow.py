#!/usr/bin/env python3
"""Test the proper L&I workflow"""

import requests
import re
import sys
from urllib.parse import urlencode

def test_li_workflow(usdot):
    """Test the L&I system workflow"""
    
    print(f"\nTesting L&I Workflow for USDOT: {usdot}")
    print("="*60)
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://li-public.fmcsa.dot.gov/'
    })
    
    # Step 1: Go to the main search page
    search_page = "https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_carrlist"
    print(f"\n1. Getting search page: {search_page}")
    
    resp = session.get(search_page)
    print(f"   Status: {resp.status_code}")
    
    # Step 2: Search for the carrier
    print(f"\n2. Searching for USDOT {usdot}...")
    
    # Try different parameter names based on what the form might expect
    search_params = [
        {'pn_dotno': str(usdot)},
        {'n_dotno': str(usdot)},
        {'p_USDOT': str(usdot)},
        {'p_usdot_number': str(usdot)},
    ]
    
    for params in search_params:
        print(f"   Trying params: {params}")
        search_url = f"https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_carrlist?{urlencode(params)}"
        
        resp = session.get(search_url)
        print(f"   Status: {resp.status_code}, Length: {len(resp.text)}")
        
        if resp.status_code == 200 and len(resp.text) > 1000:
            # Save the response
            with open(f"li_search_{usdot}.html", "w", encoding="utf-8") as f:
                f.write(resp.text)
            print(f"   Saved to li_search_{usdot}.html")
            
            # Check for carrier in results
            if str(usdot) in resp.text:
                print(f"   ✅ Found USDOT {usdot} in response")
                
                # Look for links to details/insurance
                links = re.findall(r'href="([^"]*(?:activeinsurance|getdetail)[^"]*)"', resp.text, re.IGNORECASE)
                if links:
                    print(f"   Found {len(links)} detail links")
                    for link in links[:3]:
                        print(f"     - {link}")
                
                # Extract any visible insurance info
                if "Progressive" in resp.text or "Nationwide" in resp.text:
                    print("   ✅ Found insurance company names")
                
                # Look for insurance-related text
                insurance_mentions = len(re.findall(r'insurance|liability|cargo|bond', resp.text, re.IGNORECASE))
                print(f"   Found {insurance_mentions} insurance-related mentions")
                
                return resp.text
    
    return None

if __name__ == "__main__":
    usdot = int(sys.argv[1]) if len(sys.argv) > 1 else 905413
    test_li_workflow(usdot)