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
        """Perform search in Jumbo app"""
        try:
            print(f"🔍 Searching for '{product_name}' in Jumbo app")
            
            # Common search element selectors
            search_selectors = [
                "//*[contains(@resource-id,'search')]",
                "//*[contains(@class,'search')]",
                "//*[contains(@content-desc,'search')]",
                "//*[contains(@content-desc,'Buscar')]",
                "//android.widget.EditText[contains(@text,'Buscar')]",
                "//android.widget.EditText[contains(@hint,'Buscar')]",
                "//*[@class='android.widget.EditText']",
                "//*[contains(@text,'Buscar')]"
            ]
            
            search_element = None
            successful_selector = None
            for selector in search_selectors:
                try:
                    search_element = self.wait.until(
                        EC.presence_of_element_located((AppiumBy.XPATH, selector))
                    )
                    if search_element.is_displayed():
                        successful_selector = selector
                        print(f"✅ Found Jumbo search element with selector: {selector}")
                        break
                except:
                    continue
            
            if not search_element:
                print("❌ Could not find search element in Jumbo app")
                return False
            
            # Prepare the element for text input
            try:
                # First, click on the search element to focus it
                search_element.click()
                time.sleep(1)
                print("✅ Search element clicked and focused")
                
                # Clear any existing text
                search_element.clear()
                time.sleep(1)
                
                # Send the search text
                search_element.send_keys(product_name)
                time.sleep(2)
                print(f"✅ Text '{product_name}' entered successfully")
                
            except Exception as text_error:
                print(f"❌ Error entering text: {text_error}")
                return False
            
            # Submit search (try Enter key or search button)
            try:
                # Try pressing Enter first
                self.driver.press_keycode(66)  # Android Enter key
                time.sleep(3)
                print("✅ Search submitted with Enter key")
            except:
                # Try finding search button
                search_button_selectors = [
                    "//*[contains(@resource-id,'search_button')]",
                    "//*[contains(@content-desc,'search')]",
                    "//*[contains(@content-desc,'Buscar')]",
                    "//*[contains(@text,'Buscar')]"
                ]
                
                for selector in search_button_selectors:
                    try:
                        search_btn = self.driver.find_element(AppiumBy.XPATH, selector)
                        search_btn.click()
                        print(f"✅ Search submitted with button: {selector}")
                        break
                    except:
                        continue
            
            # Wait for results to load
            time.sleep(5)
            print("✅ Jumbo search executed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Jumbo search error: {e}")
            return False
    
    async def _perform_lider_search(self, product_name: str) -> bool:
        """Perform search in Lider app"""
        try:
            print(f"🔍 Searching for '{product_name}' in Lider app")
            
            # Similar logic to Jumbo but with Lider-specific selectors
            search_selectors = [
                "//*[contains(@resource-id,'search')]",
                "//*[contains(@class,'search')]", 
                "//*[contains(@content-desc,'search')]",
                "//*[contains(@content-desc,'Buscar')]",
                "//android.widget.EditText[contains(@text,'Buscar')]",
                "//android.widget.EditText[contains(@hint,'Buscar')]",
                "//*[@class='android.widget.EditText']",
                "//*[contains(@text,'Buscar')]"
            ]
            
            search_element = None
            successful_selector = None
            for selector in search_selectors:
                try:
                    search_element = self.wait.until(
                        EC.presence_of_element_located((AppiumBy.XPATH, selector))
                    )
                    if search_element.is_displayed():
                        successful_selector = selector
                        print(f"✅ Found Lider search element with selector: {selector}")
                        break
                except:
                    continue
            
            if not search_element:
                print("❌ Could not find search element in Lider app")
                return False
            
            # Prepare the element for text input
            try:
                # First, click on the search element to focus it
                search_element.click()
                time.sleep(1)
                print("✅ Search element clicked and focused")
                
                # Clear any existing text
                search_element.clear()
                time.sleep(1)
                
                # Send the search text
                search_element.send_keys(product_name)
                time.sleep(2)
                print(f"✅ Text '{product_name}' entered successfully")
                
            except Exception as text_error:
                print(f"❌ Error entering text: {text_error}")
                return False
            
            # Submit search
            try:
                self.driver.press_keycode(66)  # Android Enter key
                time.sleep(3)
                print("✅ Search submitted with Enter key")
            except:
                # Try search button
                search_button_selectors = [
                    "//*[contains(@resource-id,'search_button')]",
                    "//*[contains(@content-desc,'search')]",
                    "//*[contains(@content-desc,'Buscar')]",
                    "//*[contains(@text,'Buscar')]"
                ]
                
                for selector in search_button_selectors:
                    try:
                        search_btn = self.driver.find_element(AppiumBy.XPATH, selector)
                        search_btn.click()
                        print(f"✅ Search submitted with button: {selector}")
                        break
                    except:
                        continue
            
            time.sleep(5)
            print("✅ Lider search executed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Lider search error: {e}")
            return False
    
    async def _extract_jumbo_products(self) -> List[Dict]:
        """Extract product information from Jumbo search results"""
        products = []
        
        try:
            print("📦 Extracting Jumbo products...")
            
            # Common product container selectors
            product_selectors = [
                "//*[contains(@resource-id,'product')]",
                "//*[contains(@class,'product')]",
                "//*[contains(@resource-id,'item')]",
                "//*[contains(@class,'item')]"
            ]
            
            product_elements = []
            for selector in product_selectors:
                try:
                    elements = self.driver.find_elements(AppiumBy.XPATH, selector)
                    if elements:
                        product_elements = elements[:10]  # Limit to first 10
                        print(f"✅ Found {len(product_elements)} products with selector: {selector}")
                        break
                except:
                    continue
            
            if not product_elements:
                print("❌ No product elements found")
                return products
            
            for i, element in enumerate(product_elements):
                try:
                    print(f"📦 Processing product {i+1}...")
                    
                    # Extract product name
                    name = "Unknown"
                    name_selectors = [
                        ".//text()[contains(@resource-id,'name')]",
                        ".//text()[contains(@resource-id,'title')]",
                        ".//text()[contains(@class,'name')]",
                        ".//text()[contains(@class,'title')]"
                    ]
                    
                    for selector in name_selectors:
                        try:
                            name_element = element.find_element(AppiumBy.XPATH, selector)
                            name = name_element.text.strip()
                            if name:
                                break
                        except:
                            continue
                    
                    # Extract price
                    price_text = "$0"
                    price_selectors = [
                        ".//text()[contains(@resource-id,'price')]",
                        ".//text()[contains(@class,'price')]",
                        ".//text()[contains(@resource-id,'precio')]",
                        ".//text()[contains(text(),'$')]"
                    ]
                    
                    for selector in price_selectors:
                        try:
                            price_element = element.find_element(AppiumBy.XPATH, selector)
                            price_text = price_element.text.strip()
                            if '$' in price_text:
                                break
                        except:
                            continue
                    
                    # Parse numeric price
                    price = self._parse_chilean_price(price_text)
                    
                    if name != "Unknown" and price > 0:
                        products.append({
                            'name': name,
                            'price': price,
                            'price_text': price_text,
                            'store': 'Jumbo',
                            'url': ''  # Can be extracted if needed
                        })
                        print(f"✅ Product added: {name} - ${price}")
                    
                except Exception as e:
                    print(f"⚠️ Error processing product {i+1}: {e}")
                    continue
            
            print(f"✅ Extracted {len(products)} products from Jumbo")
            
        except Exception as e:
            print(f"❌ Error extracting Jumbo products: {e}")
        
        return products
    
    async def _extract_lider_products(self) -> List[Dict]:
        """Extract product information from Lider search results"""
        products = []
        
        try:
            print("📦 Extracting Lider products...")
            
            # Similar logic to Jumbo extraction
            product_selectors = [
                "//*[contains(@resource-id,'product')]",
                "//*[contains(@class,'product')]",
                "//*[contains(@resource-id,'item')]",
                "//*[contains(@class,'item')]"
            ]
            
            product_elements = []
            for selector in product_selectors:
                try:
                    elements = self.driver.find_elements(AppiumBy.XPATH, selector)
                    if elements:
                        product_elements = elements[:10]  # Limit to first 10
                        print(f"✅ Found {len(product_elements)} products with selector: {selector}")
                        break
                except:
                    continue
            
            if not product_elements:
                print("❌ No product elements found")
                return products
            
            for i, element in enumerate(product_elements):
                try:
                    print(f"📦 Processing product {i+1}...")
                    
                    # Extract product name
                    name = "Unknown"
                    name_selectors = [
                        ".//text()[contains(@resource-id,'name')]",
                        ".//text()[contains(@resource-id,'title')]", 
                        ".//text()[contains(@class,'name')]",
                        ".//text()[contains(@class,'title')]"
                    ]
                    
                    for selector in name_selectors:
                        try:
                            name_element = element.find_element(AppiumBy.XPATH, selector)
                            name = name_element.text.strip()
                            if name:
                                break
                        except:
                            continue
                    
                    # Extract price
                    price_text = "$0"
                    price_selectors = [
                        ".//text()[contains(@resource-id,'price')]",
                        ".//text()[contains(@class,'price')]",
                        ".//text()[contains(@resource-id,'precio')]",
                        ".//text()[contains(text(),'$')]"
                    ]
                    
                    for selector in price_selectors:
                        try:
                            price_element = element.find_element(AppiumBy.XPATH, selector)
                            price_text = price_element.text.strip()
                            if '$' in price_text:
                                break
                        except:
                            continue
                    
                    # Parse numeric price
                    price = self._parse_chilean_price(price_text)
                    
                    if name != "Unknown" and price > 0:
                        products.append({
                            'name': name,
                            'price': price,
                            'price_text': price_text,
                            'store': 'Lider',
                            'url': ''  # Can be extracted if needed
                        })
                        print(f"✅ Product added: {name} - ${price}")
                    
                except Exception as e:
                    print(f"⚠️ Error processing product {i+1}: {e}")
                    continue
            
            print(f"✅ Extracted {len(products)} products from Lider")
            
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