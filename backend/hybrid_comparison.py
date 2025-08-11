#!/usr/bin/env python3
"""
Hybrid Manual-Automated Grocery Price Comparison
Combines manual price collection with automated intelligent comparison
"""

import json
import sys
import uuid
from typing import List, Dict
import requests
import pandas as pd

class HybridGroceryComparison:
    """Hybrid system for manual price input + automated comparison"""
    
    def __init__(self, backend_url="http://localhost:8001"):
        self.backend_url = backend_url
        
    def create_manual_price_entry_template(self, products: List[str]) -> str:
        """Create a template for manual price entry"""
        
        template = """# MANUAL PRICE COLLECTION TEMPLATE
# Instructions:
# 1. Open both Jumbo and Lider apps on your phone
# 2. Search for each product below
# 3. Fill in the prices you find (use 0 if not found)
# 4. Save this file and run the comparison

PRODUCTS_WITH_PRICES = {
"""
        
        for product in products:
            template += f"""    "{product}": {{
        "jumbo": {{
            "found": False,  # Change to True if found
            "name": "",      # Exact product name you see
            "price": 0,      # Price in CLP (Chilean pesos)
            "size": "",      # Size (e.g., "500ml", "1L", "1kg")
        }},
        "lider": {{
            "found": False,  # Change to True if found  
            "name": "",      # Exact product name you see
            "price": 0,      # Price in CLP (Chilean pesos)
            "size": "",      # Size (e.g., "500ml", "1L", "1kg")
        }}
    }},
"""
        
        template += "}\n\n# After filling this out, run: python hybrid_comparison.py"
        
        return template
        
    def normalize_price_per_unit(self, price: float, size: str) -> float:
        """Calculate price per standard unit (per liter, per kg, etc.)"""
        try:
            size_lower = size.lower()
            
            # Extract numeric value
            import re
            numbers = re.findall(r'[\d,\.]+', size_lower)
            if not numbers:
                return price  # Can't normalize, return original
                
            size_value = float(numbers[0].replace(',', '.'))
            
            # Normalize to standard units
            if 'ml' in size_lower:
                # Convert to per liter
                return (price / size_value) * 1000
            elif 'l' in size_lower and 'ml' not in size_lower:
                # Already per liter
                return price / size_value
            elif 'g' in size_lower and 'kg' not in size_lower:
                # Convert to per kg
                return (price / size_value) * 1000
            elif 'kg' in size_lower:
                # Already per kg
                return price / size_value
            else:
                # Unknown unit, return original price
                return price
                
        except Exception:
            return price
    
    def compare_products(self, products_data: Dict) -> Dict:
        """Compare products and find best deals"""
        comparison_results = []
        
        for product_name, stores in products_data.items():
            result = {
                "product": product_name,
                "jumbo": stores.get("jumbo", {}),
                "lider": stores.get("lider", {}),
                "comparison": {}
            }
            
            jumbo_data = stores.get("jumbo", {})
            lider_data = stores.get("lider", {})
            
            # Check if both products found
            jumbo_found = jumbo_data.get("found", False)
            lider_found = lider_data.get("found", False)
            
            if not jumbo_found and not lider_found:
                result["comparison"] = {
                    "status": "not_found",
                    "message": "Product not found in either store"
                }
            elif jumbo_found and not lider_found:
                result["comparison"] = {
                    "status": "jumbo_only",
                    "winner": "Jumbo",
                    "message": "Only available at Jumbo"
                }
            elif lider_found and not jumbo_found:
                result["comparison"] = {
                    "status": "lider_only", 
                    "winner": "Lider",
                    "message": "Only available at Lider"
                }
            else:
                # Both found - do intelligent comparison
                jumbo_price = jumbo_data.get("price", 0)
                lider_price = lider_data.get("price", 0)
                
                jumbo_size = jumbo_data.get("size", "")
                lider_size = lider_data.get("size", "")
                
                # Calculate normalized prices (per unit)
                jumbo_per_unit = self.normalize_price_per_unit(jumbo_price, jumbo_size)
                lider_per_unit = self.normalize_price_per_unit(lider_price, lider_size)
                
                # Determine winner
                if jumbo_per_unit < lider_per_unit:
                    winner = "Jumbo"
                    savings = lider_per_unit - jumbo_per_unit
                    savings_percent = (savings / lider_per_unit) * 100
                elif lider_per_unit < jumbo_per_unit:
                    winner = "Lider"
                    savings = jumbo_per_unit - lider_per_unit
                    savings_percent = (savings / jumbo_per_unit) * 100
                else:
                    winner = "Tie"
                    savings = 0
                    savings_percent = 0
                
                result["comparison"] = {
                    "status": "compared",
                    "winner": winner,
                    "jumbo_per_unit": round(jumbo_per_unit, 2),
                    "lider_per_unit": round(lider_per_unit, 2),
                    "savings_per_unit": round(savings, 2),
                    "savings_percent": round(savings_percent, 1),
                    "recommendation": self._generate_recommendation(winner, savings_percent, jumbo_data, lider_data)
                }
            
            comparison_results.append(result)
        
        return {
            "results": comparison_results,
            "summary": self._generate_summary(comparison_results)
        }
    
    def _generate_recommendation(self, winner: str, savings_percent: float, jumbo_data: Dict, lider_data: Dict) -> str:
        """Generate human-readable recommendation"""
        if winner == "Tie":
            return "Both options have the same value. Choose based on convenience."
        elif savings_percent < 5:
            return f"{winner} is slightly cheaper ({savings_percent:.1f}% savings). Minimal difference."
        elif savings_percent < 15:
            return f"{winner} is noticeably cheaper ({savings_percent:.1f}% savings). Good deal!"
        else:
            return f"{winner} is significantly cheaper ({savings_percent:.1f}% savings). Excellent deal!"
    
    def _generate_summary(self, results: List[Dict]) -> Dict:
        """Generate summary statistics"""
        total_products = len(results)
        jumbo_wins = len([r for r in results if r["comparison"].get("winner") == "Jumbo"])
        lider_wins = len([r for r in results if r["comparison"].get("winner") == "Lider"])
        ties = len([r for r in results if r["comparison"].get("winner") == "Tie"])
        not_found = len([r for r in results if r["comparison"].get("status") == "not_found"])
        
        return {
            "total_products": total_products,
            "jumbo_wins": jumbo_wins,
            "lider_wins": lider_wins,
            "ties": ties,
            "not_found": not_found,
            "jumbo_advantage": f"{(jumbo_wins/max(1,total_products-not_found))*100:.1f}%",
            "lider_advantage": f"{(lider_wins/max(1,total_products-not_found))*100:.1f}%"
        }
    
    def print_comparison_report(self, comparison_data: Dict):
        """Print a beautiful comparison report"""
        print("🛒 GROCERY PRICE COMPARISON REPORT")
        print("=" * 60)
        
        results = comparison_data["results"]
        summary = comparison_data["summary"]
        
        for result in results:
            product = result["product"]
            comparison = result["comparison"]
            
            print(f"\n📦 {product.upper()}")
            print("-" * 40)
            
            if comparison["status"] == "not_found":
                print("❌ Not found in either store")
            elif comparison["status"] == "jumbo_only":
                jumbo = result["jumbo"]
                print(f"🟠 Jumbo Only: {jumbo['name']} - ${jumbo['price']:,} ({jumbo['size']})")
            elif comparison["status"] == "lider_only":
                lider = result["lider"]
                print(f"🔴 Lider Only: {lider['name']} - ${lider['price']:,} ({lider['size']})")
            else:
                # Full comparison
                jumbo = result["jumbo"] 
                lider = result["lider"]
                comp = comparison
                
                print(f"🟠 Jumbo: {jumbo['name']} - ${jumbo['price']:,} ({jumbo['size']})")
                print(f"   Per unit: ${comp['jumbo_per_unit']:,}")
                print(f"🔴 Lider: {lider['name']} - ${lider['price']:,} ({lider['size']})")
                print(f"   Per unit: ${comp['lider_per_unit']:,}")
                
                winner_emoji = "🏆" if comp["winner"] != "Tie" else "🤝"
                print(f"{winner_emoji} WINNER: {comp['winner']}")
                print(f"💡 {comp['recommendation']}")
        
        print("\n" + "=" * 60)
        print("📊 SUMMARY")
        print(f"Total products compared: {summary['total_products']}")
        print(f"🟠 Jumbo wins: {summary['jumbo_wins']} ({summary['jumbo_advantage']})")
        print(f"🔴 Lider wins: {summary['lider_wins']} ({summary['lider_advantage']})")
        print(f"🤝 Ties: {summary['ties']}")
        print(f"❌ Not found: {summary['not_found']}")


def main():
    """Main function for manual testing"""
    print("🤖 Hybrid Grocery Comparison System")
    print("=" * 50)
    
    # Sample data for demonstration
    sample_products = ["Coca Cola", "Pan de molde", "Leche", "Aceite", "Arroz"]
    
    comparator = HybridGroceryComparison()
    
    # Create template for manual entry
    template = comparator.create_manual_price_entry_template(sample_products)
    
    # Save template file
    with open('/app/backend/manual_prices_template.py', 'w') as f:
        f.write(template)
    
    print("✅ Created manual price entry template")
    print("📄 File: /app/backend/manual_prices_template.py")
    print("\n🔍 NEXT STEPS:")
    print("1. Open both Jumbo and Lider apps")
    print("2. Search for each product:")
    for i, product in enumerate(sample_products, 1):
        print(f"   {i}. {product}")
    print("3. Edit the template file with the prices you find")
    print("4. Run comparison analysis")
    
    # Demo with sample data
    print("\n🧪 DEMO WITH SAMPLE DATA:")
    sample_data = {
        "Coca Cola": {
            "jumbo": {"found": True, "name": "Coca Cola 500ml", "price": 1290, "size": "500ml"},
            "lider": {"found": True, "name": "Coca Cola 500ml", "price": 1390, "size": "500ml"}
        },
        "Leche": {
            "jumbo": {"found": True, "name": "Leche Soprole 1L", "price": 990, "size": "1L"},
            "lider": {"found": True, "name": "Leche Colun 1L", "price": 1090, "size": "1L"}
        }
    }
    
    comparison_result = comparator.compare_products(sample_data)
    comparator.print_comparison_report(comparison_result)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())