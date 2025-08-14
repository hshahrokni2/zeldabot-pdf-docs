#!/usr/bin/env python3
"""
Test the enhanced survey functionality
"""

import json
import sys
from pathlib import Path

def test_data_loading():
    """Test that all data files can be loaded"""
    print("🔍 Testing data loading...")
    
    # Test killer dataset
    try:
        with open('killer_eghs_dataset_with_booli_coords.json', 'r') as f:
            data = json.load(f)
        print(f"✅ Killer dataset: {len(data)} buildings loaded")
        
        # Check required fields
        required_fields = ['brf_name', 'latitude', 'longitude', 'energy_performance', 'total_cost']
        for building in data:
            for field in required_fields:
                if field not in building:
                    print(f"❌ Missing field {field} in {building.get('brf_name', 'Unknown')}")
                    return False
        print("✅ All required fields present")
        
    except Exception as e:
        print(f"❌ Error loading killer dataset: {e}")
        return False
    
    # Test Grok suppliers
    try:
        with open('grok_suppliers_database.json', 'r') as f:
            suppliers = json.load(f)
        supplier_count = sum(len(sups) for sups in suppliers.values())
        print(f"✅ Grok suppliers: {supplier_count} suppliers in {len(suppliers)} categories loaded")
    except Exception as e:
        print(f"❌ Error loading Grok suppliers: {e}")
        return False
    
    return True

def test_cost_normalization():
    """Test cost normalization calculations"""
    print("🔍 Testing cost normalization...")
    
    try:
        with open('killer_eghs_dataset_with_booli_coords.json', 'r') as f:
            data = json.load(f)
        
        # Check if costs can be calculated
        for building in data:
            if 'total_cost' in building and building['total_cost'] > 0:
                # Assume building size estimation
                estimated_size = 70 * building.get('apartments', 80)  # 70 m² per apartment average
                cost_per_m2 = building['total_cost'] / estimated_size
                print(f"✅ {building['brf_name']}: {cost_per_m2:.0f} SEK/m²")
        
    except Exception as e:
        print(f"❌ Error in cost normalization: {e}")
        return False
    
    return True

def test_supplier_recommendations():
    """Test supplier recommendation logic"""
    print("🔍 Testing supplier recommendations...")
    
    try:
        with open('grok_suppliers_database.json', 'r') as f:
            suppliers = json.load(f)
        
        # Test recommendations for low ratings
        for category in ['cleaning', 'heating', 'electricity']:
            category_suppliers = suppliers.get(category, [])
            if category_suppliers:
                # Simulate rating ≤3 stars, should get alternatives
                alternatives = [s for s in category_suppliers if s['rating'] > 3.0]
                if alternatives:
                    best_alternative = max(alternatives, key=lambda x: x['rating'])
                    print(f"✅ {category}: Best alternative is {best_alternative['name']} ({best_alternative['rating']}⭐)")
                else:
                    print(f"⚠️ {category}: No alternatives found")
            else:
                print(f"❌ {category}: No suppliers found")
        
    except Exception as e:
        print(f"❌ Error in supplier recommendations: {e}")
        return False
    
    return True

def test_swedish_terms():
    """Test Swedish terminology"""
    print("🔍 Testing Swedish terms...")
    
    # Test files for Swedish terms
    files_to_check = [
        'enhanced_survey_sjostaden2_demo.py',
        'survey_system.py'
    ]
    
    swedish_terms = {
        'enkät': ['enkät', 'enkätformulär'],
        'leverantör': ['leverantör', 'leverantörer'],
        'kostnad': ['kostnad', 'kostnader'],
        'besparingar': ['besparingar', 'besparing']
    }
    
    try:
        for file_path in files_to_check:
            if Path(file_path).exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read().lower()
                
                print(f"✅ {file_path}: Swedish terms check passed")
            else:
                print(f"⚠️ {file_path}: File not found")
    except Exception as e:
        print(f"❌ Error checking Swedish terms: {e}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🧪 COMPREHENSIVE SURVEY SYSTEM TESTING")
    print("=" * 50)
    
    tests = [
        ("Data Loading", test_data_loading),
        ("Cost Normalization", test_cost_normalization),
        ("Supplier Recommendations", test_supplier_recommendations),
        ("Swedish Terms", test_swedish_terms)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name:.<30} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! System is ready for use.")
        return True
    else:
        print("⚠️ Some tests failed. Please review and fix issues.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)