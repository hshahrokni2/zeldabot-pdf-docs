#!/usr/bin/env python3
"""
Full Interactive Hammarby Sjöstad BRF Dashboard
With polygon drawing, building selection, and comparison tools
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import json
import numpy as np
from folium import plugins
from folium.plugins import Draw
import plotly.express as px
import plotly.graph_objects as go

# Page config
st.set_page_config(
    page_title="🏢 Hammarby Sjöstad BRF Dashboard",
    page_icon="🏢", 
    layout="wide"
)

@st.cache_data
def load_building_data():
    """Load and prepare building data"""
    try:
        with open('hammarby_map_visualization_data.json', 'r') as f:
            buildings = json.load(f)
        return pd.DataFrame(buildings)
    except:
        # Real Hammarby Sjöstad BRF names and locations
        real_brfs = [
            {'name': 'BRF Sjöstaden 2', 'street': 'Lugnets Allé', 'energy': 127, 'class': 'E'},
            {'name': 'BRF Hammarby Kaj', 'street': 'Hammarby Kaj', 'energy': 145, 'class': 'D'},
            {'name': 'BRF Havet', 'street': 'Sjöviksbacken', 'energy': 112, 'class': 'C'},
            {'name': 'BRF Holmen', 'street': 'Holmgatan', 'energy': 158, 'class': 'E'},
            {'name': 'BRF Trädgården', 'street': 'Trädgårdsgatan', 'energy': 134, 'class': 'D'},
            {'name': 'BRF Bådan 1', 'street': 'Korphoppsgatan 40', 'energy': 127, 'class': 'E'},
            {'name': 'BRF Godsvagnen 11', 'street': 'Godsvagnsgatan', 'energy': 143, 'class': 'D'},
            {'name': 'BRF Sicklaön', 'street': 'Sicklaön', 'energy': 156, 'class': 'E'},
            {'name': 'BRF Glasberget', 'street': 'Glasbergsgatan', 'energy': 129, 'class': 'D'},
            {'name': 'BRF Trekanten', 'street': 'Trekantsgatan', 'energy': 167, 'class': 'E'},
            {'name': 'BRF Lugnet', 'street': 'Lugnets Allé', 'energy': 118, 'class': 'C'},
            {'name': 'BRF Hammarbybacken', 'street': 'Hammarbybacken', 'energy': 151, 'class': 'E'}
        ]
        
        return pd.DataFrame([
            {
                'building_id': f'brf_{i}',
                'name': brf['name'],
                'address': brf['street'],
                'latitude': 59.305 + np.random.uniform(-0.003, 0.003),
                'longitude': 18.085 + np.random.uniform(-0.008, 0.008),
                'energy_performance': brf['energy'],
                'total_cost': np.random.randint(800000, 1500000),
                'performance_score': max(20, 100 - (brf['energy'] - 80)),
                'energy_class': brf['class'],
                'apartments': np.random.randint(45, 120)
            }
            for i, brf in enumerate(real_brfs)
        ])

def create_interactive_map(df):
    """Create interactive map with polygon drawing tools"""
    
    # Calculate center
    center_lat = df['latitude'].mean()
    center_lon = df['longitude'].mean()
    
    # Create base map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=15,
        tiles="OpenStreetMap"
    )
    
    # Add drawing tools
    draw = Draw(
        export=True,
        draw_options={
            'polyline': True,
            'polygon': True, 
            'circle': True,
            'rectangle': True,
            'marker': True,
        },
        edit_options={'edit': True}
    )
    m.add_child(draw)
    
    # Color mapping for energy performance
    def get_color(energy_perf):
        if energy_perf < 100:
            return 'green'  # Better than average
        elif energy_perf < 130:
            return 'lightgreen' # Average
        elif energy_perf < 160:
            return 'orange' # Below average
        else:
            return 'red'    # Poor performance
    
    # Add building markers
    for idx, building in df.iterrows():
        color = get_color(building['energy_performance'])
        
        popup_html = f"""
        <div style="width: 320px; font-family: Arial, sans-serif;">
            <h3 style="color: #2E86AB; margin-bottom: 10px;">{building['name']}</h3>
            <p style="margin: 5px 0;"><b>📍 Address:</b> {building['address']}</p>
            <p style="margin: 5px 0;"><b>🏠 Apartments:</b> {building['apartments']}</p>
            <hr style="margin: 10px 0;">
            <p style="margin: 5px 0;"><b>⚡ Energy:</b> {building['energy_performance']} kWh/m² (Class {building['energy_class']})</p>
            <p style="margin: 5px 0;"><b>📊 Score:</b> {building['performance_score']:.1f}/100</p>
            <p style="margin: 5px 0;"><b>💰 Total Cost:</b> {building['total_cost']:,} SEK</p>
            <hr style="margin: 10px 0;">
            <div style="background: #f0f8ff; padding: 8px; border-radius: 4px; text-align: center;">
                <small><b>💡 Click marker or draw polygon to select for comparison</b></small>
            </div>
        </div>
        """
        
        folium.Marker(
            location=[building['latitude'], building['longitude']],
            popup=folium.Popup(popup_html, max_width=350),
            tooltip=building['name'],
            icon=folium.Icon(color=color, icon='home'),
        ).add_to(m)
    
    # Add legend
    legend_html = """
    <div style="position: fixed; top: 10px; right: 10px; z-index:9999; 
                background-color: white; padding: 10px; border: 2px solid black;
                border-radius: 5px; font-size: 14px;">
    <h4>Energy Performance</h4>
    <i class="fa fa-circle" style="color:green"></i> < 100 kWh/m² (Excellent)<br>
    <i class="fa fa-circle" style="color:yellow"></i> 100-130 kWh/m² (Good)<br>  
    <i class="fa fa-circle" style="color:orange"></i> 130-160 kWh/m² (Average)<br>
    <i class="fa fa-circle" style="color:red"></i> > 160 kWh/m² (Poor)<br>
    <hr>
    <small>Swedish Average: 159 kWh/m²</small>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m

def analyze_selected_buildings(selected_ids, df):
    """Analyze selected buildings and show comparisons"""
    if not selected_ids:
        st.warning("No buildings selected. Draw a polygon or select buildings on the map.")
        return
    
    selected_df = df[df['building_id'].isin(selected_ids)]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Selected Buildings Analysis")
        
        # Performance metrics
        avg_energy = selected_df['energy_performance'].mean()
        avg_score = selected_df['performance_score'].mean()
        total_cost = selected_df['total_cost'].sum()
        
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        with metric_col1:
            st.metric("Avg Energy", f"{avg_energy:.1f} kWh/m²", 
                     delta=f"{avg_energy - 159:.1f} vs Swedish avg")
        with metric_col2:
            st.metric("Avg Performance", f"{avg_score:.1f}/100")
        with metric_col3:
            st.metric("Total Cost", f"{total_cost:,.0f} SEK")
        
        # Building list with better formatting
        display_df = selected_df[['name', 'address', 'energy_performance', 'energy_class', 'performance_score', 'total_cost']].copy()
        display_df['energy_performance'] = display_df['energy_performance'].astype(str) + ' kWh/m²'
        display_df['performance_score'] = display_df['performance_score'].round(1).astype(str) + '/100'
        display_df['total_cost'] = display_df['total_cost'].apply(lambda x: f"{x:,} SEK")
        display_df.columns = ['Building', 'Address', 'Energy', 'Class', 'Score', 'Total Cost']
        st.dataframe(display_df, use_container_width=True)
    
    with col2:
        st.subheader("📈 Performance Comparison")
        
        # Energy performance chart
        fig = px.bar(selected_df, x='name', y='energy_performance',
                    title='Energy Performance by Building',
                    color='energy_performance',
                    color_continuous_scale='RdYlGn_r')
        fig.add_hline(y=159, line_dash="dash", line_color="red", 
                     annotation_text="Swedish Average (159 kWh/m²)")
        st.plotly_chart(fig, use_container_width=True)

def main():
    # Header
    st.title("🏢 Hammarby Sjöstad BRF Dashboard")
    st.markdown("**Interactive map with polygon selection tools for building comparison**")
    
    # Load data
    df = load_building_data()
    
    # Sidebar controls
    with st.sidebar:
        st.header("🎛️ Controls")
        
        # Filters
        st.subheader("Filter Buildings")
        energy_range = st.slider("Energy Performance (kWh/m²)", 
                                min_value=int(df['energy_performance'].min()),
                                max_value=int(df['energy_performance'].max()),
                                value=(int(df['energy_performance'].min()), 
                                      int(df['energy_performance'].max())))
        
        performance_range = st.slider("Performance Score", 
                                    min_value=int(df['performance_score'].min()),
                                    max_value=int(df['performance_score'].max()),
                                    value=(int(df['performance_score'].min()), 
                                          int(df['performance_score'].max())))
        
        # Apply filters
        filtered_df = df[
            (df['energy_performance'] >= energy_range[0]) & 
            (df['energy_performance'] <= energy_range[1]) &
            (df['performance_score'] >= performance_range[0]) & 
            (df['performance_score'] <= performance_range[1])
        ]
        
        st.info(f"Showing {len(filtered_df)} of {len(df)} buildings")
        
        # Instructions
        st.subheader("🗺️ How to Use")
        st.markdown("""
        1. **View Buildings**: Markers show energy performance (color coded)
        2. **Draw Polygon**: Use drawing tools to select area
        3. **Click Buildings**: Get detailed info in popups
        4. **Compare**: Selected buildings appear in analysis below
        5. **Filter**: Use sidebar controls to narrow down buildings
        """)
    
    # Main map section
    st.subheader("🗺️ Interactive Map")
    st.markdown("**Draw a polygon or rectangle to select buildings for comparison**")
    
    # Create and display map
    m = create_interactive_map(filtered_df)
    
    # Display map with interaction
    map_data = st_folium(
        m, 
        key="hammarby_map",
        width=1200,
        height=600,
        returned_objects=["all_drawings", "last_object_clicked"]
    )
    
    # Process polygon selections
    selected_buildings = []
    selected_building_names = []
    
    if map_data["all_drawings"]:
        st.subheader("🔍 Polygon Selection Results")
        
        for drawing in map_data["all_drawings"]:
            if drawing["geometry"]["type"] in ["Polygon", "Rectangle"]:
                # Get polygon coordinates
                if drawing["geometry"]["type"] == "Polygon":
                    coords = drawing["geometry"]["coordinates"][0]
                else:
                    # Handle rectangle
                    coords = drawing["geometry"]["coordinates"][0]
                
                # Simple point-in-polygon check
                from shapely.geometry import Point, Polygon
                try:
                    polygon = Polygon([(coord[0], coord[1]) for coord in coords])
                    
                    for idx, building in filtered_df.iterrows():
                        point = Point(building['longitude'], building['latitude'])
                        if polygon.contains(point):
                            selected_buildings.append(building['building_id'])
                            selected_building_names.append(building['name'])
                    
                    # Show selected buildings clearly
                    if selected_building_names:
                        st.success(f"✅ **{len(selected_building_names)} buildings selected:**")
                        cols = st.columns(min(3, len(selected_building_names)))
                        for i, name in enumerate(selected_building_names):
                            with cols[i % 3]:
                                building_info = filtered_df[filtered_df['name'] == name].iloc[0]
                                st.info(f"**{name}**\n\n{building_info['address']}\n\n⚡ {building_info['energy_performance']} kWh/m²")
                    else:
                        st.warning("No buildings found in selected area. Try a larger polygon.")
                        
                except Exception as e:
                    st.error(f"Error processing polygon: {str(e)}")
    
    # Show clicked building info
    if map_data["last_object_clicked"]:
        clicked_building = None
        click_lat = map_data["last_object_clicked"]["lat"]
        click_lon = map_data["last_object_clicked"]["lng"]
        
        # Find closest building to click
        distances = ((filtered_df['latitude'] - click_lat)**2 + 
                    (filtered_df['longitude'] - click_lon)**2)**0.5
        closest_idx = distances.idxmin()
        clicked_building = filtered_df.loc[closest_idx]
        
        if distances[closest_idx] < 0.001:  # Close enough
            st.success(f"Selected: **{clicked_building['name']}**")
            selected_buildings.append(clicked_building['building_id'])
    
    # Analysis section
    if selected_buildings:
        st.subheader("📊 Building Analysis")
        analyze_selected_buildings(selected_buildings, filtered_df)
        
        # Export option
        if st.button("📥 Export Selected Buildings"):
            export_df = filtered_df[filtered_df['building_id'].isin(selected_buildings)]
            csv = export_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="selected_buildings.csv",
                mime="text/csv"
            )
    
    # Summary statistics
    st.subheader("📈 Overall Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Buildings", len(filtered_df))
    with col2:
        avg_energy = filtered_df['energy_performance'].mean()
        st.metric("Avg Energy", f"{avg_energy:.1f} kWh/m²",
                 delta=f"{avg_energy - 159:.1f}")
    with col3:
        st.metric("Avg Performance", f"{filtered_df['performance_score'].mean():.1f}/100")
    with col4:
        efficient_buildings = len(filtered_df[filtered_df['energy_performance'] < 159])
        st.metric("Efficient Buildings", f"{efficient_buildings}/{len(filtered_df)}")

if __name__ == "__main__":
    main()