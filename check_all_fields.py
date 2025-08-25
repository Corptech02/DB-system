#!/usr/bin/env python3
"""Check all available fields in the FMCSA data"""

import json
import os

# Try to load a sample to see all fields
if os.path.exists("all_carriers.json"):
    print("Loading carriers to check fields...")
    with open("all_carriers.json", "r") as f:
        carriers = json.load(f)
    
    if carriers:
        # Get first carrier with data
        sample = carriers[0]
        
        print("\nAll available fields in FMCSA data:")
        print("=" * 60)
        
        for key, value in sorted(sample.items()):
            # Show field name, type, and sample value
            value_type = type(value).__name__
            if isinstance(value, str) and len(value) > 50:
                value = value[:50] + "..."
            print(f"{key:30} | {value_type:10} | {value}")
        
        print("\n" + "=" * 60)
        print(f"Total fields available: {len(sample.keys())}")
        
        # Check a few more carriers to see if some have additional fields
        all_keys = set()
        for carrier in carriers[:100]:  # Check first 100
            all_keys.update(carrier.keys())
        
        print(f"Total unique fields across 100 carriers: {len(all_keys)}")
        
        # Show all unique field names
        print("\nAll unique field names:")
        for key in sorted(all_keys):
            print(f"  - {key}")
else:
    print("all_carriers.json not found!")
    print("Checking for real_carriers_sample.json...")
    
    if os.path.exists("real_carriers_sample.json"):
        with open("real_carriers_sample.json", "r") as f:
            carriers = json.load(f)
        
        if carriers:
            sample = carriers[0]
            print("\nFields in sample data:")
            for key in sorted(sample.keys()):
                print(f"  - {key}")