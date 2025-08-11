import requests
import sys
import json
import io
from datetime import datetime

class GroceryAutomationTester:
    def __init__(self, base_url="https://6f023277-2e24-4ba8-9f6c-63dc72cd1bff.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.list_id = None

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

    def test_health_check(self):
        """Test health endpoint"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "api/health",
            200
        )
        return success

    def test_single_product_search(self, product_name):
        """Test single product search"""
        success, response = self.run_test(
            f"Single Product Search - {product_name}",
            "POST",
            "api/search-product",
            200,
            data={"product_name": product_name}
        )
        
        if success:
            print(f"   Found {response.get('total_found', 0)} total products")
            print(f"   Jumbo results: {len(response.get('jumbo_results', []))}")
            print(f"   Lider results: {len(response.get('lider_results', []))}")
            
            # Check if we got actual results
            if response.get('total_found', 0) > 0:
                print("   ✅ Web scraping working - found products!")
                
                # Show sample results
                jumbo_results = response.get('jumbo_results', [])
                if jumbo_results:
                    sample = jumbo_results[0]
                    print(f"   Sample Jumbo: {sample.get('name', 'N/A')} - ${sample.get('price', 0)}")
                
                lider_results = response.get('lider_results', [])
                if lider_results:
                    sample = lider_results[0]
                    print(f"   Sample Lider: {sample.get('name', 'N/A')} - ${sample.get('price', 0)}")
            else:
                print("   ⚠️  No products found - may indicate scraping issues")
        
        return success, response

    def test_csv_upload(self):
        """Test CSV file upload"""
        # Create a test CSV content
        csv_content = """Producto,Tamaño Preferido
Coca Cola,500ml
Pan de molde,Grande
Leche,1L"""
        
        # Create file-like object
        csv_file = io.StringIO(csv_content)
        files = {'file': ('test_products.csv', csv_file.getvalue(), 'text/csv')}
        
        success, response = self.run_test(
            "CSV Upload",
            "POST",
            "api/upload-csv",
            200,
            files=files
        )
        
        if success:
            self.list_id = response.get('list_id')
            print(f"   Uploaded {len(response.get('products', []))} products")
            print(f"   List ID: {self.list_id}")
        
        return success, response

    def test_search_all_products(self):
        """Test bulk product search"""
        if not self.list_id:
            print("❌ Cannot test search all - no list_id available")
            return False, {}
        
        success, response = self.run_test(
            "Search All Products",
            "POST",
            "api/search-all-products",
            200,
            data={"list_id": self.list_id}
        )
        
        if success:
            results = response.get('results', [])
            print(f"   Processed {len(results)} products")
            print(f"   Successful searches: {response.get('successful_searches', 0)}")
            
            # Check for errors in results
            errors = [r for r in results if 'error' in r]
            if errors:
                print(f"   ⚠️  {len(errors)} products had errors")
                for error in errors[:2]:  # Show first 2 errors
                    print(f"      - {error['product']['name']}: {error['error']}")
            
            # Show successful results
            successful = [r for r in results if 'error' not in r]
            for result in successful[:2]:  # Show first 2 successful
                product_name = result['product']['name']
                jumbo_count = len(result.get('jumbo_results', []))
                lider_count = len(result.get('lider_results', []))
                print(f"   ✅ {product_name}: Jumbo({jumbo_count}), Lider({lider_count})")
                
                if result.get('cheaper_option'):
                    cheaper = result['cheaper_option']
                    print(f"      Best: {cheaper['store']} - ${cheaper['price']}")
        
        return success, response

def main():
    print("🚀 Starting Grocery Automation System Tests")
    print("=" * 60)
    
    tester = GroceryAutomationTester()
    
    # Test 1: Health Check
    if not tester.test_health_check():
        print("❌ Health check failed - stopping tests")
        return 1
    
    # Test 2: Single Product Search with Chilean products
    chilean_products = ["Coca Cola", "Pan de molde", "Leche"]
    
    for product in chilean_products:
        success, response = tester.test_single_product_search(product)
        if not success:
            print(f"❌ Product search failed for {product}")
        else:
            # Check if scraping actually worked
            total_found = response.get('total_found', 0)
            if total_found == 0:
                print(f"⚠️  Warning: No products found for '{product}' - possible scraping issue")
    
    # Test 3: CSV Upload
    if not tester.test_csv_upload():
        print("❌ CSV upload failed")
        return 1
    
    # Test 4: Bulk Product Search
    if not tester.test_search_all_products():
        print("❌ Bulk product search failed")
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed - check logs above")
        return 1

if __name__ == "__main__":
    sys.exit(main())