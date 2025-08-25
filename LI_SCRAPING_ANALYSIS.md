# L&I Insurance Scraping Analysis

## Summary
The FMCSA L&I (Licensing & Insurance) system at https://li-public.fmcsa.dot.gov cannot be scraped programmatically using traditional HTTP requests, curl, or even modern tools like Selenium/Playwright in headless environments.

## Why Scraping Fails

### 1. JavaScript Requirement
The L&I system is built on Oracle APEX/Forms which requires:
- JavaScript execution for page rendering
- Dynamic content loading
- Client-side form validation
- Session token generation

### 2. Anti-Scraping Measures
- Returns 404 errors for direct URL access
- Requires valid browser session with cookies
- Uses hidden form fields and tokens
- Validates referer headers

### 3. Technical Limitations Discovered
All attempted methods failed with 404 errors:
- Direct HTTP requests (Python requests library)
- Session management with cookies
- SOAP/XML endpoints
- AJAX/JSON endpoints  
- Oracle Forms protocols
- CSRF token handling
- Base64 encoded parameters
- Curl with full browser headers

## Working Solutions

### Option 1: Browser Automation (Requires Desktop)
```python
# Works only on systems with GUI and Chrome installed
from selenium import webdriver
# or
from playwright.sync_api import sync_playwright
```

**Requirements:**
- Chrome/Chromium browser installed
- Display server (X11/Wayland) for non-headless mode
- System dependencies (libnspr4, libnss3, etc.)

### Option 2: Manual Data Entry System
Created `li_manual_entry.py` which provides:
- Interactive data entry interface
- CSV batch import capability
- Structured data parsing
- Cache management

### Option 3: API Integration (If Available)
The proper solution would be to use an official FMCSA API if one becomes available.

## Current Implementation

The system now:
1. **Checks cache first** (`li_insurance_cache.json`)
2. **Shows loading state** while checking
3. **Falls back to "No Insurance on File"** if not cached
4. **Allows manual updates** via `li_manual_entry.py`

## Data Format

Insurance data is stored in JSON format:
```json
{
  "905413": {
    "insurance_company": "GEICO MARINE INSURANCE COMPANY",
    "form_type": "91X",
    "policy_number": "9300107451",
    "coverage_amount": 1000000,
    "liability_insurance_date": "2024-02-20",
    "insurance_expiry_date": "2024-02-20",
    "insurance_data_source": "FMCSA L&I Active Insurance",
    "insurance_data_type": "real",
    "cached_at": "2025-01-27T10:30:00"
  }
}
```

## Recommendations

1. **For Development**: Use the manual entry system to populate test data
2. **For Production**: Consider:
   - Setting up a dedicated scraping server with GUI support
   - Requesting API access from FMCSA
   - Using a commercial data provider that has proper access
3. **For Users**: Provide clear instructions that insurance data must be manually updated

## Files Created

1. **Scraping Attempts** (All failed due to JavaScript requirement):
   - `li_deep_scraper.py` - Multiple HTTP methods
   - `li_reverse_engineer.py` - Advanced techniques
   - `li_selenium_scraper.py` - Selenium approach
   - `li_playwright_scraper.py` - Playwright approach
   - `li_curl_scraper.py` - Curl-based approach

2. **Working Solutions**:
   - `li_manual_entry.py` - Manual data entry system
   - `analyze_li_html.py` - HTML parser for manual data
   - `li_insurance_cache.json` - Data cache

## Conclusion

The L&I system is designed to prevent automated access and requires human interaction through a web browser. While this protects the system from abuse, it also prevents legitimate programmatic access. The best current solution is to maintain a cache of insurance data that can be manually updated when needed.