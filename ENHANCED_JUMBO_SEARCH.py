# Enhanced Jumbo Search Methods
# Replace your existing _perform_jumbo_search method with this enhanced version

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
        self.save_page_source(f"jumbo_before_search.xml")
        
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
        self.save_page_source(f"jumbo_after_search.xml") 
        
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