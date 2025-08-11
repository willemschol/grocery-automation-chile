import asyncio
import time
import re
from typing import List, Dict
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class MobileAppScraper:
    """Android app automation for Jumbo and Lider price scraping"""
    
    def __init__(self):
        self.driver = None
        self.wait = None
        self.appium_port = 4723  # Default Appium port
        
    def setup_driver(self, app_package: str = None):
        """Initialize Appium driver for Android automation"""
        try:
            options = UiAutomator2Options()
            options.platform_name = "Android"
            options.device_name = "grocery_automation"
            options.automation_name = "UiAutomator2"
            options.no_reset = True
            
            if app_package:
                options.app_package = app_package
                
            self.driver = webdriver.Remote(f'http://localhost:{self.appium_port}', options=options)
            self.wait = WebDriverWait(self.driver, 15)
            
            print("✅ Appium driver initialized")
            return True
            
        except Exception as e:
            print(f"❌ Error setting up driver: {e}")
            return False
    
    def close_driver(self):
        """Clean up driver resources"""
        try:
            if self.driver:
                self.driver.quit()
        except Exception as e:
            print(f"Error closing driver: {e}")
    
    async def search_jumbo_app(self, product_name: str) -> List[Dict]:
        """Search Jumbo mobile app for products"""
        print(f"🔍 Searching Jumbo app for: {product_name}")
        
        try:
            # Common Jumbo app package names
            jumbo_packages = ['cl.jumbo.mobile', 'cl.jumbo.android', 'com.jumbo.cl']
            
            for package in jumbo_packages:
                if self.setup_driver(package):
                    break
            else:
                print("❌ Could not connect to Jumbo app")
                return []
            
            # Wait for app to load
            time.sleep(5)
            
            # Handle permissions and login if needed
            await self._handle_app_permissions()
            
            # Find search element
            search_selectors = [
                "//*[contains(@resource-id,'search')]",
                "//*[contains(@class,'search')]",
                "//*[contains(@content-desc,'search')]"
            ]
            
            search_element = None
            for selector in search_selectors:
                try:
                    search_element = self.wait.until(
                        EC.presence_of_element_located((AppiumBy.XPATH, selector))
                    )
                    break
                except:
                    continue
            
            if not search_element:
                print("❌ Could not find search element")
                return []
            
            # Perform search
            search_element.clear()
            search_element.send_keys(product_name)
            self.driver.press_keycode(66)  # Enter key
            
            # Wait for results
            time.sleep(5)
            
            # Extract products
            products = await self._extract_products("Jumbo")
            
            return products
            
        except Exception as e:
            print(f"❌ Error in Jumbo search: {e}")
            return []
        finally:
            self.close_driver()
    
    async def search_lider_app(self, product_name: str) -> List[Dict]:
        """Search Lider mobile app for products"""
        print(f"🔍 Searching Lider app for: {product_name}")
        
        try:
            # Common Lider app package names
            lider_packages = ['cl.lider.mobile', 'cl.lider.android', 'com.lider.cl', 'com.walmart.lider']
            
            for package in lider_packages:
                if self.setup_driver(package):
                    break
            else:
                print("❌ Could not connect to Lider app")
                return []
            
            # Wait for app to load
            time.sleep(5)
            
            # Handle permissions and login if needed
            await self._handle_app_permissions()
            
            # Find search element (similar to Jumbo)
            search_selectors = [
                "//*[contains(@resource-id,'search')]",
                "//*[contains(@class,'search')]",
                "//*[contains(@content-desc,'search')]"
            ]
            
            search_element = None
            for selector in search_selectors:
                try:
                    search_element = self.wait.until(
                        EC.presence_of_element_located((AppiumBy.XPATH, selector))
                    )
                    break
                except:
                    continue
            
            if not search_element:
                print("❌ Could not find search element")
                return []
            
            # Perform search
            search_element.clear()
            search_element.send_keys(product_name)
            self.driver.press_keycode(66)  # Enter key
            
            # Wait for results
            time.sleep(5)
            
            # Extract products
            products = await self._extract_products("Lider")
            
            return products
            
        except Exception as e:
            print(f"❌ Error in Lider search: {e}")
            return []
        finally:
            self.close_driver()
    
    async def _handle_app_permissions(self):
        """Handle common Android app permissions"""
        try:
            permission_buttons = ["ALLOW", "PERMITIR", "OK", "ACEPTAR"]
            
            for button_text in permission_buttons:
                try:
                    element = self.driver.find_element(AppiumBy.XPATH, f"//*[contains(@text,'{button_text}')]")
                    if element.is_displayed():
                        element.click()
                        time.sleep(2)
                        break
                except:
                    continue
        except Exception as e:
            print(f"Permission handling: {e}")
    
    async def _extract_products(self, store_name: str) -> List[Dict]:
        """Extract product information from search results"""
        products = []
        
        try:
            # Common product container selectors
            product_selectors = [
                "//*[contains(@resource-id,'product')]",
                "//*[contains(@class,'product')]",
                "//*[contains(@resource-id,'item')]"
            ]
            
            product_elements = []
            for selector in product_selectors:
                try:
                    elements = self.driver.find_elements(AppiumBy.XPATH, selector)
                    if elements:
                        product_elements = elements[:10]  # First 10 results
                        break
                except:
                    continue
            
            for element in product_elements:
                try:
                    # Extract product name
                    name_selectors = [
                        ".//text()[contains(@resource-id,'name')]",
                        ".//text()[contains(@class,'name')]",
                        ".//text()[contains(@resource-id,'title')]"
                    ]
                    
                    name = "Unknown"
                    for selector in name_selectors:
                        try:
                            name_element = element.find_element(AppiumBy.XPATH, selector)
                            name = name_element.text.strip()
                            if name:
                                break
                        except:
                            continue
                    
                    # Extract price
                    price_selectors = [
                        ".//text()[contains(@resource-id,'price')]",
                        ".//text()[contains(@class,'price')]",
                        ".//text()[contains(text(),'$')]"
                    ]
                    
                    price_text = "$0"
                    for selector in price_selectors:
                        try:
                            price_element = element.find_element(AppiumBy.XPATH, selector)
                            price_text = price_element.text.strip()
                            if '$' in price_text:
                                break
                        except:
                            continue
                    
                    # Parse Chilean price format
                    price = self._parse_chilean_price(price_text)
                    
                    if name != "Unknown" and price > 0:
                        products.append({
                            'name': name,
                            'price': price,
                            'price_text': price_text,
                            'store': store_name,
                            'url': ''
                        })
                
                except Exception as e:
                    continue
            
            print(f"✅ Extracted {len(products)} products from {store_name}")
            return products
            
        except Exception as e:
            print(f"❌ Error extracting products: {e}")
            return []
    
    def _parse_chilean_price(self, price_text: str) -> float:
        """Parse Chilean price format (e.g., $1.990, $12.350)"""
        try:
            if not price_text:
                return 0.0
            
            # Remove currency symbols
            clean_price = price_text.replace('$', '').replace(' ', '')
            
            # Handle Chilean thousand separators (periods)
            if '.' in clean_price and ',' not in clean_price:
                clean_price = clean_price.replace('.', '')
            
            # Extract numeric value
            price_match = re.search(r'[\d,]+', clean_price)
            if price_match:
                return float(price_match.group().replace(',', '.'))
            
            return 0.0
            
        except Exception:
            return 0.0