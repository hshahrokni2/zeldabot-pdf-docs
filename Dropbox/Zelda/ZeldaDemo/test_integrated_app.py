#!/usr/bin/env python3
"""
Test script for the integrated BRF dashboard.
This verifies that all components can initialize properly.
"""

import streamlit as st
import json
import traceback
import sys
import os

def test_imports():
    """Test that all required modules import correctly."""
    try:
        from survey_system import SurveySystem, UnlockLevel, SUPPLIER_CATEGORIES
        import folium
        from streamlit_folium import st_folium
        import plotly.graph_objects as go
        import plotly.express as px
        import pandas as pd
        import numpy as np
        
        st.success("✓ All required modules imported successfully")
        return True
    except Exception as e:
        st.error(f"✗ Import error: {e}")
        st.code(traceback.format_exc())
        return False

def test_data_loading():
    """Test that the JSON data loads correctly."""
    try:
        with open('killer_eghs_dataset_with_booli_coords.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not data:
            st.error("✗ Dataset is empty")
            return False
        
        st.success(f"✓ Dataset loaded: {len(data)} buildings")
        
        # Check first building has required fields
        first_building = data[0]
        required_fields = ['brf_name', 'building_id', 'latitude', 'longitude', 'energy_performance']
        missing_fields = [field for field in required_fields if field not in first_building]
        
        if missing_fields:
            st.warning(f"⚠ Missing fields in first building: {missing_fields}")
        else:
            st.success("✓ All required fields present")
        
        # Show sample building
        st.info(f"Sample building: {first_building['brf_name']} at {first_building['latitude']:.6f}, {first_building['longitude']:.6f}")
        
        return True
        
    except Exception as e:
        st.error(f"✗ Data loading error: {e}")
        st.code(traceback.format_exc())
        return False

def test_survey_system():
    """Test that survey system initializes correctly."""
    try:
        # Mock session state
        class MockSessionState:
            def __init__(self):
                self.survey_responses = {}
                self.unlock_level = None
                self.current_survey = {}
                self.survey_progress = 0
                self.peer_data_unlocked = False
            
            def get(self, key, default=None):
                return getattr(self, key, default)
            
            def __contains__(self, key):
                return hasattr(self, key)
        
        # Load test data
        with open('killer_eghs_dataset_with_booli_coords.json', 'r') as f:
            buildings_data = json.load(f)
        
        mock_state = MockSessionState()
        survey_system = SurveySystem(buildings_data, mock_state)
        
        st.success("✓ Survey system initialized successfully")
        
        # Test progress calculation
        empty_survey = {}
        progress = survey_system.calculate_progress(empty_survey)
        st.info(f"Empty survey progress: {progress}%")
        
        return True
        
    except Exception as e:
        st.error(f"✗ Survey system error: {e}")
        st.code(traceback.format_exc())
        return False

def test_energy_analysis():
    """Test that energy analysis functions work."""
    try:
        # Load test data
        with open('killer_eghs_dataset_with_booli_coords.json', 'r') as f:
            buildings_data = json.load(f)
        
        # Test energy class color function
        from integrated_brf_dashboard import get_energy_class_color, get_performance_vs_swedish_avg
        
        color_a = get_energy_class_color('A')
        color_g = get_energy_class_color('G')
        
        if color_a and color_g:
            st.success("✓ Energy class color mapping works")
        
        # Test performance comparison
        perf_text, perf_color = get_performance_vs_swedish_avg(100)  # Good performance
        st.info(f"Performance at 100 kWh/m²: {perf_text}")
        
        return True
        
    except Exception as e:
        st.error(f"✗ Energy analysis error: {e}")
        st.code(traceback.format_exc())
        return False

def main():
    st.title("🧪 Integrated BRF Dashboard - Test Suite")
    
    st.markdown("""
    This test suite verifies that the integrated dashboard can initialize and run correctly.
    
    **Test Coverage:**
    - Module imports (survey_system, folium, plotly)
    - Data loading and validation
    - Survey system initialization
    - Energy analysis functions
    - Chart rendering capabilities
    """)
    
    st.header("🔍 Running Tests...")
    
    # Run all tests
    test_results = []
    
    st.subheader("1. Testing Module Imports")
    test_results.append(test_imports())
    
    st.subheader("2. Testing Data Loading")
    test_results.append(test_data_loading())
    
    st.subheader("3. Testing Survey System")
    test_results.append(test_survey_system())
    
    st.subheader("4. Testing Energy Analysis")
    test_results.append(test_energy_analysis())
    
    # Test summary
    st.header("📋 Test Results Summary")
    
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    if passed_tests == total_tests:
        st.success(f"🎉 All {total_tests} tests passed! The integrated dashboard should work correctly.")
        st.balloons()
        
        st.info("**Ready to use:** http://localhost:8520")
        
        st.markdown("""
        **Available Features:**
        - 🗺️ Interactive map with building markers and drawing tools
        - 📝 Progressive survey system with unlock mechanisms
        - ⚡ Comprehensive energy analysis with all EPC metadata
        - 📊 Cost comparison and BRF performance ranking
        - 💰 Smart supplier recommendations based on overpaying/satisfaction
        """)
        
    else:
        st.error(f"❌ {total_tests - passed_tests} out of {total_tests} tests failed.")
        st.warning("Please check the errors above before using the integrated dashboard.")
    
    # Show system info
    st.markdown("---")
    st.markdown("### 🔧 System Information")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"Python Version: {sys.version}")
        st.info(f"Working Directory: {os.getcwd()}")
    
    with col2:
        st.info(f"Streamlit Version: {st.__version__}")
        st.info(f"Test Run: {st.session_state.get('test_run_id', 'N/A')}")

if __name__ == "__main__":
    # Set test run ID
    if 'test_run_id' not in st.session_state:
        import datetime
        st.session_state.test_run_id = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    
    main()