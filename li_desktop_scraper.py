#!/usr/bin/env python3
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
        