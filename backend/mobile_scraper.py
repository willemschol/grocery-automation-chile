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
        self.appium_port = 4723
        
    def setup_driver(self, app_package: str = None):
        """Initialize Appium driver for Android automation with proper session management"""
        try:
            # Close any existing driver to prevent context mixing
            if self.driver:
                try:
                    self.driver.quit()
                    print("🔄 Closed existing driver to prevent app context mixing")
                except:
                    pass
                self.driver = None
                
            options = UiAutomator2Options()
            options.platform_name = "Android"
            options.device_name = "grocery_automation" 
            options.automation_name = "UiAutomator2"
            options.no_reset = True  # Keep app data between sessions
            options.full_reset = False
            
            if app_package:
                options.app_package = app_package
                print(f"🚀 Setting up new driver for app: {app_package}")
                
            # Additional capabilities for stability
            options.new_command_timeout = 300  # 5 minutes
            options.implicit_wait = 10
            
            print(f"Connecting to Appium server at http://localhost:{self.appium_port}")
            self.driver = webdriver.Remote(f'http://localhost:{self.appium_port}', options=options)
            self.wait = WebDriverWait(self.driver, 15)
            
            # Verify we have the correct app package active
            actual_package = self.driver.current_package
            print(f"✅ Driver initialized - Expected: {app_package}, Actual: {actual_package}")
            
            # If package doesn't match, try to activate the correct app
            if app_package and actual_package != app_package:
                print(f"⚠️ Package mismatch! Attempting to launch correct appp...")
                try:
                    self.driver.activate_app(app_package)
                    time.sleep(2)
                    actual_package = self.driver.current_package
                    print(f"🔄 After activation - Actual package: {actual_package}")
                except Exception as activation_error:
                    print(f"⚠️ App activation failed: {activation_error}")
            
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
            
            # Perform search using ultra-robust method
            if await self._perform_jumbo_search_ultra_robust(product_name):
                # Extract products using corrected method
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
            
            # Perform search using ultra-robust method
            if await self._perform_lider_search_ultra_robust(product_name):
                # Extract products using corrected method
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
    
    async def _perform_jumbo_search_ultra_robust(self, product_name: str) -> bool:
        """Ultra-robust Jumbo search with per-operation element re-finding"""
        try:
            print(f"🎯 Starting ULTRA-ROBUST Jumbo search for '{product_name}'")
            
            # Define multiple search element strategies
            search_strategies = [
                ("🔄 Attempt 1: Clickable EditText", "//android.widget.EditText[@clickable='true']"),
                ("🔄 Attempt 2: Any EditText", "//android.widget.EditText"),
                ("🔄 Attempt 3: Search Resource ID", "//*[contains(@resource-id,'search')]"),
                ("🔄 Attempt 4: Text Input Field", "//*[@class='android.widget.EditText']"),
                ("🔄 Attempt 5: Focusable EditText", "//android.widget.EditText[@focusable='true']")
            ]
            
            for attempt, (strategy_name, xpath_selector) in enumerate(search_strategies, 1):
                try:
                    print(strategy_name)
                    
                    # Step 1: Find elements to ensure they exist
                    try:
                        search_elements = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_all_elements_located((AppiumBy.XPATH, xpath_selector))
                        )
                    except:
                        print(f"   ❌ No elements found with strategy {attempt}")
                        continue
                    
                    if not search_elements:
                        print(f"   ❌ No elements found with strategy {attempt}")
                        continue
                    
                    print(f"   🎯 Trying element 1/{len(search_elements)}")
                    
                    # Step 2: Per-operation element re-finding to prevent staleness
                    try:
                        print(f"   📝 Performing per-operation element re-finding...")
                        
                        # OPERATION 1: Click - Find fresh element
                        try:
                            click_element = WebDriverWait(self.driver, 3).until(
                                EC.element_to_be_clickable((AppiumBy.XPATH, xpath_selector))
                            )
                            click_element.click()
                            print(f"   ✅ Click successful")
                            time.sleep(0.3)
                        except Exception as click_error:
                            print(f"   ❌ Click failed: {click_error}")
                            continue
                        
                        # OPERATION 2: Clear - Find fresh element again
                        try:
                            clear_element = WebDriverWait(self.driver, 3).until(
                                EC.presence_of_element_located((AppiumBy.XPATH, xpath_selector))
                            )
                            clear_element.clear()
                            print(f"   ✅ Clear successful")
                        except Exception as clear_error:
                            print(f"   ⚠️ Clear failed, continuing: {clear_error}")
                        
                        # OPERATION 3: Send keys - Find fresh element again
                        try:
                            type_element = WebDriverWait(self.driver, 3).until(
                                EC.presence_of_element_located((AppiumBy.XPATH, xpath_selector))
                            )
                            type_element.send_keys(product_name)
                            print(f"   ✅ Text input successful")
                            time.sleep(0.5)
                        except Exception as type_error:
                            print(f"   ❌ Text input failed: {type_error}")
                            continue
                        
                        # OPERATION 4: Verify text - Find fresh element again
                        try:
                            verify_element = WebDriverWait(self.driver, 3).until(
                                EC.presence_of_element_located((AppiumBy.XPATH, xpath_selector))
                            )
                            current_text = verify_element.get_attribute("text") or verify_element.text or ""
                            if product_name.lower() in current_text.lower():
                                print(f"   ✅ Text verified: '{current_text}'")
                                
                                # Submit with Jumbo-specific search triggers
                                try:
                                    print(f"   🎯 Trying Jumbo-specific search submission methods...")
                                    
                                    # Method 1: Try common Jumbo search button patterns first
                                    jumbo_search_patterns = [
                                        "//android.widget.ImageView[contains(@content-desc,'search') or contains(@content-desc,'buscar')]",
                                        "//android.widget.ImageButton[contains(@content-desc,'search') or contains(@content-desc,'buscar')]",
                                        "//*[contains(@resource-id,'search_button') or contains(@resource-id,'btn_search')]",
                                        "//android.widget.Button[contains(@text,'Buscar') or contains(@text,'BUSCAR')]",
                                        "//*[contains(@class,'SearchView')]//android.widget.ImageButton",
                                        "//*[@content-desc='Search' or @content-desc='Buscar']",
                                        "//android.widget.ImageView[@clickable='true'][contains(@bounds,'search')]"
                                    ]
                                    
                                    search_button_found = False
                                    for i, pattern in enumerate(jumbo_search_patterns, 1):
                                        try:
                                            print(f"   🔍 Trying pattern {i}: {pattern[:50]}...")
                                            search_btn = WebDriverWait(self.driver, 2).until(
                                                EC.element_to_be_clickable((AppiumBy.XPATH, pattern))
                                            )
                                            search_btn.click()
                                            print(f"   ✅ Jumbo search button clicked (pattern {i})")
                                            search_button_found = True
                                            time.sleep(4)  # Wait for navigation
                                            break
                                        except Exception as pattern_error:
                                            print(f"   ❌ Pattern {i} failed: search button not found")
                                            continue
                                    
                                    # Method 2: If no search button, try alternative keycodes
                                    if not search_button_found:
                                        print(f"   🎯 No search button found, trying alternative submission methods...")
                                        alternative_methods = [
                                            (84, "KEYCODE_SEARCH"),      # Android search key
                                            (23, "KEYCODE_DPAD_CENTER"), # Center/OK key
                                            (61, "KEYCODE_TAB"),         # Tab to next element
                                        ]
                                        
                                        for keycode, method_name in alternative_methods:
                                            try:
                                                print(f"   🔑 Trying {method_name} (keycode {keycode})")
                                                self.driver.press_keycode(keycode)
                                                time.sleep(3)
                                                
                                                # Check if we're still in MainActivity
                                                activity_check = self.driver.current_activity
                                                if activity_check != ".features.main.activity.MainActivity":
                                                    print(f"   ✅ {method_name} worked! New activity: {activity_check}")
                                                    search_button_found = True
                                                    break
                                                else:
                                                    print(f"   ❌ {method_name} failed, still in MainActivity")
                                            except Exception as key_error:
                                                print(f"   ❌ {method_name} error: {key_error}")
                                                continue
                                    
                                    # Method 3: Final fallback - try Enter key as last resort
                                    if not search_button_found:
                                        print(f"   🎯 Final fallback: Enter key")
                                        self.driver.press_keycode(66)  # Enter key
                                        time.sleep(4)
                                    
                                    # Final validation
                                    final_activity = self.driver.current_activity
                                    print(f"   📱 Final activity: {final_activity}")
                                    
                                    return await self._validate_jumbo_navigation()
                                
                                except Exception as submit_error:
                                    print(f"   ❌ All Jumbo search methods failed: {submit_error}")
                                    continue
                            else:
                                print(f"   ❌ Text verification failed: expected '{product_name}', got '{current_text}'")
                                continue
                        except Exception as verify_error:
                            print(f"   ❌ Text verification failed: {verify_error}")
                            continue
                            
                    except Exception as interaction_error:
                        print(f"   ❌ Element {attempt} failed: {interaction_error}")
                        continue
                        
                except Exception as strategy_error:
                    print(f"   ❌ Strategy {attempt} failed: {strategy_error}")
                    continue
            
            print("❌ All search strategies failed")
            return False
            
        except Exception as e:
            print(f"❌ Ultra-robust search error: {e}")
            return False
    
    async def _perform_lider_search_ultra_robust(self, product_name: str) -> bool:
        """Ultra-robust Lider search with per-operation element re-finding"""
        try:
            print(f"🎯 Starting ULTRA-ROBUST Lider search for '{product_name}'")
            
            # Define multiple search element strategies for Lider
            search_strategies = [
                ("🔄 Lider Attempt 1: Clickable EditText", "//android.widget.EditText[@clickable='true']"),
                ("🔄 Lider Attempt 2: Search Input Resource ID", "//*[contains(@resource-id,'searchInput')]"),
                ("🔄 Lider Attempt 3: Search Resource ID", "//*[contains(@resource-id,'search')]"),
                ("🔄 Lider Attempt 4: Any EditText", "//android.widget.EditText"),
                ("🔄 Lider Attempt 5: Text Field with Hint", "//*[contains(@hint,'Buscar') or contains(@hint,'Search')]")
            ]
            
            for attempt, (strategy_name, xpath_selector) in enumerate(search_strategies, 1):
                try:
                    print(strategy_name)
                    
                    # Step 1: Find elements to ensure they exist
                    try:
                        search_elements = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_all_elements_located((AppiumBy.XPATH, xpath_selector))
                        )
                    except:
                        print(f"   ❌ No {strategy_name} elements found")
                        continue
                    
                    if not search_elements:
                        print(f"   ❌ No {strategy_name} elements found")
                        continue
                    
                    print(f"   🎯 Trying Lider element 1/{len(search_elements)}")
                    
                    # Step 2: Per-operation element re-finding to prevent staleness
                    try:
                        print(f"   📝 Performing per-operation Lider element re-finding...")
                        
                        # OPERATION 1: Click - Find fresh element
                        try:
                            click_element = WebDriverWait(self.driver, 3).until(
                                EC.element_to_be_clickable((AppiumBy.XPATH, xpath_selector))
                            )
                            click_element.click()
                            print(f"   ✅ Lider click successful")
                            time.sleep(0.3)
                        except Exception as click_error:
                            print(f"   ❌ Lider click failed: {click_error}")
                            continue
                        
                        # OPERATION 2: Clear - Find fresh element again
                        try:
                            clear_element = WebDriverWait(self.driver, 3).until(
                                EC.presence_of_element_located((AppiumBy.XPATH, xpath_selector))
                            )
                            clear_element.clear()
                            print(f"   ✅ Lider clear successful")
                        except Exception as clear_error:
                            print(f"   ⚠️ Lider clear failed, continuing: {clear_error}")
                        
                        # OPERATION 3: Send keys - Find fresh element again with state validation
                        try:
                            type_element = WebDriverWait(self.driver, 3).until(
                                EC.presence_of_element_located((AppiumBy.XPATH, xpath_selector))
                            )
                            
                            # Validate element state before typing
                            if not type_element.is_enabled():
                                print(f"   ⚠️ Lider element not enabled, trying to enable...")
                                type_element.click()  # Try to enable/focus
                                time.sleep(0.5)
                            
                            # Alternative text input methods for problematic elements
                            try:
                                type_element.send_keys(product_name)
                                print(f"   ✅ Lider text input successful")
                            except Exception as send_keys_error:
                                print(f"   ⚠️ send_keys failed, trying set_value: {send_keys_error}")
                                try:
                                    type_element.set_value(product_name)
                                    print(f"   ✅ Lider set_value successful")
                                except Exception as set_value_error:
                                    print(f"   ⚠️ set_value failed, trying character input: {set_value_error}")
                                    # Character by character input as last resort
                                    for char in product_name:
                                        type_element.send_keys(char)
                                        time.sleep(0.1)
                                    print(f"   ✅ Lider character-by-character input successful")
                            
                            time.sleep(0.5)
                        except Exception as type_error:
                            print(f"   ❌ Lider text input failed: {type_error}")
                            continue
                        
                        # OPERATION 4: Verify text - Find fresh element again
                        try:
                            verify_element = WebDriverWait(self.driver, 3).until(
                                EC.presence_of_element_located((AppiumBy.XPATH, xpath_selector))
                            )
                            current_text = verify_element.get_attribute("text") or verify_element.text or ""
                            if product_name.lower() in current_text.lower():
                                print(f"   ✅ Lider text verified: '{current_text}'")
                                
                                # Submit with Enter key
                                try:
                                    self.driver.press_keycode(66)  # Enter key
                                    print(f"   🚀 Lider search submitted")
                                    time.sleep(3)  # Wait for Lider results
                                    return True  # Lider doesn't need navigation validation like Jumbo
                                
                                except Exception as submit_error:
                                    print(f"   ⚠️ Lider submit failed: {submit_error}")
                                    continue
                            else:
                                print(f"   ❌ Lider text verification failed")
                                continue
                        except Exception as verify_error:
                            print(f"   ❌ Lider text verification failed: {verify_error}")
                            continue
                            
                    except Exception as interaction_error:
                        print(f"   ❌ Lider element {attempt} failed: {interaction_error}")
                        continue
                        
                except Exception as strategy_error:
                    print(f"   ❌ Lider strategy {attempt} failed: {strategy_error}")
                    continue
            
            print("❌ All Lider search strategies failed")
            return False
            
        except Exception as e:
            print(f"❌ Lider ultra-robust search error: {e}")
            return False

    async def _validate_jumbo_navigation(self) -> bool:
        """STRICT Jumbo navigation validation - no more benefit of doubt"""
        try:
            print(f"🎯 STRICT Jumbo navigation validation...")
            
            # Wait a moment for navigation to complete
            time.sleep(2)
            
            # Check current activity
            current_activity = self.driver.current_activity
            print(f"   📱 Current activity: {current_activity}")
            
            # Get page source to check content
            page_source = self.driver.page_source.lower()
            
            # STRICT check: Look for clear home page indicators
            home_page_indicators = [
                "experiencia única", "variedad de cortes", "¡participa!",
                "categorías destacadas", "frutas y verduras", "productos frecuentes",
                "mostrar más", "despacho a:", "¿qué estás buscando?"
            ]
            
            home_indicators_found = 0
            for indicator in home_page_indicators:
                if indicator in page_source:
                    home_indicators_found += 1
                    print(f"   🏠 Found home indicator: '{indicator}'")
            
            # STRICT check: Look for search result indicators
            search_result_indicators = [
                "resultados", "productos encontrados", "filtrar resultados",
                "ordenar por", "precio desde", "precio hasta", "agregar al carrito",
                "disponible en tienda", "sin stock", "ver producto"
            ]
            
            search_indicators_found = 0
            for indicator in search_result_indicators:
                if indicator in page_source:
                    search_indicators_found += 1
                    print(f"   📦 Found search indicator: '{indicator}'")
            
            # STRICT decision logic
            if home_indicators_found >= 3:
                print(f"   ❌ STRICT VALIDATION: Found {home_indicators_found} home indicators - clearly on home page")
                print(f"   🚫 Search failed - Jumbo returned to home instead of showing results")
                return False
            elif search_indicators_found >= 2:
                print(f"   ✅ STRICT VALIDATION: Found {search_indicators_found} search indicators - on search results")
                return True
            elif current_activity != ".features.main.activity.MainActivity":
                print(f"   ✅ STRICT VALIDATION: Different activity - likely search results")
                return True
            else:
                print(f"   ❌ STRICT VALIDATION: MainActivity + unclear content = search failed")
                print(f"   📊 Home indicators: {home_indicators_found}, Search indicators: {search_indicators_found}")
                return False
                
        except Exception as e:
            print(f"   ❌ Navigation validation error: {e}")
            return False

    
    async def _extract_jumbo_products(self) -> List[Dict]:
        """Extract product information from Jumbo search results using corrected proximity-based approach"""
        products = []
        
        try:
            print("📦 Starting corrected Jumbo product extraction with Y-coordinate proximity grouping...")
            
            # Save page source for analysis with Windows-compatible path
            import tempfile
            debug_file = f"{tempfile.gettempdir()}/jumbo_products_page.xml"
            self.save_page_source(debug_file)
            
            # Get all TextView elements that might contain product information - ENHANCED DISCOVERY
            all_text_elements = []
            try:
                # Try multiple element discovery strategies
                discovery_strategies = [
                    ("android.widget.TextView", "Primary TextView discovery"),
                    ("//*[@class='android.widget.TextView']", "XPath TextView discovery"),
                    ("//*[contains(@class,'TextView')]", "Partial TextView class discovery"),
                    ("//*", "All elements discovery")
                ]
                
                print(f"🔍 Trying multiple element discovery strategies...")
                
                for strategy, description in discovery_strategies:
                    try:
                        if strategy.startswith("//"):
                            # XPath strategy
                            elements = self.driver.find_elements(AppiumBy.XPATH, strategy)
                        else:
                            # Class name strategy
                            elements = self.driver.find_elements(AppiumBy.CLASS_NAME, strategy)
                        
                        print(f"   📱 {description}: Found {len(elements)} elements")
                        
                        # Use the strategy that finds the most elements
                        if len(elements) > len(all_text_elements):
                            all_text_elements = elements
                            print(f"   ✅ Using {description} (most elements found)")
                        
                    except Exception as e:
                        print(f"   ⚠️ {description} failed: {e}")
                        continue
                
                print(f"🔍 Final element count: {len(all_text_elements)} elements")
                
                # Process the elements to extract text and location info
                processed_elements = []
                for elem in all_text_elements:
                    try:
                        text = elem.text.strip() if elem.text else ""
                        if text and len(text) > 0:
                            location = elem.location
                            processed_elements.append({
                                'element': elem,
                                'text': text,
                                'x': location['x'],
                                'y': location['y'],
                                'size': elem.size
                            })
                    except:
                        continue
                
                all_text_elements = processed_elements
                print(f"📝 Extracted {len(all_text_elements)} valid text elements")
                
            except Exception as e:
                print(f"❌ Error finding text elements: {e}")
                return products
            
            if not all_text_elements:
                print("❌ No text elements found")
                return []
            
            # Find potential price elements with ENHANCED debugging
            potential_price_elements = []
            print(f"🔍 Analyzing {len(all_text_elements)} elements for price patterns...")
            
            for i, elem_info in enumerate(all_text_elements):
                text = elem_info['text']
                print(f"   📝 Element {i+1}: '{text}'")
                
                if self._looks_like_price(text):
                    potential_price_elements.append(elem_info)
                    print(f"   💰 PRICE DETECTED: '{text}'")
                else:
                    print(f"   ❌ Not a price: '{text}'")
            
            price_elements = potential_price_elements
            
            print(f"💰 Found {len(price_elements)} potential price elements")
            
            if not price_elements:
                print("❌ No potential price elements found")
                
                # Take screenshot for debugging when no products found
                try:
                    import tempfile
                    import datetime
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    screenshot_file = f"{tempfile.gettempdir()}/jumbo_no_products_{timestamp}.png"
                    self.driver.save_screenshot(screenshot_file)
                    print(f"📸 Screenshot saved for debugging: {screenshot_file}")
                except Exception as screenshot_error:
                    print(f"⚠️ Could not save screenshot: {screenshot_error}")
                
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
                    
                    # Extract product information from this group with the SPECIFIC price element
                    product_info = self._extract_product_from_group_corrected(related_elements, "Jumbo", price_elem)
                    
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
        """Extract product information from Lider search results using corrected proximity-based approach"""
        products = []
        
        try:
            print("📦 Starting corrected Lider product extraction with Y-coordinate proximity grouping...")
            
            # Save page source for analysis with Windows-compatible path
            import tempfile
            debug_file = f"{tempfile.gettempdir()}/lider_products_page.xml"
            self.save_page_source(debug_file)
            
            # Get all TextView elements that might contain product information - ENHANCED DISCOVERY
            all_text_elements = []
            try:
                # Try multiple element discovery strategies
                discovery_strategies = [
                    ("android.widget.TextView", "Primary TextView discovery"),
                    ("//*[@class='android.widget.TextView']", "XPath TextView discovery"),
                    ("//*[contains(@class,'TextView')]", "Partial TextView class discovery"),
                    ("//*", "All elements discovery")
                ]
                
                print(f"🔍 Trying multiple element discovery strategies...")
                
                for strategy, description in discovery_strategies:
                    try:
                        if strategy.startswith("//"):
                            # XPath strategy
                            elements = self.driver.find_elements(AppiumBy.XPATH, strategy)
                        else:
                            # Class name strategy
                            elements = self.driver.find_elements(AppiumBy.CLASS_NAME, strategy)
                        
                        print(f"   📱 {description}: Found {len(elements)} elements")
                        
                        # Use the strategy that finds the most elements
                        if len(elements) > len(all_text_elements):
                            all_text_elements = elements
                            print(f"   ✅ Using {description} (most elements found)")
                        
                    except Exception as e:
                        print(f"   ⚠️ {description} failed: {e}")
                        continue
                
                print(f"🔍 Final element count: {len(all_text_elements)} elements")
                
                # Process the elements to extract text and location info
                processed_elements = []
                for elem in all_text_elements:
                    try:
                        text = elem.text.strip() if elem.text else ""
                        if text and len(text) > 0:
                            location = elem.location
                            processed_elements.append({
                                'element': elem,
                                'text': text,
                                'x': location['x'],
                                'y': location['y'],
                                'size': elem.size
                            })
                    except:
                        continue
                
                all_text_elements = processed_elements
                print(f"📝 Extracted {len(all_text_elements)} valid text elements")
                
            except Exception as e:
                print(f"❌ Error finding text elements: {e}")
                return products
            
            if not all_text_elements:
                print("❌ No text elements found")
                return []
            
            # Find potential price elements with ENHANCED debugging
            potential_price_elements = []
            print(f"🔍 Analyzing {len(all_text_elements)} elements for price patterns...")
            
            for i, elem_info in enumerate(all_text_elements):
                text = elem_info['text']
                print(f"   📝 Element {i+1}: '{text}'")
                
                if self._looks_like_price(text):
                    potential_price_elements.append(elem_info)
                    print(f"   💰 PRICE DETECTED: '{text}'")
                else:
                    print(f"   ❌ Not a price: '{text}'")
            
            price_elements = potential_price_elements
            
            print(f"💰 Found {len(price_elements)} potential price elements")
            
            if not price_elements:
                print("❌ No potential price elements found")
                
                # Take screenshot for debugging when no products found
                try:
                    import tempfile
                    import datetime
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    screenshot_file = f"{tempfile.gettempdir()}/lider_no_products_{timestamp}.png"
                    self.driver.save_screenshot(screenshot_file)
                    print(f"📸 Screenshot saved for debugging: {screenshot_file}")
                except Exception as screenshot_error:
                    print(f"⚠️ Could not save screenshot: {screenshot_error}")
                
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
                    
                    # Extract product information from this group with the SPECIFIC price element
                    product_info = self._extract_product_from_group_corrected(related_elements, "Lider", price_elem)
                    
                    if product_info:
                        products.append(product_info)
                        print(f"   ✅ Extracted: {product_info['name']} - ${product_info['price']}")
                    else:
                        print(f"   ❌ Could not extract product from group")
                        
                except Exception as e:
                    print(f"❌ Error processing price element {i+1}: {e}")
                    continue
            
            print(f"✅ Successfully extracted {len(products)} products from Lider using corrected method")
            
        except Exception as e:
            print(f"❌ Error in corrected Lider product extraction: {e}")
        
        return products
    
    def _looks_like_price(self, text: str) -> bool:
        """Check if text looks like a price - BROADENED patterns for better detection"""
        if not text:
            return False
        
        text_clean = text.strip()
        
        # BROADENED price patterns to catch more price formats
        price_patterns = [
            # Traditional patterns
            r'\$\d+',  # $123
            r'\d+\.\d+',  # 1.990 (Chilean format)
            r'\d+,\d+',  # 1,990
            r'\d+\s*x\s*\$\d+',  # 2 x $1000 (promotion format)
            r'\d+\s*pesos',  # 1000 pesos
            
            # BROADENED patterns for mobile apps
            r'\$\s*\d+',  # $ 123 (with space)
            r'\d+\s*\$',  # 123$ or 123 $
            r'^\d{3,}$',  # Any number with 3+ digits (likely price)
            r'\d+\s*CLP',  # Chilean pesos format
            r'\d+\s*clp',  # lowercase Chilean pesos
            r'precio.*\d+',  # "precio 1990" or similar
            r'\d+\s*por\s*\$',  # "2 por $1000"
            r'ahorra.*\$\d+',  # "Ahorra $500"
            r'antes.*\$\d+',  # "Antes $2000"
            r'ahora.*\$\d+',  # "Ahora $1500"
            r'\d+\s*c/u',  # "1500 c/u" (cada uno)
            r'\$\d+\s*c/u',  # "$1500 c/u"
            r'lleva.*\$\d+',  # "Lleva 2 por $3000"
            r'\d+\s*pack',  # "1500 pack"
            r'oferta.*\d+',  # "Oferta 1990"
            r'promo.*\d+',  # "Promo 1500"
            
            # Very broad patterns (any text with currency symbols near numbers)
            r'.*\$.*\d+.*',  # Any text with $ and numbers
            r'.*\d+.*\$.*',  # Any text with numbers and $
        ]
        
        for pattern in price_patterns:
            if re.search(pattern, text_clean, re.IGNORECASE):
                print(f"   💰 Price pattern matched: '{text_clean}' with pattern: {pattern}")
                return True
        
        # Additional check: if text contains only digits and is reasonable price range
        if re.match(r'^\d{3,6}$', text_clean):  # 3-6 digits (reasonable Chilean price range)
            price_value = int(text_clean)
            if 100 <= price_value <= 999999:  # Reasonable price range
                print(f"   💰 Numeric price detected: '{text_clean}' ({price_value})")
                return True
        
        return False
    
    def _extract_product_from_group_corrected(self, related_elements: List[Dict], store_name: str, target_price_elem: Dict = None) -> Dict:
        """Extract product information from a group of related elements using corrected logic"""
        try:
            if not related_elements:
                return None
            
            # Separate elements into categories
            price_candidates = []
            name_candidates = []
            size_candidates = []
            
            for elem_info in related_elements:
                text = elem_info['text']
                
                # Identify price elements
                if "$" in text or self._looks_like_price(text):
                    price_candidates.append(text)
                
                # Identify potential product names (longer text, contains keywords)
                elif self._looks_like_product_name(text):
                    name_candidates.append(text)
                
                # Identify size indicators
                elif self._looks_like_size(text):
                    size_candidates.append(text)
            
            print(f"   📊 Categories - Prices: {len(price_candidates)}, Names: {len(name_candidates)}, Sizes: {len(size_candidates)}")
            
            # Extract the SPECIFIC price if target_price_elem is provided, otherwise use first valid price
            price_value = 0.0
            price_text = ""
            promotion_info = {}
            
            # If we have a target price element, use that specific price
            if target_price_elem and target_price_elem['text']:
                target_price_text = target_price_elem['text']
                print(f"     🔍 Parsing price: '{target_price_text}'")
                parsed_result = self._parse_chilean_price_corrected(target_price_text)
                if parsed_result['price'] > 0:
                    price_value = parsed_result['price']
                    price_text = target_price_text
                    promotion_info = parsed_result['promotion']
                    if promotion_info and promotion_info.get('is_promo', False):
                        print(f"     💰 Promotion: {promotion_info['quantity']} x ${promotion_info['unit_price']:.0f} = ${promotion_info['total_price']:.0f}")
                    else:
                        print(f"     💰 Regular price: ${price_value}")
            
            # Fallback: use first valid price from candidates if target price parsing failed
            if price_value == 0.0:
                for price_candidate in price_candidates:
                    parsed_result = self._parse_chilean_price_corrected(price_candidate)
                    if parsed_result['price'] > 0:
                        price_value = parsed_result['price']
                        price_text = price_candidate
                        promotion_info = parsed_result['promotion']
                        print(f"     🔍 Fallback parsing price: '{price_candidate}'")
                        break
            
            # Extract the best product name
            product_name = self._extract_product_name_and_size_corrected(name_candidates, size_candidates)
            
            if price_value > 0 and product_name and product_name != "Unknown Product":
                product_info = {
                    'name': product_name,
                    'price': price_value,
                    'price_text': price_text,
                    'store': store_name,
                    'url': '',
                    'promotion': promotion_info
                }
                
                # Calculate price per unit if size information is available
                if size_candidates:
                    unit_info = self._calculate_price_per_unit(price_value, size_candidates, promotion_info)
                    if unit_info:
                        product_info.update(unit_info)
                
                return product_info
            
            return None
            
        except Exception as e:
            print(f"   ❌ Error extracting from group: {e}")
            return None
    
    def _looks_like_product_name(self, text: str) -> bool:
        """Check if text looks like a product name"""
        if not text or len(text.strip()) < 3:
            return False
        
        # Filter out generic texts
        generic_texts = [
            'ver más', 'ver todo', 'agregar', 'comprar', 'añadir', 'detalle',
            'disponible', 'stock', 'envío', 'delivery', 'gratis', 'precio',
            'oferta', 'descuento', 'promoción', 'unidad', 'kg', 'gr', 'ml', 'lt'
        ]
        
        text_lower = text.lower().strip()
        
        # Skip if it's a generic text
        for generic in generic_texts:
            if generic in text_lower:
                return False
        
        # Look for product keywords (prioritize food/beverage terms)
        product_keywords = [
            'coca', 'pepsi', 'bebida', 'agua', 'jugo', 'leche', 'yogurt',
            'pan', 'arroz', 'fideos', 'pasta', 'aceite', 'azúcar', 'sal',
            'detergente', 'jabón', 'shampoo', 'crema', 'galletas', 'chocolate'
        ]
        
        # Higher priority if contains product keywords - this overrides generic text filtering
        for keyword in product_keywords:
            if keyword in text_lower:
                return True
        
        # General criteria: reasonable length and not pure numbers
        if 5 <= len(text) <= 100 and not text.isdigit():
            return True
        
        return False
    
    def _looks_like_size(self, text: str) -> bool:
        """Check if text contains size/volume information"""
        if not text:
            return False
        
        size_patterns = [
            r'\d+\s*ml', r'\d+\s*ML',
            r'\d+\s*l', r'\d+\s*L', r'\d+\s*lt', r'\d+\s*LT',
            r'\d+\s*gr', r'\d+\s*GR', r'\d+\s*g', r'\d+\s*G',
            r'\d+\s*kg', r'\d+\s*KG',
            r'\d+\s*cc', r'\d+\s*CC',
            r'\d+\s*oz', r'\d+\s*OZ'
        ]
        
        for pattern in size_patterns:
            if re.search(pattern, text):
                return True
        
        return False
    
    def _parse_chilean_price_corrected(self, price_text: str) -> Dict:
        """Parse Chilean price format with corrected promotion handling"""
        result = {
            'price': 0.0,
            'promotion': {
                'is_promo': False,
                'quantity': 1,
                'total_price': 0.0,
                'unit_price': 0.0
            }
        }
        
        try:
            if not price_text:
                return result
            
            print(f"     🔍 Parsing price: '{price_text}'")
            
            # Check for promotion patterns like "2 x $4.000"
            promo_pattern = r'(\d+)\s*x\s*\$\s*([0-9.,]+)'
            promo_match = re.search(promo_pattern, price_text, re.IGNORECASE)
            
            if promo_match:
                quantity = int(promo_match.group(1))
                price_part = promo_match.group(2)
                
                # Parse the price part (Chilean format: periods as thousand separators)
                clean_price = price_part.replace('.', '').replace(',', '.')
                total_price = float(clean_price)
                
                # CORRECTED: For "2 x $4.000", this means $4.000 total for 2 items, not $8.000
                unit_price = total_price / quantity
                
                result['price'] = total_price  # Return total price
                result['promotion'] = {
                    'is_promo': True,
                    'quantity': quantity,
                    'total_price': total_price,
                    'unit_price': unit_price
                }
                
                print(f"     💥 Promotion detected: {quantity} items for ${total_price} (${unit_price:.0f} each)")
                return result
            
            # Regular price parsing
            clean_price = price_text.replace('$', '').replace(' ', '').replace('\n', '')
            
            # Handle Chilean thousand separators (periods)
            if '.' in clean_price and ',' not in clean_price:
                # Chilean format: $1.990 = 1990 pesos
                clean_price = clean_price.replace('.', '')
            elif ',' in clean_price:
                # Handle comma as decimal separator
                clean_price = clean_price.replace('.', '').replace(',', '.')
            
            # Extract numeric value
            price_match = re.search(r'[\d.]+', clean_price)
            if price_match:
                price_value = float(price_match.group())
                result['price'] = price_value
                result['promotion']['total_price'] = price_value
                result['promotion']['unit_price'] = price_value
                
                print(f"     💰 Regular price: ${price_value}")
                return result
            
            return result
            
        except Exception as e:
            print(f"     ❌ Error parsing price '{price_text}': {e}")
            return result
    
    def _extract_product_name_and_size_corrected(self, name_candidates: List[str], size_candidates: List[str]) -> str:
        """Extract the best product name with improved logic"""
        try:
            if not name_candidates:
                return "Unknown Product"
            
            # Filter and rank name candidates
            scored_names = []
            
            for name in name_candidates:
                score = 0
                name_lower = name.lower().strip()
                
                # Bonus for product keywords
                product_keywords = [
                    'coca', 'pepsi', 'sprite', 'fanta', 'bebida', 'agua', 'jugo', 
                    'leche', 'yogurt', 'pan', 'arroz', 'fideos', 'pasta', 'aceite',
                    'azúcar', 'sal', 'detergente', 'jabón', 'shampoo', 'crema',
                    'galletas', 'chocolate', 'cerveza', 'vino'
                ]
                
                for keyword in product_keywords:
                    if keyword in name_lower:
                        score += 10
                        break
                
                # Bonus for reasonable length
                if 5 <= len(name) <= 50:
                    score += 5
                elif len(name) > 50:
                    score -= 2  # Penalize very long names
                
                # Bonus for containing size information
                if any(size_word in name_lower for size_word in ['ml', 'l', 'gr', 'kg', 'cc']):
                    score += 3
                
                # Penalty for generic words
                generic_penalty_words = ['precio', 'oferta', 'descuento', 'stock', 'disponible']
                for penalty_word in generic_penalty_words:
                    if penalty_word in name_lower:
                        score -= 5
                
                scored_names.append((name, score))
            
            # Sort by score and return the best name
            scored_names.sort(key=lambda x: x[1], reverse=True)
            best_name = scored_names[0][0]
            
            print(f"     📝 Selected name: '{best_name}' (score: {scored_names[0][1]})")
            
            # Append size information if available and not already in name
            if size_candidates:
                name_lower = best_name.lower()
                for size in size_candidates:
                    if not any(unit in name_lower for unit in ['ml', 'l', 'gr', 'kg', 'cc']) and \
                       any(unit in size.lower() for unit in ['ml', 'l', 'gr', 'kg', 'cc']):
                        best_name = f"{best_name} {size}"
                        break
            
            return best_name
            
        except Exception as e:
            print(f"     ❌ Error extracting product name: {e}")
            return "Unknown Product"
    
    def _calculate_price_per_unit(self, price: float, size_candidates: List[str], promotion_info: Dict) -> Dict:
        """Calculate price per liter/kg with corrected logic for promotions"""
        try:
            # Extract volume/weight from size candidates
            volume_ml = 0
            weight_gr = 0
            
            for size in size_candidates:
                # Extract ML/L
                ml_match = re.search(r'(\d+)\s*ml', size, re.IGNORECASE)
                l_match = re.search(r'(\d+)\s*l[^a-zA-Z]|(\d+)\s*l$', size, re.IGNORECASE)
                
                if ml_match:
                    volume_ml = int(ml_match.group(1))
                elif l_match:
                    volume_ml = int(l_match.group(1) or l_match.group(2)) * 1000
                
                # Extract GR/KG
                gr_match = re.search(r'(\d+)\s*gr', size, re.IGNORECASE)
                kg_match = re.search(r'(\d+)\s*kg', size, re.IGNORECASE)
                
                if gr_match:
                    weight_gr = int(gr_match.group(1))
                elif kg_match:
                    weight_gr = int(kg_match.group(1)) * 1000
                
                if volume_ml > 0 or weight_gr > 0:
                    break
            
            result = {}
            
            # Calculate price per liter (especially important for beverages)
            if volume_ml > 0:
                # Use unit price for promotions, total price for regular items
                effective_price = promotion_info.get('unit_price', price) if promotion_info.get('is_promo') else price
                price_per_liter = (effective_price / volume_ml) * 1000
                
                result['volume_ml'] = volume_ml
                result['price_per_liter'] = round(price_per_liter, 2)
                
                print(f"     📏 Volume: {volume_ml}ml, Price per liter: ${price_per_liter:.2f}")
            
            # Calculate price per kg
            if weight_gr > 0:
                effective_price = promotion_info.get('unit_price', price) if promotion_info.get('is_promo') else price
                price_per_kg = (effective_price / weight_gr) * 1000
                
                result['weight_gr'] = weight_gr
                result['price_per_kg'] = round(price_per_kg, 2)
                
                print(f"     ⚖️ Weight: {weight_gr}gr, Price per kg: ${price_per_kg:.2f}")
            
            return result if result else None
            
        except Exception as e:
            print(f"     ❌ Error calculating price per unit: {e}")
            return None
    
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
        """Save current page source for debugging with Windows compatibility"""
        try:
            if not self.driver:
                print("❌ No driver connected")
                return False
            
            if not filename:
                import datetime
                import tempfile
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                temp_dir = tempfile.gettempdir()
                filename = f"{temp_dir}/page_source_{timestamp}.xml"
            
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