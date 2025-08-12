import asyncio
import time
import re
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
        """Initialize Appium driver for Android automation"""
        try:
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
            
            print("✅ Appium driver initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error setting up Appium driver: {e}")
            return False
    
    def close_driver(self):
        """Clean up driver resources"""
        try:
            if self.driver:
                self.driver.quit()
                print("✅ Driver closed successfully")
        except Exception as e:
            print(f"⚠️ Error closing driver: {e}")
    
    async def search_jumbo_app(self, product_name: str) -> List[Dict]:
        """Search Jumbo mobile app for products"""
        print(f"🔍 Starting Jumbo app search for: {product_name}")
        
        try:
            # Setup driver for Jumbo app
            if not self.setup_driver("com.cencosud.cl.jumboahora"):  # Correct Jumbo package name
                return []
            
            # Launch Jumbo app
            await self._launch_and_setup_jumbo()
            
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
            # Setup driver for Lider app
            if not self.setup_driver("cl.walmart.liderapp"):  # Correct Lider package name
                return []
            
            # Launch Lider app
            await self._launch_and_setup_lider()
            
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
    
    async def _perform_jumbo_search(self, product_name: str) -> bool:
        """Perform search in Jumbo app with enhanced debugging"""
        try:
            print(f"🔍 Starting enhanced Jumbo search for '{product_name}'")
            
            # Step 1: Debug current state
            print("📋 Debugging current app state...")
            debug_info = self.debug_current_state()
            print(f"Current Activity: {debug_info.get('current_activity', 'Unknown')}")
            print(f"Current Package: {debug_info.get('current_package', 'Unknown')}")
            
            # Step 2: Save page source for debugging
            self.save_page_source(f"/tmp/jumbo_before_search.xml")
            
            # Step 3: Find all potential search elements
            print("🔍 Analyzing potential search elements...")
            potential_elements = self.find_search_elements_debug()
            
            if not potential_elements:
                print("❌ No potential search elements found in Jumbo app")
                return False
            
            # Step 4: Try each potential search element
            search_successful = False
            for i, elem_info in enumerate(potential_elements):
                try:
                    print(f"🎯 Trying search element #{i+1}: {elem_info['xpath']}")
                    
                    # Find the element again using its xpath
                    search_element = self.driver.find_element(AppiumBy.XPATH, elem_info['xpath'])
                    
                    if not search_element.is_displayed() or not search_element.is_enabled():
                        print(f"   ❌ Element not visible/enabled")
                        continue
                    
                    # Test interaction with retry logic
                    for attempt in range(3):
                        try:
                            print(f"   🔄 Attempt {attempt + 1}/3 for element interaction")
                            
                            # Re-find element to avoid stale references
                            search_element = self.driver.find_element(AppiumBy.XPATH, elem_info['xpath'])
                            
                            # Click to focus
                            search_element.click()
                            time.sleep(1)
                            
                            # Clear existing text  
                            search_element.clear()
                            time.sleep(1)
                            
                            # Send text with multiple strategies
                            try:
                                search_element.send_keys(product_name)
                                print(f"   ✅ Successfully entered '{product_name}' using send_keys")
                            except:
                                # Alternative: Use set_value
                                try:
                                    search_element.set_value(product_name)
                                    print(f"   ✅ Successfully entered '{product_name}' using set_value")
                                except:
                                    # Alternative: Type character by character
                                    for char in product_name:
                                        search_element.send_keys(char)
                                        time.sleep(0.1)
                                    print(f"   ✅ Successfully entered '{product_name}' character by character")
                            
                            time.sleep(1)
                            
                            # Verify text was entered
                            current_text = search_element.text or search_element.get_attribute("text") or ""
                            if product_name.lower() in current_text.lower():
                                print(f"   ✅ Text verification successful: '{current_text}'")
                                search_successful = True
                                break
                            else:
                                print(f"   ⚠️ Text verification failed. Expected: '{product_name}', Got: '{current_text}'")
                                continue
                                
                        except Exception as attempt_error:
                            print(f"   ❌ Attempt {attempt + 1} failed: {attempt_error}")
                            continue
                    
                    if search_successful:
                        # Submit the search
                        print("   🚀 Submitting search...")
                        await self._submit_jumbo_search(search_element)
                        break
                        
                except Exception as elem_error:
                    print(f"   ❌ Error with element #{i+1}: {elem_error}")
                    continue
            
            if not search_successful:
                print("❌ All search element attempts failed for Jumbo")
                return False
            
            # Step 5: Validate we're on results page
            time.sleep(3)
            return await self._validate_jumbo_search_results()
            
        except Exception as e:
            print(f"❌ Jumbo enhanced search error: {e}")
            return False
    
    async def _submit_jumbo_search(self, search_element):
        """Submit Jumbo search with multiple strategies"""
        submission_successful = False
        
        # Strategy 1: Press Enter key
        try:
            self.driver.press_keycode(66)  # Android Enter key
            time.sleep(2)
            print("   ✅ Search submitted using Enter key")
            submission_successful = True
        except Exception as e:
            print(f"   ❌ Enter key submission failed: {e}")
        
        # Strategy 2: Look for search/submit buttons
        if not submission_successful:
            button_selectors = [
                "//*[contains(@resource-id,'search_button')]",
                "//*[contains(@resource-id,'submit')]",
                "//*[contains(@content-desc,'search')]",
                "//*[contains(@content-desc,'buscar')]", 
                "//*[contains(@content-desc,'Buscar')]",
                "//*[contains(@text,'Buscar')]",
                "//*[contains(@text,'buscar')]",
                "//android.widget.Button[contains(@content-desc,'search')]"
            ]
            
            for selector in button_selectors:
                try:
                    submit_btn = self.driver.find_element(AppiumBy.XPATH, selector)
                    if submit_btn.is_displayed() and submit_btn.is_enabled():
                        submit_btn.click()
                        print(f"   ✅ Search submitted using button: {selector}")
                        submission_successful = True
                        break
                except:
                    continue
        
        # Strategy 3: Tap on search icon/magnifying glass
        if not submission_successful:
            icon_selectors = [
                "//*[contains(@content-desc,'lupa')]",
                "//*[contains(@content-desc,'magnify')]",
                "//*[contains(@resource-id,'search_icon')]"
            ]
            
            for selector in icon_selectors:
                try:
                    icon = self.driver.find_element(AppiumBy.XPATH, selector)
                    if icon.is_displayed():
                        icon.click()
                        print(f"   ✅ Search submitted using icon: {selector}")
                        submission_successful = True
                        break
                except:
                    continue
        
        if not submission_successful:
            print("   ⚠️ No submission method worked, search may still be pending")
    
    async def _validate_jumbo_search_results(self) -> bool:
        """Validate that Jumbo search navigated to results page"""
        try:
            print("🎯 Validating Jumbo search results page...")
            
            # Save current page source
            self.save_page_source(f"/tmp/jumbo_after_search.xml") 
            
            # Check current activity/state
            debug_info = self.debug_current_state()
            current_activity = debug_info.get('current_activity', '')
            print(f"Current activity after search: {current_activity}")
            
            # Look for indicators that we're on a results page
            results_indicators = [
                "//*[contains(@text,'resultado')]",
                "//*[contains(@text,'Resultado')]", 
                "//*[contains(@text,'product')]",
                "//*[contains(@text,'Producto')]",
                "//*[contains(@resource-id,'result')]",
                "//*[contains(@resource-id,'product')]",
                "//*[contains(@class,'result')]",
                "//*[contains(@class,'product')]",
                # Look for product containers/grids
                "//*[contains(@resource-id,'grid')]",
                "//*[contains(@resource-id,'list')]",
                "//*[contains(@class,'grid')]",
                "//*[contains(@class,'list')]"
            ]
            
            results_found = False
            for indicator in results_indicators:
                try:
                    elements = self.driver.find_elements(AppiumBy.XPATH, indicator)
                    if elements:
                        print(f"✅ Found results indicator: {indicator} ({len(elements)} elements)")
                        results_found = True
                        break
                except:
                    continue
            
            if results_found:
                print("✅ Successfully navigated to Jumbo search results page")
                return True
            else:
                print("❌ Could not confirm navigation to Jumbo results page - may have returned to home")
                return False
                
        except Exception as e:
            print(f"❌ Error validating Jumbo search results: {e}")
            return False
    
    async def _perform_lider_search(self, product_name: str) -> bool:
        """Perform search in Lider app with enhanced debugging"""
        try:
            print(f"🔍 Starting enhanced Lider search for '{product_name}'")
            
            # Step 1: Debug current state
            print("📋 Debugging current app state...")
            debug_info = self.debug_current_state()
            print(f"Current Activity: {debug_info.get('current_activity', 'Unknown')}")
            print(f"Current Package: {debug_info.get('current_package', 'Unknown')}")
            
            # Step 2: Save page source for debugging
            self.save_page_source(f"/tmp/lider_before_search.xml")
            
            # Step 3: Find all potential search elements
            print("🔍 Analyzing potential search elements...")
            potential_elements = self.find_search_elements_debug()
            
            if not potential_elements:
                print("❌ No potential search elements found in Lider app")
                return False
            
            # Step 4: Try each potential search element
            search_successful = False
            for i, elem_info in enumerate(potential_elements):
                try:
                    print(f"🎯 Trying search element #{i+1}: {elem_info['xpath']}")
                    
                    # Find the element again using its xpath
                    search_element = self.driver.find_element(AppiumBy.XPATH, elem_info['xpath'])
                    
                    if not search_element.is_displayed() or not search_element.is_enabled():
                        print(f"   ❌ Element not visible/enabled")
                        continue
                    
                    # Test interaction with retry logic
                    for attempt in range(3):
                        try:
                            print(f"   🔄 Attempt {attempt + 1}/3 for element interaction")
                            
                            # Re-find element to avoid stale references
                            search_element = self.driver.find_element(AppiumBy.XPATH, elem_info['xpath'])
                            
                            # Click to focus
                            search_element.click()
                            time.sleep(1)
                            
                            # Clear existing text  
                            search_element.clear()
                            time.sleep(1)
                            
                            # Send text with multiple strategies
                            try:
                                search_element.send_keys(product_name)
                                print(f"   ✅ Successfully entered '{product_name}' using send_keys")
                            except:
                                # Alternative: Use set_value
                                try:
                                    search_element.set_value(product_name)
                                    print(f"   ✅ Successfully entered '{product_name}' using set_value")
                                except:
                                    # Alternative: Type character by character
                                    for char in product_name:
                                        search_element.send_keys(char)
                                        time.sleep(0.1)
                                    print(f"   ✅ Successfully entered '{product_name}' character by character")
                            
                            time.sleep(1)
                            
                            # Verify text was entered
                            current_text = search_element.text or search_element.get_attribute("text") or ""
                            if product_name.lower() in current_text.lower():
                                print(f"   ✅ Text verification successful: '{current_text}'")
                                search_successful = True
                                break
                            else:
                                print(f"   ⚠️ Text verification failed. Expected: '{product_name}', Got: '{current_text}'")
                                continue
                                
                        except Exception as attempt_error:
                            print(f"   ❌ Attempt {attempt + 1} failed: {attempt_error}")
                            continue
                    
                    if search_successful:
                        # Submit the search
                        print("   🚀 Submitting search...")
                        await self._submit_lider_search(search_element)
                        break
                        
                except Exception as elem_error:
                    print(f"   ❌ Error with element #{i+1}: {elem_error}")
                    continue
            
            if not search_successful:
                print("❌ All search element attempts failed for Lider")
                return False
            
            # Step 5: Validate we're on results page
            time.sleep(3)
            return await self._validate_lider_search_results()
            
        except Exception as e:
            print(f"❌ Lider enhanced search error: {e}")
            return False
    
    async def _submit_lider_search(self, search_element):
        """Submit Lider search with multiple strategies"""
        submission_successful = False
        
        # Strategy 1: Press Enter key
        try:
            self.driver.press_keycode(66)  # Android Enter key
            time.sleep(2)
            print("   ✅ Search submitted using Enter key")
            submission_successful = True
        except Exception as e:
            print(f"   ❌ Enter key submission failed: {e}")
        
        # Strategy 2: Look for search/submit buttons
        if not submission_successful:
            button_selectors = [
                "//*[contains(@resource-id,'search_button')]",
                "//*[contains(@resource-id,'submit')]",
                "//*[contains(@content-desc,'search')]",
                "//*[contains(@content-desc,'buscar')]", 
                "//*[contains(@content-desc,'Buscar')]",
                "//*[contains(@text,'Buscar')]",
                "//*[contains(@text,'buscar')]",
                "//android.widget.Button[contains(@content-desc,'search')]"
            ]
            
            for selector in button_selectors:
                try:
                    submit_btn = self.driver.find_element(AppiumBy.XPATH, selector)
                    if submit_btn.is_displayed() and submit_btn.is_enabled():
                        submit_btn.click()
                        print(f"   ✅ Search submitted using button: {selector}")
                        submission_successful = True
                        break
                except:
                    continue
        
        # Strategy 3: Tap on search icon/magnifying glass
        if not submission_successful:
            icon_selectors = [
                "//*[contains(@content-desc,'lupa')]",
                "//*[contains(@content-desc,'magnify')]",
                "//*[contains(@resource-id,'search_icon')]"
            ]
            
            for selector in icon_selectors:
                try:
                    icon = self.driver.find_element(AppiumBy.XPATH, selector)
                    if icon.is_displayed():
                        icon.click()
                        print(f"   ✅ Search submitted using icon: {selector}")
                        submission_successful = True
                        break
                except:
                    continue
        
        if not submission_successful:
            print("   ⚠️ No submission method worked, search may still be pending")
    
    async def _validate_lider_search_results(self) -> bool:
        """Validate that Lider search navigated to results page"""
        try:
            print("🎯 Validating Lider search results page...")
            
            # Save current page source
            self.save_page_source(f"/tmp/lider_after_search.xml") 
            
            # Check current activity/state
            debug_info = self.debug_current_state()
            current_activity = debug_info.get('current_activity', '')
            print(f"Current activity after search: {current_activity}")
            
            # Look for indicators that we're on a results page
            results_indicators = [
                "//*[contains(@text,'resultado')]",
                "//*[contains(@text,'Resultado')]", 
                "//*[contains(@text,'product')]",
                "//*[contains(@text,'Producto')]",
                "//*[contains(@resource-id,'result')]",
                "//*[contains(@resource-id,'product')]",
                "//*[contains(@class,'result')]",
                "//*[contains(@class,'product')]",
                # Look for product containers/grids
                "//*[contains(@resource-id,'grid')]",
                "//*[contains(@resource-id,'list')]",
                "//*[contains(@class,'grid')]",
                "//*[contains(@class,'list')]"
            ]
            
            results_found = False
            for indicator in results_indicators:
                try:
                    elements = self.driver.find_elements(AppiumBy.XPATH, indicator)
                    if elements:
                        print(f"✅ Found results indicator: {indicator} ({len(elements)} elements)")
                        results_found = True
                        break
                except:
                    continue
            
            if results_found:
                print("✅ Successfully navigated to Lider search results page")
                return True
            else:
                print("❌ Could not confirm navigation to Lider results page - may have returned to home")
                return False
                
        except Exception as e:
            print(f"❌ Error validating Lider search results: {e}")
            return False
    
    async def _extract_jumbo_products(self) -> List[Dict]:
        """Extract product information from Jumbo search results using corrected proximity-based approach"""
        products = []
        
        try:
            print("📦 Starting corrected Jumbo product extraction with Y-coordinate proximity grouping...")
            
            # Save page source for analysis
            self.save_page_source(f"/tmp/jumbo_products_page.xml")
            
            # Get all TextView elements that might contain product information
            all_text_elements = []
            try:
                text_views = self.driver.find_elements(AppiumBy.XPATH, "//android.widget.TextView")
                print(f"🔍 Found {len(text_views)} TextView elements total")
                
                for elem in text_views:
                    try:
                        text = elem.text.strip() if elem.text else ""
                        if text and len(text) > 0:
                            location = elem.location
                            all_text_elements.append({
                                'element': elem,
                                'text': text,
                                'x': location['x'],
                                'y': location['y'],
                                'size': elem.size
                            })
                    except:
                        continue
                        
                print(f"📝 Extracted {len(all_text_elements)} valid text elements")
                
            except Exception as e:
                print(f"❌ Error finding text elements: {e}")
                return []
            
            if not all_text_elements:
                print("❌ No text elements found")
                return []
            
            # Find potential price elements first
            price_elements = []
            for elem_info in all_text_elements:
                if "$" in elem_info['text'] or self._looks_like_price(elem_info['text']):
                    price_elements.append(elem_info)
            
            print(f"💰 Found {len(price_elements)} potential price elements")
            
            if not price_elements:
                print("❌ No potential price elements found")
                return []
            
            # Group related elements by Y-coordinate proximity (within 200 pixels)
            for i, price_elem in enumerate(price_elements):
                try:
                    print(f"💰 Processing price element {i+1}/{len(price_elements)}: '{price_elem['text']}'")
                    
                    # Find all text elements within 200 pixels Y-range of this price
                    related_elements = []
                    price_y = price_elem['y']
                    
                    for text_elem in all_text_elements:
                        if abs(text_elem['y'] - price_y) <= 200:  # Within 200 pixels vertically
                            related_elements.append(text_elem)
                    
                    print(f"   📍 Found {len(related_elements)} related elements within Y-proximity")
                    
                    # Extract product information from this group
                    product_info = self._extract_product_from_group_corrected(related_elements, "Jumbo")
                    
                    if product_info:
                        products.append(product_info)
                        print(f"   ✅ Extracted: {product_info['name']} - ${product_info['price']}")
                    else:
                        print(f"   ❌ Could not extract product from group")
                        
                except Exception as e:
                    print(f"❌ Error processing price element {i+1}: {e}")
                    continue
            
            print(f"✅ Successfully extracted {len(products)} products from Jumbo using corrected method")
            
        except Exception as e:
            print(f"❌ Error in corrected Jumbo product extraction: {e}")
        
        return products
    
    async def _extract_single_product_info(self, container_element, store_name: str) -> Dict:
        """Extract information from a single product container"""
        try:
            # Get all text elements within the container
            all_text_elements = []
            try:
                text_elements = container_element.find_elements(AppiumBy.XPATH, ".//android.widget.TextView")
                for elem in text_elements:
                    try:
                        text = elem.text.strip()
                        if text:
                            all_text_elements.append(text)
                    except:
                        continue
            except:
                # Fallback: get container text directly
                container_text = container_element.text or ""
                if container_text.strip():
                    all_text_elements = [container_text.strip()]
            
            if not all_text_elements:
                return None
            
            print(f"   📝 Found text elements: {all_text_elements[:5]}...")  # Show first 5
            
            # Extract product name (usually the longest non-price text)
            name_candidates = []
            price_candidates = []
            
            for text in all_text_elements:
                if "$" in text or any(char.isdigit() for char in text):
                    # Likely a price
                    if "$" in text:
                        price_candidates.append(text)
                else:
                    # Likely a product name
                    if len(text.strip()) > 3:  # Ignore very short texts
                        name_candidates.append(text)
            
            # Select best name (longest meaningful text)
            product_name = "Unknown Product"
            if name_candidates:
                product_name = max(name_candidates, key=len)
                print(f"   📝 Selected name: '{product_name}'")
            
            # Select best price
            price_text = "$0"
            price_value = 0.0
            if price_candidates:
                for price_candidate in price_candidates:
                    parsed_price = self._parse_chilean_price(price_candidate)
                    if parsed_price > 0:
                        price_text = price_candidate
                        price_value = parsed_price
                        print(f"   💰 Selected price: '{price_text}' = {price_value}")
                        break
            
            if product_name != "Unknown Product" and price_value > 0:
                return {
                    'name': product_name,
                    'price': price_value,
                    'price_text': price_text,
                    'store': store_name,
                    'url': ''
                }
            
            return None
            
        except Exception as e:
            print(f"   ❌ Error extracting single product info: {e}")
            return None
    
    async def _extract_products_from_price_elements(self, price_elements: List, store_name: str) -> List[Dict]:
        """Fallback method to extract products directly from price elements"""
        products = []
        
        try:
            print(f"🔄 Fallback extraction from {len(price_elements)} price elements...")
            
            for i, price_elem in enumerate(price_elements[:10]):  # Limit to 10
                try:
                    price_text = price_elem.text.strip()
                    price_value = self._parse_chilean_price(price_text)
                    
                    if price_value <= 0:
                        continue
                    
                    # Try to find product name near this price element
                    product_name = f"Product {i+1}"  # Default name
                    
                    try:
                        # Look for parent/sibling text elements
                        parent = price_elem.find_element(AppiumBy.XPATH, "./..")
                        text_elements = parent.find_elements(AppiumBy.XPATH, ".//android.widget.TextView")
                        
                        for text_elem in text_elements:
                            text = text_elem.text.strip()
                            if text and "$" not in text and len(text) > 5:
                                product_name = text
                                break
                    except:
                        pass
                    
                    products.append({
                        'name': product_name,
                        'price': price_value,
                        'price_text': price_text,
                        'store': store_name,
                        'url': ''
                    })
                    
                    print(f"   ✅ Extracted: {product_name} - ${price_value}")
                    
                except Exception as e:
                    print(f"   ❌ Error with price element {i+1}: {e}")
                    continue
            
            print(f"🔄 Fallback extraction found {len(products)} products")
            
        except Exception as e:
            print(f"❌ Error in fallback extraction: {e}")
        
        return products
    
    async def _extract_lider_products(self) -> List[Dict]:
        """Extract product information from Lider search results with enhanced debugging"""
        products = []
        
        try:
            print("📦 Starting enhanced Lider product extraction...")
            
            # Save page source for analysis
            self.save_page_source(f"/tmp/lider_products_page.xml")
            
            # Step 1: Find all elements with dollar signs (price indicators)
            dollar_elements = []
            try:
                dollar_elements = self.driver.find_elements(AppiumBy.XPATH, "//*[contains(text(),'$')]")
                print(f"🔍 Found {len(dollar_elements)} elements with '$' symbol")
                
                # Log first few for debugging
                for i, elem in enumerate(dollar_elements[:5]):
                    try:
                        text = elem.text.strip()
                        location = elem.location
                        print(f"  ${i+1}: '{text}' at {location}")
                    except:
                        continue
                        
            except Exception as e:
                print(f"❌ Error finding dollar elements: {e}")
            
            # Step 2: Try comprehensive product container selectors (similar to Jumbo)
            product_container_selectors = [
                # Generic product containers
                "//*[contains(@resource-id,'product')]",
                "//*[contains(@class,'product')]",
                "//*[contains(@resource-id,'item')]", 
                "//*[contains(@class,'item')]",
                "//*[contains(@resource-id,'card')]",
                "//*[contains(@class,'card')]",
                
                # Grid/list containers
                "//*[contains(@resource-id,'grid')]//*",
                "//*[contains(@resource-id,'list')]//*",
                "//*[contains(@class,'grid')]//*",
                "//*[contains(@class,'list')]//*",
                
                # RecyclerView containers (common in Android)
                "//androidx.recyclerview.widget.RecyclerView//*",
                "//android.support.v7.widget.RecyclerView//*",
                
                # Common Android view containers
                "//android.widget.LinearLayout[.//text()[contains(text(),'$')]]",
                "//android.widget.RelativeLayout[.//text()[contains(text(),'$')]]",
                "//android.widget.FrameLayout[.//text()[contains(text(),'$')]]",
                "//android.view.ViewGroup[.//text()[contains(text(),'$')]]"
            ]
            
            product_elements = []
            successful_selector = None
            
            for selector in product_container_selectors:
                try:
                    elements = self.driver.find_elements(AppiumBy.XPATH, selector)
                    if elements:
                        # Filter elements that likely contain products (have text and reasonable size)
                        valid_elements = []
                        for elem in elements:
                            try:
                                if elem.is_displayed() and elem.size['height'] > 50 and elem.size['width'] > 50:
                                    # Check if element or its children contain price
                                    elem_text = elem.text or ""
                                    if "$" in elem_text or len(elem_text.strip()) > 0:
                                        valid_elements.append(elem)
                            except:
                                continue
                        
                        if valid_elements:
                            product_elements = valid_elements[:15]  # Limit to first 15
                            successful_selector = selector
                            print(f"✅ Found {len(product_elements)} valid product elements with selector: {selector}")
                            break
                except Exception as selector_error:
                    print(f"❌ Error with selector '{selector}': {selector_error}")
                    continue
            
            if not product_elements:
                print("❌ No product container elements found")
                
                # Fallback: Try to extract any element containing prices
                print("🔄 Attempting fallback extraction from price elements...")
                return await self._extract_products_from_price_elements(dollar_elements, "Lider")
            
            # Step 3: Extract product information from containers
            print(f"📦 Processing {len(product_elements)} product containers...")
            
            for i, element in enumerate(product_elements):
                try:
                    print(f"📦 Processing product container {i+1}/{len(product_elements)}...")
                    
                    product_info = await self._extract_single_product_info(element, "Lider")
                    if product_info:
                        products.append(product_info)
                        print(f"✅ Product {i+1} extracted: {product_info['name']} - ${product_info['price']}")
                    else:
                        print(f"⚠️ Could not extract info from product container {i+1}")
                    
                except Exception as e:
                    print(f"❌ Error processing product container {i+1}: {e}")
                    continue
            
            print(f"✅ Successfully extracted {len(products)} products from Lider")
            
        except Exception as e:
            print(f"❌ Error in enhanced Lider product extraction: {e}")
        
        return products
    
    def _parse_chilean_price(self, price_text: str) -> float:
        """Parse Chilean price format (e.g., $1.990, $12.350)"""
        try:
            if not price_text:
                return 0.0
            
            # Remove currency symbols and spaces
            clean_price = price_text.replace('$', '').replace(' ', '').replace('\n', '')
            
            # Handle Chilean thousand separators (periods)
            # Chilean format: $1.990 = 1990 pesos
            if '.' in clean_price and ',' not in clean_price:
                # Likely Chilean format with periods as thousand separators
                clean_price = clean_price.replace('.', '')
            
            # Extract numeric value
            price_match = re.search(r'[\d,]+', clean_price)
            if price_match:
                price_str = price_match.group().replace(',', '.')
                return float(price_str)
            
            return 0.0
            
        except Exception as e:
            print(f"⚠️ Error parsing price '{price_text}': {e}")
            return 0.0
    
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
    
    def debug_current_state(self) -> Dict:
        """Debug current state of the app to help identify UI elements"""
        try:
            if not self.driver:
                return {"error": "No driver connected"}
            
            debug_info = {
                "current_activity": self.driver.current_activity,
                "current_package": self.driver.current_package,
                "page_source_length": len(self.driver.page_source),
                "window_size": self.driver.get_window_size()
            }
            
            # Try to find common UI elements
            common_elements = []
            element_checks = [
                ("EditText", "//android.widget.EditText"),
                ("Button", "//android.widget.Button"),
                ("TextView", "//android.widget.TextView"),
                ("ImageView", "//android.widget.ImageView")
            ]
            
            for element_type, xpath in element_checks:
                try:
                    elements = self.driver.find_elements(AppiumBy.XPATH, xpath)
                    common_elements.append({
                        "type": element_type,
                        "count": len(elements),
                        "xpath": xpath
                    })
                except:
                    pass
            
            debug_info["common_elements"] = common_elements
            
            # Get detailed EditText information for search debugging
            try:
                edit_texts = self.driver.find_elements(AppiumBy.XPATH, "//android.widget.EditText")
                edit_text_details = []
                for i, et in enumerate(edit_texts[:5]):  # Limit to first 5
                    try:
                        details = {
                            "index": i,
                            "text": et.text,
                            "hint": et.get_attribute("hint"),
                            "resource_id": et.get_attribute("resource-id"),
                            "content_desc": et.get_attribute("content-desc"),
                            "class": et.get_attribute("class"),
                            "clickable": et.get_attribute("clickable"),
                            "enabled": et.get_attribute("enabled"),
                            "displayed": et.is_displayed()
                        }
                        edit_text_details.append(details)
                    except:
                        continue
                debug_info["edit_text_details"] = edit_text_details
            except:
                debug_info["edit_text_details"] = []
            
            return debug_info
            
        except Exception as e:
            return {"error": str(e)}
    
    def save_page_source(self, filename: str = None):
        """Save current page source for debugging"""
        try:
            if not self.driver:
                print("❌ No driver connected")
                return False
            
            if not filename:
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"/tmp/page_source_{timestamp}.xml"
            
            page_source = self.driver.page_source
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(page_source)
            
            print(f"✅ Page source saved to {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Error saving page source: {e}")
            return False
    
    def find_search_elements_debug(self) -> List[Dict]:
        """Find and analyze all potential search elements"""
        potential_elements = []
        
        try:
            if not self.driver:
                return potential_elements
            
            # Comprehensive search element selectors
            search_patterns = [
                # Resource ID patterns
                "//*[contains(@resource-id,'search')]",
                "//*[contains(@resource-id,'buscar')]",
                "//*[contains(@resource-id,'find')]",
                "//*[contains(@resource-id,'query')]",
                
                # Content description patterns  
                "//*[contains(@content-desc,'search')]",
                "//*[contains(@content-desc,'buscar')]",
                "//*[contains(@content-desc,'Buscar')]",
                "//*[contains(@content-desc,'Search')]",
                
                # Text/hint patterns
                "//android.widget.EditText[contains(@text,'buscar')]",
                "//android.widget.EditText[contains(@text,'Buscar')]",
                "//android.widget.EditText[contains(@text,'search')]",
                "//android.widget.EditText[contains(@hint,'buscar')]",
                "//android.widget.EditText[contains(@hint,'Buscar')]",
                "//android.widget.EditText[contains(@hint,'search')]",
                
                # Class-based patterns
                "//*[contains(@class,'search')]",
                "//*[contains(@class,'Search')]",
                
                # Generic EditText (all)
                "//android.widget.EditText",
                
                # Icon-based search (magnifying glass, etc.)
                "//*[contains(@content-desc,'lupa')]",
                "//*[contains(@content-desc,'magnify')]"
            ]
            
            for pattern in search_patterns:
                try:
                    elements = self.driver.find_elements(AppiumBy.XPATH, pattern)
                    for i, element in enumerate(elements):
                        try:
                            element_info = {
                                "pattern": pattern,
                                "index": i,
                                "tag": element.tag_name,
                                "text": element.text,
                                "hint": element.get_attribute("hint"),
                                "resource_id": element.get_attribute("resource-id"),
                                "content_desc": element.get_attribute("content-desc"),
                                "class": element.get_attribute("class"),
                                "clickable": element.get_attribute("clickable"),
                                "enabled": element.get_attribute("enabled"),
                                "displayed": element.is_displayed(),
                                "location": element.location,
                                "size": element.size,
                                "xpath": f"{pattern}[{i+1}]" if i > 0 else pattern
                            }
                            potential_elements.append(element_info)
                        except Exception as e:
                            continue
                except:
                    continue
            
            # Remove duplicates based on location
            unique_elements = []
            for element in potential_elements:
                is_duplicate = False
                for unique in unique_elements:
                    if (element['location'] == unique['location'] and 
                        element['size'] == unique['size']):
                        is_duplicate = True
                        break
                if not is_duplicate:
                    unique_elements.append(element)
            
            print(f"🔍 Found {len(unique_elements)} unique potential search elements")
            for i, elem in enumerate(unique_elements[:10]):  # Show first 10
                print(f"  {i+1}. {elem['tag']} - ID: {elem['resource_id']} - Text: {elem['text']} - Hint: {elem['hint']}")
            
            return unique_elements
            
        except Exception as e:
            print(f"❌ Error in search element debug: {e}")
            return potential_elements