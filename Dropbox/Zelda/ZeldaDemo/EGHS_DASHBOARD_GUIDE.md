# EGHS Interactive Map Dashboard - Complete Guide

## 🎯 Overview

The EGHS Interactive Map Dashboard is a professional geospatial analysis tool for studying energy performance and costs across 9 buildings in Hammarby Sjöstad, Stockholm. It combines real-world coordinates from PostgreSQL and Booli.se with comprehensive energy and financial data.

## 📊 Dataset Features

- **9 Buildings** with real coordinates (PostgreSQL + Booli.se geocoding)
- **Energy Performance Certificates** (EPC) data
- **Financial data** from Excel breakdowns
- **Construction information** and building characteristics
- **Cost breakdowns** by category (electricity, heating, water, etc.)

## 🗺️ Interactive Map Features

### Core Functionality
1. **Real Building Markers**
   - Color-coded by energy class (A=Green → G=Red)
   - Click for detailed building information
   - Energy class displayed on marker

2. **Rich Information Popups**
   - Building name and address
   - Energy class and performance (kWh/m²)
   - Comparison vs Swedish average (159 kWh/m²)
   - Financial details (monthly fees, total costs)
   - Construction year and property count

3. **Multiple Map Views**
   - OpenStreetMap (default)
   - Light Mode (CartoDB Positron)
   - Dark Mode (CartoDB Dark Matter)
   - Satellite imagery (Esri World Imagery)

### 🖍️ Interactive Drawing Tools

**Polygon Selection**:
- Draw custom polygons to select multiple buildings
- Real-time validation (no intersections allowed)
- Visual feedback with red outline and transparent fill

**Circle Selection**:
- Click to create circular selection areas
- Automatically selects buildings within radius

**Rectangle Selection**:
- Draw rectangular areas for building selection
- Perfect for analyzing city blocks

## 🎛️ Dashboard Controls

### Sidebar Filters
1. **Energy Class Filter**
   - Multi-select dropdown for energy classes A-G
   - Default: All classes selected

2. **Performance Range Slider**
   - Filter buildings by energy performance (kWh/m²)
   - Dynamic range based on actual data

3. **Export Options**
   - Export all filtered data to CSV
   - Export selected buildings comparison
   - Timestamped filenames for organization

## 📈 Analysis Features

### Quick Stats Panel
- Total buildings count
- Average energy performance
- Average annual costs
- Energy class distribution visualization

### Performance Analysis Tab
1. **Energy Performance Chart**
   - Interactive scatter plot with energy class colors
   - Swedish average reference line (159 kWh/m²)
   - Selected buildings highlighted in red

2. **Performance Insights**
   - Excellent performers (≤70% of Swedish average)
   - Poor performers (≥120% of Swedish average)
   - Automatic categorization and recommendations

### Cost Analysis Tab
1. **Cost Breakdown Chart**
   - Stacked bar chart by cost categories
   - Categories: Electricity, Heating, Water, Internet/TV, Recycling
   - Selected buildings highlighted

2. **Cost Insights**
   - Highest cost buildings (top 3)
   - Lowest cost buildings (bottom 3)
   - Cost optimization opportunities

## 🎯 Selection & Comparison Features

### Building Selection
- **Click Selection**: Click any building marker
- **Area Selection**: Use drawing tools for multiple buildings
- **Real-time Feedback**: Selected buildings immediately highlighted

### Comparison Interface
1. **Selected Buildings Cards**
   - Visual cards for each selected building
   - Key metrics at a glance
   - Color-coded performance indicators

2. **Detailed Comparison Table**
   - Side-by-side comparison of all attributes
   - Energy class, performance, costs, construction data
   - Performance vs Swedish average

3. **Export Capabilities**
   - Export selected buildings data
   - CSV format with comprehensive details
   - Timestamped for version control

## 🔧 Technical Implementation

### Geospatial Features
- **Coordinate System**: WGS84 (EPSG:4326)
- **Point-in-Polygon Algorithm**: Ray casting for accurate selection
- **Real Coordinates**: Verified PostgreSQL + Booli.se data
- **Responsive Design**: Mobile and desktop optimized

### Performance Optimizations
- **Data Caching**: @st.cache_data for fast loading
- **Efficient Filtering**: Client-side filtering for responsiveness
- **Optimized Rendering**: Conditional chart updates
- **Memory Management**: Efficient data structures

### Interactive Components
- **st_folium**: Full bidirectional interactivity
- **Plotly Charts**: Interactive visualizations
- **Streamlit Components**: Professional UI elements

## 🏢 Building Data Structure

Each building includes:

```json
{
  "brf_name": "Building Name",
  "building_id": "eghs_X",
  "latitude": 59.xxxx,
  "longitude": 18.xxxx,
  "formatted_address": "Street Address",
  "postal_code": "12XXX",
  "energy_performance": 147.0,
  "energy_class": "E",
  "construction_year": 2002,
  "property_count": 3,
  "monthly_fee": 5430.17,
  "total_cost": 1625276.0,
  "cost_electricity": 171277.0,
  "cost_heating": 1069532.0,
  "cost_water": 91180.0,
  "performance_score": 51.5
}
```

## 🌟 Key Features Summary

### ✅ Completed Features
- [x] Real coordinate integration (9/9 buildings)
- [x] Interactive map with multiple tile layers
- [x] Energy class color coding
- [x] Polygon/area selection tools
- [x] Rich building information popups
- [x] Performance vs Swedish average benchmarking
- [x] Cost analysis and breakdown
- [x] Building comparison interface
- [x] Export functionality (CSV)
- [x] Mobile-responsive design
- [x] Real-time selection feedback
- [x] Professional UI/UX design

### 🎯 Usage Tips
1. **Start with the map**: Explore building locations and click markers
2. **Use filters**: Narrow down by energy class or performance range
3. **Draw selections**: Use polygon tools to compare buildings in specific areas
4. **Analyze performance**: Check the Performance tab for benchmarking
5. **Compare costs**: Use the Cost Analysis tab to identify optimization opportunities
6. **Export data**: Save filtered or selected data for further analysis

## 🚀 Getting Started

1. **Launch Dashboard**:
   ```bash
   streamlit run killer_eghs_map_dashboard.py --server.port=8504
   ```

2. **Access**: Open http://localhost:8504 in your browser

3. **Explore**: Start by clicking building markers and using drawing tools

4. **Analyze**: Use the analysis tabs for deeper insights

5. **Export**: Save your findings using the export buttons

## 📞 Dashboard URL

**Local Access**: http://localhost:8504
**Features**: All interactive features fully functional
**Performance**: Optimized for real-time interaction

This dashboard represents a complete professional solution for geospatial analysis of building energy performance and costs, with full interactivity and export capabilities.