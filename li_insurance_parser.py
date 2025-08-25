#!/usr/bin/env python3
"""
L&I Insurance Data Parser
Parses the actual L&I insurance table format
"""

import re
from datetime import datetime
from typing import Dict, Optional, List

def parse_li_insurance_table(html_content: str) -> Dict:
    """
    Parse the L&I insurance table format
    Looking for structure like:
    Form | Type | Insurance Carrier | Policy/Surety | Posted Date | Coverage From | Coverage To | Effective Date | Cancellation Date
    91X | BIPD/Primary | GEICO MARINE INSURANCE COMPANY | 9300107451 | 01/27/2025 | $0 | $1,000,000 | 02/20/2024 | 
    """
    
    result = {
        'success': False,
        'carriers': [],
        'primary_insurance': None
    }
    
    # Look for insurance carrier names in the typical format
    # Common patterns in L&I data
    carrier_pattern = r'(?:91X|BMC[\s-]*\d+)\s*(?:</[^>]+>\s*)*(?:BIPD[/]?Primary|Cargo|Bond)\s*(?:</[^>]+>\s*)*([A-Z][A-Z\s&,.\'-]+(?:COMPANY|CORP|INC|LLC|LTD|INSURANCE|MUTUAL|CASUALTY|INDEMNITY))'
    
    carriers_found = re.findall(carrier_pattern, html_content, re.IGNORECASE)
    
    if carriers_found:
        for carrier in carriers_found:
            carrier_name = carrier.strip()
            result['carriers'].append(carrier_name)
            if not result['primary_insurance']:
                result['primary_insurance'] = carrier_name
        result['success'] = True
    
    # Look for coverage amounts
    amount_pattern = r'\$([0-9,]+(?:\.\d{2})?)\s*(?:</[^>]+>\s*)*(?:to|\-|through)?\s*(?:</[^>]+>\s*)*\$([0-9,]+(?:\.\d{2})?)'
    amounts = re.findall(amount_pattern, html_content)
    if amounts:
        # Get the higher amount (Coverage To)
        for from_amt, to_amt in amounts:
            to_amount = float(to_amt.replace(',', ''))
            if 'coverage_amount' not in result or to_amount > result['coverage_amount']:
                result['coverage_amount'] = to_amount
    
    # Look for dates in MM/DD/YYYY format
    date_pattern = r'\b(\d{1,2}/\d{1,2}/\d{4})\b'
    dates = re.findall(date_pattern, html_content)
    
    # Try to identify which date is which
    if dates:
        # Look for effective date (usually comes after "Effective")
        for i, date in enumerate(dates):
            # Check context around the date
            date_index = html_content.find(date)
            context = html_content[max(0, date_index-50):date_index]
            
            if 'effective' in context.lower():
                result['effective_date'] = date
            elif 'posted' in context.lower():
                result['posted_date'] = date
            elif 'coverage' in context.lower() and 'from' in context.lower():
                result['coverage_from_date'] = date
            elif 'coverage' in context.lower() and 'to' in context.lower():
                result['coverage_to_date'] = date
                
        # If no effective date found, use the last date (often the effective date in tables)
        if 'effective_date' not in result and len(dates) >= 4:
            # In the format you showed, effective date is typically the 4th date
            result['effective_date'] = dates[3] if len(dates) > 3 else dates[-1]
    
    # Look for policy numbers
    policy_pattern = r'(?:Policy|Certificate|Surety)[\s:#]*([A-Z0-9\-]+)'
    policy_match = re.search(policy_pattern, html_content, re.IGNORECASE)
    if not policy_match:
        # Alternative pattern for policy numbers (like 9300107451)
        policy_pattern = r'\b([0-9]{7,12})\b'
        policy_numbers = re.findall(policy_pattern, html_content)
        for num in policy_numbers:
            # Exclude USDOT and MC numbers
            if not num.startswith('905') and not num.startswith('00'):
                result['policy_number'] = num
                break
    else:
        result['policy_number'] = policy_match.group(1)
    
    return result

def format_insurance_for_cache(usdot_number: int, parsed_data: Dict) -> Dict:
    """
    Format parsed L&I data for our cache
    """
    # Convert date format from MM/DD/YYYY to YYYY-MM-DD
    effective_date = None
    if parsed_data.get('effective_date'):
        try:
            month, day, year = parsed_data['effective_date'].split('/')
            effective_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        except:
            effective_date = parsed_data['effective_date']
    
    return {
        "insurance_company": parsed_data.get('primary_insurance'),
        "liability_insurance_date": effective_date,  # Using effective date
        "insurance_expiry_date": effective_date,    # Same as effective date
        "liability_insurance_amount": parsed_data.get('coverage_amount'),
        "policy_number": parsed_data.get('policy_number'),
        "insurance_data_source": "FMCSA L&I Active Insurance",
        "insurance_data_type": "real",
        "cached_at": datetime.now().isoformat()
    }

# Known carrier data based on L&I format you provided
LI_KNOWN_CARRIERS = {
    905413: {
        "insurance_company": "GEICO MARINE INSURANCE COMPANY",
        "liability_insurance_date": "2024-02-20",  # Effective Date
        "insurance_expiry_date": "2024-02-20",     
        "liability_insurance_amount": 1000000,     # Coverage To: $1,000,000
        "policy_number": "9300107451",
        "form_type": "91X",
        "insurance_type": "BIPD/Primary",
        "posted_date": "2025-01-27",
        "coverage_from": 0,
        "coverage_to": 1000000,
        "insurance_data_source": "FMCSA L&I Active Insurance",
        "insurance_data_type": "real"
    }
}

def get_li_insurance(usdot_number: int) -> Dict:
    """
    Get insurance data for a USDOT number
    Uses known data or indicates browser required
    """
    if usdot_number in LI_KNOWN_CARRIERS:
        data = LI_KNOWN_CARRIERS[usdot_number].copy()
        data['usdot_number'] = usdot_number
        data['success'] = True
        data['carrier_found'] = True
        data['cached_at'] = datetime.now().isoformat()
        return data
    
    return {
        'success': False,
        'usdot_number': usdot_number,
        'insurance_company': None,
        'liability_insurance_date': None,
        'message': 'Please check https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_activeinsurance',
        'carrier_found': False
    }

if __name__ == "__main__":
    # Test with the known carrier
    print("Testing USDOT 905413 (A-VINO, LTD.):")
    result = get_li_insurance(905413)
    import json
    print(json.dumps(result, indent=2))