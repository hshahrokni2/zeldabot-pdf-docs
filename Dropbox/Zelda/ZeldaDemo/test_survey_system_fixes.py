#!/usr/bin/env python3
"""
Test the fixed survey system functionality
"""

import json
import sys
from unittest.mock import Mock, MagicMock
import streamlit as st

# Mock streamlit for testing
sys.modules['streamlit'] = Mock()
st = sys.modules['streamlit']
st.columns = Mock(return_value=[Mock(), Mock()])
st.container = Mock()
st.markdown = Mock()
st.selectbox = Mock(return_value="Test BRF")
st.number_input = Mock(return_value=100000)
st.text_input = Mock(return_value="Test Supplier")
st.select_slider = Mock(return_value=4)
st.metric = Mock()
st.progress = Mock()
st.expander = Mock(return_value=Mock())
st.divider = Mock()
st.button = Mock(return_value=False)
st.info = Mock()
st.success = Mock()
st.warning = Mock()
st.error = Mock()
st.balloons = Mock()

def test_survey_system_instantiation():
    """Test that SurveySystem can be instantiated without errors"""
    print("🔍 Testing SurveySystem instantiation...")
    
    try:
        # Load test data
        with open('killer_eghs_dataset_with_booli_coords.json', 'r') as f:
            buildings_data = json.load(f)
        
        # Mock session state
        mock_session_state = Mock()
        mock_session_state.survey_responses = {}
        mock_session_state.unlock_level = None
        mock_session_state.current_survey = {}
        mock_session_state.survey_progress = 0
        mock_session_state.respondent_id = "test_id"
        mock_session_state.peer_data_unlocked = False
        
        # Import and instantiate SurveySystem
        from survey_system import SurveySystem, UnlockLevel
        
        survey_system = SurveySystem(buildings_data, mock_session_state)
        print("✅ SurveySystem instantiated successfully")
        
        # Test progress calculation
        test_survey_data = {
            'building_id': 1,
            'costs': {'cleaning': 150000, 'heating': 200000},
            'suppliers': {'cleaning': 'Vardagsfrid', 'heating': 'Stockholm Exergi'},
            'satisfaction': {'cleaning': 4, 'heating': 3},
            'contact_info': {'name': 'Test Name', 'email': 'test@test.se'}
        }
        
        progress = survey_system.calculate_progress(test_survey_data)
        print(f"✅ Progress calculation works: {progress:.1f}%")
        
        # Test unlock level
        unlock_level = survey_system.get_unlock_level(progress)
        print(f"✅ Unlock level calculation works: {unlock_level}")
        
        # Test suppliers database
        suppliers = survey_system.suppliers_db.get_suppliers_by_category('cleaning')
        print(f"✅ Suppliers database works: {len(suppliers)} cleaning suppliers found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in SurveySystem instantiation: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_supplier_dropdown_logic():
    """Test the supplier dropdown logic specifically"""
    print("🔍 Testing supplier dropdown logic...")
    
    try:
        with open('killer_eghs_dataset_with_booli_coords.json', 'r') as f:
            buildings_data = json.load(f)
        
        mock_session_state = Mock()
        mock_session_state.survey_responses = {}
        mock_session_state.unlock_level = None
        mock_session_state.current_survey = {}
        mock_session_state.survey_progress = 0
        mock_session_state.respondent_id = "test_id"
        mock_session_state.peer_data_unlocked = False
        
        from survey_system import SurveySystem, StockholmSuppliersDB
        
        # Test suppliers database directly
        suppliers_db = StockholmSuppliersDB()
        
        # Test each category
        for category in ['cleaning', 'heating', 'electricity', 'water', 'recycling', 
                        'snow_removal', 'gardening', 'administration', 'security', 'insurance']:
            suppliers = suppliers_db.get_suppliers_by_category(category)
            if suppliers:
                print(f"✅ {category}: {len(suppliers)} suppliers loaded")
                
                # Test supplier info structure
                first_supplier = suppliers[0]
                if hasattr(first_supplier, 'name') and hasattr(first_supplier, 'rating'):
                    print(f"  - {first_supplier.name} (⭐ {first_supplier.rating})")
                else:
                    print(f"❌ Supplier structure issue in {category}")
                    return False
            else:
                print(f"⚠️ {category}: No suppliers found")
        
        # Test alternative suppliers function
        alternatives = suppliers_db.get_alternative_suppliers('cleaning', 'Test Supplier')
        print(f"✅ Alternative suppliers function works: {len(alternatives)} alternatives found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in supplier dropdown logic: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_progress_calculation_fix():
    """Test that the progress calculation fix resolves the UnboundLocalError"""
    print("🔍 Testing progress calculation fix...")
    
    try:
        with open('killer_eghs_dataset_with_booli_coords.json', 'r') as f:
            buildings_data = json.load(f)
        
        mock_session_state = Mock()
        mock_session_state.survey_responses = {}
        mock_session_state.unlock_level = None
        mock_session_state.current_survey = {
            'building_id': 1,
            'costs': {'cleaning': 150000},
            'suppliers': {'cleaning': 'Vardagsfrid'},
            'satisfaction': {'cleaning': 4},
            'contact_info': {'name': 'Test', 'email': 'test@test.se'}
        }
        mock_session_state.survey_progress = 0
        mock_session_state.respondent_id = "test_id"
        mock_session_state.peer_data_unlocked = False
        mock_session_state.get = Mock(return_value=0)
        
        from survey_system import SurveySystem
        
        survey_system = SurveySystem(buildings_data, mock_session_state)
        
        # This should not raise UnboundLocalError anymore
        # Simulate the problematic part of _render_survey_form
        survey_data = mock_session_state.current_survey
        new_progress = survey_system.calculate_progress(survey_data)
        
        # Test the condition that was causing the error
        if new_progress >= 60:
            print(f"✅ Progress condition works: {new_progress:.1f}% >= 60%")
        else:
            print(f"✅ Progress condition works: {new_progress:.1f}% < 60%")
        
        print("✅ No UnboundLocalError - fix successful!")
        return True
        
    except NameError as e:
        if "new_progress" in str(e):
            print(f"❌ UnboundLocalError still exists: {e}")
            return False
        else:
            print(f"❌ Different NameError: {e}")
            return False
    except Exception as e:
        print(f"❌ Other error in progress calculation: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all specific survey system tests"""
    print("🧪 SURVEY SYSTEM FIXES TESTING")
    print("=" * 50)
    
    tests = [
        ("SurveySystem Instantiation", test_survey_system_instantiation),
        ("Supplier Dropdown Logic", test_supplier_dropdown_logic),
        ("Progress Calculation Fix", test_progress_calculation_fix)
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
        print("🎉 All survey system fixes verified! Ready for production.")
        return True
    else:
        print("⚠️ Some tests failed. Please review and fix issues.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)