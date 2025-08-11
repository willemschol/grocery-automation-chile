from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import asyncio
import aiohttp
from playwright.async_api import async_playwright
import re
import json
from typing import List, Dict, Optional
import os
from pymongo import MongoClient
import uuid

# Set Playwright browsers path
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '/pw-browsers'

# Database setup
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/')
client = MongoClient(mongo_url)
db = client.grocery_automation

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProductSearcher:
    def __init__(self):
        self.session = None
        
    async def create_browser_session(self):
        """Create a new browser session with anti-detection measures"""
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        return playwright, browser, context, page
        
    async def search_jumbo(self, product_name: str) -> List[Dict]:
        """Search for products on jumbo.cl"""
        try:
            playwright, browser, context, page = await self.create_browser_session()
            
            # Navigate to Jumbo
            await page.goto('https://www.jumbo.cl/')
            await page.wait_for_timeout(3000)
            
            # Search for product using correct selector
            search_box = await page.wait_for_selector('.search-box', timeout=15000)
            await search_box.fill(product_name)
            
            # Click search button
            search_btn = await page.wait_for_selector('.search-btn', timeout=10000)
            await search_btn.click()
            
            # Wait for results page to load
            await page.wait_for_timeout(4000)
            
            # Extract product information
            products = []
            try:
                # Try multiple product card selectors for Jumbo
                product_selectors = [
                    '[data-testid="product-card"]',
                    '.product-item',
                    '.shelf-item', 
                    '.product-card',
                    '.item-product',
                    '[class*="product"]'
                ]
                
                product_cards = []
                for selector in product_selectors:
                    product_cards = await page.query_selector_all(selector)
                    if product_cards:
                        print(f"Found {len(product_cards)} products using selector: {selector}")
                        break
                
                for card in product_cards[:10]:  # Limit to first 10 results
                    try:
                        # Get product name - try multiple selectors
                        name = "Unknown"
                        name_selectors = [
                            '[data-testid="product-title"]',
                            '.product-name', 
                            '.product-title',
                            'h3', 'h4', '.title',
                            '[class*="name"]',
                            '[class*="title"]'
                        ]
                        
                        for selector in name_selectors:
                            name_element = await card.query_selector(selector)
                            if name_element:
                                name = await name_element.inner_text()
                                if name and name.strip():
                                    break
                        
                        # Get price - try multiple selectors
                        price_text = "$0"
                        price_selectors = [
                            '[data-testid="product-price"]',
                            '.price', 
                            '.product-price', 
                            '.price-current',
                            '[class*="price"]',
                            '.precio'
                        ]
                        
                        for selector in price_selectors:
                            price_element = await card.query_selector(selector)
                            if price_element:
                                price_text = await price_element.inner_text()
                                if price_text and price_text.strip():
                                    break
                        
                        # Extract numeric price (handle Chilean format)
                        price = 0
                        if price_text:
                            # Remove common Chilean price formatting
                            clean_price = price_text.replace('$', '').replace('.', '').replace(',', '.').replace(' ', '')
                            price_match = re.search(r'[\d,\.]+', clean_price)
                            if price_match:
                                try:
                                    price = float(price_match.group().replace(',', ''))
                                except:
                                    price = 0
                        
                        # Get product URL
                        link_element = await card.query_selector('a')
                        product_url = await link_element.get_attribute('href') if link_element else ""
                        if product_url and product_url.startswith('/'):
                            product_url = f"https://www.jumbo.cl{product_url}"
                        
                        if name != "Unknown" and price > 0:
                            products.append({
                                'name': name.strip(),
                                'price': price,
                                'price_text': price_text,
                                'url': product_url,
                                'store': 'Jumbo'
                            })
                    except Exception as e:
                        print(f"Error extracting product from card: {e}")
                        continue
                        
            except Exception as e:
                print(f"Error extracting Jumbo products: {e}")
                
            await browser.close()
            await playwright.stop()
            
            print(f"Jumbo search for '{product_name}' found {len(products)} products")
            return products
            
        except Exception as e:
            print(f"Error searching Jumbo: {e}")
            return []
    
    async def search_lider(self, product_name: str) -> List[Dict]:
        """Search for products on lider.cl"""
        try:
            playwright, browser, context, page = await self.create_browser_session()
            
            # Navigate to Lider
            await page.goto('https://www.lider.cl/')
            await page.wait_for_timeout(2000)
            
            # Search for product
            search_box = await page.wait_for_selector('input[placeholder*="Buscar"], input[placeholder*="buscar"], .search-input', timeout=10000)
            await search_box.fill(product_name)
            await page.keyboard.press('Enter')
            
            # Wait for results
            await page.wait_for_timeout(3000)
            
            # Extract product information
            products = []
            try:
                # Try different selectors for Lider product cards
                product_selectors = [
                    '.product-item',
                    '[data-testid*="product"]',
                    '.shelf-item',
                    '.product-card'
                ]
                
                product_cards = []
                for selector in product_selectors:
                    product_cards = await page.query_selector_all(selector)
                    if product_cards:
                        break
                
                for card in product_cards[:10]:  # Limit to first 10 results
                    try:
                        # Get product name - try multiple selectors
                        name = "Unknown"
                        name_selectors = ['.product-name', '.product-title', 'h3', 'h4', '.title']
                        for selector in name_selectors:
                            name_element = await card.query_selector(selector)
                            if name_element:
                                name = await name_element.inner_text()
                                break
                        
                        # Get price - try multiple selectors
                        price_text = "$0"
                        price_selectors = ['.price', '.product-price', '.price-current', '[data-testid*="price"]']
                        for selector in price_selectors:
                            price_element = await card.query_selector(selector)
                            if price_element:
                                price_text = await price_element.inner_text()
                                break
                        
                        # Extract numeric price
                        price_match = re.search(r'[\$\d.,]+', price_text.replace('.', '').replace(',', '.'))
                        price = float(price_match.group().replace('$', '').replace('.', '').replace(',', '.')) if price_match else 0
                        
                        # Get product URL
                        link_element = await card.query_selector('a')
                        product_url = await link_element.get_attribute('href') if link_element else ""
                        
                        products.append({
                            'name': name.strip(),
                            'price': price,
                            'price_text': price_text,
                            'url': f"https://www.lider.cl{product_url}" if product_url.startswith('/') else product_url,
                            'store': 'Lider'
                        })
                    except Exception as e:
                        continue
                        
            except Exception as e:
                print(f"Error extracting Lider products: {e}")
                
            await browser.close()
            await playwright.stop()
            
            return products
            
        except Exception as e:
            print(f"Error searching Lider: {e}")
            return []

# Global searcher instance
searcher = ProductSearcher()

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Grocery automation system is running"}

@app.post("/api/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    """Upload and process CSV file with product list"""
    try:
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV")
        
        # Read CSV content
        content = await file.read()
        
        # Parse CSV
        try:
            df = pd.read_csv(pd.io.common.StringIO(content.decode('utf-8')))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error parsing CSV: {str(e)}")
        
        # Validate CSV structure
        if len(df.columns) < 2:
            raise HTTPException(status_code=400, detail="CSV must have at least 2 columns: Product Name, Preferred Size")
        
        # Process products
        products = []
        for index, row in df.iterrows():
            product_name = str(row.iloc[0]).strip()
            preferred_size = str(row.iloc[1]).strip() if len(row) > 1 else "any"
            
            if product_name and product_name.lower() != 'nan':
                products.append({
                    'id': str(uuid.uuid4()),
                    'name': product_name,
                    'preferred_size': preferred_size,
                    'status': 'pending'
                })
        
        if not products:
            raise HTTPException(status_code=400, detail="No valid products found in CSV")
        
        # Store in database
        result = db.product_lists.insert_one({
            'id': str(uuid.uuid4()),
            'products': products,
            'created_at': pd.Timestamp.now().isoformat(),
            'status': 'uploaded'
        })
        
        return {
            'message': f'Successfully uploaded {len(products)} products',
            'products': products,
            'list_id': str(result.inserted_id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/api/search-product")
async def search_product(request: dict):
    """Search for a single product on both sites"""
    product_name = request.get('product_name', '')
    
    if not product_name:
        raise HTTPException(status_code=400, detail="Product name is required")
    
    try:
        # Search both sites concurrently
        jumbo_task = searcher.search_jumbo(product_name)
        lider_task = searcher.search_lider(product_name)
        
        jumbo_results, lider_results = await asyncio.gather(jumbo_task, lider_task)
        
        return {
            'product_name': product_name,
            'jumbo_results': jumbo_results,
            'lider_results': lider_results,
            'total_found': len(jumbo_results) + len(lider_results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching product: {str(e)}")

@app.post("/api/search-all-products")
async def search_all_products(request: dict):
    """Search for all products from uploaded CSV"""
    list_id = request.get('list_id', '')
    
    if not list_id:
        raise HTTPException(status_code=400, detail="List ID is required")
    
    try:
        # Get product list from database
        from bson import ObjectId
        try:
            # Try to find by MongoDB ObjectId first
            product_list = db.product_lists.find_one({'_id': ObjectId(list_id)})
        except:
            # If that fails, try to find by custom id field
            product_list = db.product_lists.find_one({'id': list_id})
        if not product_list:
            raise HTTPException(status_code=404, detail="Product list not found")
        
        results = []
        
        for product in product_list['products']:
            product_name = product['name']
            
            try:
                # Search both sites
                jumbo_task = searcher.search_jumbo(product_name)
                lider_task = searcher.search_lider(product_name)
                
                jumbo_results, lider_results = await asyncio.gather(jumbo_task, lider_task)
                
                # Find best matches and compare prices
                best_jumbo = min(jumbo_results, key=lambda x: x['price']) if jumbo_results else None
                best_lider = min(lider_results, key=lambda x: x['price']) if lider_results else None
                
                cheaper_option = None
                if best_jumbo and best_lider:
                    cheaper_option = best_jumbo if best_jumbo['price'] < best_lider['price'] else best_lider
                elif best_jumbo:
                    cheaper_option = best_jumbo
                elif best_lider:
                    cheaper_option = best_lider
                
                results.append({
                    'product': product,
                    'jumbo_results': jumbo_results,
                    'lider_results': lider_results,
                    'best_jumbo': best_jumbo,
                    'best_lider': best_lider,
                    'cheaper_option': cheaper_option,
                    'price_difference': abs(best_jumbo['price'] - best_lider['price']) if best_jumbo and best_lider else 0
                })
                
            except Exception as e:
                results.append({
                    'product': product,
                    'error': str(e),
                    'jumbo_results': [],
                    'lider_results': []
                })
        
        return {
            'results': results,
            'total_products': len(results),
            'successful_searches': len([r for r in results if 'error' not in r])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching products: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)