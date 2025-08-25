#!/usr/bin/env python3
"""Inspect actual carrier data to see what fields have values"""

import json
import os
from collections import Counter

def analyze_carriers():
    if os.path.exists("all_carriers.json"):
        print("Loading carrier data...")
        with open("all_carriers.json", "r") as f:
            carriers = json.load(f)
        
        print(f"Total carriers: {len(carriers):,}")
        
        # Analyze first 1000 carriers
        sample = carriers[:1000]
        
        # Count how many carriers have each field populated
        field_population = Counter()
        field_examples = {}
        
        for carrier in sample:
            for field, value in carrier.items():
                if value and str(value).strip() and str(value) not in ['', 'None', 'null', '0']:
                    field_population[field] += 1
                    if field not in field_examples:
                        field_examples[field] = []
                    if len(field_examples[field]) < 3:
                        field_examples[field].append(str(value)[:100])
        
        print("\n" + "="*80)
        print("FIELD POPULATION ANALYSIS (out of 1000 carriers)")
        print("="*80)
        
        # Sort by population count
        sorted_fields = sorted(field_population.items(), key=lambda x: x[1], reverse=True)
        
        for field, count in sorted_fields:
            percentage = (count / 1000) * 100
            examples = field_examples.get(field, [])
            example_str = " | ".join(examples[:2])
            if len(example_str) > 50:
                example_str = example_str[:50] + "..."
            
            print(f"{field:35} {count:4}/{1000} ({percentage:5.1f}%) Ex: {example_str}")
        
        print("\n" + "="*80)
        print("SAMPLE COMPLETE CARRIER RECORD")
        print("="*80)
        
        # Find a carrier with lots of data
        best_carrier = None
        max_fields = 0
        
        for carrier in sample:
            populated_fields = sum(1 for v in carrier.values() if v and str(v).strip() and str(v) not in ['', 'None', 'null', '0'])
            if populated_fields > max_fields:
                max_fields = populated_fields
                best_carrier = carrier
        
        if best_carrier:
            print(f"\nCarrier with most populated fields ({max_fields} fields):")
            print(f"Name: {best_carrier.get('legal_name', 'Unknown')}")
            print(f"USDOT: {best_carrier.get('dot_number', 'Unknown')}")
            print("\nAll fields with values:")
            
            for field, value in sorted(best_carrier.items()):
                if value and str(value).strip() and str(value) not in ['', 'None', 'null']:
                    print(f"  {field:35} = {str(value)[:100]}")
        
        # Check specific important fields
        print("\n" + "="*80)
        print("KEY FIELD MAPPINGS")
        print("="*80)
        
        key_mappings = {
            "USDOT Number": ["dot_number", "usdot_number"],
            "Legal Name": ["legal_name"],
            "DBA Name": ["dba_name"],
            "Phone": ["phone", "telephone"],
            "Cell Phone": ["cell_phone"],
            "Email": ["email_address", "email"],
            "Power Units": ["power_units", "nbr_power_unit"],
            "Drivers": ["total_drivers", "driver_total"],
            "Physical Address": ["phy_street", "physical_address"],
            "Physical City": ["phy_city", "physical_city"],
            "Physical State": ["phy_state", "physical_state"],
            "Physical ZIP": ["phy_zip", "physical_zip"],
            "Operating Status": ["operating_status", "status_code"],
            "Entity Type": ["entity_type", "carship"],
            "Safety Rating": ["safety_rating"],
            "MCS-150 Date": ["mcs150_date", "mcs_150_date"],
            "HazMat": ["hm_flag", "hm_ind"],
        }
        
        print("\nChecking key field availability:")
        for display_name, field_names in key_mappings.items():
            found_count = 0
            for field in field_names:
                if field in field_population:
                    found_count = field_population[field]
                    break
            percentage = (found_count / 1000) * 100
            status = "✅" if percentage > 50 else "⚠️" if percentage > 10 else "❌"
            print(f"{status} {display_name:25} {found_count:4}/{1000} ({percentage:5.1f}%)")
            
    else:
        print("all_carriers.json not found!")

if __name__ == "__main__":
    analyze_carriers()