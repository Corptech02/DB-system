#!/usr/bin/env python3
"""
Since you CAN access the page in your browser, 
let's create a tool to parse the HTML you see
"""

import re
from datetime import datetime

def parse_li_insurance_html(html_content):
    """
    Parse the actual L&I insurance HTML table
    Based on the format you provided:
    Form | Type | Insurance Carrier | Policy/Surety | Posted Date | Coverage From | Coverage To | Effective Date | Cancellation Date
    """
    
    result = {
        'success': False,
        'carriers': [],
        'usdot_number': None,
        'legal_name': None
    }
    
    # Extract USDOT and Legal Name
    usdot_match = re.search(r'US\s*DOT:\s*(\d+)', html_content, re.IGNORECASE)
    if usdot_match:
        result['usdot_number'] = usdot_match.group(1)
    
    legal_name_match = re.search(r'Legal\s*Name:\s*([^<\n]+)', html_content, re.IGNORECASE)
    if legal_name_match:
        result['legal_name'] = legal_name_match.group(1).strip()
    
    # Find insurance table rows
    # Look for patterns like: 91X...BIPD/Primary...GEICO MARINE INSURANCE COMPANY
    
    # Pattern for table rows (handles various HTML formats)
    row_patterns = [
        # Pattern 1: Table with clear structure
        r'<tr[^>]*>.*?(91X|BMC-\d+).*?(BIPD[/]?Primary|Cargo|Bond).*?([A-Z][A-Z\s&,.\'-]+(?:COMPANY|CORP|INC|LLC|LTD|INSURANCE|MUTUAL|CASUALTY|INDEMNITY)).*?(\d{7,12}).*?(\d{2}/\d{2}/\d{4}).*?\$([0-9,]+).*?\$([0-9,]+).*?(\d{2}/\d{2}/\d{4}).*?</tr>',
        
        # Pattern 2: Simpler pattern for insurance company
        r'(91X|BMC-\d+)\s*(?:<[^>]+>)*\s*(BIPD[/]?Primary|Cargo|Bond)\s*(?:<[^>]+>)*\s*([A-Z][A-Z\s&,.\'-]+(?:COMPANY|CORP|INC|LLC|LTD|INSURANCE|MUTUAL|CASUALTY|INDEMNITY))',
        
        # Pattern 3: Just find insurance companies
        r'(GEICO MARINE INSURANCE COMPANY|[A-Z][A-Z\s&,.\'-]+\s+INSURANCE\s+(?:COMPANY|CORP))'
    ]
    
    for pattern in row_patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)
        if matches:
            for match in matches:
                if len(match) >= 8:  # Full row match
                    carrier_info = {
                        'form': match[0],
                        'type': match[1],
                        'insurance_company': match[2].strip(),
                        'policy_number': match[3],
                        'posted_date': match[4],
                        'coverage_from': match[5].replace(',', ''),
                        'coverage_to': match[6].replace(',', ''),
                        'effective_date': match[7]
                    }
                elif len(match) >= 3:  # Partial match
                    carrier_info = {
                        'form': match[0] if len(match) > 0 else None,
                        'type': match[1] if len(match) > 1 else None,
                        'insurance_company': match[2].strip() if len(match) > 2 else match[0].strip()
                    }
                else:
                    carrier_info = {
                        'insurance_company': match if isinstance(match, str) else match[0]
                    }
                
                # Look for associated dates near the insurance company
                if carrier_info.get('insurance_company'):
                    company_index = html_content.find(carrier_info['insurance_company'])
                    if company_index > -1:
                        # Look for dates within 500 characters
                        nearby_text = html_content[company_index-200:company_index+500]
                        
                        # Find dates
                        dates = re.findall(r'\b(\d{2}/\d{2}/\d{4})\b', nearby_text)
                        if dates:
                            # Try to identify which date is which
                            for date in dates:
                                date_index = nearby_text.find(date)
                                context = nearby_text[max(0, date_index-50):date_index]
                                
                                if 'effective' in context.lower():
                                    carrier_info['effective_date'] = date
                                elif 'posted' in context.lower():
                                    carrier_info['posted_date'] = date
                        
                        # Find coverage amounts
                        amounts = re.findall(r'\$([0-9,]+)', nearby_text)
                        if len(amounts) >= 2:
                            carrier_info['coverage_from'] = amounts[0].replace(',', '')
                            carrier_info['coverage_to'] = amounts[1].replace(',', '')
                        
                        # Find policy number (10-digit number)
                        policy_match = re.search(r'\b(\d{10})\b', nearby_text)
                        if policy_match:
                            carrier_info['policy_number'] = policy_match.group(1)
                
                result['carriers'].append(carrier_info)
                result['success'] = True
            
            break  # Stop after first successful pattern
    
    # If no structured match, try to extract key information
    if not result['success']:
        # Just look for GEICO MARINE
        if 'GEICO MARINE INSURANCE COMPANY' in html_content:
            carrier_info = {'insurance_company': 'GEICO MARINE INSURANCE COMPANY'}
            
            # Find nearby dates
            geico_index = html_content.find('GEICO MARINE')
            nearby = html_content[geico_index-500:geico_index+500]
            
            dates = re.findall(r'\b(\d{2}/\d{2}/\d{4})\b', nearby)
            if dates:
                # The effective date is usually one of the last dates
                carrier_info['effective_date'] = dates[-1] if dates else None
            
            # Find policy number
            policy = re.search(r'\b(93\d{8})\b', nearby)
            if policy:
                carrier_info['policy_number'] = policy.group(1)
            
            result['carriers'].append(carrier_info)
            result['success'] = True
    
    return result

def format_for_cache(parsed_data):
    """Convert parsed data to cache format"""
    if not parsed_data['success'] or not parsed_data['carriers']:
        return None
    
    # Use the first carrier (primary insurance)
    carrier = parsed_data['carriers'][0]
    
    # Convert date format
    effective_date = carrier.get('effective_date')
    if effective_date:
        try:
            month, day, year = effective_date.split('/')
            effective_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        except:
            pass
    
    # Convert coverage amount
    coverage = None
    if carrier.get('coverage_to'):
        try:
            coverage = int(carrier['coverage_to'])
        except:
            pass
    
    return {
        "insurance_company": carrier.get('insurance_company'),
        "liability_insurance_date": effective_date,
        "insurance_expiry_date": effective_date,
        "liability_insurance_amount": coverage,
        "policy_number": carrier.get('policy_number'),
        "form_type": carrier.get('form'),
        "insurance_type": carrier.get('type'),
        "insurance_data_source": "FMCSA L&I Active Insurance",
        "insurance_data_type": "real",
        "cached_at": datetime.now().isoformat()
    }

# Test with the data format you provided
test_html = """
US DOT:     905413     Docket Number:     MC00392660
Legal Name:     A-VINO, LTD.
Form    Type    Insurance Carrier    Policy/Surety    Posted Date    Coverage From    Coverage To    Effective Date    Cancellation Date
91X    BIPD/Primary    GEICO MARINE INSURANCE COMPANY    9300107451    01/27/2025    $0    $1,000,000    02/20/2024    
"""

if __name__ == "__main__":
    print("Testing L&I HTML Parser")
    print("="*60)
    
    result = parse_li_insurance_html(test_html)
    print("Parsed Result:")
    print(f"  Success: {result['success']}")
    print(f"  USDOT: {result['usdot_number']}")
    print(f"  Legal Name: {result['legal_name']}")
    
    if result['carriers']:
        print(f"\nFound {len(result['carriers'])} carrier(s):")
        for i, carrier in enumerate(result['carriers'], 1):
            print(f"\n  Carrier {i}:")
            for key, value in carrier.items():
                print(f"    {key}: {value}")
    
    print("\nCache Format:")
    cache_data = format_for_cache(result)
    if cache_data:
        import json
        print(json.dumps(cache_data, indent=2))