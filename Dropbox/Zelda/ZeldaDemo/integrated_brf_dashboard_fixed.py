#!/usr/bin/env python3
"""
Integrated BRF Dashboard
=======================

A comprehensive interactive dashboard that combines:
1. Interactive map with polygon selection and building markers
2. Enhanced survey system for cost data collection
3. Comprehensive energy performance analysis with all EPC metadata
4. Smart supplier recommendations and cost analysis
5. Multi-agent Claudette team architecture

Features:
- Interactive Folium map with drawing tools
- Progressive survey system with unlock mechanisms  
- Complete EPC metadata visualization
- Financial performance indexing
- Real Stockholm supplier database
- BRF comparison and ranking systems
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from survey_system import SurveySystem, UnlockLevel, SUPPLIER_CATEGORIES
import uuid

# Page configuration
st.set_page_config(
    page_title="Integrated BRF Dashboard - Hammarby Sjöstad",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #1f4e79;
        margin: 10px 0;
    }
    .energy-class-A { background: #22c55e !important; color: white; }
    .energy-class-B { background: #84cc16 !important; color: white; }
    .energy-class-C { background: #eab308 !important; color: white; }
    .energy-class-D { background: #f59e0b !important; color: white; }
    .energy-class-E { background: #f97316 !important; color: white; }
    .energy-class-F { background: #dc2626 !important; color: white; }
    .energy-class-G { background: #991b1b !important; color: white; }
    
    .selected-building {
        border: 2px solid #ff4b4b;
        background-color: #fff5f5;
        border-radius: 8px;
        padding: 10px;
        margin: 5px 0;
    }
    .energy-metadata {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #28a745;
    }
    .epc-card {
        background: white;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_buildings_data():
    """Load and cache the complete buildings dataset."""
    try:
        with open('killer_eghs_dataset_with_booli_coords.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Transform data for consistency
        transformed_data = []
        for building in data:
            transformed_data.append({
                'id': building.get('building_id', building.get('postgres_id', 0)),
                'name': building.get('brf_name', 'Unknown BRF'),
                'building_id': building.get('building_id', building.get('postgres_id', 0)),
                **building
            })
        
        return transformed_data
    except FileNotFoundError:
        st.error("Dataset file not found!")
        return []
    except json.JSONDecodeError:
        st.error("Invalid JSON format in dataset!")
        return []

def get_energy_class_color(energy_class):
    """Get color code for energy class."""
    colors = {
        'A': '#22c55e',  # Green
        'B': '#84cc16',  # Light green  
        'C': '#eab308',  # Yellow
        'D': '#f59e0b',  # Orange
        'E': '#f97316',  # Dark orange
        'F': '#dc2626',  # Red
        'G': '#991b1b'   # Dark red
    }
    return colors.get(energy_class, '#6b7280')

def get_performance_vs_swedish_avg(energy_performance):
    """Compare performance to Swedish average (159 kWh/m²)."""
    swedish_avg = 159
    if energy_performance is None:
        return "No data", "#6b7280"
    
    percentage = (energy_performance / swedish_avg) * 100
    
    if percentage <= 70:
        return f"Excellent ({percentage:.0f}% of avg)", "#22c55e"
    elif percentage <= 85:
        return f"Very Good ({percentage:.0f}% of avg)", "#84cc16"
    elif percentage <= 100:
        return f"Good ({percentage:.0f}% of avg)", "#eab308"
    elif percentage <= 120:
        return f"Average ({percentage:.0f}% of avg)", "#f59e0b"
    else:
        return f"Poor ({percentage:.0f}% of avg)", "#dc2626"

def create_building_popup(building):
    """Create rich HTML popup for building markers."""
    perf_text, perf_color = get_performance_vs_swedish_avg(building.get('energy_performance'))
    
    total_cost = building.get('total_cost', 0)
    monthly_fee = building.get('monthly_fee', 0)
    
    popup_html = f"""
    <div style="width: 350px; font-family: Arial, sans-serif;">
        <h3 style="color: #1f4e79; margin-bottom: 10px; border-bottom: 2px solid #e5e7eb;">
            {building['brf_name']}
        </h3>
        
        <div style="margin: 10px 0;">
            <strong>Address:</strong><br>
            {building['formatted_address']}<br>
            {building['postal_code']}
        </div>
        
        <div style="background: {get_energy_class_color(building.get('energy_class', 'N/A'))}; 
                    color: white; padding: 8px; border-radius: 5px; margin: 10px 0;">
            <strong>Energy Class: {building.get('energy_class', 'N/A')}</strong><br>
            Performance: {building.get('energy_performance', 'N/A')} kWh/m²
        </div>
        
        <div style="background: {perf_color}; color: white; padding: 8px; border-radius: 5px; margin: 10px 0;">
            <strong>vs Swedish Average:</strong><br>
            {perf_text}
        </div>
        
        <div style="background: #f8f9fa; padding: 10px; border-radius: 5px; margin: 10px 0;">
            <strong>Financial Info:</strong><br>
            {'Monthly Fee: {:,.0f} SEK<br>'.format(monthly_fee) if monthly_fee else ''}
            Total Costs: {total_cost:,.0f} SEK<br>
            Built: {building.get('construction_year', 'N/A')}
        </div>
        
        <div style="font-size: 11px; color: #666; margin-top: 10px;">
            Building ID: {building['building_id']}<br>
            Properties: {building.get('property_count', 'N/A')}<br>
            {'Coordinates: ' + building.get('coordinates_source', 'Original') if building.get('coordinates_source') else ''}
        </div>
    </div>
    """
    return popup_html

def create_base_map(buildings_data):
    """Create the base folium map centered on Hammarby Sjöstad."""
    lats = [b['latitude'] for b in buildings_data if b.get('latitude')]
    lngs = [b['longitude'] for b in buildings_data if b.get('longitude')]
    
    center_lat = np.mean(lats) if lats else 59.3045
    center_lng = np.mean(lngs) if lngs else 18.103
    
    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=14,
        tiles=None
    )
    
    # Add multiple tile layers
    folium.TileLayer('OpenStreetMap', name='OpenStreetMap').add_to(m)
    folium.TileLayer('CartoDB positron', name='Light Mode').add_to(m)
    folium.TileLayer('CartoDB dark_matter', name='Dark Mode').add_to(m)
    
    # Add satellite imagery
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satellite',
        overlay=False,
        control=True
    ).add_to(m)
    
    return m

def add_building_markers(m, buildings_data):
    """Add interactive building markers to the map."""
    for building in buildings_data:
        if not building.get('latitude') or not building.get('longitude'):
            continue
            
        energy_class = building.get('energy_class', 'N/A')
        color = get_energy_class_color(energy_class)
        
        # Create custom icon
        icon_html = f"""
        <div style="background-color: {color}; 
                    width: 30px; height: 30px; 
                    border-radius: 50%; 
                    border: 3px solid white;
                    display: flex; align-items: center; justify-content: center;
                    font-weight: bold; font-size: 12px; color: white;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.3);">
            {energy_class}
        </div>
        """
        
        folium.Marker(
            location=[building['latitude'], building['longitude']],
            popup=folium.Popup(create_building_popup(building), max_width=400),
            tooltip=f"{building['brf_name']} - Energy Class {energy_class}",
            icon=folium.DivIcon(html=icon_html, icon_size=(30, 30), icon_anchor=(15, 15))
        ).add_to(m)
    
    return m

def add_drawing_tools(m):
    """Add polygon drawing tools to the map."""
    from folium.plugins import Draw
    
    draw = Draw(
        export=True,
        position='topleft',
        draw_options={
            'polyline': False,
            'polygon': {
                'allowIntersection': False,
                'drawError': {
                    'color': '#e1e100',
                    'message': "Polygon intersections not allowed!"
                },
                'shapeOptions': {
                    'color': '#ff4b4b',
                    'weight': 3,
                    'fillOpacity': 0.1
                }
            },
            'circle': True,
            'rectangle': True,
            'marker': False,
            'circlemarker': False,
        }
    )
    draw.add_to(m)
    return m

def point_in_polygon(point, polygon):
    """Check if a point is inside a polygon using ray casting algorithm."""
    x, y = point
    n = len(polygon)
    inside = False
    
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    
    return inside

def get_buildings_in_selection(buildings_data, map_data):
    """Get buildings that fall within the selected area."""
    selected_buildings = []
    
    # Single building selection via marker click
    if map_data.get('last_object_clicked_tooltip'):
        tooltip = map_data['last_object_clicked_tooltip']
        for building in buildings_data:
            if building['brf_name'] in tooltip:
                selected_buildings.append(building)
                break
    
    # Polygon/area selection
    if map_data.get('all_drawings') and len(map_data['all_drawings']) > 0:
        for drawing in map_data['all_drawings']:
            if drawing['geometry']['type'] == 'Polygon':
                polygon_coords = drawing['geometry']['coordinates'][0]
                polygon_points = [(coord[1], coord[0]) for coord in polygon_coords]
                
                for building in buildings_data:
                    if building.get('latitude') and building.get('longitude'):
                        building_point = (building['latitude'], building['longitude'])
                        if point_in_polygon(building_point, polygon_points):
                            selected_buildings.append(building)
            
            elif drawing['geometry']['type'] == 'Point':
                center = drawing['geometry']['coordinates']
                center_point = (center[1], center[0])
                radius = 0.005
                
                for building in buildings_data:
                    if building.get('latitude') and building.get('longitude'):
                        building_point = (building['latitude'], building['longitude'])
                        distance = np.sqrt((building_point[0] - center_point[0])**2 + 
                                         (building_point[1] - center_point[1])**2)
                        if distance <= radius:
                            selected_buildings.append(building)
    
    return selected_buildings

def create_energy_performance_chart(buildings_data, selected_buildings=None):
    """Create energy performance comparison chart."""
    df = pd.DataFrame(buildings_data)
    swedish_avg = 159
    
    fig = go.Figure()
    
    # All buildings
    fig.add_trace(go.Scatter(
        x=df['brf_name'],
        y=df['energy_performance'],
        mode='markers+text',
        marker=dict(
            size=12,
            color=[get_energy_class_color(ec) for ec in df['energy_class']],
            line=dict(width=2, color='white')
        ),
        text=df['energy_class'],
        textposition="middle center",
        name='All Buildings',
        hovertemplate='<b>%{x}</b><br>Energy: %{y} kWh/m²<br>Class: %{text}<extra></extra>'
    ))
    
    # Selected buildings highlight
    if selected_buildings:
        selected_df = pd.DataFrame(selected_buildings)
        fig.add_trace(go.Scatter(
            x=selected_df['brf_name'],
            y=selected_df['energy_performance'],
            mode='markers',
            marker=dict(
                size=18,
                color='rgba(255, 75, 75, 0.3)',
                line=dict(width=4, color='#ff4b4b')
            ),
            name='Selected Buildings',
            hovertemplate='<b>%{x}</b><br>Energy: %{y} kWh/m²<br><b>SELECTED</b><extra></extra>'
        ))
    
    # Swedish average line
    fig.add_hline(
        y=swedish_avg,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Swedish Average: {swedish_avg} kWh/m²",
        annotation_position="top left"
    )
    
    fig.update_layout(
        title="Energy Performance vs Swedish Average",
        xaxis_title="Building",
        yaxis_title="Energy Performance (kWh/m²)",
        height=400,
        showlegend=True,
        xaxis_tickangle=-45
    )
    
    return fig

def create_comprehensive_energy_metadata_display(building):
    """Create comprehensive display of all EPC metadata for a building."""
    st.markdown(f"### 🏢 {building['brf_name']} - Complete EPC Metadata")
    
    # Basic building information
    with st.container():
        st.markdown('<div class="energy-metadata">', unsafe_allow_html=True)
        st.markdown("#### 📍 Building Information")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Building ID", building.get('building_id', 'N/A'))
            st.metric("Construction Year", building.get('construction_year', 'N/A'))
        with col2:
            st.metric("Property Count", building.get('property_count', 'N/A'))
            st.write(f"**Address:** {building.get('formatted_address', 'N/A')}")
        with col3:
            st.write(f"**Postal Code:** {building.get('postal_code', 'N/A')}")
            st.write(f"**Coordinates:** {building.get('latitude', 'N/A'):.6f}, {building.get('longitude', 'N/A'):.6f}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Energy Performance Certificate Details
    with st.container():
        st.markdown('<div class="energy-metadata">', unsafe_allow_html=True)
        st.markdown("#### ⚡ Energy Performance Certificate (EPC)")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            energy_class = building.get('energy_class', 'N/A')
            perf_text, perf_color = get_performance_vs_swedish_avg(building.get('energy_performance'))
            
            # Energy class with color coding
            st.markdown(
                f'<div class="energy-class-{energy_class}" style="padding: 10px; border-radius: 8px; text-align: center; margin: 5px 0;">'
                f'<strong>Energy Class: {energy_class}</strong></div>',
                unsafe_allow_html=True
            )
            
            st.metric("Energy Performance", f"{building.get('energy_performance', 'N/A')} kWh/m²")
            
        with col2:
            st.markdown(f"**vs Swedish Average (159 kWh/m²):**")
            st.markdown(f'<div style="color: {perf_color}; font-weight: bold; font-size: 1.1em;">{perf_text}</div>', 
                       unsafe_allow_html=True)
            
            # Performance score
            perf_score = building.get('performance_score', 0)
            st.metric("Performance Score", f"{perf_score:.1f}/100" if perf_score else 'N/A')
            
        with col3:
            # EPC Properties breakdown
            st.markdown("**EPC Properties:**")
            epc_properties = building.get('epc_properties', [])
            if epc_properties:
                for i, prop in enumerate(epc_properties):
                    st.write(f"• {prop.get('name', 'N/A')} - House #{prop.get('house_numbers', 'N/A').strip('{}')}")
            else:
                st.write("No detailed property data available")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Financial Metadata
    with st.container():
        st.markdown('<div class="energy-metadata">', unsafe_allow_html=True)
        st.markdown("#### 💰 Financial Metadata")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Income & Expenses:**")
            st.metric("Total Income", f"{building.get('total_income', 0):,.0f} SEK" if building.get('total_income') else 'N/A')
            st.metric("Total Expenses", f"{building.get('total_expenses', 0):,.0f} SEK" if building.get('total_expenses') else 'N/A')
            st.metric("Monthly Fee", f"{building.get('monthly_fee', 0):,.0f} SEK" if building.get('monthly_fee') else 'N/A')
            
        with col2:
            st.markdown("**Funds & Loans:**")
            st.metric("Maintenance Fund", f"{building.get('maintenance_fund', 0):,.0f} SEK" if building.get('maintenance_fund') else 'N/A')
            st.metric("Loan Amount", f"{building.get('loan_amount', 0):,.0f} SEK" if building.get('loan_amount') else 'N/A')
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Cost Breakdown with PostgreSQL vs Excel comparison
    with st.container():
        st.markdown('<div class="energy-metadata">', unsafe_allow_html=True)
        st.markdown("#### 📊 Detailed Cost Analysis")
        
        # Create comparison between operational database and financial records
        cost_comparison = []
        
        # Energy costs comparison
        postgres_energy = building.get('postgres_energy_costs', 0)
        excel_electricity = building.get('cost_electricity', 0)
        if postgres_energy or excel_electricity:
            variance = abs(postgres_energy - excel_electricity) if postgres_energy and excel_electricity else 0
            variance_pct = (variance / max(postgres_energy, excel_electricity) * 100) if variance > 0 else 0
            cost_comparison.append({
                'Cost Category': 'Energy & Electricity',
                'Operational Database': f"{postgres_energy:,.0f} SEK" if postgres_energy else 'Not Available',
                'Financial Records': f"{excel_electricity:,.0f} SEK" if excel_electricity else 'Not Available',
                'Variance': f"{variance:,.0f} SEK ({variance_pct:.1f}%)" if postgres_energy and excel_electricity else 'Single Source'
            })
        
        # Water costs comparison  
        postgres_water = building.get('postgres_water_costs', 0)
        excel_water = building.get('cost_water', 0)
        if postgres_water or excel_water:
            variance = abs(postgres_water - excel_water) if postgres_water and excel_water else 0
            variance_pct = (variance / max(postgres_water, excel_water) * 100) if variance > 0 else 0
            cost_comparison.append({
                'Cost Category': 'Water & Sanitation',
                'Operational Database': f"{postgres_water:,.0f} SEK" if postgres_water else 'Not Available',
                'Financial Records': f"{excel_water:,.0f} SEK" if excel_water else 'Not Available',
                'Variance': f"{variance:,.0f} SEK ({variance_pct:.1f}%)" if postgres_water and excel_water else 'Single Source'
            })
        
        # Heating costs comparison
        postgres_heating = building.get('postgres_heating_costs', 0)
        excel_heating = building.get('cost_heating', 0)
        if postgres_heating or excel_heating:
            variance = abs(postgres_heating - excel_heating) if postgres_heating and excel_heating else 0
            variance_pct = (variance / max(postgres_heating, excel_heating) * 100) if variance > 0 else 0
            cost_comparison.append({
                'Cost Category': 'Heating & HVAC',
                'Operational Database': f"{postgres_heating:,.0f} SEK" if postgres_heating else 'Not Available',
                'Financial Records': f"{excel_heating:,.0f} SEK" if excel_heating else 'Not Available',
                'Variance': f"{variance:,.0f} SEK ({variance_pct:.1f}%)" if postgres_heating and excel_heating else 'Single Source'
            })
        
        # Additional cost categories from financial records
        additional_costs = [
            ('Cleaning & Maintenance', 'cost_cleaning'),
            ('Internet & Television', 'cost_internet_and_tv'),
            ('Waste & Recycling', 'cost_recycling'),
            ('Snow Removal', 'cost_snow_removal')
        ]
        
        for cost_name, cost_key in additional_costs:
            cost_value = building.get(cost_key, 0)
            if cost_value:
                cost_comparison.append({
                    'Cost Category': cost_name,
                    'Operational Database': 'Not Available',
                    'Financial Records': f"{cost_value:,.0f} SEK",
                    'Variance': 'Financial Records Only'
                })
        
        if cost_comparison:
            st.dataframe(pd.DataFrame(cost_comparison), use_container_width=True)
        
        # Total cost summary
        total_cost = building.get('total_cost', 0)
        if total_cost:
            st.metric("Total Annual Cost", f"{total_cost:,.0f} SEK")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Cost visualization
    cost_categories = ['cost_electricity', 'cost_heating', 'cost_water', 'cost_internet_and_tv', 
                      'cost_recycling', 'cost_cleaning', 'cost_snow_removal']
    
    cost_data = []
    cost_values = []
    
    for category in cost_categories:
        value = building.get(category, 0)
        if value > 0:
            cost_data.append(category.replace('cost_', '').replace('_', ' & ').title())
            cost_values.append(value)
    
    if cost_data:
        fig = go.Figure(data=[
            go.Pie(labels=cost_data, values=cost_values, hole=0.3)
        ])
        fig.update_layout(
            title=f"Cost Breakdown for {building['brf_name']}",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True, key=f"energy_cost_pie_{building['building_id']}")

def create_demo_header():
    """Create the integrated dashboard header."""
    st.markdown("""
    <div class="main-header">
        <h1>🏢 Integrated BRF Dashboard - Hammarby Sjöstad</h1>
        <p style="font-size: 1.2em; margin: 1rem 0;">
            Interactive Map • Enhanced Survey System • Complete Energy Analysis
        </p>
        <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 10px; margin: 1rem 0;">
            <h3>🏢 Professional BRF Management Platform</h3>
            <p>Complete Energy Performance Analysis • Cost Optimization • Peer Benchmarking • Supplier Intelligence</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

def create_integrated_sidebar():
    """Create integrated sidebar with all controls."""
    with st.sidebar:
        st.header("🎛️ Dashboard Controls")
        
        # Show current survey progress if exists
        if 'survey_progress' in st.session_state:
            st.metric(
                "Survey Progress",
                f"{st.session_state.survey_progress:.0f}%",
                help="Survey completion percentage"
            )
            st.progress(st.session_state.survey_progress / 100)
        
        st.divider()
        
        # Map controls
        st.subheader("🗺️ Map Controls")
        
        # Energy class filter
        buildings_data = load_buildings_data()
        available_classes = sorted(list(set(b.get('energy_class', 'N/A') for b in buildings_data)))
        selected_classes = st.multiselect(
            "Filter by Energy Class:",
            available_classes,
            default=available_classes,
            key="energy_class_filter"
        )
        
        # Performance filter
        performance_values = [b.get('energy_performance') for b in buildings_data if b.get('energy_performance')]
        if performance_values:
            perf_range = st.slider(
                "Energy Performance Range (kWh/m²):",
                min_value=int(min(performance_values)),
                max_value=int(max(performance_values)),
                value=(int(min(performance_values)), int(max(performance_values))),
                key="performance_filter"
            )
        else:
            perf_range = (0, 200)
        
        st.divider()
        
        # Survey controls
        st.subheader("📝 Survey System")
        st.info("Complete the cost survey to unlock peer comparisons and supplier recommendations")
        
        st.divider()
        
        # Export options
        st.subheader("📤 Export Options")
        if st.button("Export All Building Data"):
            csv = pd.DataFrame(buildings_data).to_csv(index=False)
            st.download_button(
                label="Download Complete Dataset",
                data=csv,
                file_name=f"hammarby_buildings_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        
        return selected_classes, perf_range

def create_brf_landing_page(building_data, market_position, total_buildings):
    """Create comprehensive BRF landing page with detailed analytics, suppliers, and highlights."""
    
    brf_name = building_data['brf_name']
    performance_score = building_data.get('performance_score', 0)
    
    # Performance status color and text
    if performance_score >= 75:
        status_color = "#2E8B57"
        status_text = "🟢 Excellent Performance"
        status_emoji = "🏆"
    elif performance_score >= 60:
        status_color = "#4682B4" 
        status_text = "🔵 Good Performance"
        status_emoji = "⭐"
    elif performance_score >= 40:
        status_color = "#FF8C00"
        status_text = "🟠 Average Performance" 
        status_emoji = "📊"
    else:
        status_color = "#DC143C"
        status_text = "🔴 Needs Improvement"
        status_emoji = "🔧"
    
    # Hero Section
    st.markdown("---")
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {status_color} 0%, {'#34495e' if performance_score >= 60 else '#e74c3c'} 100%);
        color: white;
        padding: 30px;
        border-radius: 15px;
        margin: 20px 0;
        box-shadow: 0 8px 20px rgba(0,0,0,0.3);
        text-align: center;
    ">
        <h1 style="margin: 0 0 10px 0; font-size: 2.2em;">{status_emoji} {brf_name}</h1>
        <h3 style="margin: 0 0 20px 0; opacity: 0.9;">{status_text}</h3>
        <div style="display: flex; justify-content: center; gap: 40px; margin-top: 20px;">
            <div>
                <h2 style="margin: 0; font-size: 2em;">{performance_score:.1f}/100</h2>
                <p style="margin: 5px 0 0 0; opacity: 0.8;">Performance Index</p>
            </div>
            <div>
                <h2 style="margin: 0; font-size: 2em;">#{market_position}</h2>
                <p style="margin: 5px 0 0 0; opacity: 0.8;">Market Ranking</p>
            </div>
            <div>
                <h2 style="margin: 0; font-size: 2em;">{((total_buildings - market_position + 1) / total_buildings * 100):.0f}%</h2>
                <p style="margin: 5px 0 0 0; opacity: 0.8;">Percentile</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Key Highlights Section
    st.markdown("### 🎯 Key Highlights")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        energy_class = building_data.get('energy_class', 'N/A')
        energy_performance = building_data.get('energy_performance', 0)
        if energy_class in ['A', 'B']:
            energy_color = "#2E8B57"
        elif energy_class in ['C', 'D']:
            energy_color = "#FF8C00"
        else:
            energy_color = "#DC143C"
        
        st.markdown(f"""
        <div style="background: {energy_color}20; padding: 15px; border-radius: 10px; border-left: 4px solid {energy_color};">
            <h4 style="margin: 0; color: {energy_color};">🔋 Energy Class</h4>
            <h2 style="margin: 5px 0 0 0; color: {energy_color};">{energy_class}</h2>
            <p style="margin: 5px 0 0 0; color: #666;">{energy_performance} kWh/m²</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        construction_year = building_data.get('construction_year', 'N/A')
        age = 2025 - construction_year if construction_year != 'N/A' else 'N/A'
        st.markdown(f"""
        <div style="background: #4682B420; padding: 15px; border-radius: 10px; border-left: 4px solid #4682B4;">
            <h4 style="margin: 0; color: #4682B4;">🏗️ Building Age</h4>
            <h2 style="margin: 5px 0 0 0; color: #4682B4;">{age} years</h2>
            <p style="margin: 5px 0 0 0; color: #666;">Built {construction_year}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        total_cost = building_data.get('total_cost', 0)
        monthly_fee = building_data.get('monthly_fee', 0)
        st.markdown(f"""
        <div style="background: #FF8C0020; padding: 15px; border-radius: 10px; border-left: 4px solid #FF8C00;">
            <h4 style="margin: 0; color: #FF8C00;">💰 Monthly Fee</h4>
            <h2 style="margin: 5px 0 0 0; color: #FF8C00;">{monthly_fee:,.0f} SEK</h2>
            <p style="margin: 5px 0 0 0; color: #666;">Annual: {total_cost:,.0f} SEK</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        property_count = building_data.get('property_count', 1)
        epc_properties = building_data.get('epc_properties', [])
        st.markdown(f"""
        <div style="background: #8A2BE220; padding: 15px; border-radius: 10px; border-left: 4px solid #8A2BE2;">
            <h4 style="margin: 0; color: #8A2BE2;">🏠 Properties</h4>
            <h2 style="margin: 5px 0 0 0; color: #8A2BE2;">{property_count}</h2>
            <p style="margin: 5px 0 0 0; color: #666;">{len(epc_properties)} EPC units</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Financial Overview & Suppliers Section
    st.markdown("### 💼 Financial Overview & Service Providers")
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Financial metrics
        total_income = building_data.get('total_income', 0)
        total_expenses = building_data.get('total_expenses', 0)
        maintenance_fund = building_data.get('maintenance_fund', 0)
        loan_amount = building_data.get('loan_amount', 0)
        
        st.markdown("#### 📊 Financial Performance")
        
        # Create financial metrics chart
        financial_metrics = {
            'Total Income': total_income,
            'Total Expenses': total_expenses, 
            'Maintenance Fund': maintenance_fund,
            'Outstanding Loans': loan_amount
        }
        
        fig_financial = go.Figure()
        fig_financial.add_trace(go.Bar(
            x=list(financial_metrics.keys()),
            y=list(financial_metrics.values()),
            marker_color=['#2E8B57', '#DC143C', '#4682B4', '#FF8C00'],
            text=[f"{v/1000:.0f}k" for v in financial_metrics.values()],
            textposition='outside'
        ))
        
        fig_financial.update_layout(
            title="Financial Overview (SEK)",
            height=300,
            showlegend=False,
            yaxis=dict(title="Amount (SEK)"),
            margin=dict(l=50, r=50, t=50, b=50)
        )
        st.plotly_chart(fig_financial, use_container_width=True)
    
    with col2:
        st.markdown("#### 🏢 Service Providers & Suppliers")
        
        # Create realistic supplier information based on BRF type and costs
        electricity_cost = building_data.get('cost_electricity', 0)
        heating_cost = building_data.get('cost_heating', 0)
        water_cost = building_data.get('cost_water', 0)
        internet_cost = building_data.get('cost_internet_and_tv', 0)
        
        suppliers = []
        
        # Energy supplier (based on performance and costs)
        if electricity_cost > 1000000:  # High electricity costs
            suppliers.append({"name": "Vattenfall", "service": "Electricity", "rating": "⭐⭐⭐", "status": "Active"})
        elif electricity_cost > 500000:
            suppliers.append({"name": "E.ON", "service": "Electricity", "rating": "⭐⭐⭐⭐", "status": "Active"}) 
        else:
            suppliers.append({"name": "Fortum", "service": "Electricity", "rating": "⭐⭐⭐⭐⭐", "status": "Active"})
        
        # Heating supplier
        if heating_cost > 500000:
            suppliers.append({"name": "Stockholm Exergi", "service": "District Heating", "rating": "⭐⭐⭐⭐", "status": "Active"})
        else:
            suppliers.append({"name": "Norrenergi", "service": "District Heating", "rating": "⭐⭐⭐⭐⭐", "status": "Active"})
        
        # Internet/TV
        if internet_cost > 200000:
            suppliers.append({"name": "Telia", "service": "Internet/TV", "rating": "⭐⭐⭐", "status": "Active"})
        else:
            suppliers.append({"name": "Com Hem", "service": "Internet/TV", "rating": "⭐⭐⭐⭐", "status": "Active"})
        
        # Property management
        suppliers.append({"name": "Svensk Fastighetsförvaltning", "service": "Property Mgmt", "rating": "⭐⭐⭐⭐", "status": "Active"})
        
        for supplier in suppliers:
            st.markdown(f"""
            <div style="background: #f8f9fa; padding: 10px; margin: 5px 0; border-radius: 8px; border-left: 3px solid #007bff;">
                <strong>{supplier['name']}</strong><br>
                <small>{supplier['service']} • {supplier['rating']} • {supplier['status']}</small>
            </div>
            """, unsafe_allow_html=True)
    
    # Detailed Cost Breakdown
    st.markdown("### 💰 Annual Cost Breakdown")
    
    cost_categories = {
        'Electricity': building_data.get('cost_electricity', 0),
        'Heating': building_data.get('cost_heating', 0), 
        'Water': building_data.get('cost_water', 0),
        'Internet/TV': building_data.get('cost_internet_and_tv', 0),
        'Recycling': building_data.get('cost_recycling', 0),
        'Snow Removal': building_data.get('cost_snow_removal', 0),
        'Cleaning': building_data.get('cost_cleaning', 0)
    }
    
    # Filter out zero costs
    cost_categories = {k: v for k, v in cost_categories.items() if v > 0}
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart of costs
        fig_pie = go.Figure(data=[
            go.Pie(
                labels=list(cost_categories.keys()),
                values=list(cost_categories.values()),
                hole=0.4,
                hovertemplate='<b>%{label}</b><br>%{value:,.0f} SEK<br>%{percent}<extra></extra>'
            )
        ])
        fig_pie.update_layout(
            title="Cost Distribution",
            height=400,
            showlegend=True,
            legend=dict(orientation="v", yanchor="middle", y=0.5)
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Cost efficiency analysis
        st.markdown("#### 📈 Cost Efficiency Analysis")
        
        # Compare to market averages (mock data based on realistic Swedish BRF costs)
        market_averages = {
            'Electricity': 800000,
            'Heating': 600000,
            'Water': 200000,
            'Internet/TV': 150000,
            'Recycling': 100000
        }
        
        for category, cost in cost_categories.items():
            if category in market_averages:
                market_avg = market_averages[category]
                efficiency = cost / market_avg if market_avg > 0 else 1
                
                if efficiency < 0.8:
                    color = "#2E8B57"
                    status = "🟢 Efficient"
                elif efficiency < 1.2:
                    color = "#FF8C00" 
                    status = "🟡 Average"
                else:
                    color = "#DC143C"
                    status = "🔴 Above Average"
                
                st.markdown(f"""
                <div style="background: {color}15; padding: 8px; margin: 3px 0; border-radius: 6px;">
                    <strong>{category}</strong>: {status}<br>
                    <small>{cost:,.0f} SEK vs {market_avg:,.0f} SEK market avg</small>
                </div>
                """, unsafe_allow_html=True)
    
    # Property Details & Location
    st.markdown("### 📍 Property Information")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🏠 Property Details")
        formatted_address = building_data.get('formatted_address', 'N/A')
        postal_code = building_data.get('postal_code', 'N/A')
        
        st.write(f"**Address:** {formatted_address}")
        st.write(f"**Postal Code:** {postal_code}")
        st.write(f"**Construction Year:** {construction_year}")
        st.write(f"**Property Count:** {property_count}")
        
        # EPC Properties
        if epc_properties:
            st.markdown("**EPC Properties:**")
            for prop in epc_properties:
                prop_name = prop.get('name', 'N/A')
                house_numbers = prop.get('house_numbers', 'N/A')
                # Clean up house numbers display - remove braces and format nicely
                if house_numbers != 'N/A':
                    clean_numbers = house_numbers.strip('{}').replace(',', ', ')
                    st.write(f"• {prop_name} - Units: {clean_numbers}")
                else:
                    st.write(f"• {prop_name} - Units: N/A")
    
    with col2:
        st.markdown("#### 🌍 Location & Coordinates")
        latitude = building_data.get('latitude', 0)
        longitude = building_data.get('longitude', 0)
        
        st.write(f"**Latitude:** {latitude}")
        st.write(f"**Longitude:** {longitude}")
        st.write(f"**District:** Hammarby Sjöstad")
        
        # Coordinate source
        coord_source = building_data.get('coordinates_source', 'original')
        if coord_source == 'booli.se':
            st.success("✅ Verified coordinates from Booli.se")
        else:
            st.info("📍 Approximate coordinates")
    
    # Action Buttons
    st.markdown("### 🎯 Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 View Energy Analysis", key=f"energy_{brf_name}"):
            st.info("Navigate to Energy Analysis tab to see detailed energy performance")
    
    with col2:
        if st.button("💰 Cost Comparison", key=f"cost_{brf_name}"):
            st.info("Navigate to Cost Comparison tab to compare with other BRFs")
    
    with col3:
        if st.button("🔍 Supplier Recommendations", key=f"supplier_{brf_name}"):
            st.info("Navigate to Supplier Recommendations tab for optimization suggestions")
    
    with col4:
        if st.button("📋 Complete Survey", key=f"survey_{brf_name}"):
            st.info("Navigate to Survey System tab to provide detailed information")
    
    st.info("💡 Click on another bar in the Performance Ranking chart to view a different BRF profile")
    st.markdown("---")

def main():
    """Main integrated dashboard application."""
    # Create header
    create_demo_header()
    
    # Load data
    buildings_data = load_buildings_data()
    if not buildings_data:
        st.error("No building data available!")
        return
    
    # Create sidebar controls
    selected_classes, perf_range = create_integrated_sidebar()
    
    # Filter buildings based on sidebar controls
    filtered_buildings = []
    for building in buildings_data:
        energy_class = building.get('energy_class', 'N/A')
        performance = building.get('energy_performance')
        
        if energy_class in selected_classes:
            if performance is None or perf_range[0] <= performance <= perf_range[1]:
                filtered_buildings.append(building)
    
    # Initialize survey system
    survey_system = SurveySystem(buildings_data, st.session_state)
    
    # Main application tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🗺️ Interactive Map", 
        "📝 Survey System", 
        "⚡ Energy Analysis",
        "📊 Cost Comparison", 
        "💰 Supplier Recommendations",
        "📈 Performance Index"
    ])
    
    with tab1:
        # Check if a BRF profile is selected for viewing
        selected_brf_name = st.session_state.get('selected_brf_profile', None)
        
        
        if selected_brf_name:
            # Show BRF profile inline with back button
            if st.button("← Back to Map", key="back_to_map"):
                del st.session_state.selected_brf_profile
                st.rerun()
            
            # Find the selected BRF
            selected_building = next((b for b in buildings_data if b['brf_name'] == selected_brf_name), None)
            if selected_building:
                # Calculate market position for this BRF
                all_buildings_with_scores = []
                for building in buildings_data:
                    score = building.get('performance_score', 0)
                    if score > 0:  # Only include buildings with valid scores
                        all_buildings_with_scores.append({
                            'name': building['brf_name'],
                            'score': score,
                            'is_current': building['brf_name'] == selected_brf_name
                        })
                
                # Sort by score descending to get rankings
                all_buildings_with_scores.sort(key=lambda x: x['score'], reverse=True)
                
                # Find position of selected BRF
                market_position = next((i+1 for i, b in enumerate(all_buildings_with_scores) if b['name'] == selected_brf_name), len(all_buildings_with_scores))
                
                # Show comprehensive BRF landing page
                create_brf_landing_page(selected_building, market_position, len(all_buildings_with_scores))
            else:
                st.error(f"BRF '{selected_brf_name}' not found in dataset.")
                if st.button("← Back to Map", key="back_to_map_error"):
                    del st.session_state.selected_brf_profile
                    st.rerun()
        else:
            # Show normal map view
            st.markdown("## 🗺️ Interactive Map Dashboard")
            st.info("💡 **Instructions**: Click building markers for details, use drawing tools to select areas, draw polygons to compare multiple buildings")
            
            # Map and selection analysis
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Create and display map
                m = create_base_map(filtered_buildings)
                m = add_building_markers(m, filtered_buildings)
                m = add_drawing_tools(m)
                folium.LayerControl().add_to(m)
            
                # Display map
                map_data = st_folium(
                    m,
                    width=700,
                    height=600,
                    returned_objects=["last_object_clicked_tooltip", "all_drawings"],
                    key="main_map"
                )
            
            with col2:
                st.subheader("📊 Quick Stats")
                
                # Overall statistics
                total_buildings = len(filtered_buildings)
                avg_performance = np.mean([b.get('energy_performance', 0) for b in filtered_buildings if b.get('energy_performance')])
                avg_cost = np.mean([b.get('total_cost', 0) for b in filtered_buildings if b.get('total_cost')])
                
                st.metric("Filtered Buildings", total_buildings)
                st.metric("Avg Performance", f"{avg_performance:.1f} kWh/m²")
                st.metric("Avg Annual Cost", f"{avg_cost:,.0f} SEK")
                
                # Energy class distribution
                class_counts = {}
                for building in filtered_buildings:
                    ec = building.get('energy_class', 'N/A')
                    class_counts[ec] = class_counts.get(ec, 0) + 1
                
                st.subheader("Energy Class Distribution")
                for ec, count in sorted(class_counts.items()):
                    st.markdown(
                        f'<div class="energy-class-{ec}" style="padding: 5px; margin: 2px; border-radius: 5px; text-align: center;">'
                        f'Class {ec}: {count} buildings</div>',
                        unsafe_allow_html=True
                    )
            
            # Selection analysis
            selected_buildings = get_buildings_in_selection(filtered_buildings, map_data)
            
            if selected_buildings:
                st.markdown(f"### 🎯 Selected Buildings Analysis ({len(selected_buildings)} buildings)")
                
                # Performance comparison chart for selected buildings
                fig_energy = create_energy_performance_chart(filtered_buildings, selected_buildings)
                st.plotly_chart(fig_energy, use_container_width=True, key="map_energy_chart")
                
                # Selected buildings summary cards
                cols = st.columns(min(3, len(selected_buildings)))
                for i, building in enumerate(selected_buildings):
                    with cols[i % 3]:
                        perf_text, perf_color = get_performance_vs_swedish_avg(building.get('energy_performance'))
                        st.markdown(
                            f'<div class="selected-building">'
                            f'<h4>{building["brf_name"]}</h4>'
                            f'<p><strong>Class:</strong> {building.get("energy_class", "N/A")}</p>'
                            f'<p><strong>Performance:</strong> {building.get("energy_performance", "N/A")} kWh/m²</p>'
                            f'<p style="color: {perf_color};"><strong>{perf_text}</strong></p>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                        
                        # Add button to view full BRF profile
                        if st.button(f"🏢 View Full Profile", key=f"map_profile_{building['brf_name']}", help=f"View detailed profile for {building['brf_name']}"):
                            st.session_state.selected_brf_profile = building['brf_name']
                            st.rerun()
    
    with tab2:
        st.markdown("## 📝 BRF Cost Survey System")
        st.markdown("*Share your BRF cost data to unlock peer comparisons and supplier recommendations.*")
        
        # Check if user has completed survey or unlocked data
        if not st.session_state.get('peer_data_unlocked', False):
            show_survey = survey_system.show_survey_modal_trigger()
            
            if show_survey or st.session_state.get('show_survey', False):
                st.session_state.show_survey = True
                
                # Pre-populate with BRF Sjöstaden 2 demo data for quick testing
                if 'current_survey' not in st.session_state or not st.session_state.current_survey.get('building_id'):
                    # Find BRF Sjöstaden 2 in the dataset
                    sjostaden_2 = None
                    for building in buildings_data:
                        if 'sjöstaden' in building.get('brf_name', '').lower() and '2' in building.get('brf_name', ''):
                            sjostaden_2 = building
                            break
                    
                    if sjostaden_2:
                        if 'current_survey' not in st.session_state:
                            st.session_state.current_survey = {}
                        
                        # Ensure both id and building_id are set for compatibility
                        st.session_state.current_survey['building_id'] = sjostaden_2.get('building_id', sjostaden_2.get('id'))
                        st.session_state.current_survey['id'] = sjostaden_2.get('building_id', sjostaden_2.get('id'))  
                        st.session_state.current_survey['building_name'] = sjostaden_2['brf_name']
                        
                        # Pre-populate with 5 ESSENTIAL cost categories (streamlined UX)
                        st.session_state.current_survey['costs'] = {
                            'electricity': 1828349.0,    # Essential - highest cost
                            'heating': 84077.0,          # Essential - major utility
                            'water': 476731.0,           # Essential - major utility
                            'cleaning': 250000.0,        # Essential - major service
                            'insurance': 185000.0        # Essential - required service
                            # Additional categories can be added through "expand survey" option
                        }
                        st.session_state.current_survey['suppliers'] = {
                            'electricity': 'Ellevio',
                            'heating': 'Stockholm Exergi',
                            'water': 'Stockholm Vatten och Avfall',
                            'cleaning': 'Städbolaget Stockholm',
                            'insurance': 'Länsförsäkringar'
                        }
                        st.session_state.current_survey['satisfaction'] = {
                            'electricity': 4,
                            'heating': 3,       # Low rating to trigger recommendations
                            'water': 5,
                            'cleaning': 3,      # Low rating to trigger recommendations
                            'insurance': 4
                        }
                        st.session_state.current_survey['contact_info'] = {
                            'name': 'Anna Styrelseledamot',
                            'email': 'anna@sjostaden2.se',
                            'phone': '08-123 456 78',
                            'position': 'Ordförande'
                        }
                        # Mark as completed to unlock all features
                        st.session_state.peer_data_unlocked = True
                
                # Show survey form
                survey_submitted = survey_system.create_survey_modal()
                
                if survey_submitted:
                    st.session_state.show_survey = False
                    st.rerun()
        else:
            st.success("✅ Survey completed! You have access to all features.")
            
            # Show survey summary
            survey_data = st.session_state.get('current_survey', {})
            if survey_data:
                st.markdown("### 📋 Your Survey Data")
                
                costs = survey_data.get('costs', {})
                suppliers = survey_data.get('suppliers', {})
                satisfaction = survey_data.get('satisfaction', {})
                
                if costs:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown("**💰 Annual Costs**")
                        for category, cost in costs.items():
                            st.write(f"{category.title()}: {cost:,.0f} SEK")
                    
                    with col2:
                        st.markdown("**🏪 Current Suppliers**")
                        for category, supplier in suppliers.items():
                            if category in costs:
                                st.write(f"{category.title()}: {supplier}")
                    
                    with col3:
                        st.markdown("**⭐ Satisfaction Ratings**")
                        for category, rating in satisfaction.items():
                            if category in costs:
                                stars = "⭐" * rating
                                st.write(f"{category.title()}: {stars} ({rating}/5)")
    
    with tab3:
        st.markdown("## ⚡ Comprehensive Energy Analysis")
        
        # Building selector for detailed analysis
        building_names = [b['brf_name'] for b in buildings_data]
        selected_building_name = st.selectbox(
            "Select Building for Detailed Energy Analysis:",
            building_names,
            key="energy_analysis_building"
        )
        
        selected_building = next((b for b in buildings_data if b['brf_name'] == selected_building_name), None)
        
        if selected_building:
            # Show comprehensive energy metadata
            create_comprehensive_energy_metadata_display(selected_building)
        
        st.divider()
        
        # Overall energy performance comparison
        st.markdown("### 📊 All Buildings Energy Performance")
        fig_all_energy = create_energy_performance_chart(filtered_buildings)
        st.plotly_chart(fig_all_energy, use_container_width=True, key="all_buildings_energy")
        
        # Dual comparison system - Sweden vs Local District
        st.markdown("### 🔍 Energy Performance Analysis")
        
        # Comparison selector
        comparison_tabs = st.tabs(["🏘️ Local District (Hammarby Sjöstad)", "🇸🇪 Sweden-wide Comparison"])
        
        with comparison_tabs[0]:
            st.markdown("#### 🏘️ Your Neighborhood Performance - **Focus on Local Peer Competition**")
            st.info("💡 **Community Impact**: See how your BRF compares to your immediate neighbors in Hammarby Sjöstad. This is where you can make the biggest difference and learn from nearby success stories!")
            
            # Local district analysis (existing buildings in dataset)
            st.markdown("##### 📊 Hammarby Sjöstad BRF Performance Distribution")
            
            # Calculate local performance statistics  
            performance_values = [b.get('energy_performance') for b in filtered_buildings if b.get('energy_performance')]
            if performance_values:
                # Local district average (this neighborhood)
                local_avg = np.mean(performance_values)
                local_median = np.median(performance_values)
                local_min = min(performance_values)
                local_max = max(performance_values)
                local_spread = local_max - local_min
                
                # Neighborhood performance overview
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("🏆 Neighborhood Champion", f"{local_min:.0f} kWh/m²", 
                             help="Best performing BRF in your immediate area")
                
                with col2:
                    st.metric("📊 Local Average", f"{local_avg:.0f} kWh/m²",
                             f"{((local_avg - 159) / 159 * 100):+.0f}% vs Sweden", 
                             help="Average of all BRFs in Hammarby Sjöstad")
                
                with col3:
                    st.metric("📈 Improvement Opportunity", f"{local_max:.0f} kWh/m²",
                             help="Highest consumption BRF - potential for improvement")
                
                with col4:
                    st.metric("🎯 Peer Competition Range", f"{local_spread:.0f} kWh/m²",
                             help="Performance gap between best and worst in your area")
                
                # Find selected building's position if survey is completed
                current_building = None
                survey_data = st.session_state.get('current_survey', {})
                if survey_data.get('building_id'):
                    for building in filtered_buildings:
                        # Multiple matching criteria for robustness
                        if (building.get('id') == survey_data.get('building_id') or 
                            building.get('building_id') == survey_data.get('building_id') or
                            building.get('brf_name') == survey_data.get('building_name')):
                            current_building = building
                            break
                
                # Peer ranking with focus on community competition
                st.markdown("##### 🏘️ Your Neighborhood Ranking")
                
                # Sort buildings by performance (best first)
                sorted_buildings = sorted(
                    [b for b in filtered_buildings if b.get('energy_performance')], 
                    key=lambda x: x.get('energy_performance')
                )
                
                # Create ranking display with emphasis on peer competition
                ranking_data = []
                for i, building in enumerate(sorted_buildings):
                    perf = building.get('energy_performance')
                    is_current = current_building and building.get('id') == current_building.get('id')
                    
                    if i == 0:
                        badge = "🥇 DISTRICT LEADER"
                        color = "success"
                    elif i == 1:
                        badge = "🥈 STRONG PERFORMER" 
                        color = "info"
                    elif i == 2:
                        badge = "🥉 ABOVE AVERAGE"
                        color = "info"
                    elif i == len(sorted_buildings) - 1:
                        badge = "🎯 IMPROVEMENT TARGET"
                        color = "warning"
                    else:
                        badge = f"#{i+1} LOCAL RANKING"
                        color = "secondary"
                    
                    # Highlight current building
                    if is_current:
                        st.markdown(f"""
                        <div style="background: linear-gradient(90deg, #ff6b6b, #ffa726); color: white; padding: 15px; border-radius: 10px; margin: 5px 0;">
                            <h4>🏢 YOUR BRF: {building['brf_name']} - {badge}</h4>
                            <p><strong>{perf:.0f} kWh/m²</strong> • Position {i+1} of {len(sorted_buildings)} in neighborhood</p>
                            {f'<p>💪 Only {(sorted_buildings[i-1].get("energy_performance") - perf):.0f} kWh/m² behind the leader!' if i > 0 else '<p>🏆 YOU ARE THE NEIGHBORHOOD LEADER!</p>'}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        with st.container():
                            if color == "success":
                                st.success(f"**{badge}**: {building['brf_name']} - {perf:.0f} kWh/m²")
                            elif color == "info":
                                st.info(f"**{badge}**: {building['brf_name']} - {perf:.0f} kWh/m²")  
                            elif color == "warning":
                                st.warning(f"**{badge}**: {building['brf_name']} - {perf:.0f} kWh/m²")
                            else:
                                st.write(f"**{badge}**: {building['brf_name']} - {perf:.0f} kWh/m²")
                
                # Peer improvement motivation
                st.markdown("---")
                st.markdown("##### 💪 Peer Competition Insights")
                
                col1, col2 = st.columns(2)
                with col1:
                    best_performer = sorted_buildings[0]
                    st.success(f"""
                    **🏆 Learn from the Leader:**  
                    **{best_performer['brf_name']}** leads with {best_performer.get('energy_performance'):.0f} kWh/m²
                    
                    *Contact them to learn their success strategies!*
                    """)
                
                with col2:
                    if current_building and len(sorted_buildings) > 1:
                        current_rank = next((i for i, b in enumerate(sorted_buildings) if b.get('id') == current_building.get('id')), -1)
                        if current_rank > 0:
                            target_building = sorted_buildings[current_rank - 1]
                            improvement = current_building.get('energy_performance') - target_building.get('energy_performance')
                            st.info(f"""
                            **🎯 Beat Your Neighbor:**  
                            Improve by just **{improvement:.0f} kWh/m²** to surpass **{target_building['brf_name']}**
                            
                            *Small improvements make big differences in rankings!*
                            """)
                        else:
                            st.info("🏆 **You're already the neighborhood leader!** Help others improve.")
            else:
                st.warning("No energy performance data available for local analysis.")
        
        with comparison_tabs[1]:
            st.markdown("#### 🇸🇪 Sweden-wide Performance Context")
            st.info("📊 **National Perspective**: Understand where your district stands compared to all of Sweden's multi-family buildings.")
            
            # Sweden-wide statistics (using Swedish average of 159 kWh/m²)
            swedish_avg = 159
            swedish_excellent = 111  # 70% of average
            swedish_good = 135       # 85% of average  
            swedish_poor = 190       # 120% of average
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("🇸🇪 Sweden Average", f"{swedish_avg} kWh/m²", 
                         help="National average for multi-family buildings")
            
            with col2:
                performance_values = [b.get('energy_performance') for b in filtered_buildings if b.get('energy_performance')]
                if performance_values:
                    local_avg = np.mean(performance_values)
                    vs_sweden = ((swedish_avg - local_avg) / swedish_avg * 100)
                    st.metric("🏘️ Hammarby Sjöstad Avg", f"{local_avg:.0f} kWh/m²",
                             f"{vs_sweden:+.0f}% vs Sweden")
                else:
                    st.metric("🏘️ Hammarby Sjöstad Avg", "N/A")
            
            with col3:
                if performance_values:
                    excellent_count = len([b for b in filtered_buildings if b.get('energy_performance', 200) <= swedish_excellent])
                    excellent_pct = (excellent_count / len(filtered_buildings)) * 100
                    st.metric("🏆 Top 30% Performance", f"{excellent_count}/{len(filtered_buildings)}", 
                             f"{excellent_pct:.0f}% of district")
                else:
                    st.metric("🏆 Top 30% Performance", "N/A")
            
            # National performance bands
            st.markdown("##### 🇸🇪 National Performance Standards")
            
            if performance_values:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**National Performance Bands:**")
                    
                    # Excellent performers (top 30% nationally)
                    excellent_buildings = [b for b in filtered_buildings if b.get('energy_performance', 200) <= swedish_excellent]
                    st.success(f"🏆 **National Top 30%**: {len(excellent_buildings)} buildings (≤{swedish_excellent} kWh/m²)")
                    for b in excellent_buildings:
                        st.write(f"• {b['brf_name']}: {b.get('energy_performance'):.0f} kWh/m²")
                    
                    # Good performers  
                    good_buildings = [b for b in filtered_buildings if swedish_excellent < b.get('energy_performance', 200) <= swedish_good]
                    if good_buildings:
                        st.info(f"📊 **Above National Average**: {len(good_buildings)} buildings ({swedish_excellent+1}-{swedish_good} kWh/m²)")
                        for b in good_buildings:
                            st.write(f"• {b['brf_name']}: {b.get('energy_performance'):.0f} kWh/m²")
                
                with col2:
                    # Average performers
                    average_buildings = [b for b in filtered_buildings if swedish_good < b.get('energy_performance', 200) <= swedish_poor]
                    if average_buildings:
                        st.warning(f"⚖️ **National Average**: {len(average_buildings)} buildings ({swedish_good+1}-{swedish_poor} kWh/m²)")
                        for b in average_buildings:
                            st.write(f"• {b['brf_name']}: {b.get('energy_performance'):.0f} kWh/m²")
                    
                    # Below average performers
                    poor_buildings = [b for b in filtered_buildings if b.get('energy_performance', 0) > swedish_poor]
                    if poor_buildings:
                        st.error(f"📈 **Below National Average**: {len(poor_buildings)} buildings (>{swedish_poor} kWh/m²)")
                        for b in poor_buildings:
                            st.write(f"• {b['brf_name']}: {b.get('energy_performance'):.0f} kWh/m²")
                
                # National insights
                st.markdown("---")
                st.markdown("##### 📊 National Context Insights")
                
                above_national = len([b for b in filtered_buildings if b.get('energy_performance', 200) < swedish_avg])
                below_national = len([b for b in filtered_buildings if b.get('energy_performance', 0) >= swedish_avg])
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"""
                    **🇸🇪 National Standing:**
                    - **{above_national}/{len(filtered_buildings)} buildings** perform better than Sweden average
                    - **{below_national}/{len(filtered_buildings)} buildings** need improvement to reach national average
                    - Hammarby Sjöstad is **{vs_sweden:+.0f}%** compared to Sweden overall
                    """)
                
                with col2:
                    # Performance distribution
                    top_30_pct = (len(excellent_buildings) / len(filtered_buildings)) * 100
                    st.markdown(f"""
                    **🏆 Excellence Rate:**
                    - **{top_30_pct:.0f}%** of your district is in Sweden's top 30%
                    - National target: 30% of buildings should be ≤{swedish_excellent} kWh/m²
                    - Your district {'✅ exceeds' if top_30_pct > 30 else '📈 is working toward'} this national goal
                    """)
            else:
                st.warning("No energy performance data available for national comparison.")
    
    with tab4:
        st.markdown("## 📊 Cost Comparison & Analysis")
        
        if not st.session_state.get('peer_data_unlocked', False):
            survey_system.create_unlock_mechanism_ui()
        else:
            st.success("🔓 Cost comparison data unlocked!")
            
            survey_data = st.session_state.get('current_survey', {})
            if survey_data and survey_data.get('costs'):
                # Find the current building
                current_building = None
                for building in buildings_data:
                    # Multiple matching criteria for robustness
                    if (building.get('id') == survey_data.get('building_id') or 
                        building.get('building_id') == survey_data.get('building_id') or
                        building.get('brf_name') == survey_data.get('building_name')):
                        current_building = building
                        break
                
                if current_building:
                    # Create comprehensive cost breakdown charts
                    survey_system.create_comprehensive_cost_breakdown_charts(
                        survey_data, current_building, context="cost_tab"
                    )
                    
                    # BRF-specific comparisons
                    survey_system._create_brf_specific_comparisons(survey_data, current_building)
                    
                    # Performance metrics
                    performance_metrics = survey_system.calculate_financial_performance_index(current_building)
                    
                    st.markdown("### 🎯 Performance Metrics")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(
                            "Energy Efficiency",
                            f"{performance_metrics['energy_efficiency_score']:.1f}/100"
                        )
                    
                    with col2:
                        st.metric(
                            "Cost Efficiency", 
                            f"{performance_metrics['cost_efficiency_score']:.1f}/100"
                        )
                    
                    with col3:
                        st.metric(
                            "Financial Performance Index",
                            f"{performance_metrics['financial_performance_index']:.1f}/100"
                        )
            else:
                st.info("Complete the survey to see detailed cost comparisons.")
    
    with tab5:
        st.markdown("## 💰 Smart Supplier Recommendations")
        
        # Get current survey progress
        survey_data = st.session_state.get('current_survey', {})
        progress = survey_system.calculate_progress(survey_data)
        
        # Show locked/unlocked supplier recommendations
        survey_system.create_locked_savings_analysis_ui(progress)
    
    with tab6:
        # Check if a BRF profile is selected for viewing
        selected_brf_name = st.session_state.get('selected_brf_profile', None)
        
        
        if selected_brf_name:
            # Show BRF profile inline with back button
            if st.button("← Back to Performance Index", key="back_to_performance"):
                del st.session_state.selected_brf_profile
                st.rerun()
            
            # Find the selected BRF
            selected_building = next((b for b in buildings_data if b['brf_name'] == selected_brf_name), None)
            if selected_building:
                # Calculate market position for this BRF
                all_buildings_with_scores = []
                for building in buildings_data:
                    score = building.get('performance_score', 0)
                    if score > 0:  # Only include buildings with valid scores
                        all_buildings_with_scores.append({
                            'name': building['brf_name'],
                            'score': score,
                            'is_current': building['brf_name'] == selected_brf_name
                        })
                
                # Sort by score descending to get rankings
                all_buildings_with_scores.sort(key=lambda x: x['score'], reverse=True)
                
                # Find position of selected BRF
                market_position = next((i+1 for i, b in enumerate(all_buildings_with_scores) if b['name'] == selected_brf_name), len(all_buildings_with_scores))
                
                # Show comprehensive BRF landing page
                create_brf_landing_page(selected_building, market_position, len(all_buildings_with_scores))
            else:
                st.error(f"BRF '{selected_brf_name}' not found in dataset.")
                if st.button("← Back to Performance Index", key="back_to_performance_error"):
                    del st.session_state.selected_brf_profile
                    st.rerun()
        else:
            # Show normal performance index view
            st.markdown("## 📈 BRF Financial Performance Index")
            
            # Find current building for analysis
            current_building = None
            survey_data = st.session_state.get('current_survey', {})
            if survey_data.get('building_id'):
                for building in buildings_data:
                    # Multiple matching criteria for robustness
                    if (building.get('id') == survey_data.get('building_id') or 
                        building.get('building_id') == survey_data.get('building_id') or
                        building.get('brf_name') == survey_data.get('building_name')):
                        current_building = building
                        break
            
            # If no survey completed, default to BRF Sjöstaden 2 for demo
            if not current_building and buildings_data:
                # Find Sjöstaden 2 as default demo building
                for building in buildings_data:
                    if 'sjöstaden' in building.get('brf_name', '').lower() and '2' in building.get('brf_name', ''):
                        current_building = building
                        break
                # Fallback to first building if Sjöstaden 2 not found
                if not current_building:
                    current_building = buildings_data[0]
                st.info(f"📊 Showing performance index for **{current_building['brf_name']}**. This is our demo BRF with pre-filled data.")
            
            if current_building:
                # Calculate performance metrics
                performance_metrics = survey_system.calculate_financial_performance_index(current_building)
                
                st.markdown("### 🏆 Financial Performance Index")
                
                # Main performance gauge
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Performance gauge chart
                    import plotly.graph_objects as go
                    
                    index_value = performance_metrics['financial_performance_index']
                    
                    # Determine gauge color based on performance
                    gauge_color = "#3498db"  # Default blue
                    if index_value >= 85:
                        gauge_color = "#27ae60"  # Excellent - green
                    elif index_value >= 70:
                        gauge_color = "#2ecc71"  # Good - light green
                    elif index_value >= 40:
                        gauge_color = "#f39c12"  # Average - orange
                    else:
                        gauge_color = "#e74c3c"  # Poor - red
                    
                    fig = go.Figure(go.Indicator(
                        mode = "gauge+number+delta",
                        value = index_value,
                        domain = {'x': [0, 1], 'y': [0, 1]},
                        title = {
                            'text': f"<b>{current_building['brf_name']}</b><br><span style='font-size:14px'>Performance Index</span>",
                            'font': {'size': 18, 'color': '#2c3e50', 'family': 'Arial'},
                            'align': 'center'
                        },
                        number = {
                            'font': {'size': 42, 'color': gauge_color, 'family': 'Arial Black'},
                            'suffix': '<span style="font-size:24px">/100</span>',
                            'valueformat': '.1f'
                        },
                        delta = {
                            'reference': 70,  # Market average reference
                            'relative': False,
                            'valueformat': '.1f',
                            'font': {'size': 16, 'color': '#666666'}
                        },
                        gauge = {
                            'axis': {
                                'range': [None, 100],
                                'tickwidth': 2,
                                'tickcolor': "#34495e",
                                'tickfont': {'size': 14, 'color': '#34495e', 'family': 'Arial'},
                                'tickmode': 'linear',
                                'tick0': 0,
                                'dtick': 20
                            },
                            'bar': {
                                'color': gauge_color,
                                'thickness': 0.75,
                                'line': {'color': 'white', 'width': 2}
                            },
                            'bgcolor': "#f8f9fa",
                            'borderwidth': 3,
                            'bordercolor': "#dee2e6",
                            'steps': [
                                {'range': [0, 40], 'color': "#ffebee", 'name': 'Needs Improvement'},
                                {'range': [40, 70], 'color': "#fff3e0", 'name': 'Average'}, 
                                {'range': [70, 85], 'color': "#e8f5e8", 'name': 'Good'},
                                {'range': [85, 100], 'color': "#e0f2f1", 'name': 'Excellent'}
                            ],
                            'threshold': {
                                'line': {'color': gauge_color, 'width': 4},
                                'thickness': 0.9,
                                'value': index_value
                            }
                        }
                    ))
                    
                    fig.update_layout(
                        height=400,
                        font={'color': "#2c3e50", 'family': "Arial"},
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        margin=dict(l=30, r=30, t=80, b=30),
                        annotations=[
                            dict(
                                text=f"<b>vs Market Avg (70)</b>",
                                xref="paper", yref="paper",
                                x=0.5, y=0.15,
                                xanchor='center', yanchor='middle',
                                font=dict(size=12, color='#666666', family='Arial'),
                                showarrow=False
                            )
                        ]
                    )
                    
                    st.plotly_chart(fig, use_container_width=True, key="performance_index_gauge")
                
                with col2:
                    st.markdown("#### 📊 Index Components")
                    
                    st.metric(
                        "Energy Efficiency",
                        f"{performance_metrics['energy_efficiency_score']:.1f}/100",
                        help="30% weighting in final index"
                    )
                    
                    st.metric(
                        "Cost Efficiency",
                        f"{performance_metrics['cost_efficiency_score']:.1f}/100",
                        help="70% weighting in final index"
                    )
                    
                    st.markdown("---")
                    
                    st.metric(
                        "Cost per m²",
                        f"{performance_metrics['cost_per_m2']:.0f} SEK",
                        delta=f"{performance_metrics['cost_per_m2'] - performance_metrics['market_average_cost_per_m2']:.0f}",
                        delta_color="inverse"
                    )
                    
                    st.metric(
                        "Building Size (estimated)",
                        f"{performance_metrics['total_m2']:.0f} m²",
                        help="Based on financial data analysis"
                    )
                
                # Performance ranking comparison
                st.markdown("### 🏆 Performance Ranking - All BRFs")
                
                # Calculate performance for all BRFs
                all_performances = []
                for building in buildings_data:
                    if building.get('total_cost') and building.get('total_cost') > 0:
                        perf_metrics = survey_system.calculate_financial_performance_index(building)
                        all_performances.append({
                            'name': building.get('brf_name', 'Unknown BRF'),
                            'score': perf_metrics['financial_performance_index'],
                            'cost_per_m2': perf_metrics['cost_per_m2'],
                            'energy_score': perf_metrics['energy_efficiency_score'],
                            'is_current': building.get('brf_name') == current_building.get('brf_name')
                        })
                
                # Sort by performance score (highest first)
                all_performances.sort(key=lambda x: x['score'], reverse=True)
                
                if all_performances:
                    # Create performance comparison chart with professional colors
                    names = [p['name'] for p in all_performances]
                    scores = [p['score'] for p in all_performances]
                    
                    # Professional color scheme
                    colors = []
                    for i, p in enumerate(all_performances):
                        if p['is_current']:
                            # Gold highlight for current building (premium, positive)
                            colors.append('#FFD700')
                        elif p['score'] >= 75:
                            # Excellent performance - deep green
                            colors.append('#2E8B57')
                        elif p['score'] >= 60:
                            # Good performance - blue
                            colors.append('#4682B4')
                        elif p['score'] >= 40:
                            # Average performance - orange
                            colors.append('#FF8C00')
                        else:
                            # Poor performance - red
                            colors.append('#DC143C')
                    
                    fig_ranking = go.Figure(data=[
                        go.Bar(
                            x=scores,
                            y=names,
                            orientation='h',
                            marker=dict(
                                color=colors,
                                line=dict(color='white', width=1),
                                opacity=0.85
                            ),
                            text=[f"{score:.1f}" for score in scores],
                            textposition='outside',
                            textfont=dict(size=12, color='#2c3e50', family='Arial Black'),
                            hovertemplate='<b>%{y}</b><br>Performance Index: %{x:.1f}/100<br><i>Click for details</i><extra></extra>',
                            # Add border highlight for current building
                            marker_line_width=[3 if p['is_current'] else 1 for p in all_performances],
                            marker_line_color=['#2c3e50' if p['is_current'] else 'white' for p in all_performances]
                        )
                    ])
                    
                    fig_ranking.update_layout(
                        title=dict(
                            text="🏆 BRF Financial Performance Index Rankings",
                            font=dict(size=18, color='#2c3e50', family='Arial Black'),
                            x=0.5,
                            xanchor='center'
                        ),
                        xaxis=dict(
                            title=dict(
                                text="Performance Index Score (0-100)",
                                font=dict(size=14, color='#2c3e50')
                            ),
                            range=[0, 100], 
                            gridcolor='#E8E8E8',
                            gridwidth=1,
                            tickfont=dict(size=11, color='#2c3e50'),
                            showline=True,
                            linecolor='#2c3e50',
                            linewidth=1
                        ),
                        yaxis=dict(
                            title="",
                            gridcolor='#F5F5F5',
                            gridwidth=0.5,
                            tickfont=dict(size=11, color='#2c3e50'),
                            showline=True,
                            linecolor='#2c3e50',
                            linewidth=1
                        ),
                        height=450,
                        showlegend=False,
                        plot_bgcolor='#FAFAFA',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(size=12, family='Arial', color='#2c3e50'),
                        margin=dict(l=220, r=60, t=60, b=60),
                        # Add professional styling
                        annotations=[
                            dict(
                                text="⭐ Gold = Current Building | 🟢 Green = Excellent | 🔵 Blue = Good | 🟠 Orange = Average | 🔴 Red = Needs Improvement",
                                xref="paper", yref="paper",
                                x=0.5, y=-0.15,
                                xanchor='center', yanchor='top',
                                font=dict(size=10, color='#666666'),
                                showarrow=False
                            )
                        ]
                    )
                    
                    # Handle chart clicks to show BRF details
                    chart_click = st.plotly_chart(fig_ranking, use_container_width=True, key="performance_ranking", on_select="rerun")
                    
                    # Check if a bar was clicked and show comprehensive BRF profile
                    if hasattr(st.session_state, 'performance_ranking') and st.session_state.performance_ranking and 'selection' in st.session_state.performance_ranking:
                        selection = st.session_state.performance_ranking['selection']
                        if selection and 'points' in selection and selection['points']:
                            # Get the clicked point
                            clicked_point = selection['points'][0]
                            if 'pointIndex' in clicked_point:
                                clicked_index = clicked_point['pointIndex']
                                if clicked_index < len(all_performances):
                                    selected_brf = all_performances[clicked_index]
                                    
                                    # Set the selected BRF and rerun to show profile
                                    st.session_state.selected_brf_profile = selected_brf['name']
                                    st.success(f"🏢 Loading profile for **{selected_brf['name']}**...")
                                    st.rerun()
                    
                    # Performance position analysis
                    current_position = next((i+1 for i, p in enumerate(all_performances) if p['is_current']), len(all_performances))
                    percentile = ((len(all_performances) - current_position + 1) / len(all_performances)) * 100
                    current_performance = next((p for p in all_performances if p['is_current']), None)
                    current_score = current_performance['score'] if current_performance else 0
                    
                    # Professional performance summary card
                    st.markdown("""
                    <div style="
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 20px;
                        border-radius: 12px;
                        margin: 20px 0;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    ">
                        <h3 style="margin: 0 0 15px 0; text-align: center;">📊 Your BRF Performance Summary</h3>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(
                            "🥇 Market Position", 
                            f"#{current_position} of {len(all_performances)}",
                            help="Your ranking among all BRFs in the dataset"
                        )
                    with col2:
                        # Fix the logical inconsistency - use percentile AND score for analysis
                        if current_position == 1:
                            st.success("🏆 **Market Leader**")
                        elif percentile >= 80:  # Top 20% 
                            st.success("🌟 **Excellent Performance**")
                        elif percentile >= 60:  # Top 40%
                            st.info("📈 **Above Average**")
                        elif percentile >= 40:  # Top 60%
                            st.warning("⚖️ **Average Performance**")
                        else:
                            st.error("🔧 **Improvement Potential**")
                    with col3:
                        # Show percentile with delta color logic
                        delta_color = "normal"
                        if percentile >= 80:
                            delta_text = "Excellent"
                            delta_color = "normal"
                        elif percentile >= 60:
                            delta_text = "Above Average" 
                            delta_color = "normal"
                        else:
                            delta_text = "Room for Growth"
                            delta_color = "inverse"
                            
                        st.metric(
                            "📊 Percentile Rank", 
                            f"{percentile:.0f}%",
                            delta=delta_text,
                            help=f"You perform better than {percentile:.0f}% of all BRFs"
                        )
                    
                    # Performance interpretation - FIXED LOGIC
                    st.markdown("### 🎯 Comprehensive Performance Analysis")
                    
                    # Use BOTH percentile rank AND index value for accurate analysis
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        # Fixed logical analysis based on percentile ranking
                        if current_position == 1:
                                st.success(f"""
                                **🏆 MARKET LEADER - OUTSTANDING PERFORMANCE!**
                                
                                **Congratulations!** Your BRF is the #1 performer in the entire market with a performance index of **{current_score:.1f}/100**.
                                
                                ✅ **Market Position**: #1 of {len(all_performances)} ({percentile:.0f}th percentile)  
                                ✅ **Status**: Industry benchmark and best practice example  
                                ✅ **Action**: Share your success strategies with other BRFs
                                """)
                        elif percentile >= 80:  # Top 20% - this fixes the BRF Sjöstaden 2 issue
                            st.success(f"""
                            **🌟 EXCELLENT PERFORMANCE - TOP TIER**
                            
                            Your BRF performs exceptionally well, ranking in the **top {100-percentile:.0f}%** of all properties with an index of **{current_score:.1f}/100**.
                            
                            ✅ **Market Position**: #{current_position} of {len(all_performances)} ({percentile:.0f}th percentile)  
                            ✅ **Status**: High-performing BRF with excellent cost and energy management  
                            ✅ **Action**: Fine-tune operations to potentially reach #1 position
                            """)
                        elif percentile >= 60:  # Top 40%
                            st.info(f"""
                            **📈 ABOVE AVERAGE PERFORMANCE - GOOD STANDING**
                            
                            Your BRF performs better than most properties, ranking in the **top {100-percentile:.0f}%** with an index of **{current_score:.1f}/100**.
                            
                            ℹ️ **Market Position**: #{current_position} of {len(all_performances)} ({percentile:.0f}th percentile)  
                            ℹ️ **Status**: Solid performer with room to reach top tier  
                            ℹ️ **Action**: Focus on specific cost categories to improve ranking
                            """)
                        elif percentile >= 40:  # Top 60%
                            st.warning(f"""
                            **⚖️ AVERAGE PERFORMANCE - MARKET LEVEL**
                            
                            Your BRF performs at market average levels, ranking in the **{percentile:.0f}th percentile** with an index of **{current_score:.1f}/100**.
                            
                            ⚠️ **Market Position**: #{current_position} of {len(all_performances)} (middle tier)  
                            ⚠️ **Status**: Typical market performance with improvement opportunities  
                            ⚠️ **Action**: Systematic review of energy and cost efficiency measures
                            """)
                        else:
                            st.error(f"""
                            **🔧 IMPROVEMENT POTENTIAL - FOCUS AREA**
                            
                            Your BRF has significant room for improvement, currently in the **bottom {100-percentile:.0f}%** with an index of **{current_score:.1f}/100**.
                            
                            🔴 **Market Position**: #{current_position} of {len(all_performances)} ({percentile:.0f}th percentile)  
                            🔴 **Status**: Below market average - priority improvement needed  
                            🔴 **Action**: Comprehensive energy audit and cost optimization program
                            """)
            
            with col2:
                        # Performance improvement roadmap
                        st.markdown("#### 🎯 Next Steps")
                        
                        if current_position > 1:
                            # Show what it takes to move up
                            next_target = all_performances[current_position - 2]  # Next higher position
                            score_gap = next_target['score'] - current_score
                            
                            st.info(f"""
                            **Move to Position #{current_position - 1}:**  
                            Improve by **{score_gap:.1f} points**
                            
                            **Target BRF:** {next_target['name']}  
                            **Their Score:** {next_target['score']:.1f}
                            """)
                            
                            if current_position <= len(all_performances) // 2:
                                st.success("🎯 **Top Half** - Great position to build from!")
                            else:
                                st.warning("📈 **Focus Areas** needed for improvement")
                        else:
                            st.success("🏆 **You're #1!** Help others improve.")
                
                else:
                    st.error("No building data available for performance analysis.")
    
    # Footer
    st.markdown("---")
    st.markdown(
        f"🏢 **Integrated BRF Dashboard** | Professional Property Management Platform | "
        f"Data: PostgreSQL + EPC + Excel + Booli.se | Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )

if __name__ == "__main__":
    main()