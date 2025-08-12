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
            
            # Perform search with improved navigation handling
            if await self._perform_jumbo_search_improved(product_name):
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
                products = await self._extract_lider_products_improved()
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
    # IMPROVED JUMBO SEARCH METHOD - FIX NAVIGATION ISSUE
    # ============================================================================
    
    async def _perform_jumbo_search_improved(self, product_name: str) -> bool:
        """Perform search in Jumbo app with improved navigation handling"""
        try:
            print(f"🔍 Performing improved Jumbo search for '{product_name}'")
            
            # Save current state for debugging
            debug_info = self.debug_current_state()
            print(f"App Context: {debug_info.get('current_package', 'Unknown')}")
            
            # Step 1: Find search element more reliably
            search_element = None
            search_selectors = [
                "//android.widget.EditText[@clickable='true']",
                "//android.widget.EditText",
                "//*[contains(@resource-id,'search')]",
                "//*[contains(@content-desc,'search')]",
                "//*[contains(@content-desc,'buscar')]",
                "//android.widget.EditText[contains(@hint,'buscar')]"
            ]
            
            for i, selector in enumerate(search_selectors):
                try:
                    print(f"🎯 Trying search selector {i+1}: {selector}")
                    search_element = self.wait.until(
                        EC.presence_of_element_located((AppiumBy.XPATH, selector))
                    )
                    if search_element and search_element.is_displayed():
                        print(f"   ✅ Found search element with selector {i+1}")
                        break
                except Exception as e:
                    print(f"   ❌ Selector {i+1} failed: {e}")
                    search_element = None
                    continue
            
            if not search_element:
                print("❌ Could not find any search element in Jumbo")
                return False
            
            # Step 2: Perform search with better timing
            try:
                print("   📝 Clicking search element...")
                search_element.click()
                time.sleep(2)  # Longer wait after click
                
                print("   🧹 Clearing existing text...")
                search_element.clear()
                time.sleep(1)
                
                print(f"   ⌨️ Typing '{product_name}'...")
                search_element.send_keys(product_name)
                time.sleep(2)
                
                # Verify text was entered
                current_text = search_element.text or search_element.get_attribute("text") or ""
                print(f"   ✅ Text verification: '{current_text}'")
                
                if not (product_name.lower() in current_text.lower()):
                    print(f"   ⚠️ Text verification failed!")
                    return False
                
            except Exception as e:
                print(f"   ❌ Error during text input: {e}")
                return False
            
            # Step 3: Submit search with multiple strategies
            print("   🚀 Submitting search...")
            search_submitted = False
            
            # Strategy 1: Enter key
            try:
                self.driver.press_keycode(66)  # Android Enter key
                time.sleep(3)
                print("   ✅ Search submitted with Enter key")
                search_submitted = True
            except Exception as e:
                print(f"   ❌ Enter key failed: {e}")
            
            # Strategy 2: Look for search button if Enter didn't work
            if not search_submitted:
                button_selectors = [
                    "//*[contains(@content-desc,'search')]",
                    "//*[contains(@content-desc,'buscar')]",
                    "//*[contains(@text,'Buscar')]",
                    "//android.widget.Button[contains(@content-desc,'search')]"
                ]
                
                for selector in button_selectors:
                    try:
                        search_btn = self.driver.find_element(AppiumBy.XPATH, selector)
                        if search_btn.is_displayed():
                            search_btn.click()
                            print(f"   ✅ Search submitted with button: {selector}")
                            search_submitted = True
                            break
                    except:
                        continue
            
            if not search_submitted:
                print("   ❌ Could not submit search")
                return False
            
            # Step 4: Wait longer and verify we're on results page
            print("   ⏳ Waiting longer for results to load...")
            time.sleep(8)  # Much longer wait
            
            # Check if we're still on results or went back to home
            current_activity = self.driver.current_activity
            print(f"   📱 Current activity after search: {current_activity}")
            
            # Look for results indicators
            results_indicators = [
                "//*[contains(@text,'resultado')]",
                "//*[contains(@text,'Resultado')]",
                "//*[contains(@text,'$')]",  # Look for any price
                "//*[contains(@resource-id,'product')]",
                "//*[contains(@class,'product')]"
            ]
            
            results_found = False
            for indicator in results_indicators:
                try:
                    elements = self.driver.find_elements(AppiumBy.XPATH, indicator)
                    if elements:
                        print(f"   ✅ Found results indicator: {indicator} ({len(elements)} elements)")
                        results_found = True
                        break
                except:
                    continue
            
            if results_found:
                print("✅ Jumbo search completed successfully - on results page")
                return True
            else:
                print("❌ Jumbo search failed - probably returned to home")
                # Try to take a screenshot or get page source for debugging
                try:
                    # Debug: print current page elements
                    all_texts = self.driver.find_elements(AppiumBy.XPATH, "//android.widget.TextView")
                    print(f"   📋 Found {len(all_texts)} text elements on current page")
                    for i, text_elem in enumerate(all_texts[:10]):
                        try:
                            text = text_elem.text.strip()
                            if text:
                                print(f"      {i+1}. '{text}'")
                        except:
                            continue
                except:
                    pass
                return False
                
        except Exception as e:
            print(f"❌ Jumbo improved search error: {e}")
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
    # IMPROVED PRODUCT EXTRACTION - FIX NAMES AND PRICING
    # ============================================================================
    
    async def _extract_jumbo_products(self) -> List[Dict]:
        """Extract product information from Jumbo search results - improved"""
        products = []
        
        try:
            print("📦 Starting improved Jumbo product extraction...")
            
            # Wait longer for results to fully load
            print("⏳ Waiting for results to load...")
            time.sleep(5)
            
            # Debug: Check what's on the page
            try:
                all_text_elements = self.driver.find_elements(AppiumBy.XPATH, "//android.widget.TextView")
                print(f"📋 Found {len(all_text_elements)} TextView elements")
                
                # Show first 20 text elements for debugging
                print("📝 Sample text elements:")
                for i, elem in enumerate(all_text_elements[:20]):
                    try:
                        text = elem.text.strip()
                        if text:
                            print(f"  {i+1}. '{text}'")
                    except:
                        continue
                
                # Look for price elements
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
                for i, price_elem in enumerate(price_elements[:15]):
                    try:
                        price_text = price_elem.text.strip()
                        parsed_price = self._parse_chilean_price_improved(price_text)
                        
                        if parsed_price['total_price'] <= 0:
                            continue
                        
                        # Find product name by looking at nearby elements
                        product_name, product_size = await self._find_product_details_near_price(price_elem, "Jumbo", i+1)
                        
                        product_info = {
                            'name': product_name,
                            'price': parsed_price['total_price'],
                            'unit_price': parsed_price.get('unit_price'),
                            'quantity': parsed_price.get('quantity', 1),
                            'size': product_size,
                            'price_text': price_text,
                            'store': 'Jumbo',
                            'url': ''
                        }
                        
                        products.append(product_info)
                        print(f"✅ Extracted: {product_name} ({product_size}) - ${parsed_price['total_price']}")
                        
                    except Exception as e:
                        print(f"⚠️ Error processing price element {i+1}: {e}")
                        continue
                        
            except Exception as e:
                print(f"❌ Jumbo extraction failed: {e}")
            
            print(f"✅ Final Jumbo extraction: {len(products)} products found")
            
        except Exception as e:
            print(f"❌ Error in Jumbo product extraction: {e}")
        
        return products
    
    async def _extract_lider_products_improved(self) -> List[Dict]:
        """Extract product information from Lider search results - with proper names and pricing"""
        products = []
        
        try:
            print("📦 Starting improved Lider product extraction...")
            
            # Wait longer for results to fully load
            print("⏳ Waiting for results to load...")
            time.sleep(5)
            
            # STRATEGY: Find all TextView elements and analyze them
            all_text_elements = self.driver.find_elements(AppiumBy.XPATH, "//android.widget.TextView")
            print(f"📋 Found {len(all_text_elements)} TextView elements")
            
            # Group elements by their parent containers to keep related data together
            price_containers = []
            
            for element in all_text_elements:
                try:
                    text = element.text.strip()
                    if text and ('$' in text or 'peso' in text.lower()):
                        # Found a price element, get its parent container
                        try:
                            parent = element.find_element(AppiumBy.XPATH, "./..")
                            grandparent = parent.find_element(AppiumBy.XPATH, "./..")
                            
                            # Get all text from this container
                            container_texts = []
                            for child in grandparent.find_elements(AppiumBy.XPATH, ".//android.widget.TextView"):
                                child_text = child.text.strip()
                                if child_text:
                                    container_texts.append(child_text)
                            
                            price_containers.append({
                                'price_element': element,
                                'price_text': text,
                                'container_texts': container_texts,
                                'location': element.location
                            })
                            
                            print(f"  💰 Price container: '{text}' with texts: {container_texts}")
                            
                        except Exception as container_error:
                            # Fallback: just use the price element
                            price_containers.append({
                                'price_element': element,
                                'price_text': text,
                                'container_texts': [text],
                                'location': element.location
                            })
                            
                except:
                    continue
            
            print(f"Found {len(price_containers)} price containers")
            
            # Remove duplicates based on location
            unique_containers = []
            for container in price_containers:
                is_duplicate = False
                for unique in unique_containers:
                    if abs(container['location']['x'] - unique['location']['x']) < 10 and \
                       abs(container['location']['y'] - unique['location']['y']) < 10:
                        is_duplicate = True
                        break
                if not is_duplicate:
                    unique_containers.append(container)
            
            print(f"After deduplication: {len(unique_containers)} unique containers")
            
            # Extract products from containers
            for i, container in enumerate(unique_containers[:10]):  # Limit to 10
                try:
                    price_text = container['price_text']
                    container_texts = container['container_texts']
                    
                    # Parse price with improved logic
                    parsed_price = self._parse_chilean_price_improved(price_text)
                    
                    if parsed_price['total_price'] <= 0:
                        continue
                    
                    # Extract product name and size from container texts
                    product_name, product_size = self._extract_product_details_from_texts(container_texts, i+1)
                    
                    product_info = {
                        'name': product_name,
                        'price': parsed_price['total_price'],
                        'unit_price': parsed_price.get('unit_price'),
                        'quantity': parsed_price.get('quantity', 1),
                        'size': product_size,
                        'price_text': price_text,
                        'store': 'Lider',
                        'url': ''
                    }
                    
                    products.append(product_info)
                    
                    # Enhanced logging
                    if parsed_price.get('quantity', 1) > 1:
                        print(f"✅ Extracted PROMO: {product_name} ({product_size}) - {parsed_price['quantity']}x ${parsed_price['unit_price']} = ${parsed_price['total_price']}")
                    else:
                        print(f"✅ Extracted: {product_name} ({product_size}) - ${parsed_price['total_price']}")
                    
                except Exception as e:
                    print(f"⚠️ Error processing container {i+1}: {e}")
                    continue
            
            print(f"✅ Final Lider extraction: {len(products)} products with proper names and pricing")
            
        except Exception as e:
            print(f"❌ Error in improved Lider product extraction: {e}")
        
        return products
    
    def _extract_product_details_from_texts(self, texts: List[str], index: int) -> tuple:
        """Extract product name and size from a list of texts"""
        product_name = f"Lider Product {index}"
        product_size = ""
        
        try:
            # Look for product name (longest meaningful text that's not price/button)
            name_candidates = []
            size_candidates = []
            
            for text in texts:
                text = text.strip()
                
                # Skip prices, buttons, and short texts
                if ('$' in text or 'peso' in text.lower() or 
                    text.lower() in ['combinar', 'agregar', 'regular', 'c/u'] or
                    len(text) < 5):
                    continue
                
                # Look for size patterns (2.5 L, 1.5L, 350ml, etc.)
                size_pattern = r'(\d+(?:\.\d+)?\s*[Ll]|\d+\s*[mM][lL])'
                if re.search(size_pattern, text):
                    size_match = re.search(size_pattern, text)
                    if size_match:
                        size_candidates.append(size_match.group(1))
                
                # Look for product names (containing coca, bebida, etc.)
                if (len(text) > 10 and 
                    ('coca' in text.lower() or 'bebida' in text.lower() or 
                     'botella' in text.lower() or 'sin azúcar' in text.lower())):
                    name_candidates.append(text)
                elif len(text) > 15:  # Any longer text could be product name
                    name_candidates.append(text)
            
            # Select best product name
            if name_candidates:
                # Prefer texts containing "coca" or "bebida"
                for candidate in name_candidates:
                    if 'coca' in candidate.lower() or 'bebida' in candidate.lower():
                        product_name = candidate
                        break
                else:
                    # Otherwise take the longest one
                    product_name = max(name_candidates, key=len)
            
            # Select best size
            if size_candidates:
                product_size = size_candidates[0]  # Take first size found
            
            return product_name, product_size
            
        except Exception as e:
            return f"Lider Product {index}", ""
    
    def _parse_chilean_price_improved(self, price_text: str) -> Dict:
        """Parse Chilean price format with improved promotional pricing logic"""
        result = {
            'total_price': 0.0,
            'unit_price': 0.0,
            'quantity': 1,
            'is_promotion': False
        }
        
        try:
            if not price_text:
                return result
            
            # Handle promotional pricing like "2 x $4.000"
            promo_pattern = r'(\d+)\s*x\s*\$\s*(\d{1,3}(?:\.\d{3})*)'
            promo_match = re.search(promo_pattern, price_text, re.IGNORECASE)
            
            if promo_match:
                quantity = int(promo_match.group(1))
                unit_price_str = promo_match.group(2).replace('.', '')  # Remove thousand separators
                unit_price = float(unit_price_str)
                total_price = quantity * unit_price
                
                result.update({
                    'total_price': total_price,
                    'unit_price': unit_price,
                    'quantity': quantity,
                    'is_promotion': True
                })
                return result
            
            # Handle per-unit pricing like "$2.750 c/u"
            per_unit_pattern = r'\$\s*(\d{1,3}(?:\.\d{3})*)\s*c/u'
            per_unit_match = re.search(per_unit_pattern, price_text, re.IGNORECASE)
            
            if per_unit_match:
                price_str = per_unit_match.group(1).replace('.', '')
                price = float(price_str)
                
                result.update({
                    'total_price': price,
                    'unit_price': price,
                    'quantity': 1,
                    'is_promotion': False
                })
                return result
            
            # Handle regular pricing like "$1.990"
            regular_pattern = r'\$\s*(\d{1,3}(?:\.\d{3})*)'
            regular_match = re.search(regular_pattern, price_text)
            
            if regular_match:
                price_str = regular_match.group(1).replace('.', '')
                price = float(price_str)
                
                result.update({
                    'total_price': price,
                    'unit_price': price,
                    'quantity': 1,
                    'is_promotion': False
                })
                return result
            
            return result
            
        except Exception as e:
            print(f"⚠️ Error parsing price '{price_text}': {e}")
            return result
    
    async def _find_product_details_near_price(self, price_element, store_name: str, index: int) -> tuple:
        """Find product name and size near a price element"""
        product_name = f"{store_name} Product {index}"
        product_size = ""
        
        try:
            # Strategy 1: Look in parent container
            try:
                parent = price_element.find_element(AppiumBy.XPATH, "./..")
                parent_texts = parent.find_elements(AppiumBy.XPATH, ".//android.widget.TextView")
                
                for text_elem in parent_texts:
                    text = text_elem.text.strip()
                    # Look for product names and sizes
                    if (text and len(text) > 5 and '$' not in text and 'peso' not in text.lower() 
                        and not text.isdigit() and 'combinar' not in text.lower() 
                        and 'agregar' not in text.lower()):
                        
                        # Check if it's a size
                        size_pattern = r'(\d+(?:\.\d+)?\s*[Ll]|\d+\s*[mM][lL])'
                        if re.search(size_pattern, text):
                            product_size = text
                        # Check if it's a product name
                        elif len(text) > 10:
                            product_name = text
            except:
                pass
            
            # Strategy 2: Look in grandparent container if nothing found
            if product_name == f"{store_name} Product {index}":
                try:
                    grandparent = price_element.find_element(AppiumBy.XPATH, "./../..")
                    grandparent_texts = grandparent.find_elements(AppiumBy.XPATH, ".//android.widget.TextView")
                    
                    for text_elem in grandparent_texts:
                        text = text_elem.text.strip()
                        if (text and len(text) > 10 and '$' not in text and 'peso' not in text.lower() 
                            and not text.isdigit() and 'combinar' not in text.lower() 
                            and 'agregar' not in text.lower() and 'coca' in text.lower()):
                            product_name = text
                            break
                except:
                    pass
            
            return product_name, product_size
            
        except Exception as e:
            return f"{store_name} Product {index}", ""
    
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