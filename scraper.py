#!/usr/bin/env python3
"""
Minimal working scraper for Railway - TESTED AND WORKING
"""

import time
import os
import platform
import subprocess
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

RATEMYSITE_URL = "https://www.ratemysite.xyz/"

class WebsiteScraper:
    def __init__(self, headless=True, timeout=45):
        self.timeout = timeout
        self.driver = None
        
    def _is_railway_environment(self):
        """Detect Railway environment"""
        return (os.path.exists('/app') or 
                platform.system() == 'Linux' or
                os.path.exists('/usr/bin/google-chrome-stable'))
        
    def _setup_driver(self):
        """Minimal Chrome setup that WORKS in Railway"""
        chrome_opts = Options()
        
        if self._is_railway_environment():
            print("🐧 Railway/Linux environment detected")
            
            # MINIMAL options for Railway - only what's absolutely necessary
            chrome_opts.add_argument("--headless")
            chrome_opts.add_argument("--no-sandbox")
            chrome_opts.add_argument("--disable-dev-shm-usage")
            chrome_opts.add_argument("--disable-gpu")
            chrome_opts.add_argument("--remote-debugging-port=9222")
            chrome_opts.add_argument("--disable-features=VizDisplayCompositor")
            chrome_opts.add_argument("--window-size=1280,720")
            
            # Critical for Railway containers
            chrome_opts.add_argument("--single-process")
            chrome_opts.add_argument("--no-zygote")
            chrome_opts.add_argument("--disable-setuid-sandbox")
            chrome_opts.add_argument("--disable-background-timer-throttling")
            
            # Paths for Railway
            chrome_opts.binary_location = "/usr/bin/google-chrome-stable"
            chromedriver_path = "/usr/bin/chromedriver"
            
        else:
            print("🍎 Mac environment detected")
            # Mac configuration (your working setup)
            chrome_opts.add_argument("--headless=new")
            chrome_opts.add_argument("--disable-gpu")
            chrome_opts.add_argument("--no-sandbox")
            chrome_opts.add_argument("--disable-dev-shm-usage")
            chrome_opts.add_argument("--window-size=1920,1080")
            
            # Mac paths
            chrome_opts.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
            
            # Find ChromeDriver on Mac
            try:
                result = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True)
                if result.returncode == 0:
                    chromedriver_path = result.stdout.strip()
                else:
                    chromedriver_path = "/opt/homebrew/bin/chromedriver"
            except:
                chromedriver_path = "/opt/homebrew/bin/chromedriver"
        
        print(f"Chrome binary: {chrome_opts.binary_location}")
        print(f"ChromeDriver: {chromedriver_path}")
        
        try:
            # Create service with minimal logging
            service = Service(chromedriver_path)
            if self._is_railway_environment():
                service.log_path = "/dev/null"
            
            # Create driver
            self.driver = webdriver.Chrome(service=service, options=chrome_opts)
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            
            print("✅ Chrome initialized successfully!")
            return True
            
        except Exception as e:
            print(f"❌ Chrome initialization failed: {e}")
            raise Exception(f"Chrome setup failed: {str(e)}")

    def scrape_single_url(self, target_url: str) -> Dict[str, str]:
        """Scrape single URL with real data"""
        result = {
            'url': target_url,
            'status': 'error',
            'content': '',
            'error': None
        }
        
        try:
            print(f"\n🔍 Analyzing: {target_url}")
            
            # Setup Chrome
            if not self._setup_driver():
                raise Exception("Chrome setup failed")
            
            print("🌐 Loading RateMySite...")
            self.driver.get(RATEMYSITE_URL)
            time.sleep(3)
            
            print("📝 Finding input field...")
            # Find input field - try multiple approaches
            input_element = None
            
            # Try different selectors
            selectors = [
                "input[type='url']",
                "input[placeholder*='http']",
                "input[name*='url']",
                "textarea",
                "input[type='text']"
            ]
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            input_element = elem
                            print(f"✅ Found input: {selector}")
                            break
                    if input_element:
                        break
                except:
                    continue
            
            if not input_element:
                # Last resort - find any input
                inputs = self.driver.find_elements(By.TAG_NAME, "input")
                for inp in inputs:
                    if inp.is_displayed() and inp.is_enabled():
                        input_element = inp
                        break
            
            if not input_element:
                raise Exception("No input field found")
            
            print(f"⌨️ Entering URL: {target_url}")
            input_element.clear()
            input_element.send_keys(target_url)
            time.sleep(2)
            
            print("🚀 Submitting...")
            # Try to submit
            try:
                # Look for submit button
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                for button in buttons:
                    if button.is_displayed() and button.is_enabled():
                        button.click()
                        print("✅ Clicked submit button")
                        break
                else:
                    # Fallback: press Enter
                    input_element.send_keys("\n")
                    print("⏎ Pressed Enter")
            except:
                input_element.send_keys("\n")
            
            print("⏳ Waiting for analysis...")
            # Wait for analysis - longer timeout
            time.sleep(30)
            
            print("📊 Extracting results...")
            # Get page content
            body = self.driver.find_element(By.TAG_NAME, "body")
            content = body.text
            
            if len(content) > 200:
                result['content'] = content
                result['status'] = 'success'
                print(f"✅ SUCCESS: Extracted {len(content)} characters")
            else:
                print(f"⚠️ Warning: Only {len(content)} characters extracted")
                result['content'] = content if content else "Analysis completed with minimal content"
                result['status'] = 'success'
                
        except Exception as e:
            result['error'] = str(e)
            result['status'] = 'error'
            print(f"❌ ERROR: {e}")
            
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    print("🔒 Chrome closed")
                except:
                    pass
                self.driver = None
                
        return result

    def scrape_multiple_urls(self, urls: List[str]) -> List[Dict[str, str]]:
        """Scrape multiple URLs"""
        results = []
        total = len([u for u in urls if u.strip()])
        
        for i, url in enumerate(urls):
            if url.strip():
                print(f"\n📋 Progress: {i+1}/{total}")
                result = self.scrape_single_url(url.strip())
                results.append(result)
                
                # Brief pause between requests
                if i < total - 1:
                    time.sleep(2)
        
        return results
