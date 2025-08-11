#!/usr/bin/env python3
"""
WiFi ADB Connection Setup
Connects to Android device over WiFi for automation
"""

import subprocess
import time
import sys
import re

def run_adb_command(command, timeout=10):
    """Run ADB command safely"""
    try:
        result = subprocess.run(['adb'] + command, 
                              capture_output=True, 
                              text=True, 
                              timeout=timeout)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def setup_wifi_adb(phone_ip):
    """Set up ADB connection over WiFi"""
    print(f"🔗 Setting up WiFi ADB connection to {phone_ip}")
    print("=" * 50)
    
    # Step 1: Check if ADB is working
    print("1. 📡 Testing ADB server...")
    success, version, error = run_adb_command(['--version'])
    if not success:
        print(f"❌ ADB not working: {error}")
        return False
    print(f"✅ ADB Version: {version.split()[4]}")
    
    # Step 2: Kill and restart ADB server
    print("\n2. 🔄 Restarting ADB server...")
    run_adb_command(['kill-server'])
    time.sleep(2)
    run_adb_command(['start-server'])
    time.sleep(2)
    print("✅ ADB server restarted")
    
    # Step 3: Enable TCP/IP mode on port 5555
    print("\n3. 🌐 Enabling ADB over WiFi...")
    success, output, error = run_adb_command(['tcpip', '5555'])
    if success:
        print("✅ ADB TCP/IP mode enabled on port 5555")
    else:
        print(f"⚠️  TCP/IP command result: {output} {error}")
        print("📱 Make sure USB debugging is still enabled")
    
    time.sleep(3)
    
    # Step 4: Connect to device over WiFi
    print(f"\n4. 📱 Connecting to {phone_ip}:5555...")
    success, output, error = run_adb_command(['connect', f'{phone_ip}:5555'])
    
    print(f"Connection output: {output}")
    if error:
        print(f"Connection error: {error}")
    
    # Step 5: Verify connection
    print("\n5. ✅ Verifying connection...")
    success, devices_output, error = run_adb_command(['devices'])
    
    print("Connected devices:")
    print(devices_output)
    
    # Check if our WiFi device is listed
    if f"{phone_ip}:5555" in devices_output and "device" in devices_output:
        print("🎉 SUCCESS! WiFi ADB connection established!")
        
        # Get device info
        success, model, _ = run_adb_command(['-s', f'{phone_ip}:5555', 'shell', 'getprop', 'ro.product.model'])
        success2, android_ver, _ = run_adb_command(['-s', f'{phone_ip}:5555', 'shell', 'getprop', 'ro.build.version.release'])
        
        if success:
            print(f"📱 Device Model: {model}")
        if success2:
            print(f"🤖 Android Version: {android_ver}")
            
        return True
    else:
        print("❌ Connection failed or device not ready")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure phone and computer are on same WiFi network")
        print("2. Check if phone IP address is correct")
        print("3. Ensure USB Debugging is still enabled")
        print("4. Try restarting both ADB and phone's Developer Options")
        return False

def test_app_detection(phone_ip):
    """Test detection of Jumbo and Lider apps"""
    print(f"\n📦 Detecting apps on {phone_ip}...")
    
    # Common package names for Chilean grocery apps
    target_packages = [
        'cl.jumbo.mobile', 'cl.jumbo.android', 'cl.jumbo.app', 'com.jumbo.cl',
        'cl.lider.mobile', 'cl.lider.android', 'cl.lider.app', 'com.lider.cl', 'com.walmart.lider'
    ]
    
    found_apps = []
    
    for package in target_packages:
        success, output, _ = run_adb_command(['-s', f'{phone_ip}:5555', 'shell', 'pm', 'list', 'packages', package])
        if success and package in output:
            found_apps.append(package)
            print(f"✅ Found: {package}")
    
    if not found_apps:
        # Try broader search
        print("🔍 Searching for grocery-related apps...")
        success, all_packages, _ = run_adb_command(['-s', f'{phone_ip}:5555', 'shell', 'pm', 'list', 'packages'])
        
        grocery_keywords = ['jumbo', 'lider', 'walmart', 'grocery', 'super']
        potential_apps = []
        
        for line in all_packages.split('\n'):
            for keyword in grocery_keywords:
                if keyword.lower() in line.lower():
                    potential_apps.append(line.strip())
                    
        if potential_apps:
            print("🔍 Potential grocery apps found:")
            for app in potential_apps:
                print(f"  📱 {app}")
        else:
            print("❌ No grocery apps detected")
            print("💡 Make sure Jumbo and Lider apps are installed")
    
    return found_apps

def main():
    """Main WiFi ADB setup function"""
    print("📱 WiFi ADB Connection Setup")
    print("=" * 60)
    
    if len(sys.argv) != 2:
        print("❌ Usage: python wifi_adb_setup.py <PHONE_IP_ADDRESS>")
        print("📱 Example: python wifi_adb_setup.py 192.168.1.150")
        return 1
    
    phone_ip = sys.argv[1]
    
    # Validate IP format
    ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if not re.match(ip_pattern, phone_ip):
        print(f"❌ Invalid IP address format: {phone_ip}")
        print("📱 Expected format: 192.168.1.150")
        return 1
    
    print(f"🎯 Target Device: {phone_ip}")
    print("📋 Prerequisites:")
    print("  ✅ Phone and computer on same WiFi network")
    print("  ✅ USB Debugging enabled on phone")
    print("  ✅ Phone connected via USB (for initial setup)")
    print()
    
    # Setup WiFi connection
    if setup_wifi_adb(phone_ip):
        # Test app detection
        found_apps = test_app_detection(phone_ip)
        
        print("\n" + "=" * 60)
        print("🎉 WIFI ADB SETUP COMPLETE!")
        print(f"📱 Device: {phone_ip}:5555")
        print(f"📦 Apps found: {len(found_apps)}")
        
        if found_apps:
            print("\n🚀 Ready for mobile automation!")
            print("Next step: Run mobile automation tests")
        else:
            print("\n⚠️  Install Jumbo and Lider apps if not found")
            
        print("\n💡 You can now disconnect USB cable - WiFi connection is active!")
        return 0
    else:
        print("\n❌ WiFi ADB setup failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())