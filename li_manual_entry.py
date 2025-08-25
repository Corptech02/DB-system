#!/usr/bin/env python3
"""
Manual L&I Insurance Data Entry System
Since the L&I system requires JavaScript and cannot be scraped programmatically,
this provides a way to manually add insurance data from the L&I website.
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional

CACHE_FILE = "li_insurance_cache.json"

def load_cache() -> Dict:
    """Load existing cache"""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_cache(cache: Dict):
    """Save cache to file"""
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)

def parse_li_text(text: str) -> Dict:
    """
    Parse copy-pasted text from L&I website
    Expected format from the table:
    91X    BIPD/Primary    GEICO MARINE INSURANCE COMPANY    9300107451    01/27/2025    $0    $1,000,000    02/20/2024
    """
    import re
    
    result = {
        'insurance_company': None,
        'form_type': None,
        'policy_number': None,
        'coverage_amount': None,
        'liability_insurance_date': None,
        'posted_date': None
    }
    
    # Split by tabs or multiple spaces
    parts = re.split(r'\t+|\s{2,}', text.strip())
    
    if len(parts) >= 8:
        # Standard format: Form | Type | Company | Policy | Posted | From | To | Effective
        result['form_type'] = parts[0]
        result['insurance_company'] = parts[2]
        result['policy_number'] = parts[3]
        result['posted_date'] = parts[4]
        
        # Parse coverage amount (usually in parts[6])
        coverage = parts[6].replace('$', '').replace(',', '')
        try:
            result['coverage_amount'] = int(coverage)
        except:
            pass
        
        # Effective date is usually parts[7]
        result['liability_insurance_date'] = parts[7]
    
    return result

def manual_entry():
    """Interactive manual entry system"""
    print("="*70)
    print("L&I INSURANCE MANUAL ENTRY SYSTEM")
    print("="*70)
    print("\nSince the L&I system requires JavaScript, insurance data must be")
    print("entered manually. Please follow these steps:\n")
    
    print("1. Open your browser and go to:")
    print("   https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_carrlist\n")
    
    print("2. Enter the USDOT number and click Search\n")
    
    print("3. Click on 'Active Insurance' link\n")
    
    print("4. Copy the insurance table row data\n")
    
    print("-"*70)
    
    usdot = input("\nEnter USDOT number: ").strip()
    
    if not usdot.isdigit():
        print("❌ Invalid USDOT number")
        return
    
    print(f"\nNow viewing: https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_activeinsurance?pn_dotno={usdot}")
    print("\nPaste the insurance table row (or type 'manual' to enter fields individually):")
    
    table_data = input("> ").strip()
    
    if table_data.lower() == 'manual':
        # Manual field entry
        data = {
            'insurance_company': input("Insurance Company: ").strip(),
            'form_type': input("Form Type (e.g., 91X): ").strip(),
            'policy_number': input("Policy Number: ").strip(),
            'coverage_amount': input("Coverage Amount (number only): ").strip(),
            'liability_insurance_date': input("Effective Date (MM/DD/YYYY): ").strip()
        }
        
        # Convert coverage amount to int
        try:
            data['coverage_amount'] = int(data['coverage_amount'].replace(',', ''))
        except:
            pass
    else:
        # Parse pasted data
        data = parse_li_text(table_data)
        
        if not data['insurance_company']:
            print("\n⚠️  Could not parse data. Trying manual parsing...")
            print("Example format: 91X    BIPD/Primary    GEICO MARINE INSURANCE COMPANY    9300107451    01/27/2025    $0    $1,000,000    02/20/2024")
            return
    
    # Format date
    if data.get('liability_insurance_date'):
        try:
            month, day, year = data['liability_insurance_date'].split('/')
            data['liability_insurance_date'] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            data['insurance_expiry_date'] = data['liability_insurance_date']
        except:
            pass
    
    # Add metadata
    data['insurance_data_source'] = "FMCSA L&I Active Insurance (Manual Entry)"
    data['insurance_data_type'] = "real"
    data['cached_at'] = datetime.now().isoformat()
    data['usdot_number'] = int(usdot)
    
    # Save to cache
    cache = load_cache()
    cache[usdot] = data
    save_cache(cache)
    
    print("\n✅ Insurance data saved successfully!")
    print("\nSaved data:")
    print(json.dumps(data, indent=2))
    
    # Ask if want to add more
    another = input("\nAdd another USDOT? (y/n): ").strip().lower()
    if another == 'y':
        manual_entry()

def batch_import():
    """Import multiple entries from a CSV file"""
    print("="*70)
    print("BATCH IMPORT FROM CSV")
    print("="*70)
    print("\nExpected CSV format:")
    print("USDOT,Company,FormType,PolicyNumber,Coverage,EffectiveDate")
    print("905413,GEICO MARINE INSURANCE COMPANY,91X,9300107451,1000000,02/20/2024")
    print()
    
    filename = input("Enter CSV filename: ").strip()
    
    if not os.path.exists(filename):
        print(f"❌ File not found: {filename}")
        return
    
    import csv
    cache = load_cache()
    count = 0
    
    with open(filename, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            usdot = row.get('USDOT', '').strip()
            if not usdot:
                continue
            
            # Format date
            date_str = row.get('EffectiveDate', '')
            if date_str:
                try:
                    month, day, year = date_str.split('/')
                    formatted_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                except:
                    formatted_date = date_str
            else:
                formatted_date = None
            
            # Build entry
            data = {
                'insurance_company': row.get('Company', ''),
                'form_type': row.get('FormType', ''),
                'policy_number': row.get('PolicyNumber', ''),
                'coverage_amount': int(row.get('Coverage', 0)),
                'liability_insurance_date': formatted_date,
                'insurance_expiry_date': formatted_date,
                'insurance_data_source': "FMCSA L&I Active Insurance (Batch Import)",
                'insurance_data_type': "real",
                'cached_at': datetime.now().isoformat(),
                'usdot_number': int(usdot)
            }
            
            cache[usdot] = data
            count += 1
            print(f"  Added USDOT {usdot}")
    
    save_cache(cache)
    print(f"\n✅ Imported {count} insurance records")

if __name__ == "__main__":
    print("\nL&I INSURANCE DATA MANAGEMENT")
    print("="*50)
    print("\nThe L&I system requires JavaScript and cannot be")
    print("scraped programmatically. Use these tools to manage")
    print("insurance data manually.\n")
    
    print("1. Manual entry (one at a time)")
    print("2. Batch import from CSV")
    print("3. View cache")
    print("4. Exit")
    
    choice = input("\nChoice (1-4): ").strip()
    
    if choice == '1':
        manual_entry()
    elif choice == '2':
        batch_import()
    elif choice == '3':
        cache = load_cache()
        print(f"\nCache contains {len(cache)} entries:")
        for usdot, data in cache.items():
            print(f"  USDOT {usdot}: {data.get('insurance_company', 'Unknown')}")
    else:
        print("Goodbye!")