#!/usr/bin/env python3
"""
Killer EGHS Interactive Map Dashboard
====================================

A professional interactive mapping dashboard for analyzing 9 buildings in Hammarby Sjöstad
with real coordinates, energy performance data, and comprehensive cost analysis.

Features:
- Real building markers with energy performance color coding
- Interactive polygon drawing tools for area selection
- Rich popups with building details
- Energy performance benchmarking vs Swedish average (159 kWh/m²)
- Cost analysis and building comparison
- Export functionality
- Mobile-responsive design

Data Source: Complete EGHS dataset with coordinates from PostgreSQL + Booli.se
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import json
import pandas as pd
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page configuration
st.set_page_config(
    page_title="EGHS Interactive Map Dashboard",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f4e79 0%, #2d5aa0 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        text-align: center;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #1f4e79;
        margin: 10px 0;
    }
    .energy-class-A { background: #22c55e !important; }
    .energy-class-B { background: #84cc16 !important; }
    .energy-class-C { background: #eab308 !important; }
    .energy-class-D { background: #f59e0b !important; }
    .energy-class-E { background: #f97316 !important; }
    .energy-class-F { background: #dc2626 !important; }
    .energy-class-G { background: #991b1b !important; }
    
    .selected-building {
        border: 2px solid #ff4b4b;
        background-color: #fff5f5;
        border-radius: 8px;
        padding: 10px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_eghs_data():
    """Load the complete EGHS dataset with real coordinates"""
    try:
        with open('/Users/hosseins/Dropbox/Zelda/ZeldaDemo/killer_eghs_dataset_with_booli_coords.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        st.error("Dataset file not found!")
        return []
    except json.JSONDecodeError:
        st.error("Invalid JSON format in dataset!")
        return []

def get_energy_class_color(energy_class):
    """Get color code for energy class"""
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
    """Compare performance to Swedish average (159 kWh/m²)"""
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
    """Create rich HTML popup for building markers"""
    perf_text, perf_color = get_performance_vs_swedish_avg(building.get('energy_performance'))
    
    # Format costs safely
    total_cost = building.get('total_cost', 0)
    monthly_fee = building.get('monthly_fee', 0)
    
    popup_html = f"""
    <div style="width: 300px; font-family: Arial, sans-serif;">
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
    """Create the base folium map centered on Hammarby Sjöstad"""
    # Calculate center from all buildings
    lats = [b['latitude'] for b in buildings_data if b.get('latitude')]
    lngs = [b['longitude'] for b in buildings_data if b.get('longitude')]
    
    center_lat = np.mean(lats) if lats else 59.3045
    center_lng = np.mean(lngs) if lngs else 18.103
    
    # Create map
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
    """Add interactive building markers to the map"""
    for building in buildings_data:
        if not building.get('latitude') or not building.get('longitude'):
            continue
            
        # Create marker with energy class color
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
        
        # Add marker with popup
        folium.Marker(
            location=[building['latitude'], building['longitude']],
            popup=folium.Popup(create_building_popup(building), max_width=350),
            tooltip=f"{building['brf_name']} - Energy Class {energy_class}",
            icon=folium.DivIcon(html=icon_html, icon_size=(30, 30), icon_anchor=(15, 15))
        ).add_to(m)
    
    return m

def add_drawing_tools(m):
    """Add polygon drawing tools to the map"""
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
        },
        edit_options={'featureGroup': None}
    )
    draw.add_to(m)
    return m

def point_in_polygon(point, polygon):
    """Check if a point is inside a polygon using ray casting algorithm"""
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
    """Get buildings that fall within the selected area"""
    selected_buildings = []
    
    if map_data.get('last_object_clicked_tooltip'):
        # Single building selection via marker click
        tooltip = map_data['last_object_clicked_tooltip']
        for building in buildings_data:
            if building['brf_name'] in tooltip:
                selected_buildings.append(building)
                break
    
    if map_data.get('all_drawings') and len(map_data['all_drawings']) > 0:
        # Polygon/area selection
        for drawing in map_data['all_drawings']:
            if drawing['geometry']['type'] == 'Polygon':
                polygon_coords = drawing['geometry']['coordinates'][0]
                # Convert to [lat, lng] format
                polygon_points = [(coord[1], coord[0]) for coord in polygon_coords]
                
                for building in buildings_data:
                    if building.get('latitude') and building.get('longitude'):
                        building_point = (building['latitude'], building['longitude'])
                        if point_in_polygon(building_point, polygon_points):
                            selected_buildings.append(building)
            
            elif drawing['geometry']['type'] == 'Point':
                # Circle selection (approximate)
                center = drawing['geometry']['coordinates']
                center_point = (center[1], center[0])  # [lat, lng]
                radius = 0.005  # Approximate radius in degrees
                
                for building in buildings_data:
                    if building.get('latitude') and building.get('longitude'):
                        building_point = (building['latitude'], building['longitude'])
                        distance = np.sqrt((building_point[0] - center_point[0])**2 + 
                                         (building_point[1] - center_point[1])**2)
                        if distance <= radius:
                            selected_buildings.append(building)
    
    return selected_buildings

def create_energy_performance_chart(buildings_data, selected_buildings=None):
    """Create energy performance comparison chart"""
    df = pd.DataFrame(buildings_data)
    
    # Swedish average line
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

def create_cost_analysis_chart(buildings_data, selected_buildings=None):
    """Create cost analysis chart"""
    # Prepare cost breakdown data
    cost_categories = ['cost_electricity', 'cost_heating', 'cost_water', 'cost_internet_and_tv', 'cost_recycling']
    
    df = pd.DataFrame(buildings_data)
    
    fig = go.Figure()
    
    colors = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6']
    
    for i, category in enumerate(cost_categories):
        if category in df.columns:
            fig.add_trace(go.Bar(
                name=category.replace('cost_', '').replace('_', ' ').title(),
                x=df['brf_name'],
                y=df[category],
                marker_color=colors[i % len(colors)]
            ))
    
    # Highlight selected buildings
    if selected_buildings:
        selected_names = [b['brf_name'] for b in selected_buildings]
        shapes = []
        for name in selected_names:
            if name in df['brf_name'].values:
                idx = df[df['brf_name'] == name].index[0]
                shapes.append(
                    dict(
                        type="rect",
                        xref="x", yref="paper",
                        x0=idx-0.4, y0=0,
                        x1=idx+0.4, y1=1,
                        fillcolor="rgba(255, 75, 75, 0.1)",
                        line=dict(color="rgba(255, 75, 75, 0.8)", width=3),
                    )
                )
        
        fig.update_layout(shapes=shapes)
    
    fig.update_layout(
        title="Cost Breakdown by Building",
        xaxis_title="Building",
        yaxis_title="Cost (SEK)",
        height=500,
        barmode='stack',
        xaxis_tickangle=-45
    )
    
    return fig

def create_comparison_table(selected_buildings):
    """Create comparison table for selected buildings"""
    if not selected_buildings:
        return pd.DataFrame()
    
    comparison_data = []
    for building in selected_buildings:
        perf_text, _ = get_performance_vs_swedish_avg(building.get('energy_performance'))
        
        comparison_data.append({
            'Building': building['brf_name'],
            'Address': building['formatted_address'],
            'Energy Class': building.get('energy_class', 'N/A'),
            'Performance (kWh/m²)': building.get('energy_performance', 'N/A'),
            'vs Swedish Avg': perf_text,
            'Construction Year': building.get('construction_year', 'N/A'),
            'Total Cost (SEK)': f"{building.get('total_cost', 0):,}",
            'Monthly Fee (SEK)': f"{building.get('monthly_fee', 0):,}" if building.get('monthly_fee') else 'N/A',
            'Properties': building.get('property_count', 'N/A')
        })
    
    return pd.DataFrame(comparison_data)

def main():
    """Main application"""
    # Header
    st.markdown('<div class="main-header"><h1>🏢 EGHS Interactive Map Dashboard</h1><p>Professional energy performance analysis for 9 buildings in Hammarby Sjöstad</p></div>', 
                unsafe_allow_html=True)
    
    # Load data
    buildings_data = load_eghs_data()
    if not buildings_data:
        st.error("No data available!")
        return
    
    # Sidebar controls
    with st.sidebar:
        st.header("🎛️ Dashboard Controls")
        
        # Dataset info
        st.info(f"📊 **Dataset**: {len(buildings_data)} buildings with real coordinates")
        
        # Energy class filter
        st.subheader("Filter by Energy Class")
        available_classes = sorted(list(set(b.get('energy_class', 'N/A') for b in buildings_data)))
        selected_classes = st.multiselect(
            "Select Energy Classes:",
            available_classes,
            default=available_classes
        )
        
        # Performance filter
        st.subheader("Filter by Performance")
        performance_values = [b.get('energy_performance') for b in buildings_data if b.get('energy_performance')]
        if performance_values:
            perf_range = st.slider(
                "Energy Performance Range (kWh/m²):",
                min_value=int(min(performance_values)),
                max_value=int(max(performance_values)),
                value=(int(min(performance_values)), int(max(performance_values)))
            )
        else:
            perf_range = (0, 200)
        
        # Export options
        st.subheader("📤 Export Options")
        if st.button("Export All Data"):
            csv = pd.DataFrame(buildings_data).to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"eghs_buildings_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    # Filter buildings
    filtered_buildings = []
    for building in buildings_data:
        energy_class = building.get('energy_class', 'N/A')
        performance = building.get('energy_performance')
        
        if energy_class in selected_classes:
            if performance is None or perf_range[0] <= performance <= perf_range[1]:
                filtered_buildings.append(building)
    
    # Main content - Two columns
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🗺️ Interactive Map")
        st.info("💡 **Instructions**: Click markers for details, use drawing tools to select areas, draw polygons to compare buildings")
        
        # Create and display map
        m = create_base_map(filtered_buildings)
        m = add_building_markers(m, filtered_buildings)
        m = add_drawing_tools(m)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Display map
        map_data = st_folium(
            m,
            width=700,
            height=600,
            returned_objects=["last_object_clicked_tooltip", "all_drawings"]
        )
    
    with col2:
        st.subheader("📊 Quick Stats")
        
        # Overall statistics
        total_buildings = len(filtered_buildings)
        avg_performance = np.mean([b.get('energy_performance', 0) for b in filtered_buildings if b.get('energy_performance')])
        avg_cost = np.mean([b.get('total_cost', 0) for b in filtered_buildings if b.get('total_cost')])
        
        st.metric("Total Buildings", total_buildings)
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
                f'<div class="energy-class-{ec}" style="padding: 5px; margin: 2px; border-radius: 5px; color: white; text-align: center;">'
                f'Class {ec}: {count} buildings</div>',
                unsafe_allow_html=True
            )
    
    # Selection analysis
    selected_buildings = get_buildings_in_selection(filtered_buildings, map_data)
    
    if selected_buildings:
        st.header(f"🎯 Selected Buildings Analysis ({len(selected_buildings)} buildings)")
        
        # Selected buildings cards
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
        
        # Comparison table
        st.subheader("📋 Detailed Comparison")
        comparison_df = create_comparison_table(selected_buildings)
        if not comparison_df.empty:
            st.dataframe(comparison_df, use_container_width=True)
            
            # Export selected data
            if st.button("Export Selected Buildings"):
                csv = comparison_df.to_csv(index=False)
                st.download_button(
                    label="Download Selected Data",
                    data=csv,
                    file_name=f"selected_buildings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
    
    # Charts section
    st.header("📈 Performance Analysis")
    
    # Create tabs for different analyses
    tab1, tab2 = st.tabs(["Energy Performance", "Cost Analysis"])
    
    with tab1:
        fig_energy = create_energy_performance_chart(filtered_buildings, selected_buildings)
        st.plotly_chart(fig_energy, use_container_width=True)
        
        # Performance insights
        st.subheader("🔍 Performance Insights")
        excellent_buildings = [b for b in filtered_buildings if b.get('energy_performance', 200) <= 111]  # 70% of Swedish avg
        poor_buildings = [b for b in filtered_buildings if b.get('energy_performance', 0) > 190]  # 120% of Swedish avg
        
        col1, col2 = st.columns(2)
        with col1:
            st.success(f"✅ **Excellent Performance**: {len(excellent_buildings)} buildings")
            for b in excellent_buildings:
                st.write(f"- {b['brf_name']}: {b.get('energy_performance', 'N/A')} kWh/m²")
        
        with col2:
            if poor_buildings:
                st.warning(f"⚠️ **Poor Performance**: {len(poor_buildings)} buildings")
                for b in poor_buildings:
                    st.write(f"- {b['brf_name']}: {b.get('energy_performance', 'N/A')} kWh/m²")
            else:
                st.info("🎉 No buildings with poor performance!")
    
    with tab2:
        fig_cost = create_cost_analysis_chart(filtered_buildings, selected_buildings)
        st.plotly_chart(fig_cost, use_container_width=True)
        
        # Cost insights
        st.subheader("💰 Cost Insights")
        cost_data = [(b['brf_name'], b.get('total_cost', 0)) for b in filtered_buildings if b.get('total_cost')]
        if cost_data:
            cost_data.sort(key=lambda x: x[1], reverse=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.error(f"📈 **Highest Costs** (Top 3):")
                for name, cost in cost_data[:3]:
                    st.write(f"- {name}: {cost:,} SEK")
            
            with col2:
                st.success(f"📉 **Lowest Costs** (Bottom 3):")
                for name, cost in cost_data[-3:]:
                    st.write(f"- {name}: {cost:,} SEK")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "🏢 **EGHS Dashboard** | Data sources: PostgreSQL + Booli.se coordinates | "
        f"Energy Performance Certificates | Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )

if __name__ == "__main__":
    main()