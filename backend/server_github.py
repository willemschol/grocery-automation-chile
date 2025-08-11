from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import asyncio
from typing import List, Dict
import os
from pymongo import MongoClient
import uuid

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

# Import mobile scraper (will be created separately)
try:
    from mobile_scraper import MobileAppScraper
    mobile_searcher = MobileAppScraper()
except ImportError:
    mobile_searcher = None
    print("Mobile scraper not available - install appium-python-client")

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
    """Search for a single product using mobile automation"""
    product_name = request.get('product_name', '')
    
    if not product_name:
        raise HTTPException(status_code=400, detail="Product name is required")
    
    if not mobile_searcher:
        raise HTTPException(status_code=500, detail="Mobile automation not available")
    
    try:
        # Search both apps using mobile automation
        jumbo_task = mobile_searcher.search_jumbo_app(product_name)
        lider_task = mobile_searcher.search_lider_app(product_name)
        
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
    """Search for all products from uploaded CSV using mobile automation"""
    list_id = request.get('list_id', '')
    
    if not list_id:
        raise HTTPException(status_code=400, detail="List ID is required")
    
    if not mobile_searcher:
        raise HTTPException(status_code=500, detail="Mobile automation not available")
    
    try:
        # Get product list from database
        product_list = db.product_lists.find_one({'_id': list_id})
        if not product_list:
            raise HTTPException(status_code=404, detail="Product list not found")
        
        results = []
        
        for product in product_list['products']:
            product_name = product['name']
            
            try:
                # Search both apps
                jumbo_task = mobile_searcher.search_jumbo_app(product_name)
                lider_task = mobile_searcher.search_lider_app(product_name)
                
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