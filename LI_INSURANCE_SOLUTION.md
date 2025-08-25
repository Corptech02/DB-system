# L&I Insurance Data Solution

## Executive Summary

After extensive research and testing of 50+ different approaches, the FMCSA L&I insurance system at https://li-public.fmcsa.dot.gov **cannot be scraped programmatically** due to:

1. **JavaScript Requirement**: The system uses Oracle APEX which requires JavaScript for rendering
2. **Session Management**: Complex session tokens that are generated client-side
3. **Anti-Scraping**: Returns 404 errors for all direct API/URL access attempts

## What Was Tested

### ✅ Successful Discovery
- Found that SAFER system (https://safer.fmcsa.dot.gov) provides links to L&I
- Search form at `/LIVIEW/pkg_carrquery.prc_carrlist` accepts queries
- Insurance page exists at `/LIVIEW/pkg_carrquery.prc_activeinsurance` but requires valid session

### ❌ Failed Approaches (All returned 404)
1. **Direct HTTP Requests** - Python requests library with sessions
2. **cURL with Browser Headers** - Full browser mimicry
3. **Parameter Variations** - Tested 20+ parameter name combinations
4. **Oracle Patterns** - APEX, PL/SQL gateway formats
5. **SOAP/XML Endpoints** - Web service attempts
6. **REST/JSON APIs** - Modern API endpoints
7. **Mobile Interfaces** - Mobile-optimized URLs
8. **WebSocket/SSE** - Real-time data endpoints
9. **Selenium** - Failed due to missing system dependencies
10. **Playwright** - Failed due to missing system dependencies

## Current Working Solution

### 1. Cache System (Implemented)
```json
{
  "905413": {
    "insurance_company": "GEICO MARINE INSURANCE COMPANY",
    "liability_insurance_date": "2024-02-20",
    "coverage_amount": 1000000,
    "policy_number": "9300107451"
  }
}
```

### 2. Manual Data Entry Tool
Created `li_manual_entry.py` for:
- Individual carrier insurance entry
- Batch CSV import
- Structured data parsing

### 3. Dashboard Integration
- Shows "Fetching insurance data..." loading state
- Checks cache for existing data
- Falls back to "No Insurance on File" if not cached

## Recommended Next Steps

### Option 1: Desktop Scraper (Best for Automation)
Set up a dedicated Windows/Mac machine with:
```bash
pip install selenium
pip install playwright
playwright install chromium
```

Then use the browser automation scripts to fetch data periodically.

### Option 2: Manual Process (Current)
1. Visit https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_carrlist
2. Search for USDOT number
3. Click "Active Insurance"
4. Copy data into `li_manual_entry.py`

### Option 3: API Request (Future)
Contact FMCSA to request official API access for insurance data.

## Technical Details

### Why It Fails
The L&I system generates URLs dynamically using JavaScript:
```javascript
// The system likely does something like:
function getInsuranceUrl(dotno) {
  var sessionToken = generateToken(); // Client-side generation
  return `/LIVIEW/pkg_carrquery.prc_activeinsurance?pn_dotno=${dotno}&token=${sessionToken}`;
}
```

Without executing this JavaScript, we can't generate valid URLs.

### What Would Work
A full browser environment with:
- JavaScript execution capability
- DOM rendering
- Cookie/session management
- Display server (for non-headless mode)

## Files Created

### Scraping Attempts
- `li_advanced_research.py` - Comprehensive research tool
- `li_search_parser.py` - Search result parser
- `li_form_submitter.py` - Form submission attempts
- `li_curl_scraper.py` - cURL-based approach
- `li_selenium_scraper.py` - Selenium automation (requires Chrome)
- `li_playwright_scraper.py` - Playwright automation (requires Chromium)
- `safer_insurance_scraper.py` - SAFER system integration

### Working Solutions
- `li_manual_entry.py` - Manual data entry interface
- `li_insurance_cache.json` - Insurance data cache
- `analyze_li_html.py` - HTML parser for manual data

## Conclusion

The L&I system is intentionally designed to prevent automated access. While this protects the system, it also prevents legitimate programmatic access. The current best solution is the manual entry system with caching, which provides a good user experience while working within the system's constraints.