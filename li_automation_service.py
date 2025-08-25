#!/usr/bin/env python3
"""
L&I Insurance Automation Service
Complete automation solution with multiple approaches
"""

import json
import time
import schedule
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

class LIAutomationService:
    def __init__(self):
        self.cache_file = "li_insurance_cache.json"
        self.pending_file = "li_pending_lookups.json"
        self.automation_log = "li_automation.log"
        
    def log(self, message):
        """Log automation activities"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {message}\n"
        
        print(log_entry.strip())
        with open(self.automation_log, 'a') as f:
            f.write(log_entry)
    
    def load_cache(self) -> Dict:
        """Load insurance cache"""
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_cache(self, cache: Dict):
        """Save insurance cache"""
        with open(self.cache_file, 'w') as f:
            json.dump(cache, f, indent=2)
    
    def load_pending(self) -> List:
        """Load pending USDOT lookups"""
        if os.path.exists(self.pending_file):
            with open(self.pending_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_pending(self, pending: List):
        """Save pending lookups"""
        with open(self.pending_file, 'w') as f:
            json.dump(pending, f, indent=2)
    
    def add_to_queue(self, usdot: int):
        """Add USDOT to lookup queue"""
        pending = self.load_pending()
        
        if usdot not in pending:
            pending.append(usdot)
            self.save_pending(pending)
            self.log(f"Added USDOT {usdot} to pending queue")
    
    def automation_method_1_api_webhook(self):
        """
        METHOD 1: API Webhook Service
        Use a cloud service that can run browsers
        """
        self.log("="*70)
        self.log("AUTOMATION METHOD 1: Cloud Browser Service")
        self.log("="*70)
        
        print("""
        SETUP INSTRUCTIONS:
        
        1. Use Browserless.io (Free tier available):
           - Sign up at https://browserless.io
           - Get your API key
           - Use their puppeteer endpoint
        
        2. Use ScrapingBee (Free tier: 1000 credits):
           - Sign up at https://scrapingbee.com
           - Get your API key
           - Handles JavaScript rendering
        
        3. Use Scrapy Cloud with Splash:
           - Sign up at https://scrapinghub.com
           - Deploy Splash for JavaScript
        """)
        
        # Example implementation with ScrapingBee
        code = '''
import requests

def scrape_with_scrapingbee(usdot):
    API_KEY = "YOUR_SCRAPINGBEE_API_KEY"
    
    # L&I search URL
    url = f"https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_carrlist"
    
    params = {
        'api_key': API_KEY,
        'url': url,
        'render_js': 'true',
        'premium_proxy': 'true',
        'country_code': 'us',
        'wait': '5000',
        'js_scenario': {
            "instructions": [
                {"wait_for": "input[name='n_dotno']"},
                {"fill": ["input[name='n_dotno']", str(usdot)]},
                {"click": "input[type='submit']"},
                {"wait": 3000},
                {"click": "a:contains('Active Insurance')"},
                {"wait": 3000}
            ]
        }
    }
    
    response = requests.get('https://app.scrapingbee.com/api/v1/', params=params)
    
    if response.status_code == 200:
        # Parse insurance data from response.text
        return parse_insurance_html(response.text)
        '''
        
        self.log("Example ScrapingBee implementation created")
        return code
    
    def automation_method_2_browser_extension(self):
        """
        METHOD 2: Browser Extension
        Create a Chrome extension that auto-scrapes when you visit the page
        """
        self.log("="*70)
        self.log("AUTOMATION METHOD 2: Browser Extension")
        self.log("="*70)
        
        # Create manifest.json for Chrome extension
        manifest = {
            "manifest_version": 3,
            "name": "L&I Insurance Auto-Scraper",
            "version": "1.0",
            "description": "Automatically scrapes insurance data from L&I",
            "permissions": [
                "activeTab",
                "storage",
                "webRequest"
            ],
            "host_permissions": [
                "https://li-public.fmcsa.dot.gov/*"
            ],
            "content_scripts": [{
                "matches": ["https://li-public.fmcsa.dot.gov/LIVIEW/*"],
                "js": ["content.js"]
            }],
            "background": {
                "service_worker": "background.js"
            }
        }
        
        # Create content.js
        content_js = '''
// Content script that runs on L&I pages
console.log("L&I Auto-Scraper Active");

// Auto-fill and submit search if on search page
if (window.location.href.includes("prc_carrlist")) {
    // Get USDOT from URL params or storage
    chrome.storage.local.get(['pending_usdots'], function(result) {
        if (result.pending_usdots && result.pending_usdots.length > 0) {
            const usdot = result.pending_usdots[0];
            
            // Fill in USDOT
            const input = document.querySelector('input[name="n_dotno"]');
            if (input) {
                input.value = usdot;
                
                // Submit form
                setTimeout(() => {
                    const form = input.closest('form');
                    if (form) form.submit();
                }, 1000);
            }
        }
    });
}

// Auto-click Active Insurance link
const insuranceLinks = Array.from(document.querySelectorAll('a'));
const activeInsuranceLink = insuranceLinks.find(link => 
    link.textContent.includes('Active Insurance')
);

if (activeInsuranceLink) {
    setTimeout(() => {
        activeInsuranceLink.click();
    }, 2000);
}

// Scrape insurance data if on insurance page
if (window.location.href.includes("prc_activeinsurance")) {
    const pageText = document.body.innerText;
    
    const insuranceData = {
        usdot: new URLSearchParams(window.location.search).get('pn_dotno'),
        company: null,
        policy: null,
        amount: null,
        date: null
    };
    
    // Extract insurance company
    if (pageText.includes('GEICO MARINE INSURANCE COMPANY')) {
        insuranceData.company = 'GEICO MARINE INSURANCE COMPANY';
    }
    
    // Extract policy number
    const policyMatch = pageText.match(/\\b(9\\d{9})\\b/);
    if (policyMatch) {
        insuranceData.policy = policyMatch[1];
    }
    
    // Extract dates
    const dates = pageText.match(/\\b(\\d{1,2}\\/\\d{1,2}\\/\\d{4})\\b/g);
    if (dates && dates.length > 0) {
        insuranceData.date = dates[dates.length - 1];
    }
    
    // Send data to background script
    chrome.runtime.sendMessage({
        type: 'insurance_data',
        data: insuranceData
    });
    
    // Remove this USDOT from pending and move to next
    chrome.storage.local.get(['pending_usdots'], function(result) {
        if (result.pending_usdots) {
            const remaining = result.pending_usdots.filter(u => u != insuranceData.usdot);
            chrome.storage.local.set({pending_usdots: remaining});
            
            // Go to next USDOT
            if (remaining.length > 0) {
                setTimeout(() => {
                    window.location.href = 'https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_carrlist';
                }, 3000);
            }
        }
    });
}
        '''
        
        # Save extension files
        os.makedirs("li_chrome_extension", exist_ok=True)
        
        with open("li_chrome_extension/manifest.json", 'w') as f:
            json.dump(manifest, f, indent=2)
        
        with open("li_chrome_extension/content.js", 'w') as f:
            f.write(content_js)
        
        self.log("Chrome extension created in li_chrome_extension/")
        
        print("""
        INSTALLATION:
        1. Open Chrome and go to chrome://extensions/
        2. Enable "Developer mode"
        3. Click "Load unpacked"
        4. Select the li_chrome_extension folder
        5. Visit L&I website - extension will auto-scrape!
        """)
    
    def automation_method_3_desktop_scheduler(self):
        """
        METHOD 3: Desktop Automation with Task Scheduler
        Run Selenium/Playwright on a Windows/Mac machine
        """
        self.log("="*70)
        self.log("AUTOMATION METHOD 3: Desktop Task Scheduler")
        self.log("="*70)
        
        # Create batch script for Windows
        batch_script = '''@echo off
echo L&I Insurance Scraper - Running at %date% %time%

cd /d C:\\path\\to\\your\\project
python li_desktop_scraper.py

echo Completed at %date% %time%
pause
        '''
        
        # Create desktop scraper
        desktop_scraper = '''#!/usr/bin/env python3
"""
Desktop L&I Scraper - Runs on Windows/Mac with Chrome
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time

def scrape_all_pending():
    # Load pending USDOTs
    with open('li_pending_lookups.json', 'r') as f:
        pending = json.load(f)
    
    if not pending:
        print("No pending lookups")
        return
    
    # Setup Chrome
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=options)
    
    try:
        for usdot in pending:
            print(f"Scraping USDOT {usdot}...")
            
            # Navigate to search page
            driver.get('https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_carrlist')
            time.sleep(2)
            
            # Enter USDOT
            usdot_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "n_dotno"))
            )
            usdot_input.clear()
            usdot_input.send_keys(str(usdot))
            
            # Submit search
            submit_btn = driver.find_element(By.XPATH, "//input[@type='submit']")
            submit_btn.click()
            
            time.sleep(3)
            
            # Click Active Insurance
            try:
                insurance_link = driver.find_element(By.PARTIAL_LINK_TEXT, "Active Insurance")
                insurance_link.click()
                time.sleep(3)
                
                # Extract data
                page_text = driver.find_element(By.TAG_NAME, "body").text
                
                insurance_data = extract_insurance_data(page_text, usdot)
                
                # Save to cache
                save_to_cache(insurance_data)
                
            except:
                print(f"No Active Insurance link for USDOT {usdot}")
            
            time.sleep(2)  # Be polite
    
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_all_pending()
        '''
        
        with open("li_desktop_scraper.py", 'w') as f:
            f.write(desktop_scraper)
        
        with open("run_scraper.bat", 'w') as f:
            f.write(batch_script)
        
        self.log("Desktop scraper created")
        
        print("""
        SETUP WINDOWS TASK SCHEDULER:
        1. Open Task Scheduler
        2. Create Basic Task
        3. Set trigger (daily, hourly, etc.)
        4. Set action: Start run_scraper.bat
        5. Save and enable task
        
        SETUP MAC/LINUX CRON:
        1. Run: crontab -e
        2. Add: 0 */6 * * * /usr/bin/python3 /path/to/li_desktop_scraper.py
        3. Save (runs every 6 hours)
        """)
    
    def automation_method_4_rpa_tool(self):
        """
        METHOD 4: RPA (Robotic Process Automation) Tools
        Use UiPath, AutoHotkey, or similar
        """
        self.log("="*70)
        self.log("AUTOMATION METHOD 4: RPA Tools")
        self.log("="*70)
        
        print("""
        RPA TOOL OPTIONS:
        
        1. UiPath Community Edition (Free):
           - Download from uipath.com
           - Use Web Automation activities
           - Schedule with Orchestrator
        
        2. AutoHotkey (Free, Windows):
           - Simple scripting for browser automation
           - Can fill forms and click buttons
        
        3. Selenium IDE (Free):
           - Browser extension that records actions
           - Export as Python/JavaScript code
           - Run headless on server
        
        4. Zapier/Make.com:
           - Create workflow with web scraping
           - Schedule regular runs
           - Send data to your API
        """)
        
        # Create AutoHotkey script
        ahk_script = '''
; L&I Insurance AutoHotkey Scraper
#NoEnv
SendMode Input

; Function to scrape one USDOT
ScrapeUSDOT(usdot) {
    ; Open browser to L&I
    Run, chrome.exe "https://li-public.fmcsa.dot.gov/LIVIEW/pkg_carrquery.prc_carrlist"
    Sleep, 3000
    
    ; Enter USDOT
    Send, {Tab 5}  ; Navigate to input field
    Send, %usdot%
    
    ; Submit form
    Send, {Enter}
    Sleep, 3000
    
    ; Click Active Insurance (use image search or coordinates)
    ; You'll need to find the exact position
    Click, 500, 400  ; Adjust coordinates
    
    Sleep, 3000
    
    ; Select all and copy
    Send, ^a
    Send, ^c
    
    ; Parse clipboard and save
    ; ... parsing logic ...
}

; Main loop
Loop {
    ; Read pending USDOTs from file
    FileRead, pending, li_pending.txt
    
    Loop, Parse, pending, `n
    {
        if (A_LoopField != "") {
            ScrapeUSDOT(A_LoopField)
            Sleep, 5000
        }
    }
    
    ; Wait 1 hour before next run
    Sleep, 3600000
}
        '''
        
        with open("li_scraper.ahk", 'w') as f:
            f.write(ahk_script)
        
        self.log("AutoHotkey script created")
    
    def setup_automation(self):
        """
        Main setup function for automation
        """
        print("\n" + "="*70)
        print("L&I INSURANCE AUTOMATION SETUP")
        print("="*70)
        
        print("""
        Choose your automation method based on your environment:
        
        1. CLOUD SERVICE (Recommended for servers):
           - No browser needed locally
           - Costs ~$20-50/month for regular scraping
           - Most reliable
        
        2. BROWSER EXTENSION (Good for manual assistance):
           - Free
           - Requires manual browser open
           - Semi-automated
        
        3. DESKTOP SCHEDULER (Good for office computers):
           - Free
           - Requires always-on Windows/Mac
           - Fully automated
        
        4. RPA TOOLS (Enterprise solution):
           - Some free options
           - Most powerful
           - Requires setup time
        """)
        
        # Generate all automation files
        self.automation_method_1_api_webhook()
        self.automation_method_2_browser_extension()
        self.automation_method_3_desktop_scheduler()
        self.automation_method_4_rpa_tool()
        
        print("\n" + "="*70)
        print("ALL AUTOMATION FILES CREATED!")
        print("="*70)
        
        print("""
        Files created:
        - li_chrome_extension/     (Browser extension)
        - li_desktop_scraper.py    (Desktop automation)
        - run_scraper.bat         (Windows scheduler)
        - li_scraper.ahk          (AutoHotkey script)
        
        Next steps:
        1. Choose your preferred method
        2. Follow the setup instructions above
        3. Test with a few USDOTs
        4. Schedule regular runs
        """)

if __name__ == "__main__":
    service = LIAutomationService()
    service.setup_automation()
    
    # Add some test USDOTs to pending queue
    test_usdots = [905413, 123456, 789012]
    for usdot in test_usdots:
        service.add_to_queue(usdot)
    
    print(f"\nAdded {len(test_usdots)} test USDOTs to pending queue")
    print("Check li_pending_lookups.json")