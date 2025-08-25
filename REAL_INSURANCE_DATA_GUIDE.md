# Getting Real FMCSA Insurance Data

## Overview
The FMCSA (Federal Motor Carrier Safety Administration) maintains real insurance data through their L&I (Licensing & Insurance) system. This data includes actual insurance carrier names, policy numbers, coverage amounts, and expiration dates.

## Available Data Sources

### 1. FMCSA QCMobile API (Official)
**Website:** https://mobile.fmcsa.dot.gov/QCDevsite/docs/getStarted

**How to Get Access:**
1. Create a developer account at https://mobile.fmcsa.dot.gov/QCDevsite/
2. Log in with Login.gov
3. Go to "My WebKeys" and click "Get a new WebKey"
4. Use the WebKey in all API calls

**API Base URL:** `https://mobile.fmcsa.dot.gov/qc/services/`

**Example Call:**
```
GET https://mobile.fmcsa.dot.gov/qc/services/carriers/docket-number/MC-123456?webKey=YOUR_KEY_HERE
```

**Insurance Data Available:**
- Insurance carrier name
- Policy/Surety numbers
- Coverage amounts
- Effective dates
- Cancellation dates (if pending)
- Historical insurance records since 1995

### 2. FMCSA L&I Public Search (Web Scraping)
**Website:** https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_carrlist

**Note:** This is a web interface, not an API. You would need to:
- Use web scraping tools (Selenium, Puppeteer, etc.)
- Search by USDOT or Docket Number
- Parse the HTML for insurance information

### 3. Socrata Open Data API (SODA)
**Website:** https://data.transportation.gov/

**Dataset:** Licensing and Insurance - QCMobile API
**URL:** https://data.transportation.gov/Trucking-and-Motorcoaches/Licensing-and-Insurance-QCMobile-API/7xzn-4j4j

**Access Method:**
```python
import requests

# No API key required for public datasets
url = "https://data.transportation.gov/resource/7xzn-4j4j.json"
params = {
    "$limit": 100,
    "$where": "usdot_number = '123456'"
}
response = requests.get(url, params=params)
data = response.json()
```

### 4. Third-Party APIs

#### Carrier Details API
**Website:** https://carrierdetails.com/
- Provides comprehensive FMCSA database access
- Real-time insurance status updates
- Requires paid subscription
- Returns docket numbers, granted dates, insurance details

#### Other Commercial Providers:
- **SaferWatch:** https://saferwatch.com/
- **Highway:** https://www.highwayinc.com/
- **TruckingOffice:** https://www.truckingoffice.com/

## Implementation Steps

### Step 1: Get FMCSA WebKey
```python
# register.py
import requests

# 1. Go to https://mobile.fmcsa.dot.gov/QCDevsite/
# 2. Create account
# 3. Get WebKey
FMCSA_WEBKEY = "your_webkey_here"
```

### Step 2: Create Insurance Data Service
```python
# insurance_service.py
import requests
from datetime import datetime
from typing import Optional, Dict, Any

class FMCSAInsuranceService:
    def __init__(self, webkey: str):
        self.webkey = webkey
        self.base_url = "https://mobile.fmcsa.dot.gov/qc/services"
    
    def get_carrier_insurance(self, usdot_number: int) -> Dict[str, Any]:
        """Get real insurance data for a carrier"""
        
        # Try QCMobile API
        url = f"{self.base_url}/carriers/{usdot_number}"
        params = {"webKey": self.webkey}
        
        try:
            response = requests.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                
                # Extract insurance information
                carrier = data.get("content", {}).get("carrier", {})
                
                insurance_info = {
                    "insurance_carrier": carrier.get("insuranceCarrier"),
                    "policy_number": carrier.get("policyNumber"),
                    "coverage_from": carrier.get("coverageFrom"),
                    "coverage_to": carrier.get("coverageTo"),
                    "liability_amount": carrier.get("liabilityCoverage"),
                    "cargo_amount": carrier.get("cargoCoverage"),
                    "bond_amount": carrier.get("bondCoverage"),
                    "insurance_on_file": carrier.get("insuranceOnFile"),
                    "insurance_required": carrier.get("insuranceRequired"),
                    "bipd_required": carrier.get("bipdInsuranceRequired"),
                    "bipd_on_file": carrier.get("bipdInsuranceOnFile"),
                    "cargo_required": carrier.get("cargoInsuranceRequired"),
                    "cargo_on_file": carrier.get("cargoInsuranceOnFile"),
                    "bond_required": carrier.get("bondInsuranceRequired"),
                    "bond_on_file": carrier.get("bondInsuranceOnFile")
                }
                
                return insurance_info
                
        except Exception as e:
            print(f"Error fetching insurance data: {e}")
            return None
```

### Step 3: Integrate with Your API
```python
# demo_real_api.py - UPDATE THIS SECTION

@app.get("/api/carriers/{usdot_number}")
async def get_carrier(usdot_number: int):
    """Get specific carrier by USDOT number with real insurance data."""
    carrier = next((c for c in CARRIERS if c.get("usdot_number") == usdot_number), None)
    if not carrier:
        raise HTTPException(status_code=404, detail="Carrier not found")
    
    carrier_copy = carrier.copy()
    
    # Try to get real insurance data
    if FMCSA_WEBKEY:  # Set this in environment variable
        insurance_service = FMCSAInsuranceService(FMCSA_WEBKEY)
        real_insurance = insurance_service.get_carrier_insurance(usdot_number)
        
        if real_insurance:
            # Use real data
            carrier_copy.update(real_insurance)
        else:
            # Fall back to simulated data
            carrier_copy["insurance_note"] = "Real insurance data unavailable"
    
    return carrier_copy
```

## Insurance Data Fields Available

### From FMCSA L&I System:
- **Insurance Carrier Name** - The actual insurance company
- **Policy/Surety Number** - Policy identification
- **Coverage Type** - Liability, Cargo, Bond
- **Coverage Amount** - Actual coverage (may exceed minimums)
- **Effective Date** - When coverage started
- **Cancellation Date** - If pending cancellation
- **Filing Date** - When filed with FMCSA
- **Form Type** - BMC-91, BMC-34, etc.

### Federal Minimum Requirements:
- **Liability Insurance:**
  - General freight: $750,000
  - Hazmat: $1,000,000 - $5,000,000
  - Passengers (16+): $5,000,000
  - Passengers (15 or less): $1,500,000

- **Cargo Insurance:**
  - Household goods: $5,000 per vehicle
  - General commodities: $10,000 per occurrence

- **Bond/Trust Fund (Brokers):**
  - $75,000

## Environment Variables
```bash
# .env file
FMCSA_WEBKEY=your_webkey_here
FMCSA_USE_REAL_DATA=true
CARRIER_DETAILS_API_KEY=your_carrier_details_key  # If using third-party
```

## Testing Real Data
```python
# test_real_insurance.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

WEBKEY = os.getenv("FMCSA_WEBKEY")

# Test with a known carrier (e.g., FedEx USDOT: 80321)
url = f"https://mobile.fmcsa.dot.gov/qc/services/carriers/80321?webKey={WEBKEY}"
response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    print("Real Insurance Data Retrieved!")
    print(json.dumps(data, indent=2))
else:
    print(f"Error: {response.status_code}")
```

## Important Notes

1. **API Rate Limits:** FMCSA may have rate limits. Be respectful of their servers.

2. **Data Privacy:** Insurance information is public record but should be handled responsibly.

3. **Caching:** Consider caching insurance data to reduce API calls:
   - Cache for 24 hours for active policies
   - Cache for 1 hour for expiring/expired policies

4. **Compliance:** Ensure your use complies with FMCSA terms of service.

5. **Fallback Strategy:** Always have a fallback when real data is unavailable:
   - Show "Insurance on file: Yes/No" from basic FMCSA data
   - Display federal minimum requirements
   - Show last known good data with timestamp

## Next Steps

1. Register for FMCSA developer account
2. Get your WebKey
3. Test the API with known USDOT numbers
4. Implement caching strategy
5. Add error handling and fallbacks
6. Consider third-party APIs for enhanced features

## Resources

- FMCSA Developer Portal: https://mobile.fmcsa.dot.gov/QCDevsite/
- L&I Public Search: https://li-public.fmcsa.dot.gov/
- API Documentation: https://mobile.fmcsa.dot.gov/QCDevsite/docs/qcApi
- Insurance Requirements: https://www.fmcsa.dot.gov/registration/insurance-filing-requirements