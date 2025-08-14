#!/usr/bin/env python3
"""
Test that the survey system can be imported without errors and basic functionality works
"""

import sys

def test_survey_imports():
    """Test that survey system imports correctly"""
    print("🔍 Testing survey system imports...")
    
    try:
        from survey_system import (
            SurveySystem, 
            UnlockLevel, 
            SurveyResponse, 
            StockholmSuppliersDB,
            COST_CATEGORIES,
            SUPPLIER_CATEGORIES
        )
        print("✅ All survey system classes and constants imported successfully")
        
        # Test basic instantiation of suppliers database
        suppliers_db = StockholmSuppliersDB()
        print("✅ StockholmSuppliersDB instantiated successfully")
        
        # Test that it can load suppliers
        cleaning_suppliers = suppliers_db.get_suppliers_by_category('cleaning')
        print(f"✅ Retrieved {len(cleaning_suppliers)} cleaning suppliers")
        
        if cleaning_suppliers:
            first_supplier = cleaning_suppliers[0]
            print(f"  - Example: {first_supplier.name} (⭐ {first_supplier.rating})")
        
        # Test constants
        print(f"✅ {len(COST_CATEGORIES)} cost categories defined")
        print(f"✅ {len(SUPPLIER_CATEGORIES)} supplier categories defined")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_supplier_database():
    """Test supplier database functionality specifically"""
    print("🔍 Testing supplier database functionality...")
    
    try:
        from survey_system import StockholmSuppliersDB
        
        db = StockholmSuppliersDB()
        
        # Test all categories
        all_supplier_count = 0
        for category in ['cleaning', 'heating', 'electricity', 'water', 'recycling', 
                        'snow_removal', 'gardening', 'administration', 'security', 'insurance']:
            suppliers = db.get_suppliers_by_category(category)
            all_supplier_count += len(suppliers)
            print(f"  ✅ {category}: {len(suppliers)} suppliers")
            
            if suppliers:
                # Test alternative suppliers function
                alternatives = db.get_alternative_suppliers(category, "Test Supplier")
                print(f"    → {len(alternatives)} alternatives available")
        
        print(f"✅ Total suppliers in database: {all_supplier_count}")
        return True
        
    except Exception as e:
        print(f"❌ Error in supplier database testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_syntax_and_structure():
    """Test that the file can be parsed and has correct syntax"""
    print("🔍 Testing syntax and structure...")
    
    try:
        # This tests that the file can be compiled without syntax errors
        with open('survey_system.py', 'r') as f:
            content = f.read()
        
        compile(content, 'survey_system.py', 'exec')
        print("✅ survey_system.py has valid Python syntax")
        
        # Check for the specific fix - new_progress should be calculated before use
        lines = content.split('\n')
        new_progress_calculation_line = None
        new_progress_usage_line = None
        
        for i, line in enumerate(lines):
            if 'new_progress = self.calculate_progress(' in line:
                new_progress_calculation_line = i + 1
            elif 'if new_progress >= 60:' in line and new_progress_calculation_line is None:
                new_progress_usage_line = i + 1
        
        if new_progress_calculation_line and new_progress_usage_line:
            if new_progress_calculation_line < new_progress_usage_line:
                print(f"✅ new_progress calculation (line {new_progress_calculation_line}) comes before usage (line {new_progress_usage_line})")
            else:
                print(f"❌ new_progress usage (line {new_progress_usage_line}) comes before calculation (line {new_progress_calculation_line})")
                return False
        elif new_progress_calculation_line:
            print("✅ new_progress calculation found, no early usage detected")
        else:
            print("❌ Could not find new_progress calculation or usage lines")
            return False
        
        return True
        
    except SyntaxError as e:
        print(f"❌ Syntax error in survey_system.py: {e}")
        return False
    except Exception as e:
        print(f"❌ Error during syntax checking: {e}")
        return False

def main():
    """Run all import and structure tests"""
    print("🧪 SURVEY SYSTEM IMPORT & STRUCTURE TESTING")
    print("=" * 60)
    
    tests = [
        ("Survey System Imports", test_survey_imports),
        ("Supplier Database", test_supplier_database),
        ("Syntax and Structure", test_syntax_and_structure)
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
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name:.<40} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 Survey system structure and imports are working correctly!")
        return True
    else:
        print("⚠️ Some tests failed. Please review and fix issues.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)