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
        """Initialize Appium driver for Android automation"""
        try:
            options = UiAutomator2Options()
            options.platform_name = "Android"
            options.device_name = "grocery_automation"
            options.automation_name = "UiAutomator2"
            options.no_reset = True
            options.full_reset = False

            # Additional capabilities for stability
            options.new_command_timeout = 300  # 5 minutes
            options.implicit_wait = 10

            print(f"Connecting to Appium server at http://localhost:{self.appium_port}")
            self.driver = webdriver.Remote(f'http://localhost:{self.appium_port}', options=options)
            self.wait = WebDriverWait(self.driver, 15)

            print("✅ Appium driver initialized successfully")

            # NOW manually launch the app
            if app_package:
                try:
                    print(f"🚀 Launching app: {app_package}")
                    self.driver.activate_app(app_package)
                    time.sleep(5)  # Give more time for app to fully load

                    # Verify app launched
                    current_package = self.driver.current_package
                    print(f"📱 Current app after launch: {current_package}")

                    if current_package == app_package:
                        print("✅ App launched successfully!")
                    else:
                        print(f"⚠️ App may not have launched properly. Expected: {app_package}, Got: {current_package}")

                except Exception as e:
                    print(f"❌ Error launching app: {e}")
                    print("🔄 Trying alternative launch method...")
                    try:
                        # Alternative: Use start_activity
                        if "jumbo" in app_package.lower():
                            self.driver.start_activity(app_package, "com.cencosud.cl.jumboahora.MainActivity")
                        elif "lider" in app_package.lower():
                            self.driver.start_activity(app_package, "cl.walmart.liderapp.MainActivity")
                        time.sleep(5)
                        print("✅ Alternative launch attempted")
                    except Exception as e2:
                        print(f"❌ Alternative launch also failed: {e2}")

            return True

        except Exception as e:
            print(f"❌ Error setting up Appium driver: {e}")
            return False

    def debug_current_state(self):
        """Debug what's currently on screen"""
        try:
            current_package = self.driver.current_package
            current_activity = self.driver.current_activity
            print(f"📱 Current package: {current_package}")
            print(f"📱 Current activity: {current_activity}")

            # List some visible elements
            elements = self.driver.find_elements(AppiumBy.XPATH, "//*[@clickable='true']")
            print(f"📱 Found {len(elements)} clickable elements")

            # Show text of first few elements
            for i, elem in enumerate(elements[:5]):
                try:
                    text = elem.text
                    if text:
                        print(f"  Element {i+1}: '{text}'")
                except:
                    pass

        except Exception as e:
            print(f"❌ Debug error: {e}")

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
            if not self.setup_driver("com.cencosud.cl.jumboahora"):
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
            if not self.setup_driver("cl.walmart.liderapp"):
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

        # DEBUG: See what's actually on screen
        self.debug_current_state()

        # Handle potential welcome screens, permissions, etc.
        await self._handle_app_permissions()
        await self._handle_jumbo_login_if_needed()

        print("✅ Jumbo app setup complete")

    async def _launch_and_setup_lider(self):
        """Launch Lider app and handle initial setup"""
        print("📱 Launching Lider app...")

        # Give app time to launch
        time.sleep(5)

        # DEBUG: See what's actually on screen
        self.debug_current_state()

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
        """Perform search in Jumbo app"""
        try:
            print(f"🔍 Searching for '{product_name}' in Jumbo app")

            # Wait longer for the page to settle
            time.sleep(3)

            # Enhanced search element selectors - try more specific ones first
            search_selectors = [
                "//android.widget.EditText[contains(@hint,'Buscar') or contains(@hint,'Search')]",
                "//android.widget.EditText[contains(@text,'Buscar') or contains(@text,'Search')]",
                "//*[contains(@resource-id,'search_edit') or contains(@resource-id,'searchEdit')]",
                "//*[contains(@resource-id,'et_search') or contains(@resource-id,'etSearch')]",
                "//*[contains(@content-desc,'Buscar') or contains(@content-desc,'Search')]",
                "//android.widget.EditText[@clickable='true']",
                "//*[@class='android.widget.EditText']"
            ]

            # Find the best search element
            successful_selector = None
            search_element = None
            for i, selector in enumerate(search_selectors):
                try:
                    elements = self.driver.find_elements(AppiumBy.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            # Check if it's likely a search field
                            hint = element.get_attribute("hint") or ""
                            text = element.get_attribute("text") or ""
                            content_desc = element.get_attribute("content-desc") or ""

                            if any(keyword in (hint + text + content_desc).lower()
                                for keyword in ['buscar', 'search', 'producto']):
                                successful_selector = selector
                                search_element = element
                                print(f"✅ Found optimal Jumbo search element (#{i}): {selector}")
                                print(f"   Hint: '{hint}', Text: '{text}', Desc: '{content_desc}'")
                                break
                            else:
                                # If no keyword match, still consider if it's the only EditText
                                if not successful_selector and "EditText" in selector:
                                    successful_selector = selector
                                    search_element = element
                                    print(f"⚠️ Using fallback Jumbo search element (#{i}): {selector}")

                    if successful_selector:
                        break
                except:
                    continue

            if not search_element:
                print("❌ Could not find search element in Jumbo app")
                return False

            # Perform search with multiple strategies
            max_retries = 2
            for attempt in range(max_retries):
                try:
                    print(f"🔄 Jumbo search attempt {attempt + 1}/{max_retries}")

                    # Re-find element to avoid stale references
                    search_element = self.driver.find_element(AppiumBy.XPATH, successful_selector)

                    # Strategy 1: Click and use send_keys
                    search_element.click()
                    time.sleep(2)
                    print("✅ Search element clicked")

                    # Clear field (try multiple methods)
                    try:
                        search_element.clear()
                        print("✅ Field cleared with clear()")
                    except:
                        try:
                            # Alternative: Select all and delete
                            search_element.send_keys("\ue009\ue003")  # Ctrl+A, Delete
                            print("✅ Field cleared with select-all-delete")
                        except:
                            print("⚠️ Could not clear field, proceeding anyway")

                    time.sleep(1)

                    # Input text
                    search_element.send_keys(product_name)
                    time.sleep(2)
                    print(f"✅ Text '{product_name}' entered")

                    # Submit search - try multiple methods
                    submitted = False

                    # Method 1: Enter key
                    try:
                        self.driver.press_keycode(66)  # Android Enter
                        time.sleep(1)
                        print("✅ Enter key pressed")
                        submitted = True
                    except:
                        pass

                    # Method 2: Search button
                    if not submitted:
                        search_btn_selectors = [
                            "//*[contains(@resource-id,'search_button') or contains(@resource-id,'btn_search')]",
                            "//*[contains(@content-desc,'Buscar') or contains(@content-desc,'Search')]",
                            "//*[contains(@text,'Buscar') or contains(@text,'Search')]",
                            "//android.widget.Button[contains(@text,'Buscar')]",
                            "//android.widget.ImageButton[@clickable='true']"
                        ]

                        for btn_selector in search_btn_selectors:
                            try:
                                search_btn = self.driver.find_element(AppiumBy.XPATH, btn_selector)
                                if search_btn.is_displayed():
                                    search_btn.click()
                                    print(f"✅ Search button clicked: {btn_selector}")
                                    submitted = True
                                    break
                            except:
                                continue

                    # Method 3: Tap search area or submit via keyboard
                    if not submitted:
                        try:
                            # Send Enter via keyboard
                            search_element.send_keys("\ue007")  # Enter key code
                            print("✅ Enter sent via send_keys")
                            submitted = True
                        except:
                            pass

                    if submitted:
                        # Wait longer for results to load
                        time.sleep(8)
                        print("✅ Jumbo search submitted successfully")
                        return True
                    else:
                        print("⚠️ Could not submit search, trying again...")

                except Exception as e:
                    print(f"⚠️ Jumbo search attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(3)

            print("❌ All Jumbo search attempts failed")
            return False

        except Exception as e:
            print(f"❌ Jumbo search error: {e}")
            return False

    async def _perform_lider_search(self, product_name: str) -> bool:
        """Perform search in Lider app"""
        try:
            print(f"🔍 Searching for '{product_name}' in Lider app")

            # Wait for page to settle
            time.sleep(3)

            # Enhanced Lider search selectors
            search_selectors = [
                "//android.widget.EditText[contains(@hint,'Buscar') or contains(@hint,'Search')]",
                "//android.widget.EditText[contains(@text,'Buscar') or contains(@text,'Search')]",
                "//*[contains(@resource-id,'search_edit') or contains(@resource-id,'searchEdit')]",
                "//*[contains(@resource-id,'et_search') or contains(@resource-id,'etSearch')]",
                "//*[contains(@resource-id,'search_bar') or contains(@resource-id,'searchBar')]",
                "//android.widget.AutoCompleteTextView[@clickable='true']",
                "//android.widget.EditText[@clickable='true' and @enabled='true']",
                "//*[contains(@content-desc,'Buscar') or contains(@content-desc,'Search')]"
            ]

            # Find the best search element for Lider
            successful_selector = None
            search_element = None
            for i, selector in enumerate(search_selectors):
                try:
                    elements = self.driver.find_elements(AppiumBy.XPATH, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            # Check element attributes
                            hint = element.get_attribute("hint") or ""
                            text = element.get_attribute("text") or ""
                            content_desc = element.get_attribute("content-desc") or ""
                            class_name = element.get_attribute("class") or ""

                            print(f"🔍 Checking element {i}: class='{class_name}', hint='{hint}', text='{text}', desc='{content_desc}'")

                            # Prioritize elements with search-related attributes
                            if any(keyword in (hint + text + content_desc).lower()
                                   for keyword in ['buscar', 'search', 'producto', 'buscador']):
                                successful_selector = selector
                                search_element = element
                                print(f"✅ Found optimal Lider search element (#{i}): {selector}")
                                break
                            elif "EditText" in class_name or "AutoCompleteTextView" in class_name:
                                if not successful_selector:  # Use as fallback
                                    successful_selector = selector
                                    search_element = element
                                    print(f"⚠️ Using fallback Lider search element (#{i}): {selector}")

                    if successful_selector:
                        break
                except Exception as e:
                    print(f"⚠️ Error checking selector {i}: {e}")
                    continue

            if not search_element:
                print("❌ Could not find search element in Lider app")
                return False

            # Perform search with enhanced error handling
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    print(f"🔄 Lider search attempt {attempt + 1}/{max_retries}")

                    # Re-find element
                    search_element = self.driver.find_element(AppiumBy.XPATH, successful_selector)

                    # Multi-step interaction
                    print("📱 Clicking search element...")
                    search_element.click()
                    time.sleep(2)

                    print("📱 Attempting to focus element...")
                    # Try to focus the element properly
                    try:
                        # Tap the element coordinates directly
                        location = search_element.location
                        size = search_element.size
                        x = location['x'] + size['width'] // 2
                        y = location['y'] + size['height'] // 2
                        self.driver.tap([(x, y)])
                        time.sleep(1)
                        print("✅ Element tapped at coordinates")
                    except:
                        pass

                    # Clear field
                    print("📱 Clearing field...")
                    try:
                        search_element.clear()
                        print("✅ Field cleared")
                    except:
                        print("⚠️ Could not clear field")

                    time.sleep(1)

                    # Try different text input methods
                    input_success = False

                    # Method 1: Direct send_keys
                    try:
                        search_element.send_keys(product_name)
                        print(f"✅ Method 1: Text '{product_name}' entered with send_keys")
                        input_success = True
                    except Exception as e1:
                        print(f"⚠️ Method 1 failed: {e1}")

                        # Method 2: Use driver.set_value (if available)
                        try:
                            search_element.set_value(product_name)
                            print(f"✅ Method 2: Text '{product_name}' entered with set_value")
                            input_success = True
                        except Exception as e2:
                            print(f"⚠️ Method 2 failed: {e2}")

                            # Method 3: Type character by character
                            try:
                                for char in product_name:
                                    search_element.send_keys(char)
                                    time.sleep(0.1)
                                print(f"✅ Method 3: Text '{product_name}' entered character by character")
                                input_success = True
                            except Exception as e3:
                                print(f"⚠️ Method 3 failed: {e3}")

                    if not input_success:
                        print("❌ Could not input text, trying next attempt...")
                        time.sleep(2)
                        continue

                    time.sleep(2)

                    # Submit search
                    self.driver.press_keycode(66)  # Enter key
                    time.sleep(8)  # Wait longer for results

                    print("✅ Lider search submitted successfully")
                    return True

                except Exception as e:
                    print(f"⚠️ Lider search attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(3)

            print("❌ All Lider search attempts failed")
            return False

        except Exception as e:
            print(f"❌ Lider search error: {e}")
            return False

    async def _extract_jumbo_products(self) -> List[Dict]:
        """Extract product information from Jumbo search results"""
        products = []

        try:
            print("📦 Extracting Jumbo products...")

            # Wait for results to load
            time.sleep(3)

            # Try different product container selectors
            product_selectors = [
                "//*[contains(@resource-id,'product') or contains(@resource-id,'item')]",
                "//*[contains(@class,'product') or contains(@class,'item')]",
                "//android.widget.LinearLayout[.//android.widget.TextView[contains(@text,'$')]]",
                "//android.widget.RelativeLayout[.//android.widget.TextView[contains(@text,'$')]]",
                "//android.view.ViewGroup[.//android.widget.TextView[contains(@text,'$')]]",
                "//*[@clickable='true'][.//android.widget.TextView[contains(@text,'$')]]"
            ]

            product_elements = []
            for selector in product_selectors:
                try:
                    elements = self.driver.find_elements(AppiumBy.XPATH, selector)
                    if elements:
                        product_elements = elements[:10]  # Limit to first 10
                        print(f"✅ Found {len(product_elements)} potential products with selector: {selector}")
                        break
                except:
                    continue

            if not product_elements:
                print("❌ No product elements found, trying to find any text with prices...")
                # Fallback: find any elements containing price-like text
                try:
                    price_elements = self.driver.find_elements(AppiumBy.XPATH, "//*[contains(@text,'$')]")
                    print(f"🔍 Found {len(price_elements)} elements with '$' symbol")

                    # Create mock products from price elements for testing
                    for i, elem in enumerate(price_elements[:5]):
                        try:
                            price_text = elem.text
                            price = self._parse_chilean_price(price_text)
                            if price > 0:
                                products.append({
                                    'name': f'Product {i+1}',
                                    'price': price,
                                    'price_text': price_text,
                                    'store': 'Jumbo',
                                    'url': ''
                                })
                                print(f"✅ Added product: Product {i+1} - {price_text}")
                        except:
                            continue
                except:
                    pass
            else:
                # Process found product elements
                for i, element in enumerate(product_elements):
                    try:
                        print(f"📦 Processing product {i+1}...")

                        # Try to find product name
                        name = "Unknown Product"
                        try:
                            name_elements = element.find_elements(AppiumBy.XPATH, ".//android.widget.TextView")
                            for name_elem in name_elements:
                                text = name_elem.text
                                if text and len(text) > 3 and '$' not in text:
                                    name = text
                                    break
                        except:
                            pass

                        # Try to find price
                        price_text = "$0"
                        price = 0
                        try:
                            price_elements = element.find_elements(AppiumBy.XPATH, ".//android.widget.TextView[contains(@text,'$')]")
                            for price_elem in price_elements:
                                text = price_elem.text
                                if '$' in text:
                                    price_text = text
                                    price = self._parse_chilean_price(text)
                                    break
                        except:
                            pass

                        if price > 0:
                            products.append({
                                'name': name,
                                'price': price,
                                'price_text': price_text,
                                'store': 'Jumbo',
                                'url': ''
                            })
                            print(f"✅ Product added: {name} - {price_text}")

                    except Exception as e:
                        print(f"⚠️ Error processing product {i+1}: {e}")
                        continue

            print(f"✅ Extracted {len(products)} products from Jumbo")
            return products

        except Exception as e:
            print(f"❌ Error extracting Jumbo products: {e}")
            return products

    async def _extract_lider_products(self) -> List[Dict]:
        """Extract product information from Lider search results"""
        products = []

        try:
            print("📦 Extracting Lider products...")

            # Wait for results to load
            time.sleep(3)

            # Similar logic to Jumbo extraction
            product_selectors = [
                "//*[contains(@resource-id,'product') or contains(@resource-id,'item')]",
                "//*[contains(@class,'product') or contains(@class,'item')]",
                "//android.widget.LinearLayout[.//android.widget.TextView[contains(@text,'$')]]",
                "//android.widget.RelativeLayout[.//android.widget.TextView[contains(@text,'$')]]",
                "//android.view.ViewGroup[.//android.widget.TextView[contains(@text,'$')]]"
            ]

            product_elements = []
            for selector in product_selectors:
                try:
                    elements = self.driver.find_elements(AppiumBy.XPATH, selector)
                    if elements:
                        product_elements = elements[:10]  # Limit to first 10
                        print(f"✅ Found {len(product_elements)} potential products with selector: {selector}")
                        break
                except:
                    continue

            if not product_elements:
                print("❌ No product elements found in Lider")
                # Fallback similar to Jumbo
                try:
                    price_elements = self.driver.find_elements(AppiumBy.XPATH, "//*[contains(@text,'$')]")
                    print(f"🔍 Found {len(price_elements)} elements with '$' symbol in Lider")

                    for i, elem in enumerate(price_elements[:5]):
                        try:
                            price_text = elem.text
                            price = self._parse_chilean_price(price_text)
                            if price > 0:
                                products.append({
                                    'name': f'Lider Product {i+1}',
                                    'price': price,
                                    'price_text': price_text,
                                    'store': 'Lider',
                                    'url': ''
                                })
                                print(f"✅ Added Lider product: Lider Product {i+1} - {price_text}")
                        except:
                            continue
                except:
                    pass
            else:
                # Process found product elements
                for i, element in enumerate(product_elements):
                    try:
                        print(f"📦 Processing Lider product {i+1}...")

                        # Extract product name
                        name = "Unknown Lider Product"
                        try:
                            name_elements = element.find_elements(AppiumBy.XPATH, ".//android.widget.TextView")
                            for name_elem in name_elements:
                                text = name_elem.text
                                if text and len(text) > 3 and '$' not in text:
                                    name = text
                                    break
                        except:
                            pass

                        # Extract price
                        price_text = "$0"
                        price = 0
                        try:
                            price_elements = element.find_elements(AppiumBy.XPATH, ".//android.widget.TextView[contains(@text,'$')]")
                            for price_elem in price_elements:
                                text = price_elem.text
                                if '$' in text:
                                    price_text = text
                                    price = self._parse_chilean_price(text)
                                    break
                        except:
                            pass

                        if price > 0:
                            products.append({
                                'name': name,
                                'price': price,
                                'price_text': price_text,
                                'store': 'Lider',
                                'url': ''
                            })
                            print(f"✅ Lider product added: {name} - {price_text}")

                    except Exception as e:
                        print(f"⚠️ Error processing Lider product {i+1}: {e}")
                        continue

            print(f"✅ Extracted {len(products)} products from Lider")
            return products

        except Exception as e:
            print(f"❌ Error extracting Lider products: {e}")
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