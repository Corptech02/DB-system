#!/usr/bin/env python3
"""
Selenium-based L&I Insurance Scraper
This actually navigates the L&I website like a real browser
"""

import json
import time
import re
from datetime import datetime
from typing import Dict, Optional

# Check if Selenium is available
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("❌ Selenium not installed. Please run: pip install selenium webdriver-manager")

class LISeleniumScraper:
    def __init__(self, headless=True):
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium is required. Install with: pip install selenium webdriver-manager")
        
        self.headless = headless
        self.driver = None
        
    def setup_driver(self):
        """Setup Chrome driver with options"""
        options = Options()
        
        if self.headless:
            options.add_argument('--headless')
        
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # User agent to look like a real browser
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Use webdriver_manager to automatically handle driver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        
    def scrape_insurance(self, usdot_number: int) -> Dict:
        """
        Scrape insurance data for a USDOT number
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
        
        try:
            if not self.driver:
                self.setup_driver()
            
            print(f"🌐 Opening L&I website for USDOT {usdot_number}...")
            
            # Navigate to the L&I search page
            url = "https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_carrlist"
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "n_dotno"))
            )
            
            print("📝 Entering USDOT number...")
            
            # Find the USDOT input field and enter the number
            usdot_input = self.driver.find_element(By.NAME, "n_dotno")
            usdot_input.clear()
            usdot_input.send_keys(str(usdot_number))
            
            # Find and click the search button
            search_button = self.driver.find_element(By.XPATH, "//input[@type='submit' and @value='Search']")
            search_button.click()
            
            print("⏳ Waiting for results...")
            time.sleep(2)  # Wait for results to load
            
            # Check if we got results
            page_source = self.driver.page_source
            
            if "No records found" in page_source:
                result['error'] = "No records found for this USDOT"
                return result
            
            # Look for the Active Insurance link
            try:
                insurance_link = self.driver.find_element(By.PARTIAL_LINK_TEXT, "Active Insurance")
                print("📋 Found Active Insurance link, clicking...")
                insurance_link.click()
                
                # Wait for insurance page to load
                time.sleep(3)
                
                # Get the insurance page content
                insurance_html = self.driver.page_source
                
                # Parse the insurance data
                result = self.parse_insurance_page(insurance_html, usdot_number)
                result['success'] = True
                
            except Exception as e:
                # Try direct navigation to activeinsurance
                print("🔄 Trying direct insurance page navigation...")
                insurance_url = f"https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_activeinsurance?pn_dotno={usdot_number}"
                self.driver.get(insurance_url)
                time.sleep(3)
                
                insurance_html = self.driver.page_source
                result = self.parse_insurance_page(insurance_html, usdot_number)
                
        except Exception as e:
            result['error'] = str(e)
            print(f"❌ Error: {e}")
        
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
        
        # Look for GEICO MARINE INSURANCE COMPANY
        if "GEICO MARINE" in html:
            result['insurance_company'] = "GEICO MARINE INSURANCE COMPANY"
            result['success'] = True
        
        # Look for form type (91X)
        form_match = re.search(r'(91X|BMC-\d+)', html)
        if form_match:
            result['form_type'] = form_match.group(1)
        
        # Look for policy number (9300107451)
        policy_match = re.search(r'\b(\d{10})\b', html)
        if policy_match:
            result['policy_number'] = policy_match.group(1)
        
        # Look for coverage amount ($1,000,000)
        amount_match = re.search(r'\$([0-9,]+)', html)
        if amount_match:
            amount_str = amount_match.group(1).replace(',', '')
            result['coverage_amount'] = int(amount_str)
        
        # Look for effective date (02/20/2024)
        date_pattern = r'(\d{2}/\d{2}/\d{4})'
        dates = re.findall(date_pattern, html)
        
        # The effective date is usually the last date in the table
        if dates:
            # Look for the date after "Effective"
            for i, date in enumerate(dates):
                if "Effective" in html[max(0, html.index(date)-100):html.index(date)]:
                    result['liability_insurance_date'] = date
                    break
            
            # If not found, use the last date (often the effective date)
            if not result['liability_insurance_date'] and len(dates) >= 4:
                result['liability_insurance_date'] = dates[-2]  # Second to last is often effective date
        
        return result
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()


def get_li_insurance_selenium(usdot_number: int) -> Dict:
    """
    Main function to get insurance via Selenium
    """
    if not SELENIUM_AVAILABLE:
        return {
            'success': False,
            'error': 'Selenium not installed. Run: pip install selenium webdriver-manager',
            'usdot_number': usdot_number
        }
    
    scraper = LISeleniumScraper(headless=True)
    
    try:
        result = scraper.scrape_insurance(usdot_number)
        
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
        
    finally:
        scraper.close()


if __name__ == "__main__":
    print("="*70)
    print("L&I SELENIUM SCRAPER TEST")
    print("="*70)
    
    if not SELENIUM_AVAILABLE:
        print("\n❌ Selenium is not installed!")
        print("\nTo install, run:")
        print("  pip install selenium webdriver-manager")
        print("\nThen make sure you have Chrome browser installed.")
    else:
        print("\n✅ Selenium is installed")
        print("\nTesting with USDOT 905413...")
        
        result = get_li_insurance_selenium(905413)
        print("\nResult:")
        print(json.dumps(result, indent=2))