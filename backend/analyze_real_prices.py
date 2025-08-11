# REAL PRICE DATA FROM USER'S APPS
# Data collected from Jumbo and Lider apps for Coca Cola Zero 1.5L

REAL_PRODUCTS_DATA = {
    "Coca Cola Zero": {
        "jumbo": {
            "found": True,
            "name": "Coca Cola Zero 1,5L", 
            "price": 2090,  # Single unit price
            "size": "1.5L",
            "promotion": {
                "has_promo": True,
                "promo_description": "2 units for $3.090",
                "promo_total": 3090,
                "promo_quantity": 2,
                "promo_unit_price": 1545  # 3090 / 2 = 1545
            }
        },
        "lider": {
            "found": True,
            "name": "Coca Cola Zero 1,5L",
            "price": 1990,  # Single unit price  
            "size": "1.5L",
            "promotion": {
                "has_promo": False
            }
        }
    }
}

# Run comparison analysis
if __name__ == "__main__":
    import sys
    sys.path.append('/app/backend')
    from hybrid_comparison import HybridGroceryComparison
    
    print("🔍 ANALYZING REAL PRICE DATA FROM YOUR APPS")
    print("=" * 60)
    
    comparator = HybridGroceryComparison()
    
    # Standard comparison (without promotions)
    print("📊 STANDARD COMPARISON (Single Unit):")
    standard_data = {
        "Coca Cola Zero": {
            "jumbo": {"found": True, "name": "Coca Cola Zero 1,5L", "price": 2090, "size": "1.5L"},
            "lider": {"found": True, "name": "Coca Cola Zero 1,5L", "price": 1990, "size": "1.5L"}
        }
    }
    
    standard_result = comparator.compare_products(standard_data)
    comparator.print_comparison_report(standard_result)
    
    # Promotion comparison (bulk pricing)
    print("\n" + "="*60)
    print("🎁 PROMOTION ANALYSIS (Jumbo 2x1 Deal):")
    promo_data = {
        "Coca Cola Zero": {
            "jumbo": {"found": True, "name": "Coca Cola Zero 1,5L (2x promo)", "price": 1545, "size": "1.5L"},
            "lider": {"found": True, "name": "Coca Cola Zero 1,5L", "price": 1990, "size": "1.5L"}
        }
    }
    
    promo_result = comparator.compare_products(promo_data)
    comparator.print_comparison_report(promo_result)
    
    print("\n" + "="*60)
    print("💡 INTELLIGENT RECOMMENDATION:")
    
    single_jumbo = 2090
    bulk_jumbo = 1545  # per unit in 2-pack
    single_lider = 1990
    
    print(f"🟠 Jumbo Single Unit: ${single_jumbo:,}")
    print(f"🟠 Jumbo Bulk Deal (2 units): ${bulk_jumbo:,} per unit")
    print(f"🔴 Lider Single Unit: ${single_lider:,}")
    
    best_option = "Jumbo bulk deal"
    savings_vs_lider = single_lider - bulk_jumbo
    savings_percent = (savings_vs_lider / single_lider) * 100
    
    print(f"\n🏆 WINNER: {best_option}")
    print(f"💰 SAVINGS: ${savings_vs_lider:,} per unit ({savings_percent:.1f}% cheaper than Lider)")
    
    total_savings_2_units = savings_vs_lider * 2
    print(f"📈 If buying 2 units: Total savings of ${total_savings_2_units:,}")
    
    print(f"\n🎯 RECOMMENDATION:")
    if savings_percent > 15:
        print("🔥 EXCELLENT DEAL! Jumbo's promotion offers significant savings.")
        print("💡 Buy 2 units from Jumbo to maximize savings.")
    else:
        print("👍 Good deal at Jumbo with bulk purchase.")
    
    print(f"\n📋 SHOPPING STRATEGY:")
    print("• If you need 1 unit: Buy from Lider ($1.990)")  
    print("• If you can buy 2 units: Buy from Jumbo ($3.090 total)")
    print("• If you drink lots of Coca Cola: Stock up at Jumbo!")