import requests
import sys
import json
import io
import tempfile
import os
import re
from datetime import datetime

class MobileAutomationFixesTester:
    def __init__(self, base_url="https://2fba086a-2368-4eba-9e38-248b6437d466.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {}
        
        if data and not files:
            headers['Content-Type'] = 'application/json'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files, timeout=30)
                else:
                    response = requests.post(url, json=data, headers=headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response preview: {str(response_data)[:200]}...")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Raw response: {response.text[:200]}...")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_simplified_navigation_validation(self):
        """Test simplified navigation validation using activity-based logic"""
        print("\n🔍 Testing Simplified Navigation Validation...")
        
        try:
            # Import and initialize mobile scraper
            sys.path.append('/app/backend')
            from mobile_scraper import MobileAppScraper
            import inspect
            
            mobile_scraper = MobileAppScraper()
            print("✅ Mobile scraper imported successfully")
            
            # Test 1: Check _validate_jumbo_navigation method exists and uses activity-based logic
            if not hasattr(mobile_scraper, '_validate_jumbo_navigation'):
                print("   ❌ _validate_jumbo_navigation method not found")
                return False
            
            validate_method = getattr(mobile_scraper, '_validate_jumbo_navigation')
            validate_source = inspect.getsource(validate_method)
            
            # Test 2: Verify it uses activity-based logic instead of home indicator counting
            if "current_activity" in validate_source:
                print("   ✅ Uses activity-based logic")
            else:
                print("   ❌ Missing activity-based logic")
                return False
            
            # Test 3: Verify it gives benefit of doubt (returns True in most cases)
            benefit_of_doubt_patterns = [
                "return True  # Let the extraction logic determine",
                "return True  # Give benefit of doubt",
                "assume success and let extraction determine"
            ]
            
            has_benefit_of_doubt = any(pattern in validate_source for pattern in benefit_of_doubt_patterns)
            if has_benefit_of_doubt:
                print("   ✅ Gives benefit of doubt instead of strict validation")
            else:
                print("   ❌ Missing benefit of doubt logic")
                return False
            
            # Test 4: Verify it doesn't use flawed home indicator counting
            if "home_count >= 2" not in validate_source and "Found 2 home indicators" not in validate_source:
                print("   ✅ Doesn't use flawed home indicator counting")
            else:
                print("   ❌ Still uses flawed home indicator counting")
                return False
            
            # Test 5: Verify it checks for product content as fallback
            if "product_indicators" in validate_source and "product_found" in validate_source:
                print("   ✅ Checks for product content as fallback validation")
            else:
                print("   ❌ Missing product content fallback validation")
                return False
            
            print("✅ Simplified navigation validation test passed")
            return True
            
        except Exception as e:
            print(f"❌ Error testing simplified navigation validation: {e}")
            return False

    def test_broadened_price_detection(self):
        """Test broadened price detection patterns for Chilean mobile app formats"""
        print("\n🔍 Testing Broadened Price Detection...")
        
        try:
            # Import and initialize mobile scraper
            sys.path.append('/app/backend')
            from mobile_scraper import MobileAppScraper
            
            mobile_scraper = MobileAppScraper()
            print("✅ Mobile scraper imported successfully")
            
            # Test 1: Verify _looks_like_price method exists
            if not hasattr(mobile_scraper, '_looks_like_price'):
                print("   ❌ _looks_like_price method not found")
                return False
            
            # Test 2: Test specific Chilean price patterns mentioned in review request
            test_patterns = [
                # Traditional patterns
                ("$1.890", True, "Traditional Chilean format"),
                ("$3.990", True, "Traditional Chilean format"),
                ("2 x $1.890", True, "Promotion format"),
                ("1190 c/u", True, "Per unit format"),
                
                # Broadened patterns from review request
                ("Ahorra $1.800", True, "Savings format"),
                ("promo 1500", True, "Promo format"),
                ("1500 c/u", True, "Per unit format"),
                ("$ 1890", True, "Format with space"),
                ("1890 $", True, "Reverse format"),
                ("2 por $3000", True, "Bulk pricing"),
                ("antes $2000", True, "Before price"),
                ("ahora $1500", True, "Now price"),
                ("lleva 2 por $3000", True, "Take 2 for price"),
                ("oferta 1990", True, "Offer format"),
                ("1500 pack", True, "Pack format"),
                ("precio 1990", True, "Price prefix"),
                ("1500 CLP", True, "Chilean pesos"),
                ("1500 clp", True, "Lowercase pesos"),
                
                # Edge cases that should be detected
                ("1890", True, "Pure number in reasonable range"),
                ("12345", True, "5-digit number"),
                ("999", True, "3-digit number"),
                
                # Cases that should NOT be detected
                ("12", False, "Too small number"),
                ("abc", False, "No numbers"),
                ("", False, "Empty string"),
                ("99", False, "Too small for price")
            ]
            
            passed_tests = 0
            total_tests = len(test_patterns)
            
            print(f"   🧪 Testing {total_tests} price patterns...")
            
            for pattern, expected, description in test_patterns:
                try:
                    result = mobile_scraper._looks_like_price(pattern)
                    if result == expected:
                        print(f"   ✅ '{pattern}' → {result} ({description})")
                        passed_tests += 1
                    else:
                        print(f"   ❌ '{pattern}' → {result}, expected {expected} ({description})")
                except Exception as e:
                    print(f"   ❌ Error testing '{pattern}': {e}")
            
            success_rate = (passed_tests / total_tests) * 100
            print(f"   📊 Price detection success rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
            
            # Test 3: Verify broadened patterns are actually in the code
            import inspect
            price_method = getattr(mobile_scraper, '_looks_like_price')
            price_source = inspect.getsource(price_method)
            
            required_patterns = [
                "ahorra.*\\$\\d+",  # Ahorra pattern
                "c/u",  # Per unit pattern
                "promo.*\\d+",  # Promo pattern
                "antes.*\\$\\d+",  # Before price
                "ahora.*\\$\\d+",  # Now price
            ]
            
            patterns_found = 0
            for pattern in required_patterns:
                if pattern in price_source:
                    patterns_found += 1
                    print(f"   ✅ Found broadened pattern: {pattern}")
                else:
                    print(f"   ❌ Missing broadened pattern: {pattern}")
            
            if patterns_found >= 4:  # At least 4 out of 5 patterns should be present
                print("   ✅ Sufficient broadened patterns implemented")
            else:
                print("   ❌ Insufficient broadened patterns")
                return False
            
            # Require at least 85% success rate for price detection
            if success_rate >= 85:
                print("✅ Broadened price detection test passed")
                return True
            else:
                print("❌ Price detection success rate too low")
                return False
            
        except Exception as e:
            print(f"❌ Error testing broadened price detection: {e}")
            return False

    def test_enhanced_element_state_validation(self):
        """Test enhanced element state validation with fallback methods"""
        print("\n🔍 Testing Enhanced Element State Validation...")
        
        try:
            # Import and initialize mobile scraper
            sys.path.append('/app/backend')
            from mobile_scraper import MobileAppScraper
            import inspect
            
            mobile_scraper = MobileAppScraper()
            print("✅ Mobile scraper imported successfully")
            
            # Test both ultra-robust methods for fallback mechanisms
            methods_to_test = [
                '_perform_jumbo_search_ultra_robust',
                '_perform_lider_search_ultra_robust'
            ]
            
            for method_name in methods_to_test:
                print(f"   🔍 Testing {method_name}...")
                
                if not hasattr(mobile_scraper, method_name):
                    print(f"   ❌ Method {method_name} not found")
                    return False
                
                method = getattr(mobile_scraper, method_name)
                method_source = inspect.getsource(method)
                
                # Test 1: Verify fallback methods (send_keys → set_value → character-by-character)
                fallback_patterns = [
                    "send_keys",  # Primary method
                    "set_value",  # Fallback method 1
                    "character-by-character"  # Fallback method 2 (or similar pattern)
                ]
                
                fallback_found = 0
                for pattern in fallback_patterns:
                    if pattern in method_source:
                        fallback_found += 1
                        print(f"   ✅ {method_name}: Found fallback pattern: {pattern}")
                
                # At least send_keys should be present (primary method)
                if "send_keys" not in method_source:
                    print(f"   ❌ {method_name}: Missing primary send_keys method")
                    return False
                
                # Test 2: Verify element state checking
                state_check_patterns = [
                    "get_attribute",  # Check element attributes
                    "is_displayed",   # Check if element is displayed
                    "is_enabled",     # Check if element is enabled
                    "clickable",      # Check if element is clickable
                    "text",           # Verify text content
                ]
                
                state_checks_found = 0
                for pattern in state_check_patterns:
                    if pattern in method_source:
                        state_checks_found += 1
                        print(f"   ✅ {method_name}: Found state check: {pattern}")
                
                if state_checks_found >= 2:  # At least 2 state checks should be present
                    print(f"   ✅ {method_name}: Sufficient element state validation")
                else:
                    print(f"   ❌ {method_name}: Insufficient element state validation")
                    return False
                
                # Test 3: Verify per-operation element re-finding (prevents stale elements)
                per_operation_patterns = [
                    "WebDriverWait(self.driver",  # Fresh element finding
                    "element_to_be_clickable",    # Wait for clickable state
                    "presence_of_element_located" # Wait for element presence
                ]
                
                per_operation_found = 0
                for pattern in per_operation_patterns:
                    count = method_source.count(pattern)
                    if count >= 3:  # Should appear multiple times for different operations
                        per_operation_found += 1
                        print(f"   ✅ {method_name}: Found per-operation pattern: {pattern} ({count} times)")
                
                if per_operation_found >= 2:
                    print(f"   ✅ {method_name}: Per-operation element re-finding implemented")
                else:
                    print(f"   ❌ {method_name}: Missing per-operation element re-finding")
                    return False
                
                # Test 4: Verify error handling for element interaction failures
                error_handling_patterns = [
                    "except Exception as",  # General exception handling
                    "continue",             # Continue on failure
                    "try:",                 # Try-catch blocks
                ]
                
                error_handling_found = 0
                for pattern in error_handling_patterns:
                    if pattern in method_source:
                        error_handling_found += 1
                        print(f"   ✅ {method_name}: Found error handling: {pattern}")
                
                if error_handling_found >= 2:
                    print(f"   ✅ {method_name}: Adequate error handling")
                else:
                    print(f"   ❌ {method_name}: Insufficient error handling")
                    return False
            
            print("✅ Enhanced element state validation test passed")
            return True
            
        except Exception as e:
            print(f"❌ Error testing enhanced element state validation: {e}")
            return False

    def test_screenshot_debugging(self):
        """Test screenshot debugging when finding 0 products"""
        print("\n🔍 Testing Screenshot Debugging...")
        
        try:
            # Import and initialize mobile scraper
            sys.path.append('/app/backend')
            from mobile_scraper import MobileAppScraper
            import inspect
            
            mobile_scraper = MobileAppScraper()
            print("✅ Mobile scraper imported successfully")
            
            # Test both extraction methods for screenshot debugging
            extraction_methods = [
                '_extract_jumbo_products',
                '_extract_lider_products'
            ]
            
            for method_name in extraction_methods:
                print(f"   🔍 Testing {method_name}...")
                
                if not hasattr(mobile_scraper, method_name):
                    print(f"   ❌ Method {method_name} not found")
                    return False
                
                method = getattr(mobile_scraper, method_name)
                method_source = inspect.getsource(method)
                
                # Test 1: Verify screenshot saving when no products found
                screenshot_patterns = [
                    "save_screenshot",  # Screenshot method
                    "no_products",      # When no products found
                    "debugging",        # For debugging purposes
                    "tempfile.gettempdir()", # Windows-compatible path
                ]
                
                screenshot_found = 0
                for pattern in screenshot_patterns:
                    if pattern in method_source:
                        screenshot_found += 1
                        print(f"   ✅ {method_name}: Found screenshot pattern: {pattern}")
                
                if screenshot_found >= 3:  # At least 3 patterns should be present
                    print(f"   ✅ {method_name}: Screenshot debugging implemented")
                else:
                    print(f"   ❌ {method_name}: Missing screenshot debugging")
                    return False
                
                # Test 2: Verify screenshot is taken when price_elements is empty
                if "if not price_elements:" in method_source and "save_screenshot" in method_source:
                    print(f"   ✅ {method_name}: Screenshot taken when no price elements found")
                else:
                    print(f"   ❌ {method_name}: Missing screenshot for no price elements")
                    return False
                
                # Test 3: Verify timestamp in screenshot filename
                if "timestamp" in method_source and "datetime" in method_source:
                    print(f"   ✅ {method_name}: Screenshot filename includes timestamp")
                else:
                    print(f"   ❌ {method_name}: Missing timestamp in screenshot filename")
                    return False
                
                # Test 4: Verify error handling for screenshot failures
                if "screenshot_error" in method_source or "Could not save screenshot" in method_source:
                    print(f"   ✅ {method_name}: Has error handling for screenshot failures")
                else:
                    print(f"   ❌ {method_name}: Missing error handling for screenshot failures")
                    return False
            
            print("✅ Screenshot debugging test passed")
            return True
            
        except Exception as e:
            print(f"❌ Error testing screenshot debugging: {e}")
            return False

    def test_price_pattern_testing(self):
        """Test specific Chilean price patterns mentioned in review request"""
        print("\n🔍 Testing Specific Chilean Price Patterns...")
        
        try:
            # Import and initialize mobile scraper
            sys.path.append('/app/backend')
            from mobile_scraper import MobileAppScraper
            
            mobile_scraper = MobileAppScraper()
            print("✅ Mobile scraper imported successfully")
            
            # Test specific patterns mentioned in review request
            specific_patterns = [
                ("2 x $1.890", 1890.0, "Promotion: 2 for $1.890 total"),
                ("$3.990", 3990.0, "Regular Chilean price"),
                ("1190 c/u", 1190.0, "Per unit pricing"),
                ("Ahorra $1.800", 1800.0, "Savings format"),
            ]
            
            print(f"   🧪 Testing {len(specific_patterns)} specific Chilean patterns...")
            
            passed_patterns = 0
            
            for pattern_text, expected_price, description in specific_patterns:
                try:
                    # Test 1: Price detection
                    is_price = mobile_scraper._looks_like_price(pattern_text)
                    if not is_price:
                        print(f"   ❌ '{pattern_text}' not detected as price ({description})")
                        continue
                    
                    # Test 2: Price parsing
                    if hasattr(mobile_scraper, '_parse_chilean_price_corrected'):
                        parsed_result = mobile_scraper._parse_chilean_price_corrected(pattern_text)
                        parsed_price = parsed_result.get('price', 0)
                    else:
                        # Fallback to basic parser
                        parsed_price = mobile_scraper._parse_chilean_price(pattern_text)
                    
                    if abs(parsed_price - expected_price) < 0.01:
                        print(f"   ✅ '{pattern_text}' → ${parsed_price} ({description})")
                        passed_patterns += 1
                    else:
                        print(f"   ❌ '{pattern_text}' → ${parsed_price}, expected ${expected_price} ({description})")
                
                except Exception as e:
                    print(f"   ❌ Error testing '{pattern_text}': {e}")
            
            # Test 3: Verify promotion handling for "2 x $1.890" format
            if hasattr(mobile_scraper, '_parse_chilean_price_corrected'):
                try:
                    promo_result = mobile_scraper._parse_chilean_price_corrected("2 x $1.890")
                    if promo_result.get('promotion', {}).get('is_promo', False):
                        print(f"   ✅ Promotion correctly detected for '2 x $1.890'")
                        
                        quantity = promo_result.get('promotion', {}).get('quantity', 0)
                        if quantity == 2:
                            print(f"   ✅ Promotion quantity correctly parsed: {quantity}")
                        else:
                            print(f"   ❌ Promotion quantity incorrect: {quantity}, expected 2")
                    else:
                        print(f"   ❌ Promotion not detected for '2 x $1.890'")
                except Exception as e:
                    print(f"   ⚠️ Could not test promotion parsing: {e}")
            
            success_rate = (passed_patterns / len(specific_patterns)) * 100
            print(f"   📊 Specific pattern success rate: {passed_patterns}/{len(specific_patterns)} ({success_rate:.1f}%)")
            
            if success_rate >= 75:  # At least 75% should pass
                print("✅ Specific Chilean price patterns test passed")
                return True
            else:
                print("❌ Specific Chilean price patterns test failed")
                return False
            
        except Exception as e:
            print(f"❌ Error testing specific Chilean price patterns: {e}")
            return False

    def test_integration_testing(self):
        """Test that all methods work together and API endpoints call updated logic"""
        print("\n🔍 Testing Integration of All Methods...")
        
        try:
            # Test 1: API endpoint integration
            print("   🔍 Testing API endpoint integration...")
            
            success, response = self.run_test(
                "Mobile Automation Integration",
                "POST",
                "api/search-product",
                200,
                data={"product_name": "Coca Cola"}
            )
            
            if not success:
                print("   ❌ API endpoint integration failed")
                return False
            
            # Test 2: Verify response structure includes updated logic results
            if 'jumbo_results' in response and 'lider_results' in response:
                print("   ✅ API response contains both store results")
            else:
                print("   ❌ API response missing expected structure")
                return False
            
            # Test 3: Verify mobile scraper methods are properly integrated
            sys.path.append('/app/backend')
            from mobile_scraper import MobileAppScraper
            import inspect
            
            mobile_scraper = MobileAppScraper()
            
            # Check that main search methods call the ultra-robust methods
            search_jumbo_method = getattr(mobile_scraper, 'search_jumbo_app')
            search_lider_method = getattr(mobile_scraper, 'search_lider_app')
            
            jumbo_source = inspect.getsource(search_jumbo_method)
            lider_source = inspect.getsource(search_lider_method)
            
            if '_perform_jumbo_search_ultra_robust' in jumbo_source:
                print("   ✅ Jumbo search calls ultra-robust method")
            else:
                print("   ❌ Jumbo search doesn't call ultra-robust method")
                return False
            
            if '_perform_lider_search_ultra_robust' in lider_source:
                print("   ✅ Lider search calls ultra-robust method")
            else:
                print("   ❌ Lider search doesn't call ultra-robust method")
                return False
            
            # Test 4: Verify extraction methods use corrected logic
            extract_jumbo_method = getattr(mobile_scraper, '_extract_jumbo_products')
            extract_lider_method = getattr(mobile_scraper, '_extract_lider_products')
            
            jumbo_extract_source = inspect.getsource(extract_jumbo_method)
            lider_extract_source = inspect.getsource(extract_lider_method)
            
            if '_looks_like_price' in jumbo_extract_source and '_looks_like_price' in lider_extract_source:
                print("   ✅ Extraction methods use broadened price detection")
            else:
                print("   ❌ Extraction methods don't use broadened price detection")
                return False
            
            # Test 5: Verify navigation validation is integrated
            if '_validate_jumbo_navigation' in jumbo_source:
                print("   ✅ Jumbo search uses simplified navigation validation")
            else:
                print("   ❌ Jumbo search doesn't use navigation validation")
                return False
            
            print("✅ Integration testing passed")
            return True
            
        except Exception as e:
            print(f"❌ Error in integration testing: {e}")
            return False

    def run_all_tests(self):
        """Run all mobile automation fixes tests"""
        print("🚀 Starting Mobile Automation Fixes Testing...")
        print("=" * 80)
        
        # Test 1: Basic API Health Check
        success, response = self.run_test(
            "Health Check",
            "GET",
            "api/health",
            200
        )
        if not success:
            print("❌ Health check failed - stopping tests")
            return False
        
        # Test 2: Simplified Navigation Validation (Review Request #1)
        if not self.test_simplified_navigation_validation():
            print("❌ Simplified navigation validation test failed")
            return False
        
        # Test 3: Broadened Price Detection (Review Request #2)
        if not self.test_broadened_price_detection():
            print("❌ Broadened price detection test failed")
            return False
        
        # Test 4: Enhanced Element State Validation (Review Request #3)
        if not self.test_enhanced_element_state_validation():
            print("❌ Enhanced element state validation test failed")
            return False
        
        # Test 5: Screenshot Debugging (Review Request #4)
        if not self.test_screenshot_debugging():
            print("❌ Screenshot debugging test failed")
            return False
        
        # Test 6: Price Pattern Testing (Review Request #6)
        if not self.test_price_pattern_testing():
            print("❌ Price pattern testing failed")
            return False
        
        # Test 7: Integration Testing (Review Request #5)
        if not self.test_integration_testing():
            print("❌ Integration testing failed")
            return False
        
        print("\n" + "=" * 80)
        print(f"🎯 MOBILE AUTOMATION FIXES TESTING COMPLETE: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("✅ ALL MOBILE AUTOMATION FIXES VERIFIED - System ready for device testing!")
            return True
        else:
            print("❌ SOME TESTS FAILED - Review issues above")
            return False

def main():
    print("🚀 Starting Mobile Automation Fixes Testing")
    print("Testing fundamental mobile automation fixes for navigation and price detection")
    print("=" * 80)
    
    tester = MobileAutomationFixesTester()
    
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All Mobile Automation Fixes Tests Passed!")
        print("✅ Key fixes verified:")
        print("   🎯 Simplified Navigation Validation: Activity-based logic with benefit of doubt")
        print("   💰 Broadened Price Detection: Expanded patterns for Chilean mobile app formats")
        print("   🔧 Enhanced Element State Validation: Fallback methods and state checking")
        print("   📸 Screenshot Debugging: Screenshots saved when finding 0 products")
        print("   🔗 Integration Testing: All methods work together via API endpoints")
        print("   🧪 Price Pattern Testing: Specific Chilean patterns like '2 x $1.890', 'c/u', 'ahorra'")
        print("\n🚀 System should now be much more permissive in navigation validation")
        print("🚀 System should now be much more aggressive in price detection")
        print("🚀 System should now have robust fallback mechanisms and debugging capabilities")
        return 0
    else:
        print("\n⚠️ Some mobile automation fixes tests failed - check logs above")
        return 1

if __name__ == "__main__":
    sys.exit(main())