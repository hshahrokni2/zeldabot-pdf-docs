#!/usr/bin/env python3
"""
Simple Working BRF Dashboard
Using properly merged data from all sources
"""

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go

# Page config
st.set_page_config(
    page_title="🏢 Hammarby Sjöstad BRF Dashboard",
    page_icon="🏢", 
    layout="wide"
)

@st.cache_data
def load_unified_data():
    """Load the unified merged data"""
    with open('hammarby_unified_data.json', 'r') as f:
        data = json.load(f)
    return pd.DataFrame(data)

def create_simple_map(df, selected_buildings=None):
    """Create simple interactive map"""
    center_lat = df['latitude'].mean()
    center_lon = df['longitude'].mean()
    
    m = folium.Map(location=[center_lat, center_lon], zoom_start=15)
    
    for _, building in df.iterrows():
        # Color by energy efficiency
        if building['energy_performance'] < 100:
            color = 'green'
        elif building['energy_performance'] < 130:
            color = 'lightgreen' 
        elif building['energy_performance'] < 160:
            color = 'orange'
        else:
            color = 'red'
        
        # Highlight if selected
        if selected_buildings and building['building_id'] in selected_buildings:
            color = 'blue'
            icon = folium.Icon(color=color, icon='star')
        else:
            icon = folium.Icon(color=color, icon='home')
        
        popup_html = f"""
        <div style="width: 300px;">
            <h3 style="color: #2E86AB;">{building['name']}</h3>
            <p><b>📍</b> {building['address']}</p>
            <p><b>🏠</b> {building['apartments']} apartments</p>
            <hr>
            <p><b>⚡ Energy:</b> {building['energy_performance']} kWh/m² (Class {building['energy_class']})</p>
            <p><b>📊 Score:</b> {building['performance_score']:.1f}/100</p>
            <p><b>💰 Total Cost:</b> {building['total_cost']:,} SEK</p>
        </div>
        """
        
        folium.Marker(
            location=[building['latitude'], building['longitude']],
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=building['name'],
            icon=icon
        ).add_to(m)
    
    return m

def main():
    # Load data
    df = load_unified_data()
    
    # Header
    st.title("🏢 Hammarby Sjöstad BRF Dashboard")
    st.markdown("**Real data merged from PostgreSQL, EPC certificates, and cost records**")
    
    # Sidebar for building selection
    with st.sidebar:
        st.header("🎛️ Building Selection")
        
        # Multi-select for buildings
        selected_building_names = st.multiselect(
            "Select buildings to compare:",
            options=df['name'].tolist(),
            default=[]
        )
        
        selected_buildings = df[df['name'].isin(selected_building_names)]['building_id'].tolist()
        
        st.markdown("---")
        
        # Filters
        st.subheader("🔍 Filters")
        
        energy_range = st.slider(
            "Energy Performance (kWh/m²)",
            min_value=int(df['energy_performance'].min()),
            max_value=int(df['energy_performance'].max()),
            value=(int(df['energy_performance'].min()), int(df['energy_performance'].max()))
        )
        
        cost_range = st.slider(
            "Total Cost (SEK)",
            min_value=int(df['total_cost'].min()),
            max_value=int(df['total_cost'].max()),
            value=(int(df['total_cost'].min()), int(df['total_cost'].max())),
            format="%d"
        )
        
        # Apply filters
        filtered_df = df[
            (df['energy_performance'] >= energy_range[0]) & 
            (df['energy_performance'] <= energy_range[1]) &
            (df['total_cost'] >= cost_range[0]) & 
            (df['total_cost'] <= cost_range[1])
        ]
        
        st.info(f"Showing {len(filtered_df)} of {len(df)} buildings")
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🗺️ Interactive Map")
        st.markdown("**Click buildings to see details, or select from sidebar for comparison**")
        
        # Create and display map
        m = create_simple_map(filtered_df, selected_buildings)
        map_data = st_folium(m, key="brf_map", width=800, height=500)
        
        # Show clicked building info
        if map_data and map_data.get("last_object_clicked"):
            click_lat = map_data["last_object_clicked"]["lat"]
            click_lon = map_data["last_object_clicked"]["lng"]
            
            # Find closest building
            distances = ((filtered_df['latitude'] - click_lat)**2 + 
                        (filtered_df['longitude'] - click_lon)**2)**0.5
            
            if distances.min() < 0.001:  # Close enough
                closest_building = filtered_df.loc[distances.idxmin()]
                st.success(f"**Selected: {closest_building['name']}**")
                
                # Show building details
                with st.expander(f"Details for {closest_building['name']}", expanded=True):
                    detail_col1, detail_col2, detail_col3 = st.columns(3)
                    
                    with detail_col1:
                        st.metric("Energy Performance", f"{closest_building['energy_performance']} kWh/m²",
                                 delta=f"{closest_building['energy_performance'] - 159:.0f} vs Swedish avg")
                    
                    with detail_col2:
                        st.metric("Performance Score", f"{closest_building['performance_score']:.1f}/100")
                    
                    with detail_col3:
                        st.metric("Total Annual Cost", f"{closest_building['total_cost']:,} SEK")
    
    with col2:
        st.subheader("📊 Quick Stats")
        
        # Overall metrics
        st.metric("Total Buildings", len(filtered_df))
        st.metric("Avg Energy", f"{filtered_df['energy_performance'].mean():.1f} kWh/m²")
        st.metric("Avg Cost", f"{filtered_df['total_cost'].mean():,.0f} SEK")
        
        # Energy class distribution
        st.subheader("🔋 Energy Classes")
        energy_counts = filtered_df['energy_class'].value_counts()
        for class_name, count in energy_counts.items():
            st.write(f"**Class {class_name}:** {count} buildings")
    
    # Comparison section
    if selected_building_names:
        st.subheader("🔍 Building Comparison")
        
        selected_df = df[df['name'].isin(selected_building_names)]
        
        # Comparison table
        comparison_df = selected_df[[
            'name', 'address', 'energy_performance', 'energy_class', 
            'performance_score', 'total_cost', 'apartments'
        ]].copy()
        
        comparison_df.columns = [
            'Building', 'Address', 'Energy (kWh/m²)', 'Class', 
            'Score (/100)', 'Total Cost (SEK)', 'Apartments'
        ]
        
        st.dataframe(comparison_df, use_container_width=True)
        
        # Charts
        if len(selected_df) > 1:
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                # Energy performance comparison
                fig_energy = px.bar(
                    selected_df, 
                    x='name', 
                    y='energy_performance',
                    title='Energy Performance Comparison',
                    color='energy_performance',
                    color_continuous_scale='RdYlGn_r'
                )
                fig_energy.add_hline(y=159, line_dash="dash", line_color="red", 
                                    annotation_text="Swedish Average")
                fig_energy.update_xaxis(tickangle=45)
                st.plotly_chart(fig_energy, use_container_width=True)
            
            with chart_col2:
                # Cost breakdown pie chart for first selected building
                first_building = selected_df.iloc[0]
                cost_categories = {
                    'Heating': first_building['cost_heating'],
                    'Electricity': first_building['cost_electricity'], 
                    'Cleaning': first_building['cost_cleaning'],
                    'Water': first_building['cost_water'],
                    'Snow Removal': first_building['cost_snow_removal'],
                    'Internet/TV': first_building['cost_internet_and_tv'],
                    'Recycling': first_building['cost_recycling']
                }
                
                fig_pie = px.pie(
                    values=list(cost_categories.values()),
                    names=list(cost_categories.keys()),
                    title=f'Cost Breakdown: {first_building["name"]}'
                )
                st.plotly_chart(fig_pie, use_container_width=True)
    
    # All buildings table
    st.subheader("📋 All Buildings")
    
    display_df = filtered_df[[
        'name', 'address', 'energy_performance', 'energy_class', 
        'performance_score', 'total_cost', 'apartments'
    ]].copy()
    
    display_df.columns = [
        'Building', 'Address', 'Energy (kWh/m²)', 'Class', 
        'Score (/100)', 'Total Cost (SEK)', 'Apartments'
    ]
    
    st.dataframe(display_df, use_container_width=True)
    
    # Export functionality
    if st.button("📥 Export Data"):
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name="hammarby_brf_data.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()