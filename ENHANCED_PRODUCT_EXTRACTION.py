# Enhanced Product Extraction Methods
# Replace your existing _extract_jumbo_products and _extract_lider_products methods

async def _extract_jumbo_products(self) -> List[Dict]:
    """Extract product information from Jumbo search results with enhanced debugging"""
    products = []
    
    try:
        print("📦 Starting enhanced Jumbo product extraction...")
        
        # Save page source for analysis
        self.save_page_source(f"jumbo_products_page.xml")
        
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
        
        # Step 2: Try comprehensive product container selectors
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
            return await self._extract_products_from_price_elements(dollar_elements, "Jumbo")
        
        # Step 3: Extract product information from containers
        print(f"📦 Processing {len(product_elements)} product containers...")
        
        for i, element in enumerate(product_elements):
            try:
                print(f"📦 Processing product container {i+1}/{len(product_elements)}...")
                
                product_info = await self._extract_single_product_info(element, "Jumbo")
                if product_info:
                    products.append(product_info)
                    print(f"✅ Product {i+1} extracted: {product_info['name']} - ${product_info['price']}")
                else:
                    print(f"⚠️ Could not extract info from product container {i+1}")
                
            except Exception as e:
                print(f"❌ Error processing product container {i+1}: {e}")
                continue
        
        print(f"✅ Successfully extracted {len(products)} products from Jumbo")
        
    except Exception as e:
        print(f"❌ Error in enhanced Jumbo product extraction: {e}")
    
    return products

async def _extract_lider_products(self) -> List[Dict]:
    """Extract product information from Lider search results with enhanced debugging"""
    products = []
    
    try:
        print("📦 Starting enhanced Lider product extraction...")
        
        # Save page source for analysis
        self.save_page_source(f"lider_products_page.xml")
        
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