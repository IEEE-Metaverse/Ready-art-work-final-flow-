#!/usr/bin/env python3
"""
Scraper optimized for Railway with improved Chrome handling
"""

import time
import os
import tempfile
import shutil
from typing import Optional, List, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import *
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

RATEMYSITE_URL = "https://www.ratemysite.xyz/"
DEFAULT_TIMEOUT = 20

class WebsiteScraper:
    def __init__(self, headless=True, timeout=DEFAULT_TIMEOUT):
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        self.temp_dir = None
        
    def _setup_driver(self):
        """Setup Chrome driver with Railway-optimized settings"""
        try:
            # Create temporary directory for Chrome data
            self.temp_dir = tempfile.mkdtemp()
            
            chrome_opts = Options()
            
            # Critical Railway settings
            chrome_opts.add_argument("--headless=new")
            chrome_opts.add_argument("--no-sandbox")
            chrome_opts.add_argument("--disable-dev-shm-usage")
            chrome_opts.add_argument("--disable-gpu")
            chrome_opts.add_argument("--remote-debugging-port=9222")
            
            # Data directory settings
            chrome_opts.add_argument(f"--user-data-dir={self.temp_dir}")
            chrome_opts.add_argument(f"--crash-dumps-dir={self.temp_dir}")
            chrome_opts.add_argument("--disable-dev-shm-usage")
            
            # Process and memory settings
            chrome_opts.add_argument("--single-process")
            chrome_opts.add_argument("--no-zygote")
            chrome_opts.add_argument("--disable-setuid-sandbox")
            
            # Window settings
            chrome_opts.add_argument("--window-size=1280,720")
            chrome_opts.add_argument("--disable-web-security")
            chrome_opts.add_argument("--allow-running-insecure-content")
            
            # Disable features that can cause issues
            chrome_opts.add_argument("--disable-features=VizDisplayCompositor")
            chrome_opts.add_argument("--disable-extensions")
            chrome_opts.add_argument("--disable-plugins")
            chrome_opts.add_argument("--disable-background-timer-throttling")
            chrome_opts.add_argument("--disable-backgrounding-occluded-windows")
            chrome_opts.add_argument("--disable-renderer-backgrounding")
            
            # Set Chrome binary
            chrome_opts.binary_location = "/usr/bin/google-chrome-stable"
            
            # Logging settings
            chrome_opts.add_argument("--log-level=3")
            chrome_opts.add_argument("--silent")
            
            print(f"Chrome binary: {chrome_opts.binary_location}")
            print(f"Temp directory: {self.temp_dir}")
            
            # Initialize service
            service = Service(
                executable_path="/usr/bin/chromedriver",
                log_path=os.path.join(self.temp_dir, "chromedriver.log")
            )
            
            # Create driver
            self.driver = webdriver.Chrome(service=service, options=chrome_opts)
            
            # Set timeouts
            self.driver.set_page_load_timeout(self.timeout)
            self.driver.implicitly_wait(5)
            
            print("Chrome driver initialized successfully")
            return WebDriverWait(self.driver, self.timeout)
            
        except Exception as e:
            print(f"Failed to initialize Chrome: {e}")
            self._cleanup_temp_dir()
            raise Exception(f"Chrome initialization failed: {str(e)}")

    def _cleanup_temp_dir(self):
        """Clean up temporary directory"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                print(f"Failed to cleanup temp directory: {e}")

    def scrape_single_url(self, target_url: str) -> Dict[str, str]:
        """Scrape a single URL and return results"""
        result = {
            'url': target_url,
            'status': 'success',
            'content': '',
            'error': None
        }
        
        try:
            print(f"Starting analysis for: {target_url}")
            wait = self._setup_driver()
            
            print("Navigating to RateMySite...")
            self.driver.get(RATEMYSITE_URL)
            time.sleep(3)

            # Find input field
            print("Looking for input field...")
            input_el = None
            input_selectors = [
                "input[type='url']",
                "input[placeholder*='http']",
                "input[placeholder*='website']",
                "input",
                "textarea"
            ]
            
            for selector in input_selectors:
                try:
                    input_el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    if input_el.is_displayed():
                        break
                except:
                    continue
            
            if not input_el:
                raise Exception("Could not find input field on RateMySite")

            print(f"Entering URL: {target_url}")
            input_el.clear()
            input_el.send_keys(target_url)
            time.sleep(2)

            # Submit form
            print("Submitting form...")
            try:
                # Try to find submit button
                submit_selectors = [
                    "button[type='submit']",
                    "button:contains('Analyze')",
                    "button:contains('Submit')",
                    "button",
                    "input[type='submit']"
                ]
                
                submitted = False
                for selector in submit_selectors:
                    try:
                        btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if btn.is_displayed() and btn.is_enabled():
                            self.driver.execute_script("arguments[0].click();", btn)
                            submitted = True
                            break
                    except:
                        continue
                
                if not submitted:
                    # Fallback: press Enter
                    input_el.send_keys("\n")
                
            except Exception as e:
                print(f"Submit failed, trying Enter key: {e}")
                input_el.send_keys("\n")

            print("Waiting for results...")
            # Wait longer for analysis to complete
            time.sleep(20)
            
            # Try to find results
            try:
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            except:
                pass
            
            # Extract content
            print("Extracting content...")
            content = ""
            
            # Get page text
            try:
                body = self.driver.find_element(By.TAG_NAME, "body")
                content = body.text or ""
            except Exception as e:
                print(f"Failed to extract body text: {e}")
                content = ""
            
            if content and len(content) > 100:
                result['content'] = content
                print(f"Successfully extracted {len(content)} characters")
            else:
                result['content'] = "Analysis completed but limited content extracted"
                print("Limited content extracted")
            
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            print(f"Error analyzing {target_url}: {e}")
            
        finally:
            # Cleanup
            if self.driver:
                try:
                    self.driver.quit()
                except Exception as e:
                    print(f"Error closing driver: {e}")
                self.driver = None
            
            self._cleanup_temp_dir()
                
        return result

    def scrape_multiple_urls(self, urls: List[str]) -> List[Dict[str, str]]:
        """Scrape multiple URLs"""
        results = []
        for url in urls:
            if url.strip():
                result = self.scrape_single_url(url.strip())
                results.append(result)
        return results
