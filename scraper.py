#!/usr/bin/env python3
"""
Scraper optimized for Railway deployment with container-specific Chrome settings
"""

import time
import os
from typing import Optional, List, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

RATEMYSITE_URL = "https://www.ratemysite.xyz/"
DEFAULT_TIMEOUT = 30  # Reduced timeout for faster response

class WebsiteScraper:
    def __init__(self, headless=True, timeout=DEFAULT_TIMEOUT):
        self.headless = headless
        self.timeout = timeout
        self.driver = None
        
    def _setup_driver(self):
        """Setup Chrome driver optimized for Railway container deployment"""
        chrome_opts = Options()
        
        # Critical options for Railway container environment
        chrome_opts.add_argument("--headless=new")
        chrome_opts.add_argument("--no-sandbox")
        chrome_opts.add_argument("--disable-dev-shm-usage")
        chrome_opts.add_argument("--disable-gpu")
        chrome_opts.add_argument("--disable-software-rasterizer")
        chrome_opts.add_argument("--disable-background-timer-throttling")
        chrome_opts.add_argument("--disable-backgrounding-occluded-windows")
        chrome_opts.add_argument("--disable-renderer-backgrounding")
        chrome_opts.add_argument("--disable-features=TranslateUI")
        chrome_opts.add_argument("--disable-ipc-flooding-protection")
        chrome_opts.add_argument("--disable-features=VizDisplayCompositor")
        
        # Memory and resource optimizations for Railway
        chrome_opts.add_argument("--memory-pressure-off")
        chrome_opts.add_argument("--disable-features=VizDisplayCompositor")
        chrome_opts.add_argument("--disable-extensions")
        chrome_opts.add_argument("--disable-plugins")
        chrome_opts.add_argument("--disable-images")
        chrome_opts.add_argument("--disable-javascript")
        chrome_opts.add_argument("--disable-web-security")
        chrome_opts.add_argument("--allow-running-insecure-content")
        
        # Container-specific settings
        chrome_opts.add_argument("--single-process")
        chrome_opts.add_argument("--no-zygote")
        chrome_opts.add_argument("--disable-setuid-sandbox")
        chrome_opts.add_argument("--disable-dev-shm-usage")
        
        # Window and display settings
        chrome_opts.add_argument("--window-size=1280,720")
        chrome_opts.add_argument("--start-maximized")
        chrome_opts.add_argument("--disable-infobars")
        chrome_opts.add_argument("--disable-notifications")
        
        # Network and security settings
        chrome_opts.add_argument("--ignore-certificate-errors")
        chrome_opts.add_argument("--ignore-ssl-errors")
        chrome_opts.add_argument("--ignore-certificate-errors-spki-list")
        chrome_opts.add_argument("--ignore-certificate-errors-ssl-errors")
        
        # User agent
        chrome_opts.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Set Chrome binary path
        chrome_opts.binary_location = "/usr/bin/google-chrome-stable"
        
        # Disable logging to reduce noise
        chrome_opts.add_argument("--log-level=3")
        chrome_opts.add_argument("--silent")
        chrome_opts.add_argument("--disable-logging")
        chrome_opts.add_argument("--disable-gpu-logging")
        
        # Additional Railway-specific settings
        chrome_opts.add_argument("--remote-debugging-port=9222")
        chrome_opts.add_argument("--remote-debugging-address=0.0.0.0")
        
        print(f"Using Chrome binary at: {chrome_opts.binary_location}")
        print(f"Using ChromeDriver at: /usr/bin/chromedriver")
        
        try:
            service = Service(
                executable_path="/usr/bin/chromedriver",
                log_path='/tmp/chromedriver.log'
            )
            self.driver = webdriver.Chrome(service=service, options=chrome_opts)
            
            # Set timeouts
            self.driver.set_page_load_timeout(self.timeout)
            self.driver.implicitly_wait(10)
            
            print("Chrome browser initialized successfully")
            return WebDriverWait(self.driver, self.timeout)
            
        except Exception as e:
            print(f"Failed to initialize Chrome: {e}")
            # Try with additional fallback options
            try:
                chrome_opts.add_argument("--crash-dumps-dir=/tmp")
                chrome_opts.add_argument("--user-data-dir=/tmp/chrome-user-data")
                
                self.driver = webdriver.Chrome(service=service, options=chrome_opts)
                self.driver.set_page_load_timeout(self.timeout)
                self.driver.implicitly_wait(10)
                print("Chrome browser initialized with fallback options")
                return WebDriverWait(self.driver, self.timeout)
                
            except Exception as e2:
                print(f"Fallback Chrome initialization also failed: {e2}")
                raise Exception(f"Could not initialize Chrome browser: {str(e2)}")

    def _find_first(self, xpaths: List[str]) -> Optional[object]:
        """Find first matching element from list of xpaths"""
        for xp in xpaths:
            try:
                el = self.driver.find_element(By.XPATH, xp)
                if el and el.is_displayed():
                    return el
            except (NoSuchElementException, StaleElementReferenceException):
                continue
        return None

    def _click_best_button(self) -> bool:
        """Try to click analysis/submit button"""
        xpaths = [
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'analy')]",
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'rate')]",
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'submit')]",
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'),'generate')]",
            "//button[@type='submit']",
            "//button",
        ]
        btn = self._find_first(xpaths)
        if not btn:
            return False
        try:
            if btn.is_enabled():
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView();", btn)
                    time.sleep(0.5)
                    btn.click()
                except ElementClickInterceptedException:
                    self.driver.execute_script("arguments[0].click();", btn)
                return True
        except Exception:
            pass
        return False

    def _collect_result_text(self) -> str:
        """Extract result text from the page"""
        # Wait a bit for content to load
        time.sleep(2)
        
        containers = self.driver.find_elements(
            By.XPATH,
            "//*[contains(@class,'result') or contains(@class,'report') or contains(@class,'output')]",
        )
        texts = [c.text.strip() for c in containers if c.text and c.text.strip()]
        if texts:
            return "\n\n".join(texts).strip()

        # Fallback to body text
        try:
            body = self.driver.find_element(By.TAG_NAME, "body")
            return (body.text or "").strip()
        except Exception:
            return ""

    def scrape_single_url(self, target_url: str) -> Dict[str, str]:
        """Scrape a single URL and return results"""
        result = {
            'url': target_url,
            'status': 'success',
            'content': '',
            'error': None
        }
        
        try:
            print(f"Setting up browser for {target_url}...")
            wait = self._setup_driver()
        except Exception as e:
            result['status'] = 'error'
            result['error'] = f'Failed to initialize browser: {str(e)}'
            print(f"Browser setup failed: {e}")
            return result
        
        try:
            print(f"Navigating to RateMySite...")
            self.driver.get(RATEMYSITE_URL)
            time.sleep(2)

            # Find URL input - simplified approach
            input_el = None
            try:
                input_el = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='url']")))
            except:
                try:
                    input_el = self.driver.find_element(By.XPATH, "//input[contains(@placeholder,'http')]")
                except:
                    try:
                        input_el = self.driver.find_element(By.XPATH, "//input")
                    except:
                        pass

            if not input_el:
                result['status'] = 'error'
                result['error'] = 'Could not locate input field on RateMySite'
                return result

            print(f"Entering URL: {target_url}")
            input_el.clear()
            input_el.send_keys(target_url)
            time.sleep(1)

            print("Submitting for analysis...")
            # Try to submit
            clicked = self._click_best_button()
            if not clicked:
                input_el.send_keys("\n")

            print("Waiting for results...")
            # Wait for results with simpler approach
            time.sleep(15)  # Give more time for analysis

            # Extract content
            content = self._collect_result_text()
            result['content'] = content if content else 'Analysis completed but no detailed content found'
            print(f"Analysis complete for {target_url}")
            
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            print(f"Error analyzing {target_url}: {e}")
            
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except Exception:
                    pass
                self.driver = None
                
        return result

    def scrape_multiple_urls(self, urls: List[str]) -> List[Dict[str, str]]:
        """Scrape multiple URLs"""
        results = []
        for url in urls:
            if url.strip():  # Only process non-empty URLs
                result = self.scrape_single_url(url.strip())
                results.append(result)
        return results
