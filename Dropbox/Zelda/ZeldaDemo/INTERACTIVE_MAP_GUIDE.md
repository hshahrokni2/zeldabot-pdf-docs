# Hammarby Sjöstad Interactive Map - User Guide

## Overview

The Hammarby Sjöstad Interactive Map is a sophisticated geospatial visualization tool designed for BRF (housing cooperative) board members to explore building performance data, compare properties, and make data-driven decisions about energy efficiency and cost optimization.

## Features

### 🗺️ Interactive Map Interface
- **Responsive Folium-based map** centered on Hammarby Sjöstad (59.305°N, 18.085°E)
- **Multiple tile layers**: OpenStreetMap, Satellite imagery, Light theme
- **Zoom and pan** controls for detailed exploration
- **Building markers** with color-coded performance indicators

### 🎨 Color Coding Systems
Choose from three visualization schemes:

1. **Energy Efficiency** (vs Swedish Average 159 kWh/m²)
   - 🟢 Excellent: ≤70% of Swedish average
   - 🟢 Good: 70-90% of Swedish average
   - 🟡 Average: 90-110% of Swedish average
   - 🟠 Below Average: 110-130% of Swedish average
   - 🔴 Poor: >130% of Swedish average

2. **Performance Score** (0-100 composite score)
   - 🟢 Excellent: 80-100
   - 🟢 Good: 60-79
   - 🟡 Average: 40-59
   - 🟠 Below Average: 20-39
   - 🔴 Poor: <20

3. **Cost Efficiency** (value rating)
   - 🟢 Excellent: ≥2.0
   - 🟢 Good: 1.7-1.99
   - 🟡 Average: 1.4-1.69
   - 🟠 Below Average: 1.0-1.39
   - 🔴 Poor: <1.0

### 🔺 Polygon Selection Tools
- **Polygon tool**: Draw custom shapes around building clusters
- **Rectangle tool**: Select rectangular areas
- **Edit mode**: Modify existing selections
- **Delete mode**: Remove unwanted selections

### 📊 Building Information Popups
Click any building marker to see:
- **Basic Information**: Name, address, postal code
- **Energy Performance**: kWh/m², energy class, efficiency rating
- **Cost Breakdown**: Monthly fees, energy costs, heating costs, water costs
- **Performance Metrics**: Performance score, value rating
- **Data Quality**: Confidence levels for energy and cost data

### 📈 Performance Analytics
Three interactive chart views:
1. **Energy Performance**: Bar chart comparing buildings to Swedish benchmark
2. **Performance Scores**: Comparative performance across all buildings  
3. **Cost Analysis**: Average cost breakdown by category

### 📤 Export & Integration
- **Multiple formats**: JSON, CSV, GeoJSON for different use cases
- **Database integration**: Connect to document retrieval system
- **Download functionality**: Export selected building data
- **Analysis reports**: Comprehensive selection analysis

## Getting Started

### Installation & Launch

1. **Automated Setup**:
   ```bash
   python launch_interactive_map.py
   ```

2. **Manual Launch**:
   ```bash
   pip install -r requirements.txt
   streamlit run hammarby_interactive_map.py
   ```

3. **Validation** (optional):
   ```bash
   python validate_setup.py
   ```

### Web Interface Access
- **Local URL**: http://localhost:8501
- **Browser**: Works with Chrome, Firefox, Safari, Edge
- **Mobile**: Responsive design supports tablets and phones

## Usage Workflow

### 1. Explore Buildings
1. Open the application in your web browser
2. Use the **Color Buildings By** dropdown to choose visualization scheme
3. Click building markers to see detailed information
4. Use map controls to zoom and pan around Hammarby Sjöstad

### 2. Select Areas of Interest
1. Use the **polygon/rectangle tools** on the left side of the map
2. Draw around buildings you want to analyze
3. Selected buildings appear in the **Data Overview** panel
4. View selection summary in the sidebar

### 3. Filter and Refine
1. Use **Data Filters** in the sidebar:
   - Energy efficiency percentage range
   - Performance score range
2. Apply filters to focus on specific building types
3. Toggle map layers on/off as needed

### 4. Analyze Selection
1. Go to the **Selection Management** section
2. View the **Analysis Report** tab for:
   - Comparative metrics vs. dataset average
   - Geographic distribution analysis
   - Recommendations based on selection
3. Review detailed metrics and performance comparisons

### 5. Export Results
1. Switch to **Export & Integration** tab
2. Choose export format:
   - **JSON**: Full data with metadata
   - **CSV**: Tabular format for spreadsheet analysis
   - **GeoJSON**: GIS-compatible format
3. Click **Generate Export** and download results
4. Optional: Use **Get Related Documents** for database integration

## Advanced Features

### Database Integration
If `database_integration.py` is available:
- Selected building IDs automatically trigger document retrieval
- Access related annual reports, energy certificates, cost analyses
- Streamlined workflow from map selection to document analysis

### Geographic Analysis
The system automatically calculates:
- **Selection center point**: Geographic centroid of selected buildings
- **Bounding box**: Coverage area of selection
- **Geographic spread**: Diversity metrics for selection area

### Performance Comparisons
Selected buildings are compared to the full dataset:
- **Relative performance**: How selection compares to average
- **Cost analysis**: Selection cost efficiency vs. average
- **Diversity metrics**: Variation within selected buildings

## Data Sources

### Building Data
- **Energy Performance Certificates**: Official EPC data where available
- **Cost Data**: Parsed from annual reports (heating, electricity, water, maintenance)
- **Performance Scores**: Composite metrics based on multiple factors

### Quality Indicators
Each building shows data confidence levels:
- **EPC Confidence**: Reliability of energy performance data
- **Cost Confidence**: Reliability of financial data

### Coverage Statistics
Current dataset includes:
- **Total Buildings**: 12 BRFs in Hammarby Sjöstad
- **Energy Data**: 1 building with complete EPC data
- **Cost Data**: 10 buildings with detailed cost breakdowns

## Troubleshooting

### Common Issues

**Map not loading:**
- Refresh browser page
- Check internet connection
- Ensure `streamlit-folium` is installed

**Polygon tools not working:**
- Make sure you're using the drawing controls on the left side of the map
- Try using rectangle tool first (simpler than polygon)
- Clear browser cache if tools are unresponsive

**Performance issues:**
- Use data filters to reduce displayed buildings
- Close other browser tabs to free memory
- Try the light map theme for better performance

**Export not working:**
- Ensure you have buildings selected first
- Check file download permissions in browser
- Try different export formats

### Browser Compatibility
- ✅ **Chrome/Chromium**: Full support, recommended
- ✅ **Firefox**: Full support
- ✅ **Safari**: Full support
- ✅ **Edge**: Full support
- ⚠️ **Internet Explorer**: Not supported

### Performance Optimization
- Use filters to limit displayed buildings
- Close unused browser tabs
- For large selections (>50 buildings), use CSV export format
- Clear browser cache periodically

## Integration with Existing Systems

### Database Workflow
The interactive map integrates with the document retrieval pipeline:

1. **Selection**: Use map to select buildings of interest
2. **Export**: Export building IDs for processing
3. **Retrieval**: Use `database_integration.py` to get related documents
4. **Analysis**: Process retrieved documents for insights

### API Integration
Building selection data can be exported in formats suitable for:
- **GIS systems**: GeoJSON format
- **Spreadsheet analysis**: CSV format
- **API integration**: JSON format with full metadata

## Future Enhancements

### Planned Features
- **Real-time data updates** from building management systems
- **Comparison benchmarking** with similar BRFs across Stockholm
- **Energy forecasting** based on weather and usage patterns
- **Cost optimization recommendations** based on best practices
- **Mobile app version** for on-site inspections

### Data Expansion
- **More buildings**: Expand coverage to entire Hammarby Sjöstad
- **Historical data**: Multi-year performance trends
- **Additional metrics**: Environmental impact, resident satisfaction
- **Weather correlation**: Energy usage vs. temperature data

## Support & Documentation

### Files Structure
```
hammarby_interactive_map.py     # Main application
polygon_selection_handler.py   # Selection logic
launch_interactive_map.py      # Setup and launcher
validate_setup.py             # Validation tests
requirements.txt               # Python dependencies
hammarby_map_visualization_data.json  # Building data
```

### Key Technical Components
- **Streamlit**: Web application framework
- **Folium**: Interactive map rendering
- **Shapely**: Geometric operations for polygon selection
- **Plotly**: Interactive charts and analytics
- **Pandas**: Data processing and export functionality

### Contact & Development
For technical issues, feature requests, or data updates, this tool integrates with the broader ZeldaDemo ecosystem for BRF document processing and analysis.

---

**Version**: 1.0  
**Last Updated**: August 13, 2025  
**Compatible with**: Python 3.8+, Modern web browsers