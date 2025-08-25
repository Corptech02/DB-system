#!/usr/bin/env python3
"""Test raw fetching to see what we're getting from L&I"""

import requests
import sys

def test_fetch(usdot):
    """Test fetching raw HTML from L&I system"""
    
    print(f"\nTesting USDOT: {usdot}")
    print("="*60)
    
    # Create session with headers
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    })
    
    # Method 1: Direct active insurance URL with USDOT
    url1 = f"https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_activeinsurance?pn_dotno={usdot}"
    print(f"\nTrying: {url1}")
    
    try:
        resp = session.get(url1, timeout=10)
        print(f"Status: {resp.status_code}")
        print(f"Content length: {len(resp.text)}")
        
        # Check if we got insurance data
        if "insurance" in resp.text.lower():
            print("✅ Found 'insurance' in response")
        
        # Save to file for inspection
        with open(f"li_response_{usdot}.html", "w", encoding="utf-8") as f:
            f.write(resp.text)
        print(f"Saved to li_response_{usdot}.html")
        
        # Look for key markers
        if "No Active Insurance" in resp.text:
            print("⚠️ No Active Insurance message found")
        if "Progressive" in resp.text or "Nationwide" in resp.text:
            print("✅ Found insurance company name")
        if "BMC" in resp.text:
            print("✅ Found BMC form reference")
            
    except Exception as e:
        print(f"Error: {e}")
    
    # Method 2: Try the detail endpoint
    url2 = f"https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_getdetail?pn_dotno={usdot}"
    print(f"\nTrying: {url2}")
    
    try:
        resp = session.get(url2, timeout=10)
        print(f"Status: {resp.status_code}")
        print(f"Content length: {len(resp.text)}")
        
        # Save to file
        with open(f"li_detail_{usdot}.html", "w", encoding="utf-8") as f:
            f.write(resp.text)
        print(f"Saved to li_detail_{usdot}.html")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    usdot = int(sys.argv[1]) if len(sys.argv) > 1 else 905413
    test_fetch(usdot)