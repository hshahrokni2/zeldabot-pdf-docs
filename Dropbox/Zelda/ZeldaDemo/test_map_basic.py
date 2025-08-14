#!/usr/bin/env python3
"""
Basic test to verify the interactive map setup works correctly.
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import json

# Test the basic setup
st.title("🧪 Interactive Map Test")
st.write("Testing basic map functionality...")

# Load test data
try:
    with open("/Users/hosseins/Dropbox/Zelda/ZeldaDemo/hammarby_map_visualization_data.json", 'r') as f:
        data = json.load(f)
    
    buildings = data.get('buildings', [])
    st.success(f"✅ Data loaded: {len(buildings)} buildings found")
    
    # Create simple map
    center = [59.305, 18.085]
    m = folium.Map(location=center, zoom_start=14)
    
    # Add a few test markers
    for i, building in enumerate(buildings[:5]):  # Just first 5 for testing
        folium.CircleMarker(
            location=[building['coordinates']['lat'], building['coordinates']['lng']],
            radius=6,
            popup=building['name'],
            tooltip=f"Click for details",
            color='red',
            fillColor='red',
            fillOpacity=0.8
        ).add_to(m)
    
    # Display map
    st.write("Interactive map test:")
    map_data = st_folium(m, width=700, height=400)
    
    if map_data['last_object_clicked_tooltip']:
        st.info(f"Clicked: {map_data['last_object_clicked_tooltip']}")
    
    st.success("✅ Map rendering works!")
    
    # Test polygon functionality
    st.write("Polygon handler test:")
    try:
        from polygon_selection_handler import PolygonSelectionHandler
        handler = PolygonSelectionHandler(buildings)
        st.success("✅ Polygon selection handler loaded!")
        
        # Test rectangle selection
        test_bounds = {
            'north': 59.308,
            'south': 59.302,
            'east': 18.110,
            'west': 18.080
        }
        
        selected = handler.select_buildings_in_rectangle(test_bounds)
        st.info(f"Test rectangle selection: {len(selected)} buildings selected")
        
    except Exception as e:
        st.error(f"❌ Polygon handler error: {e}")
    
except FileNotFoundError:
    st.error("❌ Data file not found. Please ensure hammarby_map_visualization_data.json exists.")
except json.JSONDecodeError:
    st.error("❌ Invalid JSON in data file.")
except Exception as e:
    st.error(f"❌ Unexpected error: {e}")

st.write("---")
st.write("If all tests pass, you can now run the full interactive map!")
st.code("streamlit run hammarby_interactive_map.py")