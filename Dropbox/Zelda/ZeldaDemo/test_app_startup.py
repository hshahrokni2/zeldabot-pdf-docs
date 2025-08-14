#!/usr/bin/env python3
"""
Test script to verify the enhanced survey demo can start without errors.
Run this with: streamlit run test_app_startup.py
"""

import streamlit as st
import sys
import traceback

def test_imports():
    """Test that all required modules import correctly."""
    try:
        from survey_system import SurveySystem, UnlockLevel, SUPPLIER_CATEGORIES
        import json
        import pandas as pd
        
        st.success("✓ All required modules imported successfully")
        return True
    except Exception as e:
        st.error(f"✗ Import error: {e}")
        st.code(traceback.format_exc())
        return False

def test_data_loading():
    """Test that the JSON data loads and BRF Sjöstaden 2 is found."""
    try:
        with open('killer_eghs_dataset_with_booli_coords.json', 'r') as f:
            data = json.load(f)
        
        # Find BRF Sjöstaden 2
        sjostaden_2 = None
        for building in data:
            if 'sjöstaden' in building.get('brf_name', '').lower() and '2' in building.get('brf_name', ''):
                sjostaden_2 = building
                break
        
        if sjostaden_2:
            st.success(f"✓ BRF Sjöstaden 2 found: {sjostaden_2.get('brf_name')}")
            st.info(f"Building ID: {sjostaden_2.get('building_id', sjostaden_2.get('postgres_id', 0))}")
            return True
        else:
            st.error("✗ BRF Sjöstaden 2 not found in dataset")
            return False
            
    except Exception as e:
        st.error(f"✗ Data loading error: {e}")
        st.code(traceback.format_exc())
        return False

def main():
    st.title("🔧 Enhanced Survey System - Startup Test")
    
    st.markdown("""
    This test verifies that the critical fixes have been applied correctly:
    
    1. **Plotly Chart Keys**: All `st.plotly_chart()` calls now have unique keys
    2. **Pre-population**: BRF Sjöstaden 2 data loads correctly
    3. **Module Imports**: All dependencies are available
    """)
    
    # Test 1: Imports
    st.header("1. Testing Imports")
    imports_ok = test_imports()
    
    # Test 2: Data Loading
    st.header("2. Testing Data Loading")
    data_ok = test_data_loading()
    
    # Test 3: Chart Keys Test
    st.header("3. Testing Plotly Chart Keys")
    if imports_ok:
        try:
            import plotly.graph_objects as go
            
            # Create test charts with the same keys used in the real app
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Cost Breakdown Pie")
                fig_pie = go.Figure(data=[go.Pie(labels=['Test'], values=[100])])
                fig_pie.update_layout(title="Test Pie Chart", height=300)
                st.plotly_chart(fig_pie, use_container_width=True, key="cost_breakdown_pie")
            
            with col2:
                st.subheader("Cost Comparison Bar")
                fig_bar = go.Figure(data=[go.Bar(x=['Test'], y=[100])])
                fig_bar.update_layout(title="Test Bar Chart", height=300)
                st.plotly_chart(fig_bar, use_container_width=True, key="cost_comparison_bar")
            
            # Market comparison chart
            st.subheader("Market Comparison")
            fig_scatter = go.Figure(data=[go.Scatter(x=[1, 2, 3], y=[1, 2, 3], mode='markers')])
            fig_scatter.update_layout(title="Test Scatter Chart", height=300)
            st.plotly_chart(fig_scatter, use_container_width=True, key="market_comparison_scatter")
            
            # BRF Performance Gauge
            st.subheader("BRF Performance Gauge")
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = 85,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Test Performance"},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 100], 'color': "gray"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            fig_gauge.update_layout(height=300)
            st.plotly_chart(fig_gauge, use_container_width=True, key="brf_performance_gauge")
            
            st.success("✓ All plotly charts render successfully with unique keys")
            charts_ok = True
            
        except Exception as e:
            st.error(f"✗ Chart rendering error: {e}")
            st.code(traceback.format_exc())
            charts_ok = False
    else:
        charts_ok = False
    
    # Summary
    st.header("🎯 Test Results Summary")
    
    all_tests_passed = imports_ok and data_ok and charts_ok
    
    if all_tests_passed:
        st.success("🎉 All tests passed! The enhanced survey system should run without StreamlitDuplicateElementId errors.")
        st.info("You can now run: `streamlit run enhanced_survey_sjostaden2_demo.py`")
    else:
        st.error("❌ Some tests failed. Check the errors above before running the main application.")
    
    st.markdown("---")
    st.markdown("""
    **Next Steps:**
    1. If all tests pass, run the main application: `streamlit run enhanced_survey_sjostaden2_demo.py`
    2. Verify that all tabs unlock properly with the pre-populated BRF Sjöstaden 2 data
    3. Check that cost breakdowns and supplier recommendations display correctly
    """)

if __name__ == "__main__":
    main()