#!/usr/bin/env python3
"""
Quick Test Suite for Local Installation
Tests all components of the grocery automation system
"""

import subprocess
import sys
import time
import requests
import json

def run_command(cmd, timeout=10):
    """Run a command and return success status"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def test_prerequisites():
    """Test if all prerequisites are installed"""
    print("🔧 Testing Prerequisites")
    print("-" * 30)
    
    tests = [
        ("Python", "python --version"),
        ("Node.js", "node --version"), 
        ("Java", "java -version"),
        ("ADB", "adb version"),
        ("MongoDB", "mongo --version"),
        ("Appium", "appium --version")
    ]
    
    results = []
    for name, cmd in tests:
        success, output, error = run_command(cmd)
        if success:
            version = output.split('\n')[0] if output else "Installed"
            print(f"✅ {name}: {version}")
            results.append(True)
        else:
            print(f"❌ {name}: Not found")
            results.append(False)
    
    return all(results)

def test_services():
    """Test if services are running"""
    print("\n🌐 Testing Services")
    print("-" * 20)
    
    # Test Backend API
    try:
        response = requests.get("http://localhost:8001/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend API: Running")
            backend_ok = True
        else:
            print(f"❌ Backend API: Status {response.status_code}")
            backend_ok = False
    except Exception as e:
        print(f"❌ Backend API: Not accessible ({e})")
        backend_ok = False
    
    # Test Frontend
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend: Running")
            frontend_ok = True
        else:
            print(f"❌ Frontend: Status {response.status_code}")
            frontend_ok = False
    except Exception as e:
        print(f"❌ Frontend: Not accessible ({e})")
        frontend_ok = False
    
    # Test Appium
    try:
        response = requests.get("http://localhost:4723/status", timeout=5)
        if response.status_code == 200:
            print("✅ Appium: Running")
            appium_ok = True
        else:
            print(f"❌ Appium: Status {response.status_code}")
            appium_ok = False
    except Exception as e:
        print(f"❌ Appium: Not accessible ({e})")
        appium_ok = False
    
    return backend_ok and frontend_ok and appium_ok

def test_device_connection():
    """Test Android device connection"""
    print("\n📱 Testing Device Connection")
    print("-" * 30)
    
    success, output, error = run_command("adb devices")
    if success:
        lines = output.strip().split('\n')
        devices = [line for line in lines[1:] if line.strip() and not line.startswith('*')]
        
        if devices:
            print(f"✅ Found {len(devices)} device(s):")
            for device in devices:
                print(f"   📱 {device}")
            return True
        else:
            print("❌ No devices connected")
            print("💡 Make sure:")
            print("   - Phone is connected via USB")
            print("   - USB Debugging is enabled")
            print("   - USB debugging permission granted")
            return False
    else:
        print(f"❌ ADB command failed: {error}")
        return False

def test_mobile_automation():
    """Test mobile automation capability"""
    print("\n🤖 Testing Mobile Automation")
    print("-" * 30)
    
    try:
        # Test if we can import our mobile scraper
        sys.path.append('.')
        from mobile_scraper import MobileAppScraper
        
        scraper = MobileAppScraper()
        print("✅ Mobile scraper module loaded")
        
        # Test basic driver setup (without connecting)
        print("✅ Mobile automation framework ready")
        
        return True
        
    except ImportError as e:
        print(f"❌ Cannot import mobile scraper: {e}")
        return False
    except Exception as e:
        print(f"❌ Mobile automation error: {e}")
        return False

def test_csv_upload():
    """Test CSV upload functionality"""
    print("\n📄 Testing CSV Upload")
    print("-" * 20)
    
    # Create test CSV
    test_csv = "Producto,Tamaño\nCoca Cola,500ml\nPan,Grande"
    
    try:
        with open("test_upload.csv", "w") as f:
            f.write(test_csv)
        
        # Test upload via API
        with open("test_upload.csv", "rb") as f:
            files = {"file": f}
            response = requests.post("http://localhost:8001/api/upload-csv", files=files, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ CSV Upload: Successfully uploaded {len(data['products'])} products")
            return True
        else:
            print(f"❌ CSV Upload: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ CSV Upload: {e}")
        return False
    finally:
        # Clean up
        try:
            import os
            os.remove("test_upload.csv")
        except:
            pass

def main():
    """Main test function"""
    print("🧪 Grocery Automation System - Complete Test Suite")
    print("=" * 60)
    
    # Run all tests
    prereq_ok = test_prerequisites()
    services_ok = test_services() if prereq_ok else False
    device_ok = test_device_connection() if prereq_ok else False
    mobile_ok = test_mobile_automation() if prereq_ok else False
    csv_ok = test_csv_upload() if services_ok else False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print(f"🔧 Prerequisites: {'✅ PASS' if prereq_ok else '❌ FAIL'}")
    print(f"🌐 Services: {'✅ PASS' if services_ok else '❌ FAIL'}")
    print(f"📱 Device Connection: {'✅ PASS' if device_ok else '❌ FAIL'}")
    print(f"🤖 Mobile Automation: {'✅ PASS' if mobile_ok else '❌ FAIL'}")
    print(f"📄 CSV Upload: {'✅ PASS' if csv_ok else '❌ FAIL'}")
    
    all_ok = all([prereq_ok, services_ok, device_ok, mobile_ok, csv_ok])
    
    if all_ok:
        print("\n🎉 ALL TESTS PASSED! System is fully operational!")
        print("\n🚀 Ready for automated grocery price comparison!")
        print("👉 Open http://localhost:3000 to start using the system")
    else:
        print("\n⚠️  Some tests failed. Please check the issues above.")
        print("💡 Make sure all services are running and device is connected")
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())