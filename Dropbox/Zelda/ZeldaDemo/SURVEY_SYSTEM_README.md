# BRF Peer Survey & Interactive Map System

A comprehensive survey system with unlock mechanisms for BRF (housing cooperative) peer data access, integrated with an interactive map of Hammarby Sjöstad buildings.

## 🚀 Quick Start

### Option 1: Using the launcher script (Recommended)
```bash
python run_survey_app.py
```

### Option 2: Direct Streamlit launch
```bash
streamlit run integrated_survey_map_app.py
```

The application will be available at: http://localhost:8501

## 🏗️ System Architecture

### Core Components

1. **Survey System** (`survey_system.py`)
   - Progressive modal survey forms
   - Unlock mechanism based on completion level
   - Stockholm suppliers database
   - Data validation and persistence

2. **Peer Comparison Engine** (`peer_comparison_system.py`)
   - "Half peers visible" system
   - Anonymized benchmarking
   - AI-driven cost-saving recommendations
   - Statistical analysis with confidence levels

3. **Integrated Application** (`integrated_survey_map_app.py`)
   - Main application combining map and survey
   - Responsive design with accessibility features
   - Export functionality
   - Tab-based navigation

4. **Interactive Map** (`hammarby_interactive_map.py`)
   - Building selection and visualization
   - Energy performance color coding
   - Polygon selection tools

## 📊 Survey System Features

### Progressive Unlock Levels

#### 🔒 **None** (0-29% completion)
- Survey invitation and value proposition
- Basic building selection

#### 🔓 **Basic** (30-59% completion)  
- Limited peer comparison data (30% of dataset)
- Basic cost benchmarking
- 2 actionable recommendations

#### 🔓🔓 **Intermediate** (60-89% completion)
- Extended peer data access (70% of dataset)
- Supplier alternatives with contact info
- Detailed cost-saving recommendations
- Up to 4 insights

#### 🔓🔓🔓 **Full** (90-100% completion)
- Complete peer dataset access
- Full statistical analysis with percentiles
- Premium supplier recommendations
- AI-driven prioritized action items
- Unlimited insights and recommendations

### Cost Categories

The system tracks costs across 6 key BRF operational categories:

1. **Cleaning** (`städtjänster`)
2. **Maintenance** (`underhåll & reparationer`) 
3. **Snow Removal** (`snöröjning`)
4. **Gardening** (`trädgård & grönområden`)
5. **Electricity** (`el & energi`)
6. **Heating** (`värme & VVS`)

### Supplier Database

Realistic Stockholm-based suppliers with:
- Contact information
- Cost estimates
- Quality ratings
- Specialties and certifications
- Location data

## 🎯 User Experience Design

### Mobile-First Responsive Design

- **Breakpoint**: 768px for mobile/tablet transition
- **Typography**: Scalable font sizes (14px minimum on mobile)
- **Touch Targets**: Minimum 44px for accessibility
- **Layout**: Single-column stacking on mobile devices

### Accessibility Features (WCAG 2.1 Compliance)

- **Keyboard Navigation**: Full tab-order support
- **Focus Indicators**: Clear visual focus states
- **Color Contrast**: High contrast mode support
- **Screen Readers**: ARIA labels and landmarks
- **Semantic HTML**: Proper heading hierarchy

### Progressive Disclosure

1. **Value Proposition First**: Clear benefits before data request
2. **Incremental Reveals**: Show new sections as progress increases
3. **Progress Indicators**: Visual feedback on completion status
4. **Immediate Value**: Unlock insights as soon as minimum threshold reached

## 💡 Peer Comparison Features

### Anonymized Benchmarking

- **Statistical Aggregation**: Median, mean, percentile rankings
- **Sample Size Transparency**: Show number of peers in comparison
- **Confidence Levels**: Indicate reliability of recommendations
- **Privacy Protection**: No individual building identification

### Cost-Saving Recommendations

1. **Threshold-Based Insights**: Minimum 5,000 SEK/year potential savings
2. **Confidence Scoring**: 0.0-1.0 scale based on data quality
3. **Action-Oriented**: Specific steps users can take
4. **Prioritized**: Sorted by potential financial impact

### Supplier Alternatives

- **Current vs. Alternative**: Side-by-side comparisons
- **Verified Contacts**: Phone numbers and addresses
- **Cost Estimates**: Annual cost ranges
- **Quality Indicators**: Peer ratings and specialties

## 📤 Export & Integration

### Export Formats

1. **JSON**: Complete structured data
2. **Excel**: Formatted spreadsheets with charts
3. **CSV**: Tabular data for analysis
4. **PDF**: Formatted reports (future enhancement)

### Integration Points

- **Interactive Map**: Building selection flows to survey
- **Database Integration**: PostgreSQL support via `database_integration.py`
- **API Endpoints**: REST API via `api_endpoints.py`

## 🛠️ Technical Implementation

### Session State Management

```python
# Key session variables
st.session_state.survey_responses      # User survey data
st.session_state.unlock_level         # Current access level
st.session_state.peer_data_unlocked   # Boolean unlock status
st.session_state.current_survey       # In-progress survey data
```

### Data Structures

```python
@dataclass
class SurveyResponse:
    building_id: int
    costs: Dict[str, float]
    suppliers: Dict[str, str]  
    satisfaction: Dict[str, int]
    unlock_level: UnlockLevel
    completion_percentage: float

@dataclass  
class BenchmarkData:
    user_value: float
    peer_median: float
    percentile_rank: float
    savings_potential: float
```

### Security & Privacy

- **Data Anonymization**: No personally identifiable information in comparisons
- **GDPR Compliance**: Explicit consent and data minimization
- **Local Storage**: Session-based data storage (not persistent by default)
- **Secure Export**: Sanitized data in exports

## 📱 Mobile Optimization

### Responsive Breakpoints

```css
/* Mobile-first approach */
@media (max-width: 768px) {
    .stColumns > div {
        width: 100% !important;
        flex: none !important;
    }
}
```

### Touch-Friendly Interface

- **Button Sizing**: Minimum 44px touch targets
- **Form Fields**: Larger input areas on mobile
- **Navigation**: Swipeable tabs and simplified menus
- **Map Integration**: Touch-optimized polygon drawing

## 🧪 Testing & Validation

### Data Validation

1. **Input Validation**: Cost ranges, email formats, phone numbers
2. **Business Logic**: Reasonable cost thresholds per category
3. **Completion Logic**: Progressive unlock triggers
4. **Export Integrity**: Data consistency in exports

### User Experience Testing

- **Mobile Devices**: iOS/Android testing across screen sizes
- **Accessibility**: Screen reader compatibility testing  
- **Browser Support**: Cross-browser validation
- **Performance**: Load time optimization

## 🚀 Deployment

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run application
python run_survey_app.py
```

### Production Deployment

```bash
# Streamlit Cloud
streamlit run integrated_survey_map_app.py --server.port $PORT

# Docker (optional)
docker build -t brf-survey .
docker run -p 8501:8501 brf-survey
```

### Environment Variables

```bash
# Optional database configuration
DATABASE_URL=postgresql://user:pass@host:port/db

# API keys for enhanced features
GOOGLE_MAPS_API_KEY=your_key_here
```

## 📈 Future Enhancements

### Planned Features

1. **AI-Powered Insights**: Machine learning recommendations
2. **Real-Time Collaboration**: Multi-user survey sessions
3. **Advanced Visualizations**: Interactive cost trend charts
4. **Integration APIs**: Connect with BRF management systems
5. **Notification System**: Email alerts for new insights

### Scalability Considerations

- **Database Backend**: Move from session state to persistent storage
- **Caching Layer**: Redis for frequently accessed peer data
- **API Rate Limiting**: Protect against excessive usage
- **Data Pipeline**: Automated peer data updates

## 🆘 Troubleshooting

### Common Issues

1. **Map Not Loading**: Install `streamlit-folium`
2. **Survey Data Lost**: Check browser cookies/session storage
3. **Export Failed**: Verify file permissions
4. **Mobile Layout Issues**: Clear browser cache

### Debug Mode

```python
# Enable debug output
if st.checkbox("Debug Mode"):
    st.write(st.session_state)
```

## 📞 Support

For technical issues or feature requests:

1. Check the troubleshooting section above
2. Review the application logs in terminal
3. Verify all dependencies are installed correctly
4. Ensure data files are in the correct location

## 📄 License & Attribution

This survey system is designed for BRF cost comparison and benchmarking. The supplier database contains realistic but mock data for demonstration purposes. For production use, verify all supplier information independently.

**Data Sources:**
- Building data: Hammarby Sjöstad energy performance certificates
- Supplier data: Curated realistic Stockholm supplier information
- Peer data: Statistical models based on typical BRF operational costs

---

*Built with ❤️ for Swedish housing cooperatives*