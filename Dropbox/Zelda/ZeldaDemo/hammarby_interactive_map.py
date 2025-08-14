#!/usr/bin/env python3
"""
Interactive Hammarby Sjöstad Map with Polygon Selection Tools

This application provides an interactive mapping interface for exploring
building performance data in Hammarby Sjöstad, with polygon drawing tools
for area selection and building analysis workflow integration.

Features:
- Interactive Folium map with Streamlit interface
- Building markers with energy performance color coding
- Polygon drawing tools for area selection
- Detailed popups with building metrics
- Layer controls for different data visualizations
- Export functionality for selected buildings
- Integration with database for document retrieval workflow
"""

import streamlit as st
import folium
from folium import plugins
from folium.plugins import Draw, MarkerCluster
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import sys

# Import our polygon selection handler
try:
    from polygon_selection_handler import PolygonSelectionHandler, integrate_with_database, create_selection_report
except ImportError:
    st.error("polygon_selection_handler.py not found. Please ensure all files are in the correct location.")
    st.stop()

# Import database integration if available
try:
    from database_integration import DatabaseConnector
    DB_INTEGRATION_AVAILABLE = True
except ImportError:
    DB_INTEGRATION_AVAILABLE = False

# Configuration
HAMMARBY_CENTER = [59.305, 18.085]
SWEDISH_ENERGY_BENCHMARK = 159  # kWh/m²

class HammarbyMapInterface:
    """Interactive map interface for Hammarby Sjöstad building analysis."""
    
    def __init__(self, data_file: str):
        """Initialize the map interface with building data."""
        self.data = self.load_map_data(data_file)
        self.buildings = self.data.get('buildings', [])
        self.selected_buildings = []
        
        # Initialize polygon selection handler
        self.polygon_handler = PolygonSelectionHandler(self.buildings)
        
        # Initialize session state for polygon selections
        if 'polygon_selections' not in st.session_state:
            st.session_state.polygon_selections = []
        if 'selected_building_ids' not in st.session_state:
            st.session_state.selected_building_ids = []
        
    def load_map_data(self, file_path: str) -> Dict:
        """Load building visualization data from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            st.error(f"Data file not found: {file_path}")
            return {'buildings': [], 'metadata': {}, 'summary_statistics': {}}
    
    def get_energy_color(self, building: Dict) -> str:
        """Get color coding based on energy performance vs Swedish average."""
        efficiency_ratio = building.get('efficiency_vs_swedish_avg')
        energy_performance = building.get('energy_performance_kwh_m2')
        
        # If no energy data, use gray
        if not energy_performance or not efficiency_ratio:
            return '#808080'  # Gray for missing data
        
        # Color scale based on efficiency vs Swedish average
        if efficiency_ratio <= 0.7:
            return '#2E8B57'  # Dark green - excellent
        elif efficiency_ratio <= 0.9:
            return '#32CD32'  # Green - good
        elif efficiency_ratio <= 1.1:
            return '#FFD700'  # Yellow - average
        elif efficiency_ratio <= 1.3:
            return '#FF6B35'  # Orange - below average
        else:
            return '#FF0000'  # Red - poor
    
    def get_performance_color(self, building: Dict) -> str:
        """Get color coding based on performance score."""
        score = building.get('performance_score', 0)
        
        if score >= 80:
            return '#2E8B57'  # Dark green
        elif score >= 60:
            return '#32CD32'  # Green
        elif score >= 40:
            return '#FFD700'  # Yellow
        elif score >= 20:
            return '#FF6B35'  # Orange
        else:
            return '#FF0000'  # Red
    
    def get_cost_color(self, building: Dict) -> str:
        """Get color coding based on cost efficiency (bang for buck)."""
        bang_for_buck = building.get('bang_for_buck_overall', 0)
        
        if bang_for_buck >= 2.0:
            return '#2E8B57'  # Dark green - excellent value
        elif bang_for_buck >= 1.7:
            return '#32CD32'  # Green - good value
        elif bang_for_buck >= 1.4:
            return '#FFD700'  # Yellow - average value
        elif bang_for_buck >= 1.0:
            return '#FF6B35'  # Orange - below average
        else:
            return '#FF0000'  # Red - poor value
    
    def create_building_popup(self, building: Dict) -> str:
        """Create detailed popup HTML for building marker."""
        energy_performance = building.get('energy_performance_kwh_m2')
        energy_class = building.get('energy_class', 'N/A')
        efficiency_rating = building.get('efficiency_rating', 'Unknown')
        
        # Format currency values
        monthly_fee = f"{building.get('monthly_fee', 0):,.0f} SEK" if building.get('monthly_fee') else "N/A"
        energy_costs = f"{building.get('energy_costs', 0):,.0f} SEK" if building.get('energy_costs') else "N/A"
        heating_costs = f"{building.get('heating_costs', 0):,.0f} SEK" if building.get('heating_costs') else "N/A"
        water_costs = f"{building.get('water_costs', 0):,.0f} SEK" if building.get('water_costs') else "N/A"
        
        # Performance metrics
        performance_score = building.get('performance_score', 0)
        bang_for_buck = building.get('bang_for_buck_overall', 0)
        
        # Data quality indicators
        energy_confidence = building.get('epc_confidence', 0)
        cost_confidence = building.get('cost_confidence', 0)
        
        popup_html = f"""
        <div style="width: 300px; font-family: Arial, sans-serif;">
            <h3 style="color: #2E8B57; margin: 0 0 10px 0;">{building['name']}</h3>
            <p style="margin: 0 0 15px 0; color: #666; font-size: 12px;">
                <strong>📍 {building['address']}</strong><br>
                {building.get('postal_code', '')}
            </p>
            
            <div style="margin-bottom: 15px;">
                <h4 style="color: #444; margin: 0 0 8px 0; font-size: 14px;">⚡ Energy Performance</h4>
                <p style="margin: 0; font-size: 12px;">
                    <strong>Usage:</strong> {f"{energy_performance} kWh/m²" if energy_performance else "No data"}<br>
                    <strong>Class:</strong> {energy_class}<br>
                    <strong>Rating:</strong> {efficiency_rating}<br>
                    <strong>vs Swedish Avg:</strong> {f"{building.get('efficiency_vs_swedish_avg', 0)*100:.1f}%" if building.get('efficiency_vs_swedish_avg') else "N/A"}
                </p>
            </div>
            
            <div style="margin-bottom: 15px;">
                <h4 style="color: #444; margin: 0 0 8px 0; font-size: 14px;">💰 Cost Information</h4>
                <p style="margin: 0; font-size: 12px;">
                    <strong>Monthly Fee:</strong> {monthly_fee}<br>
                    <strong>Energy Costs:</strong> {energy_costs}<br>
                    <strong>Heating Costs:</strong> {heating_costs}<br>
                    <strong>Water Costs:</strong> {water_costs}
                </p>
            </div>
            
            <div style="margin-bottom: 15px;">
                <h4 style="color: #444; margin: 0 0 8px 0; font-size: 14px;">📊 Performance Metrics</h4>
                <p style="margin: 0; font-size: 12px;">
                    <strong>Performance Score:</strong> {performance_score:.1f}/100<br>
                    <strong>Value Rating:</strong> {bang_for_buck:.2f}
                </p>
            </div>
            
            <div style="font-size: 11px; color: #888; border-top: 1px solid #eee; padding-top: 8px;">
                <strong>Data Quality:</strong><br>
                Energy Confidence: {energy_confidence*100:.0f}%<br>
                Cost Confidence: {cost_confidence*100:.0f}%
            </div>
        </div>
        """
        return popup_html
    
    def create_base_map(self) -> folium.Map:
        """Create the base Folium map with drawing tools."""
        m = folium.Map(
            location=HAMMARBY_CENTER,
            zoom_start=14,
            tiles='OpenStreetMap'
        )
        
        # Add additional tile layers
        folium.TileLayer(
            'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Satellite',
            overlay=False,
            control=True
        ).add_to(m)
        
        folium.TileLayer(
            'CartoDB positron',
            name='Light Map',
            overlay=False,
            control=True
        ).add_to(m)
        
        # Add drawing tools for polygon selection
        draw = plugins.Draw(
            export=True,
            filename='polygon_selection.geojson',
            position='topleft',
            draw_options={
                'polyline': False,
                'polygon': {
                    'allowIntersection': False,
                    'drawError': {
                        'color': '#e1e100',
                        'message': 'Polygon intersections are not allowed!'
                    },
                    'shapeOptions': {
                        'color': '#2E8B57',
                        'fillColor': '#2E8B57',
                        'fillOpacity': 0.2
                    }
                },
                'circle': False,
                'rectangle': {
                    'shapeOptions': {
                        'color': '#2E8B57',
                        'fillColor': '#2E8B57',
                        'fillOpacity': 0.2
                    }
                },
                'marker': False,
                'circlemarker': False
            },
            edit_options={
                'poly': {
                    'allowIntersection': False
                }
            }
        )
        draw.add_to(m)
        
        return m
    
    def add_building_markers(self, m: folium.Map, color_by: str = 'energy') -> folium.Map:
        """Add building markers to the map with specified coloring scheme."""
        
        # Create marker cluster for better performance with many markers
        marker_cluster = MarkerCluster(
            name="Buildings",
            overlay=True,
            control=True,
            options={'maxClusterRadius': 50}
        ).add_to(m)
        
        for building in self.buildings:
            # Get color based on selected scheme
            if color_by == 'energy':
                color = self.get_energy_color(building)
            elif color_by == 'performance':
                color = self.get_performance_color(building)
            elif color_by == 'cost':
                color = self.get_cost_color(building)
            else:
                color = '#808080'
            
            # Create marker
            folium.CircleMarker(
                location=[building['coordinates']['lat'], building['coordinates']['lng']],
                radius=8,
                popup=folium.Popup(self.create_building_popup(building), max_width=350),
                tooltip=f"{building['name']} - Click for details",
                color='white',
                weight=2,
                fillColor=color,
                fillOpacity=0.8
            ).add_to(marker_cluster)
        
        return m
    
    def add_legend(self, m: folium.Map, color_by: str = 'energy') -> folium.Map:
        """Add legend to the map based on coloring scheme."""
        
        if color_by == 'energy':
            legend_html = '''
            <div style="position: fixed; 
                        bottom: 50px; left: 50px; width: 200px; height: 120px; 
                        background-color: white; border:2px solid grey; z-index:9999; 
                        font-size:14px; padding: 10px;">
                <h4 style="margin:0 0 10px 0;">Energy Efficiency</h4>
                <p style="margin:2px 0;"><i style="background:#2E8B57;width:15px;height:15px;float:left;margin-right:8px;margin-top:2px;"></i> Excellent (≤70%)</p>
                <p style="margin:2px 0;"><i style="background:#32CD32;width:15px;height:15px;float:left;margin-right:8px;margin-top:2px;"></i> Good (70-90%)</p>
                <p style="margin:2px 0;"><i style="background:#FFD700;width:15px;height:15px;float:left;margin-right:8px;margin-top:2px;"></i> Average (90-110%)</p>
                <p style="margin:2px 0;"><i style="background:#FF6B35;width:15px;height:15px;float:left;margin-right:8px;margin-top:2px;"></i> Below Avg (110-130%)</p>
                <p style="margin:2px 0;"><i style="background:#FF0000;width:15px;height:15px;float:left;margin-right:8px;margin-top:2px;"></i> Poor (>130%)</p>
                <p style="margin:2px 0;"><i style="background:#808080;width:15px;height:15px;float:left;margin-right:8px;margin-top:2px;"></i> No Data</p>
            </div>
            '''
        elif color_by == 'performance':
            legend_html = '''
            <div style="position: fixed; 
                        bottom: 50px; left: 50px; width: 200px; height: 120px; 
                        background-color: white; border:2px solid grey; z-index:9999; 
                        font-size:14px; padding: 10px;">
                <h4 style="margin:0 0 10px 0;">Performance Score</h4>
                <p style="margin:2px 0;"><i style="background:#2E8B57;width:15px;height:15px;float:left;margin-right:8px;margin-top:2px;"></i> Excellent (80-100)</p>
                <p style="margin:2px 0;"><i style="background:#32CD32;width:15px;height:15px;float:left;margin-right:8px;margin-top:2px;"></i> Good (60-79)</p>
                <p style="margin:2px 0;"><i style="background:#FFD700;width:15px;height:15px;float:left;margin-right:8px;margin-top:2px;"></i> Average (40-59)</p>
                <p style="margin:2px 0;"><i style="background:#FF6B35;width:15px;height:15px;float:left;margin-right:8px;margin-top:2px;"></i> Below Avg (20-39)</p>
                <p style="margin:2px 0;"><i style="background:#FF0000;width:15px;height:15px;float:left;margin-right:8px;margin-top:2px;"></i> Poor (<20)</p>
            </div>
            '''
        else:  # cost
            legend_html = '''
            <div style="position: fixed; 
                        bottom: 50px; left: 50px; width: 200px; height: 120px; 
                        background-color: white; border:2px solid grey; z-index:9999; 
                        font-size:14px; padding: 10px;">
                <h4 style="margin:0 0 10px 0;">Cost Efficiency</h4>
                <p style="margin:2px 0;"><i style="background:#2E8B57;width:15px;height:15px;float:left;margin-right:8px;margin-top:2px;"></i> Excellent (≥2.0)</p>
                <p style="margin:2px 0;"><i style="background:#32CD32;width:15px;height:15px;float:left;margin-right:8px;margin-top:2px;"></i> Good (1.7-1.99)</p>
                <p style="margin:2px 0;"><i style="background:#FFD700;width:15px;height:15px;float:left;margin-right:8px;margin-top:2px;"></i> Average (1.4-1.69)</p>
                <p style="margin:2px 0;"><i style="background:#FF6B35;width:15px;height:15px;float:left;margin-right:8px;margin-top:2px;"></i> Below Avg (1.0-1.39)</p>
                <p style="margin:2px 0;"><i style="background:#FF0000;width:15px;height:15px;float:left;margin-right:8px;margin-top:2px;"></i> Poor (<1.0)</p>
            </div>
            '''
        
        m.get_root().html.add_child(folium.Element(legend_html))
        return m
    
    def create_summary_charts(self) -> Tuple[go.Figure, go.Figure, go.Figure]:
        """Create summary charts for the data overview."""
        
        # Energy performance distribution
        energy_buildings = [b for b in self.buildings if b.get('energy_performance_kwh_m2')]
        
        if energy_buildings:
            energy_data = [b['energy_performance_kwh_m2'] for b in energy_buildings]
            energy_names = [b['name'] for b in energy_buildings]
            
            fig1 = go.Figure(data=[
                go.Bar(
                    x=energy_names,
                    y=energy_data,
                    marker_color=['#2E8B57' if x < SWEDISH_ENERGY_BENCHMARK else '#FF6B35' for x in energy_data],
                    hovertemplate='<b>%{x}</b><br>Energy: %{y} kWh/m²<extra></extra>'
                )
            ])
            fig1.add_hline(y=SWEDISH_ENERGY_BENCHMARK, line_dash="dash", 
                          annotation_text=f"Swedish Average ({SWEDISH_ENERGY_BENCHMARK} kWh/m²)")
            fig1.update_layout(title="Energy Performance by Building", 
                             xaxis_title="Building", yaxis_title="kWh/m²",
                             height=400)
        else:
            fig1 = go.Figure()
            fig1.add_annotation(text="No energy performance data available", 
                              xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            fig1.update_layout(title="Energy Performance by Building", height=400)
        
        # Performance scores
        performance_data = [b.get('performance_score', 0) for b in self.buildings]
        performance_names = [b['name'] for b in self.buildings]
        
        fig2 = go.Figure(data=[
            go.Bar(
                x=performance_names,
                y=performance_data,
                marker_color=[self.get_performance_color({'performance_score': x}) for x in performance_data],
                hovertemplate='<b>%{x}</b><br>Score: %{y:.1f}/100<extra></extra>'
            )
        ])
        fig2.update_layout(title="Performance Scores by Building", 
                          xaxis_title="Building", yaxis_title="Score (0-100)",
                          height=400)
        
        # Cost breakdown pie chart (average across buildings)
        cost_ratios = {}
        count = 0
        for building in self.buildings:
            ratios = building.get('cost_ratios', {})
            for category, ratio in ratios.items():
                if category not in cost_ratios:
                    cost_ratios[category] = 0
                cost_ratios[category] += ratio
            if ratios:
                count += 1
        
        if cost_ratios and count > 0:
            # Calculate averages
            avg_cost_ratios = {k: v/count for k, v in cost_ratios.items()}
            
            fig3 = go.Figure(data=[
                go.Pie(
                    labels=list(avg_cost_ratios.keys()),
                    values=list(avg_cost_ratios.values()),
                    hovertemplate='<b>%{label}</b><br>%{percent}<br>Value: %{value:.3f}<extra></extra>'
                )
            ])
            fig3.update_layout(title="Average Cost Breakdown", height=400)
        else:
            fig3 = go.Figure()
            fig3.add_annotation(text="No cost breakdown data available", 
                              xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
            fig3.update_layout(title="Average Cost Breakdown", height=400)
        
        return fig1, fig2, fig3
    
    def handle_polygon_selection(self, geojson_data: Dict) -> List[Dict]:
        """Handle polygon selection from map interaction."""
        try:
            if geojson_data and geojson_data.get('geometry'):
                selected_buildings = self.polygon_handler.select_buildings_in_polygon(
                    geojson_data['geometry']
                )
                
                # Update session state
                if selected_buildings:
                    self.polygon_handler.add_selection(selected_buildings, "polygon")
                    st.session_state.selected_building_ids.extend([
                        b['id'] for b in selected_buildings 
                        if b['id'] not in st.session_state.selected_building_ids
                    ])
                    
                return selected_buildings
            return []
        except Exception as e:
            st.error(f"Error processing polygon selection: {e}")
            return []
    
    def create_selection_sidebar(self):
        """Create sidebar interface for polygon selection management."""
        st.sidebar.subheader("Polygon Selection")
        
        # Display current selection summary
        if self.polygon_handler.selected_buildings:
            selection_count = len(self.polygon_handler.selected_buildings)
            st.sidebar.metric("Selected Buildings", selection_count)
            
            # Show selection summary
            summary = self.polygon_handler.get_selection_summary()
            if 'energy_performance' in summary and summary['energy_performance']['avg_kwh_m2']:
                st.sidebar.metric(
                    "Avg Energy Performance", 
                    f"{summary['energy_performance']['avg_kwh_m2']} kWh/m²"
                )
            
            if 'performance_scores' in summary:
                st.sidebar.metric(
                    "Avg Performance Score", 
                    f"{summary['performance_scores']['avg_score']:.1f}/100"
                )
            
            # Selection actions
            col1, col2 = st.sidebar.columns(2)
            
            with col1:
                if st.button("Clear Selection"):
                    self.polygon_handler.clear_selection()
                    st.session_state.selected_building_ids = []
                    st.rerun()
            
            with col2:
                if st.button("Export Selection"):
                    return "export_selection"
        
        else:
            st.sidebar.info("Draw polygons on the map to select buildings")
        
        return None
    
    def create_export_interface(self):
        """Create interface for exporting selected buildings."""
        if not self.polygon_handler.selected_buildings:
            st.warning("No buildings selected for export")
            return
        
        st.subheader("Export Selected Buildings")
        
        # Export format selection
        export_format = st.selectbox(
            "Export Format:",
            options=['json', 'csv', 'geojson'],
            format_func=lambda x: {
                'json': 'JSON (Full data)',
                'csv': 'CSV (Tabular data)',
                'geojson': 'GeoJSON (GIS compatible)'
            }[x]
        )
        
        if st.button("Generate Export"):
            try:
                if export_format == 'csv':
                    export_data = self.polygon_handler.export_selection_data('dataframe')
                    csv_data = export_data.to_csv(index=False)
                    
                    st.download_button(
                        label="Download CSV",
                        data=csv_data,
                        file_name=f"hammarby_selection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                
                else:
                    export_data = self.polygon_handler.export_selection_data(export_format)
                    json_data = json.dumps(export_data, indent=2, ensure_ascii=False)
                    
                    st.download_button(
                        label=f"Download {export_format.upper()}",
                        data=json_data,
                        file_name=f"hammarby_selection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_format}",
                        mime="application/json"
                    )
                
                # Show export preview
                st.subheader("Export Preview")
                if export_format == 'csv':
                    st.dataframe(export_data.head())
                else:
                    st.json(export_data if isinstance(export_data, dict) else json.loads(json_data))
                    
            except Exception as e:
                st.error(f"Export failed: {e}")
        
        # Database integration
        if DB_INTEGRATION_AVAILABLE:
            st.subheader("Database Integration")
            if st.button("Get Related Documents"):
                try:
                    db_connector = DatabaseConnector()
                    integration_result = integrate_with_database(
                        self.polygon_handler, 
                        db_connector
                    )
                    
                    if integration_result.get('status') == 'success':
                        st.success(f"Found {integration_result['documents_found']} related documents")
                        if integration_result.get('documents'):
                            st.json(integration_result['documents'][:3])  # Show first 3
                    else:
                        st.warning(f"Database integration: {integration_result.get('message', 'Unknown result')}")
                        
                except Exception as e:
                    st.error(f"Database integration failed: {e}")
        else:
            st.info("Database integration module not available. Install database_integration.py for document retrieval.")
    
    def create_analysis_report(self):
        """Create detailed analysis report for selected buildings."""
        if not self.polygon_handler.selected_buildings:
            return
        
        st.subheader("Selection Analysis Report")
        
        # Generate comprehensive report
        report = create_selection_report(self.polygon_handler)
        
        # Display key metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            summary = report['selection_summary']
            st.metric(
                "Buildings Selected",
                summary['selection_info']['total_buildings']
            )
            
        with col2:
            if 'performance_comparison' in report['comparative_metrics']:
                perf_comp = report['comparative_metrics']['performance_comparison']
                st.metric(
                    "Relative Performance",
                    f"{perf_comp['relative_performance']:.1f}%",
                    f"vs dataset average"
                )
        
        with col3:
            if 'cost_comparison' in report['comparative_metrics']:
                cost_comp = report['comparative_metrics']['cost_comparison']
                if cost_comp['relative_cost']:
                    st.metric(
                        "Relative Cost",
                        f"{cost_comp['relative_cost']:.1f}%",
                        f"vs dataset average"
                    )
        
        # Show recommendations
        if report.get('recommendations'):
            st.subheader("Recommendations")
            for i, rec in enumerate(report['recommendations'], 1):
                st.write(f"{i}. {rec}")
        
        # Detailed metrics
        with st.expander("Detailed Metrics"):
            st.json(report)
        
        # Geographic analysis
        if 'selection_diversity' in report['comparative_metrics']:
            geo_data = report['comparative_metrics']['selection_diversity']
            if 'geographic_spread' in geo_data:
                st.subheader("Geographic Distribution")
                spread = geo_data['geographic_spread']
                
                center_map = folium.Map(
                    location=[spread['center_lat'], spread['center_lng']],
                    zoom_start=15
                )
                
                # Add selected buildings to the map
                for building in self.polygon_handler.selected_buildings:
                    folium.CircleMarker(
                        location=[building['coordinates']['lat'], building['coordinates']['lng']],
                        radius=6,
                        popup=building['name'],
                        color='red',
                        fillColor='red',
                        fillOpacity=0.8
                    ).add_to(center_map)
                
                # Add center point
                folium.Marker(
                    location=[spread['center_lat'], spread['center_lng']],
                    popup="Selection Center",
                    icon=folium.Icon(color='green', icon='star')
                ).add_to(center_map)
                
                # Display the map
                try:
                    from streamlit_folium import st_folium
                    st_folium(center_map, width=700, height=300)
                except ImportError:
                    st.components.v1.html(center_map._repr_html_(), height=300)

def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="Hammarby Sjöstad Interactive Map",
        page_icon="🏗️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🏗️ Hammarby Sjöstad Interactive Map")
    st.markdown("**Interactive building performance analysis with polygon selection tools**")
    
    # Load data
    data_file = "/Users/hosseins/Dropbox/Zelda/ZeldaDemo/hammarby_map_visualization_data.json"
    map_interface = HammarbyMapInterface(data_file)
    
    if not map_interface.buildings:
        st.error("No building data available. Please check the data file.")
        return
    
    # Sidebar controls
    st.sidebar.header("Map Controls")
    
    # Color scheme selection
    color_scheme = st.sidebar.selectbox(
        "Color Buildings By:",
        options=['energy', 'performance', 'cost'],
        format_func=lambda x: {
            'energy': 'Energy Efficiency vs Swedish Average',
            'performance': 'Performance Score (0-100)',
            'cost': 'Cost Efficiency (Value Rating)'
        }[x],
        index=0
    )
    
    # Add polygon selection sidebar
    selection_action = map_interface.create_selection_sidebar()
    
    # Layer controls
    st.sidebar.subheader("Map Layers")
    show_markers = st.sidebar.checkbox("Show Building Markers", value=True)
    show_legend = st.sidebar.checkbox("Show Legend", value=True)
    
    # Data filtering
    st.sidebar.subheader("Data Filters")
    
    # Filter by energy efficiency
    if st.sidebar.checkbox("Filter by Energy Efficiency"):
        efficiency_range = st.sidebar.slider(
            "Efficiency vs Swedish Average (%)",
            min_value=0,
            max_value=200,
            value=(0, 200),
            step=10
        )
    else:
        efficiency_range = (0, 200)
    
    # Filter by performance score
    performance_range = st.sidebar.slider(
        "Performance Score Range",
        min_value=0,
        max_value=100,
        value=(0, 100),
        step=5
    )
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Interactive Map")
        
        # Create and display map
        m = map_interface.create_base_map()
        
        if show_markers:
            # Apply filters
            filtered_buildings = []
            for building in map_interface.buildings:
                # Energy efficiency filter
                eff_ratio = building.get('efficiency_vs_swedish_avg', 1) * 100
                if not (efficiency_range[0] <= eff_ratio <= efficiency_range[1]):
                    continue
                
                # Performance score filter
                perf_score = building.get('performance_score', 0)
                if not (performance_range[0] <= perf_score <= performance_range[1]):
                    continue
                
                filtered_buildings.append(building)
            
            # Temporarily update buildings for marker display
            original_buildings = map_interface.buildings
            map_interface.buildings = filtered_buildings
            
            m = map_interface.add_building_markers(m, color_by=color_scheme)
            
            # Restore original buildings
            map_interface.buildings = original_buildings
        
        if show_legend:
            m = map_interface.add_legend(m, color_by=color_scheme)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Display map
        try:
            from streamlit_folium import st_folium
            
            # Display interactive map
            map_data = st_folium(m, width=700, height=500, returned_objects=["last_clicked", "all_drawings"])
            
            # Handle polygon selection
            if map_data.get('all_drawings'):
                for drawing in map_data['all_drawings']:
                    if drawing.get('geometry') and drawing['geometry']['type'] in ['Polygon', 'Rectangle']:
                        selected_buildings = map_interface.handle_polygon_selection(drawing)
                        if selected_buildings:
                            st.success(f"Selected {len(selected_buildings)} buildings in drawn area")
            
            # Handle building click
            if map_data.get('last_object_clicked_tooltip'):
                st.info(f"Building details: {map_data['last_object_clicked_tooltip']}")
                
        except ImportError:
            st.error("streamlit_folium not installed for full interactivity.")
            st.info("Install with: pip install streamlit-folium")
            # Show static map HTML instead
            st.components.v1.html(m._repr_html_(), width=700, height=500, scrolling=True)
            
            # Manual polygon input as fallback
            st.subheader("Manual Selection (Fallback)")
            with st.expander("Select Buildings by Coordinates"):
                st.write("Enter bounding box coordinates:")
                col1, col2 = st.columns(2)
                with col1:
                    north = st.number_input("North (Latitude)", value=59.310, format="%.6f")
                    south = st.number_input("South (Latitude)", value=59.300, format="%.6f")
                with col2:
                    east = st.number_input("East (Longitude)", value=18.110, format="%.6f")
                    west = st.number_input("West (Longitude)", value=18.080, format="%.6f")
                
                if st.button("Select Buildings in Area"):
                    bounds = {'north': north, 'south': south, 'east': east, 'west': west}
                    selected = map_interface.polygon_handler.select_buildings_in_rectangle(bounds)
                    if selected:
                        map_interface.polygon_handler.add_selection(selected, "rectangle")
                        st.success(f"Selected {len(selected)} buildings in specified area")
    
    with col2:
        st.subheader("Data Overview")
        
        # Summary statistics
        total_buildings = len(map_interface.buildings)
        energy_buildings = len([b for b in map_interface.buildings if b.get('energy_performance_kwh_m2')])
        cost_buildings = len([b for b in map_interface.buildings if b.get('monthly_fee')])
        
        st.metric("Total Buildings", total_buildings)
        st.metric("With Energy Data", f"{energy_buildings}/{total_buildings}")
        st.metric("With Cost Data", f"{cost_buildings}/{total_buildings}")
        
        # Average metrics
        if energy_buildings > 0:
            avg_energy = np.mean([b['energy_performance_kwh_m2'] for b in map_interface.buildings 
                                if b.get('energy_performance_kwh_m2')])
            vs_swedish = (avg_energy / SWEDISH_ENERGY_BENCHMARK) * 100
            st.metric(
                "Average Energy Performance", 
                f"{avg_energy:.0f} kWh/m²",
                f"{vs_swedish:.0f}% of Swedish avg"
            )
        
        avg_performance = np.mean([b.get('performance_score', 0) for b in map_interface.buildings])
        st.metric("Average Performance Score", f"{avg_performance:.1f}/100")
        
        # Building selection status
        st.subheader("Building Selection")
        
        if map_interface.polygon_handler.selected_buildings:
            selected_count = len(map_interface.polygon_handler.selected_buildings)
            selected_names = [b['name'] for b in map_interface.polygon_handler.selected_buildings[:5]]
            
            st.success(f"**{selected_count} buildings selected:**")
            st.write(", ".join(selected_names))
            if selected_count > 5:
                st.write(f"... and {selected_count - 5} more")
            
        else:
            st.markdown("**Instructions:**")
            st.markdown("1. Use polygon/rectangle tools on the map")
            st.markdown("2. Draw around buildings of interest")  
            st.markdown("3. Selected buildings will appear below")
            st.markdown("4. Export selection for further analysis")
    
    # Charts section
    st.subheader("Performance Analytics")
    
    # Create tabs for different chart views
    chart_tab1, chart_tab2, chart_tab3 = st.tabs(["Energy Performance", "Performance Scores", "Cost Analysis"])
    
    fig1, fig2, fig3 = map_interface.create_summary_charts()
    
    with chart_tab1:
        st.plotly_chart(fig1, use_container_width=True)
        
    with chart_tab2:
        st.plotly_chart(fig2, use_container_width=True)
        
    with chart_tab3:
        st.plotly_chart(fig3, use_container_width=True)
    
    # Handle export action from sidebar
    if selection_action == "export_selection":
        st.session_state.show_export = True
    
    # Export and Analysis section
    if map_interface.polygon_handler.selected_buildings:
        st.subheader("Selection Management")
        
        # Create tabs for export and analysis
        export_tab, analysis_tab = st.tabs(["Export & Integration", "Analysis Report"])
        
        with export_tab:
            map_interface.create_export_interface()
            
        with analysis_tab:
            map_interface.create_analysis_report()
    
    # Instructions and help
    with st.expander("How to Use the Polygon Selection Tools"):
        st.markdown("""
        ### Drawing Polygons for Area Selection
        
        1. **Polygon Tool** - Draw custom shapes around building clusters
        2. **Rectangle Tool** - Draw rectangular selection areas
        3. **Edit Mode** - Modify existing selections
        4. **Delete** - Remove unwanted selections
        
        ### Integration Workflow
        
        1. **Explore** - Use different color schemes to identify interesting buildings
        2. **Select** - Draw polygons around buildings of interest
        3. **Filter** - Use sidebar filters to refine your view
        4. **Export** - Export selected building IDs for document retrieval
        5. **Analyze** - Use the database integration to get related documents
        
        ### Color Coding Explained
        
        - **Energy Efficiency**: Based on performance vs Swedish average (159 kWh/m²)
        - **Performance Score**: Comprehensive score based on multiple factors (0-100)
        - **Cost Efficiency**: Value rating based on costs vs performance
        """)
    
    # Footer with data information
    st.markdown("---")
    st.markdown(f"**Data Source:** {map_interface.data.get('metadata', {}).get('created_at', 'Unknown')}")
    st.markdown(f"**Swedish Energy Benchmark:** {SWEDISH_ENERGY_BENCHMARK} kWh/m²")

if __name__ == "__main__":
    # Check if required packages are available
    try:
        import folium
        import plotly.express as px
        import plotly.graph_objects as go
    except ImportError as e:
        print(f"Missing required package: {e}")
        print("Please install required packages:")
        print("pip install folium plotly streamlit")
        exit(1)
    
    main()