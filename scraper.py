#!/usr/bin/env python3
"""
Real scraper for Railway - no mock data, only actual results
"""

import time
import os
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

RATEMYSITE_URL = "https://www.ratemysite.xyz/"
DEFAULT_TIMEOUT = 30

class WebsiteScraper:
    def __init__(self, headless=True, timeout=DEFAULT_TIMEOUT):
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        
    def _setup_driver(self):
        """Setup Chrome with Railway-specific container optimizations"""
        chrome_opts = Options()
        
        # Essential for Railway container
        chrome_opts.add_argument("--headless=new")
        chrome_opts.add_argument("--no-sandbox")
        chrome_opts.add_argument("--disable-dev-shm-usage")
        chrome_opts.add_argument("--disable-gpu")
        chrome_opts.add_argument("--disable-software-rasterizer")
        
        # Process isolation settings for containers
        chrome_opts.add_argument("--no-zygote")
        chrome_opts.add_argument("--disable-features=VizDisplayCompositor")
        chrome_opts.add_argument("--disable-dev-shm-usage")
        
        # Memory and resource optimization
        chrome_opts.add_argument("--memory-pressure-off")
        chrome_opts.add_argument("--disable-background-timer-throttling")
        chrome_opts.add_argument("--disable-backgrounding-occluded-windows")
        chrome_opts.add_argument("--disable-renderer-backgrounding")
        chrome_opts.add_argument("--disable-features=TranslateUI")
        chrome_opts.add_argument("--disable-ipc-flooding-protection")
        
        # Minimal window and display
        chrome_opts.add_argument("--window-size=1024,768")
        chrome_opts.add_argument("--virtual-time-budget=5000")
        
        # Network and security
        chrome_opts.add_argument("--disable-web-security")
        chrome_opts.add_argument("--disable-features=VizDisplayCompositor")
        chrome_opts.add_argument("--ignore-certificate-errors")
        chrome_opts.add_argument("--ignore-ssl-errors")
        chrome_opts.add_argument("--ignore-certificate-errors-spki-list")
        
        # Disable unnecessary features to reduce resource usage
        chrome_opts.add_argument("--disable-extensions")
        chrome_opts.add_argument("--disable-plugins")
        chrome_opts.add_argument("--disable-default-apps")
        chrome_opts.add_argument("--disable-sync")
        
        # Logging reduction
        chrome_opts.add_argument("--log-level=3")
        chrome_opts.add_argument("--silent")
        chrome_opts.add_argument("--disable-logging")
        
        # Set Chrome binary location
        chrome_opts.binary_location = "/usr/bin/google-chrome-stable"
        
        # User agent
        chrome_opts.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Additional Railway-specific fixes
        chrome_opts.add_argument("--disable-dev-shm-usage")
        chrome_opts.add_argument("--remote-debugging-port=9222")
        chrome_opts.add_argument("--disable-gpu-sandbox")
        chrome_opts.add_argument("--disable-software-rasterizer")
        chrome_opts.add_argument("--disable-background-timer-throttling")
        
        try:
            print("Initializing Chrome driver...")
            service = Service("/usr/bin/chromedriver")
            
            self.driver = webdriver.Chrome(service=service, options=chrome_opts)
            self.driver.set_page_load_timeout(self.timeout)
            self.driver.implicitly_wait(10)
            
            print("Chrome driver initialized successfully")
            return WebDriverWait(self.driver, self.timeout)
            
        except Exception as e:
            print(f"Chrome initialization failed: {e}")
            raise Exception(f"Failed to initialize Chrome: {str(e)}")

    def scrape_single_url(self, target_url: str) -> Dict[str, str]:
        """Scrape a single URL - REAL DATA ONLY"""
        result = {
            'url': target_url,
            'status': 'error',
            'content': '',
            'error': None
        }
        
        try:
            print(f"Starting real analysis for: {target_url}")
            wait = self._setup_driver()
            
            # Navigate to RateMySite
            print("Navigating to RateMySite...")
            self.driver.get(RATEMYSITE_URL)
            time.sleep(5)  # Wait for page load
            
            # Find the input field
            print("Looking for input field...")
            input_selectors = [
                "input[type='url']",
                "input[placeholder*='http']",
                "input[placeholder*='website']",
                "input[placeholder*='URL']",
                "input[name*='url']",
                "input[id*='url']",
                "textarea",
                "input[type='text']"
            ]
            
            input_element = None
            for selector in input_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            input_element = elem
                            print(f"Found input field with selector: {selector}")
                            break
                    if input_element:
                        break
                except:
                    continue
            
            if not input_element:
                raise Exception("Could not find URL input field on RateMySite")
            
            # Clear and enter the target URL
            print(f"Entering URL: {target_url}")
            input_element.clear()
            input_element.send_keys(target_url)
            time.sleep(2)
            
            # Find and click submit button
            print("Looking for submit button...")
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                ".submit-btn",
                ".analyze-btn",
                "button"
            ]
            
            # Handle text-based button searches separately
            text_searches = ["Analyze", "Submit", "Start", "Rate"]
            
            submitted = False
            
            # First try CSS selectors
            for selector in submit_selectors:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for button in buttons:
                        if button.is_displayed() and button.is_enabled():
                            print(f"Found submit button: {selector}")
                            self.driver.execute_script("arguments[0].scrollIntoView();", button)
                            time.sleep(1)
                            self.driver.execute_script("arguments[0].click();", button)
                            submitted = True
                            break
                    if submitted:
                        break
                except Exception as e:
                    print(f"Button selector {selector} failed: {e}")
                    continue
            
            # Then try text-based searches using XPath
            if not submitted:
                for text in text_searches:
                    try:
                        xpath = f"//button[contains(text(), '{text}')]"
                        buttons = self.driver.find_elements(By.XPATH, xpath)
                        for button in buttons:
                            if button.is_displayed() and button.is_enabled():
                                print(f"Found submit button with text: {text}")
                                self.driver.execute_script("arguments[0].scrollIntoView();", button)
                                time.sleep(1)
                                self.driver.execute_script("arguments[0].click();", button)
                                submitted = True
                                break
                        if submitted:
                            break
                    except Exception as e:
                        print(f"Text search for '{text}' failed: {e}")
                        continue
            
            if not submitted:
                print("No submit button found, trying Enter key...")
                input_element.send_keys("\n")
            
            print("Form submitted, waiting for analysis results...")
            
            # Wait for analysis to complete (longer timeout)
            analysis_timeout = 45  # seconds
            start_time = time.time()
            
            while time.time() - start_time < analysis_timeout:
                time.sleep(3)
                
                # Check for results content
                try:
                    # Look for result containers or significant content
                    page_text = self.driver.find_element(By.TAG_NAME, "body").text
                    
                    # Check if we have substantial content that looks like analysis
                    if (len(page_text) > 500 and 
                        any(keyword in page_text.lower() for keyword in 
                            ['score', 'analysis', 'rating', 'result', 'report', 'review'])):
                        print("Analysis content detected!")
                        break
                        
                except Exception as e:
                    print(f"Content check failed: {e}")
                
                print(f"Still waiting for analysis... ({time.time() - start_time:.1f}s)")
            
            # Extract final content
            print("Extracting analysis results...")
            try:
                final_content = self.driver.find_element(By.TAG_NAME, "body").text
                
                if len(final_content) > 200:
                    result['content'] = final_content
                    result['status'] = 'success'
                    print(f"Successfully extracted {len(final_content)} characters of analysis")
                else:
                    raise Exception("Insufficient content extracted - analysis may not have completed")
                    
            except Exception as e:
                raise Exception(f"Failed to extract analysis content: {str(e)}")
            
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            print(f"Error analyzing {target_url}: {e}")
            
        finally:
            # Always cleanup
            if self.driver:
                try:
                    self.driver.quit()
                    print("Chrome driver closed")
                except Exception as e:
                    print(f"Error closing driver: {e}")
                self.driver = None
                
        return result

    def scrape_multiple_urls(self, urls: List[str]) -> List[Dict[str, str]]:
        """Scrape multiple URLs sequentially"""
        results = []
        for i, url in enumerate(urls):
            if url.strip():
                print(f"Processing URL {i+1}/{len(urls)}: {url}")
                result = self.scrape_single_url(url.strip())
                results.append(result)
                
                # Small delay between URLs to avoid overwhelming
                if i < len(urls) - 1:
                    time.sleep(2)
        
        return results
