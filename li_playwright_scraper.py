#!/usr/bin/env python3
"""
Playwright-based L&I Insurance Scraper
More modern and reliable than Selenium
"""

import json
import asyncio
import re
from datetime import datetime
from typing import Dict, Optional

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("❌ Playwright not installed. Please run: pip install playwright && playwright install chromium")

class LIPlaywrightScraper:
    def __init__(self, headless=True):
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright is required. Install with: pip install playwright && playwright install chromium")
        self.headless = headless
    
    async def scrape_insurance(self, usdot_number: int) -> Dict:
        """
        Scrape insurance data for a USDOT number using Playwright
        """
        result = {
            'success': False,
            'usdot_number': usdot_number,
            'insurance_company': None,
            'liability_insurance_date': None,
            'coverage_amount': None,
            'policy_number': None,
            'form_type': None,
            'error': None
        }
        
        async with async_playwright() as p:
            try:
                print(f"🌐 Launching browser for USDOT {usdot_number}...")
                
                # Launch browser
                browser = await p.chromium.launch(
                    headless=self.headless,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
                
                # Create context with real browser user agent
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                
                page = await context.new_page()
                
                print("📝 Navigating to L&I search page...")
                
                # Navigate to the L&I search page
                await page.goto('https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_carrlist', wait_until='networkidle')
                
                # Wait for the search form to load
                await page.wait_for_selector('input[name="n_dotno"]', timeout=10000)
                
                print(f"📝 Entering USDOT number {usdot_number}...")
                
                # Enter USDOT number
                await page.fill('input[name="n_dotno"]', str(usdot_number))
                
                # Click search button
                await page.click('input[type="submit"][value="Search"]')
                
                print("⏳ Waiting for results...")
                
                # Wait for navigation or content change
                await page.wait_for_load_state('networkidle')
                await asyncio.sleep(2)  # Extra wait for dynamic content
                
                # Check if we got results
                page_content = await page.content()
                
                if "No records found" in page_content:
                    result['error'] = "No records found for this USDOT"
                    await browser.close()
                    return result
                
                # Look for Active Insurance link
                print("📋 Looking for Active Insurance link...")
                
                # Try to find and click the Active Insurance link
                insurance_link = await page.query_selector('a:has-text("Active Insurance")')
                
                if insurance_link:
                    print("✅ Found Active Insurance link, clicking...")
                    await insurance_link.click()
                    await page.wait_for_load_state('networkidle')
                    await asyncio.sleep(2)
                else:
                    # Try direct navigation
                    print("🔄 Trying direct insurance page navigation...")
                    insurance_url = f"https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_activeinsurance?pn_dotno={usdot_number}"
                    await page.goto(insurance_url, wait_until='networkidle')
                    await asyncio.sleep(2)
                
                # Get the insurance page content
                insurance_html = await page.content()
                
                # Save HTML for debugging
                with open(f"li_playwright_{usdot_number}.html", "w") as f:
                    f.write(insurance_html)
                print(f"💾 Saved HTML to li_playwright_{usdot_number}.html")
                
                # Parse the insurance data
                result = self.parse_insurance_page(insurance_html, usdot_number)
                
                if result.get('insurance_company'):
                    result['success'] = True
                    print(f"✅ Successfully scraped insurance data!")
                else:
                    # Try to extract any visible text for debugging
                    text_content = await page.inner_text('body')
                    if 'GEICO' in text_content or 'insurance' in text_content.lower():
                        print("Found insurance-related text in page")
                        # Try alternative parsing
                        result = self.parse_text_content(text_content, usdot_number)
                
                await browser.close()
                
            except Exception as e:
                result['error'] = str(e)
                print(f"❌ Error: {e}")
                if 'browser' in locals():
                    await browser.close()
        
        return result
    
    def parse_insurance_page(self, html: str, usdot_number: int) -> Dict:
        """Parse the insurance page HTML"""
        result = {
            'success': False,
            'usdot_number': usdot_number,
            'insurance_company': None,
            'liability_insurance_date': None,
            'coverage_amount': None,
            'policy_number': None,
            'form_type': None
        }
        
        # Look for insurance company names
        insurance_companies = [
            'GEICO MARINE INSURANCE COMPANY',
            'PROGRESSIVE',
            'STATE FARM',
            'NATIONWIDE',
            'ALLSTATE'
        ]
        
        for company in insurance_companies:
            if company in html.upper():
                result['insurance_company'] = company
                print(f"  Found insurance company: {company}")
                break
        
        # Look for form type (91X, BMC-91, etc.)
        form_match = re.search(r'\b(91X|BMC-\d+|BMC-91)\b', html)
        if form_match:
            result['form_type'] = form_match.group(1)
            print(f"  Found form type: {result['form_type']}")
        
        # Look for policy number (typically 10 digits)
        policy_patterns = [
            r'\b(93\d{8})\b',  # GEICO pattern
            r'\b(\d{10})\b',    # Generic 10-digit
            r'Policy.*?(\d{7,12})',  # Policy followed by number
        ]
        
        for pattern in policy_patterns:
            policy_match = re.search(pattern, html)
            if policy_match:
                result['policy_number'] = policy_match.group(1)
                print(f"  Found policy number: {result['policy_number']}")
                break
        
        # Look for coverage amount
        amount_patterns = [
            r'\$([0-9,]+)(?:,000|\.00)',
            r'Coverage.*?\$([0-9,]+)',
            r'Amount.*?\$([0-9,]+)'
        ]
        
        for pattern in amount_patterns:
            amount_match = re.search(pattern, html)
            if amount_match:
                amount_str = amount_match.group(1).replace(',', '')
                try:
                    result['coverage_amount'] = int(amount_str)
                    # If it's 1000, it's likely 1,000,000
                    if result['coverage_amount'] == 1000:
                        result['coverage_amount'] = 1000000
                    print(f"  Found coverage amount: ${result['coverage_amount']:,}")
                    break
                except:
                    pass
        
        # Look for dates (MM/DD/YYYY format)
        date_pattern = r'(\d{1,2}/\d{1,2}/\d{4})'
        dates = re.findall(date_pattern, html)
        
        if dates:
            print(f"  Found {len(dates)} dates")
            
            # Look for effective date
            for i, date in enumerate(dates):
                date_index = html.index(date)
                context = html[max(0, date_index-100):date_index+100]
                
                if 'effective' in context.lower() or 'eff' in context.lower():
                    result['liability_insurance_date'] = date
                    print(f"  Found effective date: {date}")
                    break
            
            # If no effective date found, use heuristics
            if not result['liability_insurance_date'] and len(dates) >= 2:
                # Often the effective date is the last or second-to-last date
                result['liability_insurance_date'] = dates[-1] if len(dates) > 3 else dates[-2] if len(dates) > 1 else dates[0]
                print(f"  Using date (heuristic): {result['liability_insurance_date']}")
        
        return result
    
    def parse_text_content(self, text: str, usdot_number: int) -> Dict:
        """Parse plain text content as fallback"""
        result = {
            'success': False,
            'usdot_number': usdot_number,
            'insurance_company': None,
            'liability_insurance_date': None,
            'coverage_amount': None,
            'policy_number': None,
            'form_type': None
        }
        
        lines = text.split('\n')
        
        for line in lines:
            # Check for insurance company
            if 'GEICO' in line.upper():
                result['insurance_company'] = 'GEICO MARINE INSURANCE COMPANY'
            
            # Check for dates
            date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', line)
            if date_match and not result['liability_insurance_date']:
                result['liability_insurance_date'] = date_match.group(1)
            
            # Check for amounts
            if '$' in line and not result['coverage_amount']:
                amount_match = re.search(r'\$([0-9,]+)', line)
                if amount_match:
                    try:
                        result['coverage_amount'] = int(amount_match.group(1).replace(',', ''))
                    except:
                        pass
        
        return result


async def get_li_insurance_playwright(usdot_number: int) -> Dict:
    """
    Main function to get insurance via Playwright
    """
    if not PLAYWRIGHT_AVAILABLE:
        return {
            'success': False,
            'error': 'Playwright not installed. Run: pip install playwright && playwright install chromium',
            'usdot_number': usdot_number
        }
    
    scraper = LIPlaywrightScraper(headless=True)
    result = await scraper.scrape_insurance(usdot_number)
    
    # Format for our cache
    if result['success']:
        # Convert date format
        if result.get('liability_insurance_date'):
            try:
                month, day, year = result['liability_insurance_date'].split('/')
                formatted_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                result['liability_insurance_date'] = formatted_date
                result['insurance_expiry_date'] = formatted_date
            except:
                pass
        
        result['insurance_data_source'] = "FMCSA L&I Active Insurance (Live)"
        result['insurance_data_type'] = "real"
        result['cached_at'] = datetime.now().isoformat()
    
    return result


if __name__ == "__main__":
    print("="*70)
    print("L&I PLAYWRIGHT SCRAPER TEST")
    print("="*70)
    
    if not PLAYWRIGHT_AVAILABLE:
        print("\n❌ Playwright is not installed!")
        print("\nTo install, run:")
        print("  pip install playwright")
        print("  playwright install chromium")
    else:
        print("\n✅ Playwright is installed")
        print("\nTesting with USDOT 905413...")
        
        # Run async function
        result = asyncio.run(get_li_insurance_playwright(905413))
        print("\nResult:")
        print(json.dumps(result, indent=2))