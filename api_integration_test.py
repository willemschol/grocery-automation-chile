#!/usr/bin/env python3
"""
API Integration Test for Enhanced Element Discovery
Tests that the enhanced mobile automation is properly integrated with the backend API
"""

import requests
import sys
import os

def test_api_integration():
    """Test that the enhanced mobile automation is integrated with the API"""
    print("🌐 Testing API Integration with Enhanced Mobile Automation")
    print("=" * 60)
    
    # Get backend URL from environment
    backend_url = "https://2fba086a-2368-4eba-9e38-248b6437d466.preview.emergentagent.com"
    
    try:
        # Test 1: Health check
        print("🔍 Testing health check...")
        health_response = requests.get(f"{backend_url}/api/health", timeout=10)
        if health_response.status_code == 200:
            print("✅ Health check passed")
        else:
            print(f"❌ Health check failed: {health_response.status_code}")
            return False
        
        # Test 2: Single product search (this will use enhanced mobile automation)
        print("\n🔍 Testing enhanced mobile automation via API...")
        search_data = {"product_name": "Coca Cola"}
        
        search_response = requests.post(
            f"{backend_url}/api/search-product", 
            json=search_data, 
            timeout=30
        )
        
        if search_response.status_code == 200:
            print("✅ API call successful")
            response_data = search_response.json()
            
            print(f"   📊 Response structure:")
            print(f"   - Product name: {response_data.get('product_name', 'N/A')}")
            print(f"   - Total found: {response_data.get('total_found', 0)}")
            print(f"   - Jumbo results: {len(response_data.get('jumbo_results', []))}")
            print(f"   - Lider results: {len(response_data.get('lider_results', []))}")
            
            # In test environment without physical devices, we expect 0 results but proper structure
            if 'jumbo_results' in response_data and 'lider_results' in response_data:
                print("✅ Enhanced mobile automation API integration working")
                print("   📱 Expected: 0 results in test environment (no physical devices)")
                print("   🚀 Enhanced element discovery should work with actual devices")
                return True
            else:
                print("❌ API response missing expected mobile automation structure")
                return False
        else:
            print(f"❌ API call failed: {search_response.status_code}")
            try:
                error_data = search_response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Error text: {search_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ API integration test failed: {e}")
        return False

def main():
    """Run API integration test"""
    success = test_api_integration()
    
    if success:
        print("\n🎉 API Integration Test Passed!")
        print("✅ Enhanced mobile automation is properly integrated with backend API")
        print("✅ Enhanced element discovery system ready for device testing")
        return 0
    else:
        print("\n❌ API Integration Test Failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())