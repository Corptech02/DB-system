#!/usr/bin/env python3
"""
Script to manually update insurance cache with correct data from L&I system
Run this after checking the L&I website manually
"""

import json
from datetime import datetime

def update_insurance_for_carrier(usdot_number, insurance_company, effective_date, coverage_amount=None):
    """Update the insurance cache with correct data"""
    
    # Load existing cache
    try:
        with open('insurance_cache.json', 'r') as f:
            cache = json.load(f)
    except:
        cache = {}
    
    # Update with correct data
    cache[str(usdot_number)] = {
        "insurance_company": insurance_company,
        "liability_insurance_date": effective_date,  # This should be the EFFECTIVE date from L&I
        "insurance_expiry_date": effective_date,     # Same as above
        "liability_insurance_amount": coverage_amount,
        "insurance_data_source": "FMCSA L&I System (Active Insurance)",
        "insurance_data_type": "real",
        "cached_at": datetime.now().isoformat()
    }
    
    # Save updated cache
    with open('insurance_cache.json', 'w') as f:
        json.dump(cache, f, indent=2)
    
    print(f"✅ Updated insurance cache for USDOT {usdot_number}")
    print(f"   Company: {insurance_company}")
    print(f"   Effective Date: {effective_date}")
    print(f"   Amount: ${coverage_amount:,}" if coverage_amount else "   Amount: Not specified")

if __name__ == "__main__":
    # EXAMPLE - Replace with actual data from L&I website
    # Format date as YYYY-MM-DD
    
    print("Manual Insurance Cache Updater")
    print("="*50)
    print("Please check https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_activeinsurance")
    print("And enter the correct data below:\n")
    
    usdot = input("USDOT Number: ").strip()
    company = input("Insurance Company Name (exactly as shown): ").strip()
    date_str = input("Effective Date (MM/DD/YYYY): ").strip()
    amount_str = input("Coverage Amount (or press Enter if not shown): ").strip()
    
    # Convert date format
    if date_str:
        try:
            month, day, year = date_str.split('/')
            effective_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        except:
            print("Invalid date format. Using as-is.")
            effective_date = date_str
    else:
        effective_date = None
    
    # Convert amount
    if amount_str:
        # Remove $ and commas
        amount_str = amount_str.replace('$', '').replace(',', '')
        try:
            amount = float(amount_str)
        except:
            amount = None
    else:
        amount = None
    
    if usdot and company and effective_date:
        update_insurance_for_carrier(int(usdot), company, effective_date, amount)
    else:
        print("❌ Missing required information")