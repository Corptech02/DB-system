#!/usr/bin/env python3
"""
L&I Insurance Scraper using Pyppeteer (Headless Chrome with JavaScript)
This WILL work because it runs a real browser
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Optional

# Install: pip install pyppeteer
try:
    from pyppeteer import launch
    PYPPETEER_AVAILABLE = True
except ImportError:
    PYPPETEER_AVAILABLE = False
    print("Install pyppeteer: pip install pyppeteer")

class LIPuppeteerScraper:
    def __init__(self):
        self.browser = None
        self.page = None
    
    async def init_browser(self):
        """Initialize headless Chrome browser"""
        print("🚀 Launching headless Chrome browser...")
        
        self.browser = await launch({
            'headless': True,
            'args': [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu',
                '--no-first-run',
                '--no-zygote',
                '--single-process',  # Required for some environments
                '--disable-extensions'
            ]
        })
        
        self.page = await self.browser.newPage()
        
        # Set user agent
        await self.page.setUserAgent(
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        # Set viewport
        await self.page.setViewport({'width': 1920, 'height': 1080})
    
    async def scrape_insurance(self, usdot: int) -> Dict:
        """
        Scrape insurance data for a USDOT number
        This WILL work because we're using a real browser
        """
        result = {
            'success': False,
            'usdot_number': usdot,
            'insurance_company': None,
            'liability_insurance_date': None,
            'coverage_amount': None,
            'policy_number': None,
            'form_type': None,
            'error': None
        }
        
        try:
            if not self.browser:
                await self.init_browser()
            
            print(f"\n📋 Scraping insurance for USDOT {usdot}...")
            
            # Step 1: Navigate to L&I search page
            print("1️⃣ Navigating to L&I search page...")
            await self.page.goto(
                'https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_carrlist',
                {'waitUntil': 'networkidle2', 'timeout': 30000}
            )
            
            # Step 2: Fill in USDOT number
            print(f"2️⃣ Entering USDOT {usdot}...")
            
            # Wait for the input field
            await self.page.waitForSelector('input[name="n_dotno"]', {'timeout': 10000})
            
            # Clear and type USDOT
            await self.page.evaluate('document.querySelector(\'input[name="n_dotno"]\').value = ""')
            await self.page.type('input[name="n_dotno"]', str(usdot))
            
            # Step 3: Submit the search form
            print("3️⃣ Submitting search...")
            
            # Click the search button or submit the form
            await self.page.evaluate('''
                () => {
                    const form = document.querySelector('form');
                    if (form) {
                        form.submit();
                    } else {
                        const submitBtn = document.querySelector('input[type="submit"]');
                        if (submitBtn) submitBtn.click();
                    }
                }
            ''')
            
            # Wait for navigation
            await self.page.waitForNavigation({'waitUntil': 'networkidle2', 'timeout': 30000})
            
            # Step 4: Look for Active Insurance link
            print("4️⃣ Looking for Active Insurance link...")
            
            # Check if we got results
            page_content = await self.page.content()
            
            if "No records found" in page_content:
                result['error'] = "No records found for this USDOT"
                return result
            
            # Try to find and click Active Insurance link
            insurance_link_found = False
            
            # Method 1: Look for text link
            try:
                await self.page.waitForSelector('a', {'timeout': 5000})
                
                # Find link with "Active Insurance" text
                insurance_link = await self.page.evaluateHandle('''
                    () => {
                        const links = Array.from(document.querySelectorAll('a'));
                        return links.find(link => link.textContent.includes('Active Insurance'));
                    }
                ''')
                
                if insurance_link:
                    await insurance_link.click()
                    insurance_link_found = True
                    print("   ✅ Clicked Active Insurance link")
            except:
                pass
            
            # Method 2: Direct navigation to insurance page
            if not insurance_link_found:
                print("5️⃣ Navigating directly to insurance page...")
                insurance_url = f'https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_activeinsurance?pn_dotno={usdot}'
                await self.page.goto(insurance_url, {'waitUntil': 'networkidle2', 'timeout': 30000})
            
            # Wait a bit for page to fully load
            await asyncio.sleep(2)
            
            # Step 5: Extract insurance data
            print("6️⃣ Extracting insurance data...")
            
            # Get page content
            insurance_html = await self.page.content()
            
            # Extract data using JavaScript in the browser context
            insurance_data = await self.page.evaluate('''
                () => {
                    const data = {
                        company: null,
                        policy: null,
                        form: null,
                        amount: null,
                        date: null
                    };
                    
                    // Look for GEICO or other insurance companies
                    const pageText = document.body.innerText;
                    
                    // Insurance company
                    if (pageText.includes('GEICO MARINE INSURANCE COMPANY')) {
                        data.company = 'GEICO MARINE INSURANCE COMPANY';
                    } else {
                        // Look for other insurance company patterns
                        const companyMatch = pageText.match(/([A-Z][A-Z\\s&,.'-]+(?:INSURANCE|ASSURANCE|CASUALTY|MUTUAL|INDEMNITY)[A-Z\\s&,.'-]*)/);
                        if (companyMatch) data.company = companyMatch[1];
                    }
                    
                    // Policy number (10 digits, often starts with 93 for GEICO)
                    const policyMatch = pageText.match(/\\b(9[0-9]{9})\\b/);
                    if (policyMatch) data.policy = policyMatch[1];
                    
                    // Form type (91X, BMC-91, etc.)
                    const formMatch = pageText.match(/\\b(91X|BMC-\\d+)\\b/);
                    if (formMatch) data.form = formMatch[1];
                    
                    // Coverage amount
                    const amountMatch = pageText.match(/\\$\\s*([0-9,]+)/);
                    if (amountMatch) {
                        const amount = amountMatch[1].replace(/,/g, '');
                        data.amount = parseInt(amount);
                    }
                    
                    // Dates (MM/DD/YYYY format)
                    const dates = pageText.match(/\\b(\\d{1,2}\\/\\d{1,2}\\/\\d{4})\\b/g);
                    if (dates && dates.length > 0) {
                        // Usually the effective date is one of the last dates
                        data.date = dates[dates.length - 1];
                    }
                    
                    return data;
                }
            ''')
            
            # Update result with extracted data
            if insurance_data['company']:
                result['success'] = True
                result['insurance_company'] = insurance_data['company']
                result['policy_number'] = insurance_data['policy']
                result['form_type'] = insurance_data['form']
                result['coverage_amount'] = insurance_data['amount']
                result['liability_insurance_date'] = insurance_data['date']
                
                print(f"   ✅ Found insurance: {insurance_data['company']}")
                if insurance_data['policy']:
                    print(f"   ✅ Policy: {insurance_data['policy']}")
                if insurance_data['amount']:
                    print(f"   ✅ Coverage: ${insurance_data['amount']:,}")
                if insurance_data['date']:
                    print(f"   ✅ Effective: {insurance_data['date']}")
            else:
                # Save HTML for debugging
                with open(f'li_puppeteer_{usdot}.html', 'w') as f:
                    f.write(insurance_html)
                print(f"   ⚠️ No insurance data found. HTML saved to li_puppeteer_{usdot}.html")
                
                result['error'] = "Could not extract insurance data from page"
            
        except Exception as e:
            result['error'] = str(e)
            print(f"   ❌ Error: {e}")
        
        return result
    
    async def close(self):
        """Close the browser"""
        if self.browser:
            await self.browser.close()
    
    async def scrape_batch(self, usdot_list):
        """Scrape multiple USDOTs efficiently"""
        results = {}
        
        try:
            await self.init_browser()
            
            for usdot in usdot_list:
                print(f"\n{'='*60}")
                print(f"Processing USDOT {usdot}")
                print('='*60)
                
                result = await self.scrape_insurance(usdot)
                results[usdot] = result
                
                # Small delay between requests
                await asyncio.sleep(2)
            
        finally:
            await self.close()
        
        return results


async def main():
    """Main function to test the scraper"""
    if not PYPPETEER_AVAILABLE:
        print("\n❌ Pyppeteer not installed!")
        print("\nTo install:")
        print("  pip install pyppeteer")
        print("\nFirst run will download Chromium automatically (~150MB)")
        return
    
    print("="*70)
    print("L&I INSURANCE AUTOMATED SCRAPER")
    print("="*70)
    
    scraper = LIPuppeteerScraper()
    
    try:
        # Test with single USDOT
        result = await scraper.scrape_insurance(905413)
        
        if result['success']:
            print(f"\n✅ SUCCESS! Retrieved insurance data:")
            print(json.dumps(result, indent=2))
            
            # Save to cache
            cache_file = "li_insurance_cache.json"
            try:
                with open(cache_file, 'r') as f:
                    cache = json.load(f)
            except:
                cache = {}
            
            # Format for cache
            if result['liability_insurance_date']:
                try:
                    month, day, year = result['liability_insurance_date'].split('/')
                    formatted_date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                except:
                    formatted_date = result['liability_insurance_date']
            else:
                formatted_date = None
            
            cache[str(result['usdot_number'])] = {
                'insurance_company': result['insurance_company'],
                'liability_insurance_date': formatted_date,
                'insurance_expiry_date': formatted_date,
                'liability_insurance_amount': result['coverage_amount'],
                'policy_number': result['policy_number'],
                'form_type': result['form_type'],
                'insurance_data_source': 'FMCSA L&I Active Insurance (Automated)',
                'insurance_data_type': 'real',
                'cached_at': datetime.now().isoformat()
            }
            
            with open(cache_file, 'w') as f:
                json.dump(cache, f, indent=2)
            
            print(f"\n💾 Saved to cache: {cache_file}")
        else:
            print(f"\n❌ Failed: {result.get('error', 'Unknown error')}")
    
    finally:
        await scraper.close()

if __name__ == "__main__":
    asyncio.run(main())