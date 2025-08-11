#!/usr/bin/env python3
"""
Device Connection Test Script
Tests connection to physical Android device
"""

import subprocess
import time
import sys
import json

def run_adb_command(command):
    """Run ADB command and return output"""
    try:
        result = subprocess.run(['adb'] + command, capture_output=True, text=True, timeout=10)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def check_device_connection():
    """Check if Android device is connected and ready"""
    print("📱 Android Device Connection Test")
    print("=" * 40)
    
    # Check ADB version
    success, version, error = run_adb_command(['--version'])
    if success:
        print(f"✅ ADB Version: {version.split()[4]}")
    else:
        print(f"❌ ADB Error: {error}")
        return False
    
    # Check connected devices
    print("\n🔍 Checking for connected devices...")
    success, output, error = run_adb_command(['devices', '-l'])
    
    if not success:
        print(f"❌ ADB devices command failed: {error}")
        return False
    
    print(f"ADB Output:\n{output}")
    
    lines = output.strip().split('\n')
    if len(lines) < 2:
        print("❌ No devices connected")
        print("\n💡 Make sure:")
        print("  1. USB cable is connected")
        print("  2. USB Debugging is enabled")
        print("  3. Allow USB Debugging when prompted on phone")
        return False
    
    # Parse device list
    devices = []
    for line in lines[1:]:  # Skip "List of devices attached"
        if line.strip() and not line.startswith('*'):
            parts = line.split()
            if len(parts) >= 2:
                device_id = parts[0]
                status = parts[1]
                devices.append((device_id, status))
    
    if not devices:
        print("❌ No devices found in ADB output")
        return False
    
    print(f"\n📱 Found {len(devices)} device(s):")
    for device_id, status in devices:
        print(f"  Device: {device_id}")
        print(f"  Status: {status}")
        
        if status == "device":
            print(f"  ✅ Device ready for automation")
            
            # Get device info
            success, model, _ = run_adb_command(['-s', device_id, 'shell', 'getprop', 'ro.product.model'])
            success2, android_version, _ = run_adb_command(['-s', device_id, 'shell', 'getprop', 'ro.build.version.release'])
            
            if success:
                print(f"  📱 Model: {model}")
            if success2:
                print(f"  🤖 Android: {android_version}")
                
            return True
            
        elif status == "unauthorized":
            print(f"  ⚠️  Device unauthorized - check phone screen for USB debugging prompt")
            
        elif status == "offline":
            print(f"  ⚠️  Device offline")
            
        else:
            print(f"  ⚠️  Device status: {status}")
    
    return False

def check_installed_apps():
    """Check if Jumbo and Lider apps are installed"""
    print("\n📦 Checking for required apps...")
    
    # Common package names for Chilean apps (may vary)
    app_packages = [
        'cl.jumbo.mobile',
        'cl.jumbo.android', 
        'cl.jumbo.app',
        'com.jumbo.cl',
        'cl.lider.mobile',
        'cl.lider.android',
        'cl.lider.app', 
        'com.lider.cl',
        'com.walmart.lider'  # Lider is owned by Walmart
    ]
    
    found_apps = []
    
    for package in app_packages:
        success, output, _ = run_adb_command(['shell', 'pm', 'list', 'packages', package])
        if success and package in output:
            found_apps.append(package)
            print(f"  ✅ Found: {package}")
    
    if found_apps:
        print(f"\n🎉 Found {len(found_apps)} relevant app(s)")
        return found_apps
    else:
        print("\n❌ No Jumbo/Lider apps found")
        print("💡 Please install from Google Play Store:")
        print("  - Jumbo Chile")
        print("  - Lider Chile") 
        return []

def test_appium_connection():
    """Test if device can connect to Appium"""
    print("\n🤖 Testing Appium connection...")
    
    try:
        import requests
        response = requests.get('http://localhost:4724/status', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('value', {}).get('ready'):
                print("✅ Appium server is ready")
                return True
            else:
                print("❌ Appium server not ready")
        else:
            print(f"❌ Appium server returned status {response.status_code}")
    except ImportError:
        print("⚠️  requests library not available")
        # Try with curl
        try:
            result = subprocess.run(['curl', '-s', 'http://localhost:4724/status'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and 'ready' in result.stdout:
                print("✅ Appium server is ready")
                return True
            else:
                print("❌ Appium server not responding")
        except:
            print("❌ Cannot test Appium connection")
    except Exception as e:
        print(f"❌ Appium connection error: {e}")
    
    return False

def main():
    """Main device test function"""
    print("🚀 Physical Android Device Setup Test")
    print("=" * 50)
    
    # Test 1: Device Connection
    if not check_device_connection():
        print("\n❌ Device connection test failed")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure USB cable is properly connected")
        print("2. Enable Developer Options on phone")
        print("3. Enable USB Debugging")
        print("4. Allow USB Debugging when prompted")
        print("5. Try different USB port/cable")
        return 1
    
    # Test 2: Required Apps
    found_apps = check_installed_apps()
    
    # Test 3: Appium Connection
    appium_ready = test_appium_connection()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 CONNECTION SUMMARY:")
    print("✅ Device Connected: YES")
    print(f"📦 Apps Found: {len(found_apps)}")
    print(f"🤖 Appium Ready: {'YES' if appium_ready else 'NO'}")
    
    if found_apps and appium_ready:
        print("\n🎉 READY FOR MOBILE AUTOMATION!")
        print("\n🚀 Next steps:")
        print("1. Make sure both Jumbo and Lider apps are logged in")
        print("2. Run mobile automation test")
        return 0
    else:
        print("\n⚠️  Setup incomplete:")
        if not found_apps:
            print("   - Install Jumbo and Lider apps")
        if not appium_ready:
            print("   - Make sure Appium server is running")
        return 1

if __name__ == "__main__":
    sys.exit(main())