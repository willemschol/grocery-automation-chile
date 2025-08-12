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
            
            # Perform search with anti-stale element strategy
            if await self._perform_jumbo_search_anti_stale(product_name):
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
            if await self._perform_lider_search_anti_stale(product_name):
                # Extract products with corrected pricing logic
                products = await self._extract_lider_products_corrected()
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
    # ANTI-STALE ELEMENT SEARCH METHODS
    # ============================================================================
    
    async def _perform_jumbo_search_anti_stale(self, product_name: str) -> bool:
        """Perform search in Jumbo app with anti-stale element strategy and navigation validation"""
        try:
            print(f"🔍 Jumbo anti-stale search for '{product_name}'")
            
            # Strategy: Find and interact in single operations to avoid stale references
            search_selectors = [
                "//android.widget.EditText[@clickable='true']",
                "//android.widget.EditText",
                "//*[contains(@resource-id,'search')]"
            ]
            
            for i, selector in enumerate(search_selectors):
                try:
                    print(f"🎯 Anti-stale attempt {i+1}: {selector}")
                    
                    # Single operation: find, click, clear, type, submit
                    try:
                        elements = self.driver.find_elements(AppiumBy.XPATH, selector)
                        if not elements:
                            print(f"   ❌ No elements found")
                            continue
                            
                        element = elements[0]
                        if not element.is_displayed():
                            print(f"   ❌ Element not visible")
                            continue
                        
                        print(f"   📝 Found element, performing all actions in sequence...")
                        
                        # Immediate sequence without delays to avoid staleness
                        element.click()
                        element.clear()  
                        element.send_keys(product_name)
                        
                        # Quick verification
                        current_text = element.text or element.get_attribute("text") or ""
                        print(f"   ✅ Text entered: '{current_text}'")
                        
                        # Submit immediately
                        self.driver.press_keycode(66)  # Enter key
                        print("   🚀 Search submitted, waiting for results...")
                        time.sleep(8)  # Wait for results
                        
                        # CRITICAL: Validate we stayed on results page
                        print("   🎯 Validating navigation to results page...")
                        
                        # Check current activity and page content
                        current_activity = self.driver.current_activity
                        print(f"   📱 Current activity: {current_activity}")
                        
                        # Look for evidence we're on results vs home
                        results_indicators = [
                            "//*[contains(@text,'$')]",  # Any price
                            "//*[contains(@text,'resultado')]",
                            "//*[contains(@text,'Resultado')]",
                            "//*[contains(@resource-id,'product')]",
                            "//*[contains(@class,'product')]",
                            "//*[contains(@text,'precio')]",
                            "//*[contains(@text,'Precio')]"
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
                            print("✅ Jumbo search completed - confirmed on results page")
                            return True
                        else:
                            print("❌ Jumbo search failed - not on results page, probably returned to home")
                            
                            # Debug: Show what's actually on screen
                            try:
                                all_texts = self.driver.find_elements(AppiumBy.XPATH, "//android.widget.TextView")
                                print(f"   📋 Current page has {len(all_texts)} text elements:")
                                for j, text_elem in enumerate(all_texts[:15]):
                                    try:
                                        text = text_elem.text.strip()
                                        if text:
                                            print(f"      {j+1}. '{text}'")
                                    except:
                                        continue
                            except:
                                pass
                            
                            # Try alternate submission methods
                            print("   🔄 Trying alternate search submission...")
                            
                            # Try to find and click search button instead of Enter key
                            button_selectors = [
                                "//*[contains(@content-desc,'search')]",
                                "//*[contains(@content-desc,'buscar')]",  
                                "//*[contains(@text,'Buscar')]",
                                "//android.widget.Button[contains(@content-desc,'search')]"
                            ]
                            
                            for btn_selector in button_selectors:
                                try:
                                    search_btn = self.driver.find_element(AppiumBy.XPATH, btn_selector)
                                    if search_btn.is_displayed():
                                        search_btn.click()
                                        print(f"   ✅ Clicked search button: {btn_selector}")
                                        time.sleep(8)
                                        
                                        # Check again for results
                                        for indicator in results_indicators:
                                            try:
                                                elements = self.driver.find_elements(AppiumBy.XPATH, indicator)
                                                if elements:
                                                    print(f"   ✅ Now found results: {indicator}")
                                                    return True
                                            except:
                                                continue
                                        break
                                except:
                                    continue
                            
                            continue  # Try next selector
                        
                    except Exception as sequence_error:
                        print(f"   ❌ Sequence failed: {sequence_error}")
                        continue
                        
                except Exception as selector_error:
                    print(f"   ❌ Selector {i+1} error: {selector_error}")
                    continue
            
            print("❌ All anti-stale attempts failed for Jumbo")
            return False
            
        except Exception as e:
            print(f"❌ Jumbo anti-stale search error: {e}")
            return False
    
    async def _perform_lider_search_anti_stale(self, product_name: str) -> bool:
        """Perform search in Lider app with anti-stale element strategy"""
        try:
            print(f"🔍 Lider anti-stale search for '{product_name}'")
            
            # Strategy: Find and interact in single operations to avoid stale references
            search_selectors = [
                "//android.widget.EditText[@clickable='true']",
                "//*[contains(@resource-id,'searchInput')]",
                "//*[contains(@resource-id,'search')]",
                "//android.widget.EditText"
            ]
            
            for i, selector in enumerate(search_selectors):
                try:
                    print(f"🎯 Anti-stale attempt {i+1}: {selector}")
                    
                    # Single operation: find, click, clear, type, submit
                    try:
                        elements = self.driver.find_elements(AppiumBy.XPATH, selector)
                        if not elements:
                            print(f"   ❌ No elements found")
                            continue
                            
                        element = elements[0]
                        if not element.is_displayed():
                            print(f"   ❌ Element not visible")
                            continue
                        
                        print(f"   📝 Found element, performing all actions in sequence...")
                        
                        # Immediate sequence without delays to avoid staleness
                        element.click()
                        element.clear()  
                        element.send_keys(product_name)
                        
                        # Quick verification
                        current_text = element.text or element.get_attribute("text") or ""
                        print(f"   ✅ Text entered: '{current_text}'")
                        
                        # Submit immediately
                        self.driver.press_keycode(66)  # Enter key
                        time.sleep(5)  # Wait for results
                        
                        print("✅ Lider search sequence completed")
                        return True
                        
                    except Exception as sequence_error:
                        print(f"   ❌ Sequence failed: {sequence_error}")
                        continue
                        
                except Exception as selector_error:
                    print(f"   ❌ Selector {i+1} error: {selector_error}")
                    continue
            
            print("❌ All anti-stale attempts failed for Lider")
            return False
            
        except Exception as e:
            print(f"❌ Lider anti-stale search error: {e}")
            return False
    
    # ============================================================================
    # CORRECTED PRODUCT EXTRACTION - FIXED PRICING LOGIC
    # ============================================================================
    
    async def _extract_jumbo_products(self) -> List[Dict]:
        """Extract Jumbo products with SAME CORRECTED logic as Lider"""
        products = []
        
        try:
            print("📦 Starting CORRECTED Jumbo product extraction...")
            
            # Wait for results to load
            time.sleep(5)
            
            # Get all text elements and group them by containers (SAME AS LIDER)
            all_text_elements = self.driver.find_elements(AppiumBy.XPATH, "//android.widget.TextView")
            print(f"📋 Found {len(all_text_elements)} TextView elements for analysis")
            
            # Debug: Print all text elements
            print("📝 All text elements found:")
            all_texts = []
            for i, elem in enumerate(all_text_elements):
                try:
                    text = elem.text.strip()
                    if text:
                        all_texts.append(text)
                        print(f"  {i+1}. '{text}'")
                except:
                    continue
            
            # SAME AS LIDER: Build price containers by grouping related elements
            price_containers = []
            
            # Strategy: Group elements by their Y-coordinate proximity
            price_elements = []
            
            # First, find all price elements with their positions
            for i, element in enumerate(all_text_elements):
                try:
                    text = element.text.strip()
                    if text and ('$' in text or 'peso' in text.lower()):
                        price_elements.append({
                            'element': element,
                            'text': text,
                            'location': element.location,
                            'index': i
                        })
                except:
                    continue
            
            print(f"Found {len(price_elements)} price elements at positions:")
            for pe in price_elements:
                print(f"  '{pe['text']}' at Y={pe['location']['y']}")
            
            # For each price element, group nearby text elements
            for price_info in price_elements:
                price_y = price_info['location']['y']
                price_text = price_info['text']
                
                # Collect texts that are near this price (within 200 pixels vertically)
                related_texts = [price_text]  # Start with the price
                
                for j, text_elem in enumerate(all_text_elements):
                    try:
                        text = text_elem.text.strip()
                        if not text or text == price_text:
                            continue
                        
                        elem_location = text_elem.location
                        y_distance = abs(elem_location['y'] - price_y)
                        
                        # If element is close vertically, it's likely part of same product
                        if y_distance <= 200:  # Within 200 pixels
                            related_texts.append(text)
                            print(f"  Grouped '{text}' with '{price_text}' (Y distance: {y_distance})")
                    except:
                        continue
                
                price_containers.append({
                    'price_text': price_text,
                    'all_texts': related_texts,
                    'location': price_info['location']
                })
                
                print(f"💰 Built container for '{price_text}': {related_texts}")
            
            print(f"Found {len(price_containers)} price containers")
            
            # Remove duplicates and process containers
            unique_containers = []
            for container in price_containers:
                is_duplicate = False
                for unique in unique_containers:
                    if abs(container['location']['x'] - unique['location']['x']) < 20 and \
                       abs(container['location']['y'] - unique['location']['y']) < 20:
                        is_duplicate = True
                        break
                if not is_duplicate:
                    unique_containers.append(container)
            
            print(f"After deduplication: {len(unique_containers)} unique containers")
            
            # Extract products with CORRECTED pricing logic (SAME AS LIDER)
            for i, container in enumerate(unique_containers[:10]):
                try:
                    price_text = container['price_text']
                    all_texts = container['all_texts']
                    
                    print(f"\n📦 Processing container {i+1}:")
                    print(f"  Price text: '{price_text}'")
                    print(f"  All texts: {all_texts}")
                    
                    # Parse price with CORRECTED logic
                    parsed_price = self._parse_chilean_price_corrected(price_text)
                    
                    if parsed_price['total_price'] <= 0:
                        print(f"  ❌ Invalid price: {parsed_price}")
                        continue
                    
                    # Extract product name and size from all texts (SAME AS LIDER)
                    product_name, product_size = self._extract_product_name_and_size_corrected(all_texts, i+1)
                    
                    # Calculate price per liter if we have size (SAME AS LIDER)
                    price_per_liter = 0
                    if product_size and parsed_price['total_price'] > 0:
                        # Extract volume in liters
                        volume_match = re.search(r'(\d+(?:\.\d+)?)', product_size)
                        if volume_match:
                            volume = float(volume_match.group(1))
                            if 'ml' in product_size.lower():
                                volume = volume / 1000  # Convert ml to L
                            
                            # For promotions like "2x $4.000" for 2.5L bottles
                            if parsed_price.get('is_promotion', False):
                                total_volume = volume * parsed_price['quantity']
                                price_per_liter = parsed_price['total_price'] / total_volume
                            else:
                                price_per_liter = parsed_price['total_price'] / volume
                    
                    product_info = {
                        'name': product_name,
                        'price': parsed_price['total_price'],
                        'price_per_liter': round(price_per_liter, 2) if price_per_liter > 0 else 0,
                        'quantity': parsed_price.get('quantity', 1),
                        'size': product_size,
                        'price_text': price_text,
                        'store': 'Jumbo',
                        'is_promotion': parsed_price.get('is_promotion', False),
                        'url': ''
                    }
                    
                    products.append(product_info)
                    
                    # Enhanced logging with CORRECT pricing (SAME AS LIDER)
                    if parsed_price.get('is_promotion', False):
                        if price_per_liter > 0:
                            print(f"✅ PROMO: {product_name} ({product_size}) - {parsed_price['quantity']} units for ${parsed_price['total_price']} = ${price_per_liter}/L")
                        else:
                            print(f"✅ PROMO: {product_name} ({product_size}) - {parsed_price['quantity']} units for ${parsed_price['total_price']}")
                    else:
                        if price_per_liter > 0:
                            print(f"✅ Regular: {product_name} ({product_size}) - ${parsed_price['total_price']} = ${price_per_liter}/L")
                        else:
                            print(f"✅ Regular: {product_name} ({product_size}) - ${parsed_price['total_price']}")
                    
                except Exception as e:
                    print(f"⚠️ Error processing container {i+1}: {e}")
                    continue
            
            print(f"\n✅ CORRECTED Jumbo extraction: {len(products)} products with proper pricing")
            
        except Exception as e:
            print(f"❌ Error in corrected Jumbo product extraction: {e}")
        
        return products
    
    async def _extract_lider_products_corrected(self) -> List[Dict]:
        """Extract Lider products with CORRECTED pricing logic"""
        products = []
        
        try:
            print("📦 Starting CORRECTED Lider product extraction...")
            
            # Wait for results to load
            time.sleep(5)
            
            # Get all text elements and group them by containers
            all_text_elements = self.driver.find_elements(AppiumBy.XPATH, "//android.widget.TextView")
            print(f"📋 Found {len(all_text_elements)} TextView elements for analysis")
            
            # Debug: Print all text elements
            print("📝 All text elements found:")
            all_texts = []
            for i, elem in enumerate(all_text_elements):
                try:
                    text = elem.text.strip()
                    if text:
                        all_texts.append(text)
                        print(f"  {i+1}. '{text}'")
                except:
                    continue
            
            # FIXED: Build price containers by grouping related elements
            price_containers = []
            
            # Strategy: Group elements by their Y-coordinate proximity
            price_elements = []
            
            # First, find all price elements with their positions
            for i, element in enumerate(all_text_elements):
                try:
                    text = element.text.strip()
                    if text and ('$' in text or 'peso' in text.lower()):
                        price_elements.append({
                            'element': element,
                            'text': text,
                            'location': element.location,
                            'index': i
                        })
                except:
                    continue
            
            print(f"Found {len(price_elements)} price elements at positions:")
            for pe in price_elements:
                print(f"  '{pe['text']}' at Y={pe['location']['y']}")
            
            # For each price element, group nearby text elements
            for price_info in price_elements:
                price_y = price_info['location']['y']
                price_text = price_info['text']
                
                # Collect texts that are near this price (within 200 pixels vertically)
                related_texts = [price_text]  # Start with the price
                
                for j, text_elem in enumerate(all_text_elements):
                    try:
                        text = text_elem.text.strip()
                        if not text or text == price_text:
                            continue
                        
                        elem_location = text_elem.location
                        y_distance = abs(elem_location['y'] - price_y)
                        
                        # If element is close vertically, it's likely part of same product
                        if y_distance <= 200:  # Within 200 pixels
                            related_texts.append(text)
                            print(f"  Grouped '{text}' with '{price_text}' (Y distance: {y_distance})")
                    except:
                        continue
                
                price_containers.append({
                    'price_text': price_text,
                    'all_texts': related_texts,
                    'location': price_info['location']
                })
                
                print(f"💰 Built container for '{price_text}': {related_texts}")
            
            print(f"Found {len(price_containers)} price containers")
            
            # Remove duplicates and process containers
            unique_containers = []
            for container in price_containers:
                is_duplicate = False
                for unique in unique_containers:
                    if abs(container['location']['x'] - unique['location']['x']) < 20 and \
                       abs(container['location']['y'] - unique['location']['y']) < 20:
                        is_duplicate = True
                        break
                if not is_duplicate:
                    unique_containers.append(container)
            
            print(f"After deduplication: {len(unique_containers)} unique containers")
            
            # Extract products with CORRECTED pricing logic
            for i, container in enumerate(unique_containers[:10]):
                try:
                    price_text = container['price_text']
                    all_texts = container['all_texts']
                    
                    print(f"\n📦 Processing container {i+1}:")
                    print(f"  Price text: '{price_text}'")
                    print(f"  All texts: {all_texts}")
                    
                    # Parse price with CORRECTED logic
                    parsed_price = self._parse_chilean_price_corrected(price_text)
                    
                    if parsed_price['total_price'] <= 0:
                        print(f"  ❌ Invalid price: {parsed_price}")
                        continue
                    
                    # Extract product name and size from all texts
                    product_name, product_size = self._extract_product_name_and_size_corrected(all_texts, i+1)
                    
                    # Calculate price per liter if we have size
                    price_per_liter = 0
                    if product_size and parsed_price['total_price'] > 0:
                        # Extract volume in liters
                        volume_match = re.search(r'(\d+(?:\.\d+)?)', product_size)
                        if volume_match:
                            volume = float(volume_match.group(1))
                            if 'ml' in product_size.lower():
                                volume = volume / 1000  # Convert ml to L
                            
                            # For promotions like "2x $4.000" for 2.5L bottles
                            if parsed_price.get('is_promotion', False):
                                total_volume = volume * parsed_price['quantity']
                                price_per_liter = parsed_price['total_price'] / total_volume
                            else:
                                price_per_liter = parsed_price['total_price'] / volume
                    
                    product_info = {
                        'name': product_name,
                        'price': parsed_price['total_price'],
                        'price_per_liter': round(price_per_liter, 2) if price_per_liter > 0 else 0,
                        'quantity': parsed_price.get('quantity', 1),
                        'size': product_size,
                        'price_text': price_text,
                        'store': 'Lider',
                        'is_promotion': parsed_price.get('is_promotion', False),
                        'url': ''
                    }
                    
                    products.append(product_info)
                    
                    # Enhanced logging with CORRECT pricing
                    if parsed_price.get('is_promotion', False):
                        if price_per_liter > 0:
                            print(f"✅ PROMO: {product_name} ({product_size}) - {parsed_price['quantity']} units for ${parsed_price['total_price']} = ${price_per_liter}/L")
                        else:
                            print(f"✅ PROMO: {product_name} ({product_size}) - {parsed_price['quantity']} units for ${parsed_price['total_price']}")
                    else:
                        if price_per_liter > 0:
                            print(f"✅ Regular: {product_name} ({product_size}) - ${parsed_price['total_price']} = ${price_per_liter}/L")
                        else:
                            print(f"✅ Regular: {product_name} ({product_size}) - ${parsed_price['total_price']}")
                    
                except Exception as e:
                    print(f"⚠️ Error processing container {i+1}: {e}")
                    continue
            
            print(f"\n✅ CORRECTED Lider extraction: {len(products)} products with proper pricing")
            
        except Exception as e:
            print(f"❌ Error in corrected Lider product extraction: {e}")
        
        return products
    
    def _parse_chilean_price_corrected(self, price_text: str) -> Dict:
        """Parse Chilean price format with CORRECTED promotional pricing logic"""
        result = {
            'total_price': 0.0,
            'quantity': 1,
            'is_promotion': False
        }
        
        try:
            if not price_text:
                return result
            
            print(f"  🔍 Parsing price: '{price_text}'")
            
            # Handle promotional pricing like "2 x $4.000" - CORRECTED LOGIC
            # This means 2 items for $4.000 total (NOT 2 x $4.000 each)
            promo_pattern = r'(\d+)\s*x\s*\$\s*(\d{1,3}(?:\.\d{3})*)'
            promo_match = re.search(promo_pattern, price_text, re.IGNORECASE)
            
            if promo_match:
                quantity = int(promo_match.group(1))
                total_price_str = promo_match.group(2).replace('.', '')  # Remove thousand separators
                total_price = float(total_price_str)  # This is the TOTAL price for all items
                
                result.update({
                    'total_price': total_price,  # Total price for all items
                    'quantity': quantity,
                    'is_promotion': True
                })
                
                print(f"  ✅ PROMOTION: {quantity} items for ${total_price} total")
                return result
            
            # Handle per-unit pricing like "$2.750 c/u"
            per_unit_pattern = r'\$\s*(\d{1,3}(?:\.\d{3})*)\s*c/u'
            per_unit_match = re.search(per_unit_pattern, price_text, re.IGNORECASE)
            
            if per_unit_match:
                price_str = per_unit_match.group(1).replace('.', '')
                price = float(price_str)
                
                result.update({
                    'total_price': price,
                    'quantity': 1,
                    'is_promotion': False
                })
                
                print(f"  ✅ PER UNIT: ${price} each")
                return result
            
            # Handle regular pricing like "$1.990"
            regular_pattern = r'\$\s*(\d{1,3}(?:\.\d{3})*)'
            regular_match = re.search(regular_pattern, price_text)
            
            if regular_match:
                price_str = regular_match.group(1).replace('.', '')
                price = float(price_str)
                
                result.update({
                    'total_price': price,
                    'quantity': 1,
                    'is_promotion': False
                })
                
                print(f"  ✅ REGULAR: ${price}")
                return result
            
            print(f"  ❌ Could not parse price format")
            return result
            
        except Exception as e:
            print(f"⚠️ Error parsing price '{price_text}': {e}")
            return result
    
    def _extract_product_name_and_size_corrected(self, all_texts: List[str], index: int) -> tuple:
        """Extract product name and size from container texts - CORRECTED"""
        product_name = f"Unknown Product {index}"
        product_size = ""
        
        try:
            print(f"  🔍 Extracting name and size from: {all_texts}")
            
            name_candidates = []
            size_candidates = []
            
            for text in all_texts:
                text = text.strip()
                
                # Skip prices, buttons, and very short texts
                if ('$' in text or 'peso' in text.lower() or 
                    text.lower() in ['combinar', 'agregar', 'regular', 'c/u', 'x'] or
                    len(text) < 3):
                    continue
                
                # Look for size patterns (2.5 L, 1.5L, 350ml, etc.)
                size_patterns = [
                    r'(\d+(?:\.\d+)?\s*[Ll])\b',  # 2.5 L, 1.5L
                    r'(\d+\s*[mM][lL])\b',        # 350ml, 500 ml
                    r'(\d+(?:\.\d+)?\s*[lL]itros?)\b'  # 2.5 litros
                ]
                
                for pattern in size_patterns:
                    size_match = re.search(pattern, text)
                    if size_match:
                        size_candidates.append(size_match.group(1))
                        print(f"  📏 Found size: '{size_match.group(1)}'")
                
                # Look for product names 
                if len(text) > 5:
                    # Prioritize texts containing product-related keywords
                    if any(keyword in text.lower() for keyword in ['coca', 'cola', 'bebida', 'botella', 'sin azúcar', 'original']):
                        name_candidates.insert(0, text)  # Put at front
                        print(f"  📝 Found priority name: '{text}'")
                    elif len(text) > 10:  # Any longer text could be product name
                        name_candidates.append(text)
                        print(f"  📝 Found possible name: '{text}'")
            
            # Select best product name
            if name_candidates:
                product_name = name_candidates[0]  # Take first (priority) candidate
                print(f"  ✅ Selected name: '{product_name}'")
            
            # Select best size
            if size_candidates:
                product_size = size_candidates[0]  # Take first size found
                print(f"  ✅ Selected size: '{product_size}'")
            
            return product_name, product_size
            
        except Exception as e:
            print(f"  ❌ Error extracting details: {e}")
            return f"Product {index}", ""
    
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
            
            return product_name, product_size
            
        except Exception as e:
            return f"{store_name} Product {index}", ""
    
    # ============================================================================
    # DEBUG AND UTILITY METHODS
    # ============================================================================
    
    def debug_current_state(self) -> Dict:
        """Debug current state of the app"""
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