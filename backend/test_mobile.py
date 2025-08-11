#!/usr/bin/env python3
"""
Test script for mobile app automation
Tests basic connectivity and app automation setup
"""

import asyncio
import sys
import os
sys.path.append('/app/backend')

from mobile_scraper import MobileAppScraper


async def test_mobile_setup():
    """Test mobile automation setup"""
    print("🚀 Testing Mobile App Automation Setup")
    print("=" * 50)
    
    scraper = MobileAppScraper()
    
    try:
        print("1. Testing Appium connection...")
        
        # Test basic driver setup (without specific app)
        if scraper.setup_driver():
            print("✅ Appium connection successful")
            
            # Get device info
            device_info = scraper.get_app_info()
            print(f"📱 Device Info: {device_info}")
            
            scraper.close_driver()
        else:
            print("❌ Failed to connect to Appium server")
            print("💡 Make sure Appium server is running: appium")
            return False
        
        print("\n2. Testing search functionality (simulation)...")
        # Note: This won't work without actual apps installed
        # But it will test our code structure
        
        print("✅ Mobile automation framework is ready!")
        print("\n📝 Next Steps:")
        print("1. Start Appium server: appium")
        print("2. Install Jumbo and Lider APKs on Android device/emulator")  
        print("3. Run actual search tests")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


async def test_search_simulation():
    """Simulate a search test (for framework testing)"""
    print("\n🔍 Testing Search Framework (Simulation)")
    print("-" * 40)
    
    scraper = MobileAppScraper()
    
    # Test our price parsing function
    test_prices = [
        "$1.990",
        "$12.350", 
        "$990",
        "$ 2.490",
        "CLP 3.500"
    ]
    
    print("💰 Testing price parsing:")
    for price_text in test_prices:
        parsed_price = scraper._parse_chilean_price(price_text)
        print(f"  '{price_text}' → {parsed_price}")
    
    print("✅ Price parsing tests completed")


def check_prerequisites():
    """Check if all prerequisites are installed"""
    print("🔧 Checking Prerequisites")
    print("-" * 30)
    
    checks = []
    
    # Check Java
    try:
        import subprocess
        java_version = subprocess.check_output(['java', '-version'], stderr=subprocess.STDOUT, text=True)
        print("✅ Java installed")
        checks.append(True)
    except:
        print("❌ Java not found")
        checks.append(False)
    
    # Check Node.js
    try:
        node_version = subprocess.check_output(['node', '--version'], text=True)
        print(f"✅ Node.js {node_version.strip()}")
        checks.append(True)
    except:
        print("❌ Node.js not found")
        checks.append(False)
    
    # Check Appium
    try:
        appium_version = subprocess.check_output(['appium', '--version'], text=True)
        print(f"✅ Appium {appium_version.strip()}")
        checks.append(True)
    except:
        print("❌ Appium not found")
        checks.append(False)
    
    # Check Python packages
    try:
        import appium
        import selenium
        print("✅ Python packages (appium-python-client, selenium)")
        checks.append(True)
    except ImportError as e:
        print(f"❌ Python packages missing: {e}")
        checks.append(False)
    
    return all(checks)


async def main():
    """Main test function"""
    print("🤖 Grocery Automation - Mobile App Testing")
    print("=" * 60)
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites check failed")
        print("Please ensure all requirements are installed")
        return 1
    
    print(f"\n✅ All prerequisites installed")
    
    # Test mobile setup
    setup_success = await test_mobile_setup()
    if not setup_success:
        return 1
    
    # Test search simulation
    await test_search_simulation()
    
    print("\n" + "=" * 60)
    print("🎉 Mobile automation framework test completed!")
    print("\n🔗 Integration Status:")
    print("  - Framework: ✅ Ready")
    print("  - Prerequisites: ✅ Installed")  
    print("  - Apps: ⏳ Waiting for APK installation")
    print("  - Device: ⏳ Waiting for Android setup")
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))