# 🛒 Grocery Automation System - Local Installation Guide

## 🎯 WHAT YOU'RE GETTING
Complete automated grocery price comparison system that:
- ✅ Connects to your Android phone via USB/WiFi
- ✅ Automates searches on Jumbo.cl and Lider.cl apps
- ✅ Compares prices with intelligent size normalization
- ✅ Handles promotions (2x1 deals, bulk pricing)
- ✅ Generates detailed comparison reports
- ✅ Saves you money on every grocery shop!

## 🔧 SYSTEM REQUIREMENTS
- **Windows 10/11** (you have Visual Studio ✓)
- **Android phone** with Jumbo & Lider apps installed ✓
- **USB cable** for phone connection ✓
- **Internet connection** for downloading tools

## 📥 PHASE 1: DOWNLOAD AND EXTRACT

1. **Download the system package** from the container:
   ```bash
   # Copy grocery_automation_system.tar.gz to your computer
   ```

2. **Extract to your preferred location:**
   ```bash
   # Extract to: C:\GroceryAutomation\
   # You'll have:
   # C:\GroceryAutomation\backend\
   # C:\GroceryAutomation\frontend\
   ```

## 🛠️ PHASE 2: INSTALL PREREQUISITES

### Step 1: Install Python 3.11+
1. Download from https://python.org/downloads/
2. **IMPORTANT:** Check "Add Python to PATH" during installation
3. Verify: Open Command Prompt and run `python --version`

### Step 2: Install Node.js 18+
1. Download from https://nodejs.org/
2. Install with default settings
3. Verify: Run `node --version` and `npm --version`

### Step 3: Install Java JDK 11+
1. Download from https://adoptium.net/
2. Install with default settings
3. Verify: Run `java -version`

### Step 4: Install Android SDK & ADB
**Option A: Install Android Studio (Recommended)**
1. Download from https://developer.android.com/studio
2. Install with default settings
3. This includes ADB and Android SDK

**Option B: SDK Command Line Tools Only**
1. Download from https://developer.android.com/studio#command-tools
2. Extract to C:\Android\sdk
3. Add to PATH: C:\Android\sdk\platform-tools

### Step 5: Install Appium
1. Open Command Prompt as Administrator
2. Run: `npm install -g appium`
3. Run: `appium driver install uiautomator2`
4. Verify: Run `appium --version`

## 🔧 PHASE 3: PROJECT SETUP

### Step 1: Backend Setup
```bash
cd C:\GroceryAutomation\backend
pip install -r requirements.txt
```

### Step 2: Frontend Setup
```bash
cd C:\GroceryAutomation\frontend
npm install
# or if you prefer yarn:
yarn install
```

### Step 3: Environment Configuration
1. **Backend Environment** (backend/.env):
   ```
   MONGO_URL=mongodb://localhost:27017
   DB_NAME=grocery_automation
   CORS_ORIGINS=*
   ```

2. **Frontend Environment** (frontend/.env):
   ```
   REACT_APP_BACKEND_URL=http://localhost:8001
   ```

## 🗄️ PHASE 4: DATABASE SETUP

### Install MongoDB Community Edition
1. Download from https://www.mongodb.com/try/download/community
2. Install with default settings
3. Start MongoDB service:
   ```bash
   # Windows Service should auto-start
   # Or run: net start MongoDB
   ```

## 📱 PHASE 5: ANDROID DEVICE SETUP

### Step 1: Enable Developer Options
1. Settings → About Phone → Tap "Build Number" 7 times
2. Go back → Developer Options
3. Enable "USB Debugging"
4. Enable "Stay Awake" (optional)

### Step 2: Install Required Apps
- Install **Jumbo Chile** from Google Play Store
- Install **Lider Chile** from Google Play Store
- **Log into both apps** with your credentials

### Step 3: Connect Device
1. Connect phone via USB
2. **Allow USB Debugging** when prompted
3. Test connection: `adb devices`

## 🚀 PHASE 6: LAUNCH THE SYSTEM

### Terminal 1: Start Database
```bash
# MongoDB should be running as Windows service
# If not: mongod --dbpath C:\data\db
```

### Terminal 2: Start Appium Server
```bash
appium --port 4723
```

### Terminal 3: Start Backend
```bash
cd C:\GroceryAutomation\backend
python server.py
```

### Terminal 4: Start Frontend
```bash
cd C:\GroceryAutomation\frontend
npm start
```

### Terminal 5: Test Mobile Connection
```bash
cd C:\GroceryAutomation\backend
python test_device_connection.py
```

## 🎯 PHASE 7: FIRST AUTOMATED TEST

### Test Single Product Search:
```bash
cd C:\GroceryAutomation\backend
python -c "
import asyncio
from mobile_scraper import MobileAppScraper

async def test():
    scraper = MobileAppScraper()
    results = await scraper.search_jumbo_app('Coca Cola')
    print(f'Jumbo found: {len(results)} products')
    results = await scraper.search_lider_app('Coca Cola')
    print(f'Lider found: {len(results)} products')

asyncio.run(test())
"
```

## 📊 PHASE 8: CSV AUTOMATION TEST

1. Create test CSV file (test_products.csv):
   ```csv
   Producto,Tamaño Preferido
   Coca Cola,1.5L
   Pan de molde,Grande
   Leche,1L
   ```

2. Upload via web interface: http://localhost:3000
3. Run automated comparison
4. Get detailed savings report!

## 🔧 TROUBLESHOOTING

### ADB Issues:
```bash
adb kill-server
adb start-server
adb devices
```

### Port Conflicts:
- Backend: Change port in server.py
- Frontend: Set PORT=3001 in .env
- Appium: Use --port 4724

### App Not Found:
```bash
adb shell pm list packages | grep -i jumbo
adb shell pm list packages | grep -i lider
```

## 🏆 SUCCESS INDICATORS

✅ **adb devices** shows your phone
✅ **http://localhost:3000** loads the interface
✅ **Appium server** running without errors
✅ **MongoDB** connection successful
✅ **Mobile automation** finds products in apps
✅ **Price comparison** generates savings reports

## 🎉 READY FOR AUTOMATED GROCERY SHOPPING!

Once everything is running:
1. Upload your grocery list CSV
2. Watch as the system automatically searches both apps
3. Get intelligent price comparisons
4. Save money on every shopping trip!

**The system will automatically:**
- Handle different product sizes (per liter, per kg)
- Detect and calculate promotion savings
- Generate actionable shopping recommendations
- Build optimized shopping lists for maximum savings

## 📞 NEXT STEPS AFTER INSTALLATION

1. Test with the Coca Cola example we analyzed
2. Verify it finds the same prices you found manually
3. Expand to your full grocery list
4. Set up automated weekly price monitoring
5. Enjoy effortless grocery savings! 💰

---

**Total setup time: ~30-45 minutes**
**Lifetime grocery savings: Potentially thousands of dollars!**