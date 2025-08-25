#!/usr/bin/env python3
"""Test insurance fetching to diagnose issues"""

import sys
import traceback
from fmcsa_li_insurance_api import get_real_insurance

def test_insurance_fetch(usdot_number):
    print(f"\n{'='*60}")
    print(f"Testing insurance fetch for USDOT: {usdot_number}")
    print('='*60)
    
    try:
        result = get_real_insurance(usdot_number)
        print(f"Result: {result}")
        
        if result.get('success'):
            print("✅ SUCCESS - Got insurance data!")
            print(f"  Company: {result.get('insurance_company')}")
            print(f"  Expiry: {result.get('liability_insurance_date')}")
            print(f"  Source: {result.get('source')}")
        else:
            print("❌ FAILED - No insurance data returned")
            print(f"  Error: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        print(f"Full traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    # Test with a known carrier
    test_usdot = int(sys.argv[1]) if len(sys.argv) > 1 else 80321  # FedEx
    test_insurance_fetch(test_usdot)