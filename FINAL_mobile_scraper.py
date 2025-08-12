import asyncio
import time
import re
import datetime
from typing import List, Dict, Optional
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By


class MobileAppScraper:
    """Android app automation for Jumbo and Lider price scraping"""
    
    def __init__(self):
        self.driver = None
        self.wait = None
        self.appium_port = 4724
        
    def setup_driver(self, app_package: str = None):
        """Initialize Appium driver for Android automation with proper session cleanup"""
        try:
            # CRITICAL FIX: Always close existing driver before creating new one
            if self.driver:
                print("🔄 Closing existing driver session...")
                try:
                    self.driver.quit()
                    self.driver = None
                    self.wait = None
                    time.sleep(2)  # Give time for cleanup
                except:
                    pass  # Ignore cleanup errors
            
            print(f"🚀 Setting up new driver for app: {app_package}")
            
            options = UiAutomator2Options()
            options.platform_name = "Android"
            options.device_name = "grocery_automation" 
            options.automation_name = "UiAutomator2"
            options.no_reset = True  # Keep app data between sessions
            options.full_reset = False
            
            if app_package:
                options.app_package = app_package
                
            # Additional capabilities for stability
            options.new_command_timeout = 300  # 5 minutes
            options.implicit_wait = 10
            
            print(f"Connecting to Appium server at http://localhost:{self.appium_port}")
            self.driver = webdriver.Remote(f'http://localhost:{self.appium_port}', options=options)
            self.wait = WebDriverWait(self.driver, 15)
            
            # CRITICAL VALIDATION: Verify we're in the correct app
            actual_package = self.driver.current_package
            print(f"✅ Driver initialized - Expected: {app_package}, Actual: {actual_package}")
            
            if app_package and actual_package != app_package:
                print(f"⚠️ Package mismatch! Attempting to launch correct app...")
                # Try to launch the correct app
                try:
                    self.driver.activate_app(app_package)
                    time.sleep(3)
                    actual_package = self.driver.current_package
                    print(f"🔄 After activation - Actual package: {actual_package}")
                except Exception as e:
                    print(f"❌ Failed to activate app {app_package}: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error setting up Appium driver: {e}")
            return False
    
    def close_driver(self):
        """Clean up driver resources"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.wait = None
                print("✅ Driver closed successfully")
        except Exception as e:
            print(f"⚠️ Error closing driver: {e}")
    
    async def search_jumbo_app(self, product_name: str) -> List[Dict]:
        """Search Jumbo mobile app for products"""
        print(f"🔍 Starting Jumbo app search for: {product_name}")
        
        try:
            # Setup driver for Jumbo app with proper session cleanup
            if not self.setup_driver("com.cencosud.cl.jumboahora"):
                return []
            
            # Launch Jumbo app
            await self._launch_and_setup_jumbo()
            
            # Verify we're in Jumbo app before searching
            current_package = self.driver.current_package if self.driver else "Unknown"
            if "jumbo" not in current_package.lower():
                print(f"❌ Wrong app context! Expected Jumbo, got: {current_package}")
                return []
            
            # Perform search
            if await self._perform_jumbo_search(product_name):
                # Extract products
                products = await self._extract_jumbo_products()
                print(f"✅ Jumbo search found {len(products)} products")
                return products
            else:
                print("❌ Jumbo search failed")
                return []
                
        except Exception as e:
            print(f"❌ Error in Jumbo app search: {e}")
            return []
        finally:
            self.close_driver()
    
    async def search_lider_app(self, product_name: str) -> List[Dict]:
        """Search Lider mobile app for products"""
        print(f"🔍 Starting Lider app search for: {product_name}")
        
        try:
            # Setup driver for Lider app with proper session cleanup
            if not self.setup_driver("cl.walmart.liderapp"):
                return []
            
            # Launch Lider app
            await self._launch_and_setup_lider()
            
            # Verify we're in Lider app before searching
            current_package = self.driver.current_package if self.driver else "Unknown"
            if "lider" not in current_package.lower() and "walmart" not in current_package.lower():
                print(f"❌ Wrong app context! Expected Lider, got: {current_package}")
                return []
            
            # Perform search
            if await self._perform_lider_search(product_name):
                # Extract products
                products = await self._extract_lider_products()
                print(f"✅ Lider search found {len(products)} products")
                return products
            else:
                print("❌ Lider search failed")
                return []
                
        except Exception as e:
            print(f"❌ Error in Lider app search: {e}")
            return []
        finally:
            self.close_driver()
    
    async def _launch_and_setup_jumbo(self):
        """Launch Jumbo app and handle initial setup"""
        print("📱 Launching Jumbo app...")
        
        # Give app time to launch
        time.sleep(5)
        
        # Handle potential welcome screens, permissions, etc.
        await self._handle_app_permissions()
        await self._handle_jumbo_login_if_needed()
        
        print("✅ Jumbo app setup complete")
    
    async def _launch_and_setup_lider(self):
        """Launch Lider app and handle initial setup"""
        print("📱 Launching Lider app...")
        
        # Give app time to launch
        time.sleep(5)
        
        # Handle potential welcome screens, permissions, etc.
        await self._handle_app_permissions()
        await self._handle_lider_login_if_needed()
        
        print("✅ Lider app setup complete")
    
    async def _handle_app_permissions(self):
        """Handle common Android app permissions"""
        try:
            # Common permission dialog patterns
            permission_buttons = [
                "ALLOW", "PERMITIR", "Allow", "Permitir",
                "OK", "ACEPTAR", "Accept", "Aceptar"
            ]
            
            for button_text in permission_buttons:
                try:
                    element = self.driver.find_element(AppiumBy.XPATH, f"//*[contains(@text,'{button_text}')]")
                    if element.is_displayed():
                        element.click()
                        time.sleep(2)
                        print(f"✅ Handled permission: {button_text}")
                except:
                    continue
                    
        except Exception as e:
            print(f"⚠️ Permission handling: {e}")
    
    async def _handle_jumbo_login_if_needed(self):
        """Handle Jumbo app login process"""
        try:
            # Look for login indicators
            login_indicators = [
                "Iniciar sesión", "Login", "Ingresar", 
                "Email", "Correo", "Usuario"
            ]
            
            login_needed = False
            for indicator in login_indicators:
                try:
                    element = self.driver.find_element(AppiumBy.XPATH, f"//*[contains(@text,'{indicator}')]")
                    if element.is_displayed():
                        login_needed = True
                        break
                except:
                    continue
            
            if login_needed:
                print("🔑 Login required for Jumbo app")
                
                # Try to find email/username field
                email_selectors = [
                    "//input[@type='email']",
                    "//*[contains(@resource-id,'email')]",
                    "//*[contains(@resource-id,'usuario')]",
                    "//*[contains(@class,'email')]"
                ]
                
                for selector in email_selectors:
                    try:
                        email_field = self.driver.find_element(AppiumBy.XPATH, selector)
                        email_field.clear()
                        email_field.send_keys("wschol@gmail.com")
                        print("✅ Email entered")
                        break
                    except:
                        continue
                
                # Try to find password field
                password_selectors = [
                    "//input[@type='password']",
                    "//*[contains(@resource-id,'password')]",
                    "//*[contains(@resource-id,'contraseña')]",
                    "//*[contains(@class,'password')]"
                ]
                
                for selector in password_selectors:
                    try:
                        password_field = self.driver.find_element(AppiumBy.XPATH, selector)
                        password_field.clear()
                        password_field.send_keys("w4Agustina4!")
                        print("✅ Password entered")
                        break
                    except:
                        continue
                
                # Try to find and click login button
                login_buttons = [
                    "Iniciar sesión", "Login", "Ingresar", "ENTRAR"
                ]
                
                for button_text in login_buttons:
                    try:
                        login_btn = self.driver.find_element(AppiumBy.XPATH, f"//*[contains(@text,'{button_text}')]")
                        login_btn.click()
                        time.sleep(5)
                        print("✅ Login attempted")
                        break
                    except:
                        continue
            else:
                print("✅ No login required for Jumbo")
                
        except Exception as e:
            print(f"⚠️ Jumbo login handling: {e}")
    
    async def _handle_lider_login_if_needed(self):
        """Handle Lider app login process (email verification)"""
        try:
            # Similar to Jumbo but handle email verification flow
            print("🔑 Checking Lider login status...")
            
            # Look for login indicators
            login_indicators = [
                "Iniciar sesión", "Login", "Ingresar",
                "Email", "Correo electrónico"
            ]
            
            login_needed = False
            for indicator in login_indicators:
                try:
                    element = self.driver.find_element(AppiumBy.XPATH, f"//*[contains(@text,'{indicator}')]")
                    if element.is_displayed():
                        login_needed = True
                        break
                except:
                    continue
            
            if login_needed:
                print("📧 Email verification needed for Lider")
                
                # Enter email
                email_selectors = [
                    "//input[@type='email']",
                    "//*[contains(@resource-id,'email')]",
                    "//*[contains(@class,'email')]"
                ]
                
                for selector in email_selectors:
                    try:
                        email_field = self.driver.find_element(AppiumBy.XPATH, selector)
                        email_field.clear()
                        email_field.send_keys("wschol@gmail.com")
                        print("✅ Email entered for Lider")
                        break
                    except:
                        continue
                
                # Click send verification code
                send_buttons = [
                    "Enviar código", "Send code", "ENVIAR"
                ]
                
                for button_text in send_buttons:
                    try:
                        send_btn = self.driver.find_element(AppiumBy.XPATH, f"//*[contains(@text,'{button_text}')]")
                        send_btn.click()
                        print("📧 Verification code requested")
                        print("⏳ Please check your email and manually enter the verification code in the app")
                        time.sleep(30)  # Give time to manually enter code
                        break
                    except:
                        continue
            else:
                print("✅ No login required for Lider")
                
        except Exception as e:
            print(f"⚠️ Lider login handling: {e}")
    
    # ============================================================================
    # SIMPLIFIED AND ROBUST SEARCH METHODS
    # ============================================================================
    
    async def _perform_jumbo_search(self, product_name: str) -> bool:
        """Perform search in Jumbo app with simplified, robust approach"""
        try:
            print(f"🔍 Performing Jumbo search for '{product_name}'")
            
            # Save current state for debugging
            debug_info = self.debug_current_state()
            print(f"App Context: {debug_info.get('current_package', 'Unknown')}")
            
            # Simplified search element selectors - most reliable ones first
            search_selectors = [
                "//android.widget.EditText[@clickable='true']",
                "//*[contains(@resource-id,'search')]",
                "//*[contains(@content-desc,'search')]",
                "//*[contains(@content-desc,'buscar')]",
                "//android.widget.EditText[contains(@hint,'buscar')]",
                "//android.widget.EditText[contains(@hint,'Buscar')]",
                "//android.widget.EditText"
            ]
            
            search_successful = False
            
            for i, selector in enumerate(search_selectors):
                try:
                    print(f"🎯 Trying selector {i+1}: {selector}")
                    
                    # Find element with explicit wait
                    search_element = self.wait.until(
                        EC.presence_of_element_located((AppiumBy.XPATH, selector))
                    )
                    
                    if not search_element.is_displayed():
                        print("   ❌ Element not visible")
                        continue
                    
                    # Simple interaction - no complex retry logic
                    print("   📝 Clicking element...")
                    search_element.click()
                    time.sleep(1)
                    
                    print("   🧹 Clearing element...")
                    search_element.clear()
                    time.sleep(1)
                    
                    print(f"   ⌨️ Typing '{product_name}'...")
                    search_element.send_keys(product_name)
                    time.sleep(2)
                    
                    # Verify text was entered
                    current_text = search_element.text or search_element.get_attribute("text") or ""
                    print(f"   ✅ Verification: '{current_text}'")
                    
                    if product_name.lower() in current_text.lower():
                        print("   🚀 Submitting search...")
                        # Simple submission - just press Enter
                        self.driver.press_keycode(66)  # Android Enter key
                        time.sleep(5)  # Wait longer for results to load
                        search_successful = True
                        break
                    
                except Exception as selector_error:
                    print(f"   ❌ Selector {i+1} failed: {selector_error}")
                    continue
            
            if search_successful:
                print("✅ Jumbo search submitted successfully")
                return True
            else:
                print("❌ All search attempts failed for Jumbo")
                return False
                
        except Exception as e:
            print(f"❌ Jumbo search error: {e}")
            return False
    
    async def _perform_lider_search(self, product_name: str) -> bool:
        """Perform search in Lider app with simplified, robust approach"""
        try:
            print(f"🔍 Performing Lider search for '{product_name}'")
            
            # Save current state for debugging
            debug_info = self.debug_current_state()
            print(f"App Context: {debug_info.get('current_package', 'Unknown')}")
            
            # Simplified search element selectors - most reliable ones first
            search_selectors = [
                "//android.widget.EditText[@clickable='true']",
                "//*[contains(@resource-id,'searchInput')]",
                "//*[contains(@resource-id,'search')]",
                "//*[contains(@content-desc,'search')]",
                "//*[contains(@content-desc,'buscar')]",
                "//android.widget.EditText[contains(@hint,'buscar')]",
                "//android.widget.EditText[contains(@hint,'Buscar')]",
                "//android.widget.EditText"
            ]
            
            search_successful = False
            
            for i, selector in enumerate(search_selectors):
                try:
                    print(f"🎯 Trying selector {i+1}: {selector}")
                    
                    # Find element with explicit wait
                    search_element = self.wait.until(
                        EC.presence_of_element_located((AppiumBy.XPATH, selector))
                    )
                    
                    if not search_element.is_displayed():
                        print("   ❌ Element not visible")
                        continue
                    
                    # Simple interaction - no complex retry logic
                    print("   📝 Clicking element...")
                    search_element.click()
                    time.sleep(1)
                    
                    print("   🧹 Clearing element...")
                    search_element.clear()
                    time.sleep(1)
                    
                    print(f"   ⌨️ Typing '{product_name}'...")
                    search_element.send_keys(product_name)
                    time.sleep(2)
                    
                    # Verify text was entered
                    current_text = search_element.text or search_element.get_attribute("text") or ""
                    print(f"   ✅ Verification: '{current_text}'")
                    
                    if product_name.lower() in current_text.lower():
                        print("   🚀 Submitting search...")
                        # Simple submission - just press Enter
                        self.driver.press_keycode(66)  # Android Enter key
                        time.sleep(5)  # Wait longer for results to load
                        search_successful = True
                        break
                    
                except Exception as selector_error:
                    print(f"   ❌ Selector {i+1} failed: {selector_error}")
                    continue
            
            if search_successful:
                print("✅ Lider search submitted successfully")
                return True
            else:
                print("❌ All search attempts failed for Lider")
                return False
                
        except Exception as e:
            print(f"❌ Lider search error: {e}")
            return False
    
    # ============================================================================
    # COMPLETELY REWRITTEN PRODUCT EXTRACTION - BASED ON SCREENSHOT ANALYSIS
    # ============================================================================
    
    async def _extract_jumbo_products(self) -> List[Dict]:
        """Extract product information from Jumbo search results - completely rewritten"""
        products = []
        
        try:
            print("📦 Starting comprehensive Jumbo product extraction...")
            
            # Wait longer for results to fully load
            print("⏳ Waiting for results to load...")
            time.sleep(5)
            
            # STRATEGY 1: Find ALL TextView elements and filter for prices
            print("🔍 Strategy 1: Scanning all TextView elements...")
            try:
                all_text_elements = self.driver.find_elements(AppiumBy.XPATH, "//android.widget.TextView")
                print(f"Found {len(all_text_elements)} TextView elements")
                
                price_elements = []
                for element in all_text_elements:
                    try:
                        text = element.text.strip()
                        if text and ('$' in text or 'peso' in text.lower()):
                            price_elements.append(element)
                            print(f"  💰 Found price text: '{text}'")
                    except:
                        continue
                
                print(f"Found {len(price_elements)} potential price elements")
                
                # Extract products from price elements
                for i, price_elem in enumerate(price_elements[:15]):  # Limit to first 15
                    try:
                        price_text = price_elem.text.strip()
                        price_value = self._parse_chilean_price(price_text)
                        
                        if price_value <= 0:
                            continue
                        
                        # Find product name by looking at nearby elements
                        product_name = await self._find_product_name_near_price(price_elem, "Jumbo", i+1)
                        
                        products.append({
                            'name': product_name,
                            'price': price_value,
                            'price_text': price_text,
                            'store': 'Jumbo',
                            'url': ''
                        })
                        
                        print(f"✅ Extracted: {product_name} - ${price_value}")
                        
                    except Exception as e:
                        print(f"⚠️ Error processing price element {i+1}: {e}")
                        continue
                        
            except Exception as e:
                print(f"❌ Strategy 1 failed: {e}")
            
            # STRATEGY 2: If no products found, try broader search
            if not products:
                print("🔍 Strategy 2: Broader element search...")
                try:
                    # Look for any element containing price-like text
                    broader_elements = self.driver.find_elements(AppiumBy.XPATH, "//*")
                    
                    for element in broader_elements[:200]:  # Limit to first 200 elements
                        try:
                            text = element.text.strip()
                            if text and len(text) > 0:
                                # Check if it looks like a price
                                if re.search(r'\$\s*\d+[\.,]?\d*', text):
                                    price_value = self._parse_chilean_price(text)
                                    if price_value > 0:
                                        product_name = f"Jumbo Product {len(products)+1}"
                                        products.append({
                                            'name': product_name,
                                            'price': price_value,
                                            'price_text': text,
                                            'store': 'Jumbo',
                                            'url': ''
                                        })
                                        print(f"✅ Strategy 2 found: {product_name} - ${price_value}")
                                        
                                        if len(products) >= 10:  # Limit to 10 products
                                            break
                        except:
                            continue
                            
                except Exception as e:
                    print(f"❌ Strategy 2 failed: {e}")
            
            print(f"✅ Final Jumbo extraction: {len(products)} products found")
            
        except Exception as e:
            print(f"❌ Error in Jumbo product extraction: {e}")
        
        return products
    
    async def _extract_lider_products(self) -> List[Dict]:
        """Extract product information from Lider search results - completely rewritten"""
        products = []
        
        try:
            print("📦 Starting comprehensive Lider product extraction...")
            
            # Wait longer for results to fully load
            print("⏳ Waiting for results to load...")
            time.sleep(5)
            
            # STRATEGY 1: Find ALL TextView elements and filter for prices
            print("🔍 Strategy 1: Scanning all TextView elements...")
            try:
                all_text_elements = self.driver.find_elements(AppiumBy.XPATH, "//android.widget.TextView")
                print(f"Found {len(all_text_elements)} TextView elements")
                
                price_elements = []
                for element in all_text_elements:
                    try:
                        text = element.text.strip()
                        if text and ('$' in text or 'peso' in text.lower()):
                            price_elements.append(element)
                            print(f"  💰 Found price text: '{text}'")
                    except:
                        continue
                
                print(f"Found {len(price_elements)} potential price elements")
                
                # Extract products from price elements
                for i, price_elem in enumerate(price_elements[:15]):  # Limit to first 15
                    try:
                        price_text = price_elem.text.strip()
                        price_value = self._parse_chilean_price(price_text)
                        
                        if price_value <= 0:
                            continue
                        
                        # Find product name by looking at nearby elements
                        product_name = await self._find_product_name_near_price(price_elem, "Lider", i+1)
                        
                        products.append({
                            'name': product_name,
                            'price': price_value,
                            'price_text': price_text,
                            'store': 'Lider',
                            'url': ''
                        })
                        
                        print(f"✅ Extracted: {product_name} - ${price_value}")
                        
                    except Exception as e:
                        print(f"⚠️ Error processing price element {i+1}: {e}")
                        continue
                        
            except Exception as e:
                print(f"❌ Strategy 1 failed: {e}")
            
            # STRATEGY 2: If no products found, try broader search
            if not products:
                print("🔍 Strategy 2: Broader element search...")
                try:
                    # Look for any element containing price-like text
                    broader_elements = self.driver.find_elements(AppiumBy.XPATH, "//*")
                    
                    for element in broader_elements[:200]:  # Limit to first 200 elements
                        try:
                            text = element.text.strip()
                            if text and len(text) > 0:
                                # Check if it looks like a price
                                if re.search(r'\$\s*\d+[\.,]?\d*', text):
                                    price_value = self._parse_chilean_price(text)
                                    if price_value > 0:
                                        product_name = f"Lider Product {len(products)+1}"
                                        products.append({
                                            'name': product_name,
                                            'price': price_value,
                                            'price_text': text,
                                            'store': 'Lider',
                                            'url': ''
                                        })
                                        print(f"✅ Strategy 2 found: {product_name} - ${price_value}")
                                        
                                        if len(products) >= 10:  # Limit to 10 products
                                            break
                        except:
                            continue
                            
                except Exception as e:
                    print(f"❌ Strategy 2 failed: {e}")
            
            print(f"✅ Final Lider extraction: {len(products)} products found")
            
        except Exception as e:
            print(f"❌ Error in Lider product extraction: {e}")
        
        return products
    
    async def _find_product_name_near_price(self, price_element, store_name: str, index: int) -> str:
        """Find product name near a price element"""
        try:
            # Strategy 1: Look in parent container
            try:
                parent = price_element.find_element(AppiumBy.XPATH, "./..")
                parent_texts = parent.find_elements(AppiumBy.XPATH, ".//android.widget.TextView")
                
                for text_elem in parent_texts:
                    text = text_elem.text.strip()
                    # Look for text that could be a product name
                    if (text and len(text) > 5 and '$' not in text and 'peso' not in text.lower() 
                        and not text.isdigit() and 'combinar' not in text.lower() 
                        and 'agregar' not in text.lower()):
                        return text
            except:
                pass
            
            # Strategy 2: Look in grandparent container
            try:
                grandparent = price_element.find_element(AppiumBy.XPATH, "./../..")
                grandparent_texts = grandparent.find_elements(AppiumBy.XPATH, ".//android.widget.TextView")
                
                for text_elem in grandparent_texts:
                    text = text_elem.text.strip()
                    if (text and len(text) > 10 and '$' not in text and 'peso' not in text.lower() 
                        and not text.isdigit() and 'combinar' not in text.lower() 
                        and 'agregar' not in text.lower() and 'coca' in text.lower()):
                        return text
            except:
                pass
            
            # Default name
            return f"{store_name} Product {index}"
            
        except Exception as e:
            return f"{store_name} Product {index}"
    
    def _parse_chilean_price(self, price_text: str) -> float:
        """Parse Chilean price format with improved regex"""
        try:
            if not price_text:
                return 0.0
            
            # Enhanced regex to catch various price formats
            # Matches: $1.990, $12.350, 2 x $4.000, etc.
            price_patterns = [
                r'\$\s*(\d{1,3}(?:\.\d{3})*)',  # $1.990, $12.350
                r'(\d{1,3}(?:\.\d{3})*)\s*peso',  # 1990 peso
                r'\$\s*(\d+)',  # Simple $1990
                r'(\d+)\s*CLP'  # 1990 CLP
            ]
            
            for pattern in price_patterns:
                matches = re.findall(pattern, price_text, re.IGNORECASE)
                if matches:
                    price_str = matches[0].replace('.', '')  # Remove thousand separators
                    try:
                        return float(price_str)
                    except:
                        continue
            
            return 0.0
            
        except Exception as e:
            print(f"⚠️ Error parsing price '{price_text}': {e}")
            return 0.0
    
    # ============================================================================
    # DEBUG AND UTILITY METHODS (SIMPLIFIED)
    # ============================================================================
    
    def debug_current_state(self) -> Dict:
        """Debug current state of the app (simplified)"""
        try:
            if not self.driver:
                return {"error": "No driver connected"}
            
            return {
                "current_activity": self.driver.current_activity,
                "current_package": self.driver.current_package,
                "window_size": self.driver.get_window_size()
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_app_info(self) -> Dict:
        """Get information about currently connected device and available apps"""
        try:
            if not self.driver:
                return {"error": "No driver connected"}
            
            # Get device info
            device_info = {
                "device_name": self.driver.capabilities.get('deviceName'),
                "platform_version": self.driver.capabilities.get('platformVersion'),
                "app_package": self.driver.capabilities.get('appPackage'),
                "app_activity": self.driver.capabilities.get('appActivity')
            }
            
            return device_info
            
        except Exception as e:
            return {"error": str(e)}