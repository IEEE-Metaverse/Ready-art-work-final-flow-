#!/usr/bin/env python3
"""
Minimal Chrome setup for Railway containers - REAL SCRAPING ONLY
"""

import time
import os
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

RATEMYSITE_URL = "https://www.ratemysite.xyz/"

class WebsiteScraper:
    def __init__(self, headless=True, timeout=30):
        self.timeout = timeout
        self.driver = None
        
    def _setup_driver(self):
        """Ultra-minimal Chrome setup for Railway"""
        chrome_opts = Options()
        
        # ONLY the absolutely essential options for Railway
        chrome_opts.add_argument("--headless")
        chrome_opts.add_argument("--no-sandbox")
        chrome_opts.add_argument("--disable-dev-shm-usage")
        chrome_opts.add_argument("--single-process")  # Critical for Railway
        chrome_opts.add_argument("--disable-gpu")
        chrome_opts.add_argument("--remote-debugging-port=9222")
        chrome_opts.add_argument("--window-size=800,600")
        chrome_opts.add_argument("--disable-web-security")
        chrome_opts.add_argument("--disable-features=VizDisplayCompositor")
        
        # Set binary explicitly
        chrome_opts.binary_location = "/usr/bin/google-chrome-stable"
        
        try:
            service = Service("/usr/bin/chromedriver")
            service.log_path = "/dev/null"  # Suppress logs
            
            self.driver = webdriver.Chrome(service=service, options=chrome_opts)
            self.driver.set_page_load_timeout(20)
            self.driver.implicitly_wait(5)
            
            print("✅ Chrome initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Chrome failed: {e}")
            return False

    def scrape_single_url(self, target_url: str) -> Dict[str, str]:
        """Real scraping with minimal Chrome"""
        result = {
            'url': target_url,
            'status': 'error',
            'content': '',
            'error': None
        }
        
        try:
            print(f"🔍 Starting analysis: {target_url}")
            
            if not self._setup_driver():
                raise Exception("Chrome initialization failed")
            
            # Navigate to RateMySite
            print("🌐 Loading RateMySite...")
            self.driver.get(RATEMYSITE_URL)
            time.sleep(3)
            
            # Find input and enter URL
            print("📝 Entering URL...")
            input_elem = self.driver.find_element(By.CSS_SELECTOR, "input")
            input_elem.clear()
            input_elem.send_keys(target_url)
            time.sleep(1)
            
            # Submit
            print("🚀 Submitting...")
            try:
                submit_btn = self.driver.find_element(By.CSS_SELECTOR, "button")
                submit_btn.click()
            except:
                input_elem.send_keys("\n")
            
            # Wait for results
            print("⏳ Waiting for analysis...")
            time.sleep(25)  # Give time for analysis
            
            # Extract content
            print("📊 Extracting results...")
            content = self.driver.find_element(By.TAG_NAME, "body").text
            
            if len(content) > 300:
                result['content'] = content
                result['status'] = 'success'
                print(f"✅ Success: {len(content)} chars extracted")
            else:
                raise Exception("Insufficient content - analysis incomplete")
                
        except Exception as e:
            result['error'] = str(e)
            print(f"❌ Error: {e}")
            
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass
                self.driver = None
                
        return result

    def scrape_multiple_urls(self, urls: List[str]) -> List[Dict[str, str]]:
        """Scrape multiple URLs"""
        results = []
        for i, url in enumerate(urls):
            if url.strip():
                print(f"\n📋 Processing {i+1}/{len(urls)}")
                result = self.scrape_single_url(url.strip())
                results.append(result)
        return results
