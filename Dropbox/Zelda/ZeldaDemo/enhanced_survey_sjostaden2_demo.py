#!/usr/bin/env python3
"""
Enhanced BRF Sjöstaden 2 Survey System Demo

This application demonstrates the complete enhanced survey system specifically 
designed for BRF Sjöstaden 2 with:

1. Multi-step survey for missing cost data
2. Supplier management with Stockholm providers
3. Locked savings potential analysis
4. Cost normalization to SEK/m²
5. BRF Financial Performance Index
6. Personalized metrics and recommendations

The user plays the role of a BRF Sjöstaden 2 board member collecting
and sharing cost data to unlock peer comparisons and supplier recommendations.
"""

import streamlit as st
import json
import pandas as pd
from survey_system import SurveySystem, UnlockLevel, SUPPLIER_CATEGORIES
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="BRF Sjöstaden 2 - Enhanced Survey System",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_buildings_data():
    """Load and cache the buildings dataset."""
    with open('killer_eghs_dataset_with_booli_coords.json', 'r') as f:
        data = json.load(f)
    
    # Transform data to include proper IDs and names for the survey system
    transformed_data = []
    for building in data:
        transformed_data.append({
            'id': building.get('building_id', building.get('postgres_id', 0)),
            'name': building.get('brf_name', 'Unknown BRF'),
            'building_id': building.get('building_id', building.get('postgres_id', 0)),
            **building
        })
    
    return transformed_data

def find_sjostaden_2(buildings_data):
    """Find BRF Sjöstaden 2 in the dataset."""
    for building in buildings_data:
        if 'sjöstaden' in building.get('brf_name', '').lower() and '2' in building.get('brf_name', ''):
            return building
    return None

def create_demo_header():
    """Create the demo application header."""
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        text-align: center;
        color: white;
        margin-bottom: 2rem;
    ">
        <h1>🏢 BRF Sjöstaden 2 - Enhanced Survey System</h1>
        <p style="font-size: 1.2em; margin: 1rem 0;">
            Kostnadsjämförelse & Leverantörsoptimering för Bostadsrättsföreningar
        </p>
        <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 10px; margin: 1rem 0;">
            <h3>🎯 Din roll: Styrelseledamot i BRF Sjöstaden 2</h3>
            <p>Dela kostnadsinformation och lås upp personaliserade kostnadssänkningsförslag och leverantörsrekommendationer</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

def show_brf_overview(building_data):
    """Show overview of BRF Sjöstaden 2."""
    st.markdown("### 🏢 BRF Sjöstaden 2 - Översikt")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Energiprestanda", 
            f"{building_data.get('energy_performance', 'N/A')} kWh/m²",
            help="Årlig energiförbrukning per kvadratmeter"
        )
        st.metric(
            "Energiklass",
            building_data.get('energy_class', 'N/A'),
            help="Energiklassning enligt EU-standard"
        )
    
    with col2:
        st.metric(
            "Byggnadsår",
            building_data.get('construction_year', 'N/A'),
            help="År då byggnaden färdigställdes"
        )
        st.metric(
            "Antal Fastigheter",
            building_data.get('property_count', 'N/A'),
            help="Antal registrerade fastigheter i BRF:en"
        )
    
    with col3:
        monthly_fee = building_data.get('monthly_fee', 0)
        st.metric(
            "Månadsavgift",
            f"{monthly_fee:,.0f} SEK" if monthly_fee else "N/A",
            help="Genomsnittlig månadsavgift per lägenhet"
        )
        
        total_cost = building_data.get('total_cost', 0)
        st.metric(
            "Totala Kostnader",
            f"{total_cost:,.0f} SEK/år" if total_cost else "N/A",
            help="Sammanlagda årskostnader för BRF:en"
        )
    
    with col4:
        performance_score = building_data.get('performance_score', 0)
        st.metric(
            "Prestationspoäng",
            f"{performance_score:.1f}/100" if performance_score else "N/A",
            help="Sammansatt prestationsindex baserat på kostnads- och energieffektivitet"
        )
        
        st.metric(
            "Adress",
            building_data.get('formatted_address', 'N/A'),
            help="Registrerad adress för byggnaden"
        )

def create_demo_sidebar():
    """Create demo sidebar with instructions."""
    # Show current progress in sidebar
    if 'survey_progress' in st.session_state:
        st.sidebar.metric(
            "Enkätframsteg",
            f"{st.session_state.survey_progress:.0f}%",
            help="Procentandel av enkäten som är slutförd"
        )
        st.sidebar.progress(st.session_state.survey_progress / 100)
    
    st.sidebar.markdown("## 📋 Demo Guide")
    st.sidebar.markdown("""
    **Steg 1:** Fyll i kostnadsenkäten
    - Ange årskostnader för olika kategorier
    - Specificera nuvarande leverantörer  
    - Betygsätt dina leverantörer (1-5 ⭐)
    
    **Steg 2:** Lås upp analyser
    - 30%+ = Grundläggande jämförelser
    - 60%+ = Detaljerade analyser  
    - 90%+ = Besparingsanalys upplåst
    - 100% = Full tillgång till alla funktioner
    
    **Steg 3:** Få rekommendationer  
    - Leverantörsalternativ för lågt betygsatta
    - Kostnadsbesparingsförslag
    - Benchmarking mot topp-BRF:er
    """)
    
    st.sidebar.divider()
    
    st.sidebar.markdown("## 🎁 Vad du får:")
    st.sidebar.success("""
    ✅ Kostnadsjämförelse med 50+ BRF:er
    
    ✅ AI-drivna besparingsförslag
    
    ✅ 20 verifierade Stockholm-leverantörer
    
    ✅ Finansiell prestandaindex
    
    ✅ Direkta kontaktuppgifter & priser
    
    ✅ Hållbarhetsbetyg & specialiteter
    """)

def main():
    """Main application entry point."""
    
    # Load data
    buildings_data = load_buildings_data()
    sjostaden_2 = find_sjostaden_2(buildings_data)
    
    if not sjostaden_2:
        st.error("Could not find BRF Sjöstaden 2 in the dataset.")
        st.stop()
    
    # Initialize survey system
    survey_system = SurveySystem(buildings_data, st.session_state)
    
    # Create demo interface
    create_demo_header()
    create_demo_sidebar()
    
    # Show BRF overview
    show_brf_overview(sjostaden_2)
    
    st.divider()
    
    # Main application tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 Kostnadsenkät", 
        "📊 Stadsdeljämförelse", 
        "💰 Besparingsanalys",
        "📈 Prestationsindex"
    ])
    
    with tab1:
        st.markdown("## 📝 BRF Kostnadsenkät")
        st.markdown("*Som styrelseledamot i BRF Sjöstaden 2, dela dina kostnader för att få tillgång till värdefull benchmarkingdata.*")
        
        # Show survey modal trigger or survey form
        if not st.session_state.get('peer_data_unlocked', False):
            show_survey = survey_system.show_survey_modal_trigger()
            
            if show_survey or st.session_state.get('show_survey', False):
                st.session_state.show_survey = True
                
                # Pre-populate with BRF Sjöstaden 2 data
                if 'current_survey' not in st.session_state or not st.session_state.current_survey.get('building_id'):
                    if 'current_survey' not in st.session_state:
                        st.session_state.current_survey = {}
                    st.session_state.current_survey['building_id'] = sjostaden_2['id']
                    st.session_state.current_survey['building_name'] = sjostaden_2['name']
                    
                    # Pre-populate with demo data to avoid re-doing survey
                    st.session_state.current_survey['costs'] = {
                        'electricity': 1828349.0,
                        'heating': 84077.0, 
                        'water': 476731.0,
                        'recycling': 145159.0,
                        'snow_removal': 157709.0,
                        'cleaning': 250000.0,
                        'gardening': 180000.0
                    }
                    st.session_state.current_survey['suppliers'] = {
                        'electricity': 'Ellevio',
                        'heating': 'Stockholm Exergi',
                        'water': 'Stockholm Vatten och Avfall',
                        'recycling': 'Sysav',
                        'snow_removal': 'Svensk Snöröjning',
                        'cleaning': 'Städbolaget Stockholm',
                        'gardening': 'Grön & Skön Trädgård'
                    }
                    st.session_state.current_survey['satisfaction'] = {
                        'electricity': 4,
                        'heating': 3,  # Low rating to trigger recommendations
                        'water': 5,
                        'recycling': 4,
                        'snow_removal': 2,  # Low rating to trigger recommendations
                        'cleaning': 3,  # Low rating to trigger recommendations
                        'gardening': 4
                    }
                    st.session_state.current_survey['contact_info'] = {
                        'name': 'Anna Styrelseledamot',
                        'email': 'anna@sjostaden2.se',
                        'phone': '08-123 456 78',
                        'position': 'Ordförande'
                    }
                    # Mark as completed
                    st.session_state.peer_data_unlocked = True
                
                # Show survey form
                survey_submitted = survey_system.create_survey_modal()
                
                if survey_submitted:
                    st.session_state.show_survey = False
                    st.rerun()
        else:
            st.success("✅ Enkät slutförd! Du har nu tillgång till alla funktioner.")
            
            # Show survey summary
            survey_data = st.session_state.get('current_survey', {})
            if survey_data:
                st.markdown("### 📋 Din Enkätsdata")
                
                costs = survey_data.get('costs', {})
                suppliers = survey_data.get('suppliers', {})
                satisfaction = survey_data.get('satisfaction', {})
                
                if costs:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.markdown("**💰 Kostnader**")
                        for category, cost in costs.items():
                            category_name = survey_system.suppliers_db.suppliers.get(category, [{}])[0]
                            st.write(f"{category.title()}: {cost:,.0f} SEK/år")
                    
                    with col2:
                        st.markdown("**🏪 Leverantörer**")
                        for category, supplier in suppliers.items():
                            if category in costs:
                                st.write(f"{category.title()}: {supplier}")
                    
                    with col3:
                        st.markdown("**⭐ Nöjdhet**")
                        for category, rating in satisfaction.items():
                            if category in costs:
                                stars = "⭐" * rating
                                st.write(f"{category.title()}: {stars} ({rating}/5)")
    
    with tab2:
        st.markdown("## 📊 Din BRF jämfört med de andra i stadsdelen")
        
        if not st.session_state.get('peer_data_unlocked', False):
            survey_system.create_unlock_mechanism_ui()
        else:
            st.success("🔓 Jämförelsedata upplåst!")
            
            # Show current survey data and building comparison
            survey_data = st.session_state.get('current_survey', {})
            if survey_data and survey_data.get('costs'):
                # Create comprehensive cost breakdown charts
                survey_system.create_comprehensive_cost_breakdown_charts(survey_data, sjostaden_2, context="comparison_tab")
                
                # Add BRF-specific comparisons with names
                survey_system._create_brf_specific_comparisons(survey_data, sjostaden_2)
                
                # Show performance metrics
                performance_metrics = survey_system.calculate_financial_performance_index(sjostaden_2)
                
                st.markdown("### 🎯 Prestandamätning")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Energieffektivitet",
                        f"{performance_metrics['energy_efficiency_score']:.1f}/100",
                        help="Baserat på energiprestanda jämfört med referensvärde"
                    )
                
                with col2:
                    st.metric(
                        "Kostnadseffektivitet", 
                        f"{performance_metrics['cost_efficiency_score']:.1f}/100",
                        help="Baserat på kostnad per m² jämfört med marknadsgenomsnitt"
                    )
                
                with col3:
                    st.metric(
                        "Finansiell Prestationsindex",
                        f"{performance_metrics['financial_performance_index']:.1f}/100",
                        help="Sammansatt index (30% energi + 70% kostnad)"
                    )
            else:
                st.info("Slutför enkäten för att se detaljerad jämförelsedata.")
    
    with tab3:
        st.markdown("## 💰 Besparingsanalys")
        
        # Get current survey progress
        survey_data = st.session_state.get('current_survey', {})
        progress = survey_system.calculate_progress(survey_data)
        
        # Show locked/unlocked savings analysis
        survey_system.create_locked_savings_analysis_ui(progress)
    
    with tab4:
        st.markdown("## 📈 BRF Finansiell Prestationsindex")
        
        # Calculate and show performance index for Sjöstaden 2
        performance_metrics = survey_system.calculate_financial_performance_index(sjostaden_2)
        
        st.markdown("### 🏆 Din BRFs Prestationsindex")
        
        # Main performance index
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Modern Performance gauge chart
            import plotly.graph_objects as go
            
            index_value = performance_metrics['financial_performance_index']
            
            # Create a more modern, cleaner gauge
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = index_value,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {
                    'text': "Din BRF Prestationsindex",
                    'font': {'size': 16, 'color': '#2c3e50'}
                },
                number = {
                    'font': {'size': 36, 'color': '#2c3e50'},
                    'suffix': '/100'
                },
                gauge = {
                    'axis': {
                        'range': [None, 100],
                        'tickwidth': 1,
                        'tickcolor': "#8e44ad",
                        'tickfont': {'size': 12}
                    },
                    'bar': {
                        'color': "#3498db",
                        'thickness': 0.6
                    },
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "#ecf0f1",
                    'steps': [
                        {'range': [0, 40], 'color': "#e74c3c", 'name': 'Förbättring behövs'},
                        {'range': [40, 70], 'color': "#f39c12", 'name': 'Genomsnitt'}, 
                        {'range': [70, 85], 'color': "#2ecc71", 'name': 'Bra'},
                        {'range': [85, 100], 'color': "#27ae60", 'name': 'Excellent'}
                    ],
                    'threshold': {
                        'line': {'color': "#e74c3c", 'width': 3},
                        'thickness': 0.8,
                        'value': 85
                    }
                }
            ))
            
            fig.update_layout(
                height=350,
                font={'color': "#2c3e50", 'family': "Arial"},
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=20, r=20, t=60, b=20)
            )
            
            st.plotly_chart(fig, use_container_width=True, key="brf_performance_gauge_prestationsindex")
        
        with col2:
            st.markdown("#### 📊 Indexkomponenter")
            
            st.metric(
                "Energieffektivitet",
                f"{performance_metrics['energy_efficiency_score']:.1f}",
                help="30% viktning i slutindex"
            )
            
            st.metric(
                "Kostnadseffektivitet",
                f"{performance_metrics['cost_efficiency_score']:.1f}",
                help="70% viktning i slutindex"
            )
            
            st.markdown("---")
            
            st.metric(
                "Kostnad per m²",
                f"{performance_metrics['cost_per_m2']:.0f} SEK",
                delta=f"{performance_metrics['cost_per_m2'] - performance_metrics['market_average_cost_per_m2']:.0f}",
                delta_color="inverse"
            )
            
            st.metric(
                "Byggnadsstorlek (uppskattat)",
                f"{performance_metrics['total_m2']:.0f} m²",
                help="Baserat på antal lägenheter och byggnadsår"
            )
        
        # BRF Performance Comparison with all neighbors
        st.markdown("### 🏆 Prestationsranking - Alla BRF:er i Stadsdelen")
        
        # Calculate performance for all BRFs
        all_performances = []
        for building in buildings_data:
            if building.get('total_cost') and building.get('total_cost') > 0:
                perf_metrics = survey_system.calculate_financial_performance_index(building)
                all_performances.append({
                    'name': building.get('brf_name', 'Okänd BRF'),
                    'score': perf_metrics['financial_performance_index'],
                    'cost_per_m2': perf_metrics['cost_per_m2'],
                    'energy_score': perf_metrics['energy_efficiency_score'],
                    'is_current': building.get('brf_name') == sjostaden_2.get('brf_name')
                })
        
        # Sort by performance score (highest first)
        all_performances.sort(key=lambda x: x['score'], reverse=True)
        
        # Create performance comparison chart
        import plotly.graph_objects as go
        import plotly.express as px
        
        names = [p['name'] for p in all_performances]
        scores = [p['score'] for p in all_performances]
        colors = ['#ff6b6b' if p['is_current'] else '#4ecdc4' for p in all_performances]
        
        fig_ranking = go.Figure(data=[
            go.Bar(
                x=scores,
                y=names,
                orientation='h',
                marker_color=colors,
                text=[f"{score:.1f}" for score in scores],
                textposition='outside',
                hovertemplate='<b>%{y}</b><br>Prestationsindex: %{x:.1f}/100<extra></extra>'
            )
        ])
        
        fig_ranking.update_layout(
            title="🏆 Finansiell Prestationsindex - Alla BRF:er",
            xaxis=dict(
                title="Prestationsindex (0-100)",
                range=[0, 100], 
                gridcolor='lightgray'
            ),
            yaxis=dict(
                title="",
                gridcolor='lightgray'
            ),
            height=400,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(size=12),
            margin=dict(l=200)
        )
        
        st.plotly_chart(fig_ranking, use_container_width=True, key="brf_performance_ranking")
        
        # Show your position
        current_position = next((i+1 for i, p in enumerate(all_performances) if p['is_current']), len(all_performances))
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🥇 Din Position", f"#{current_position} av {len(all_performances)}")
        with col2:
            if current_position == 1:
                st.success("🏆 Topprestaterare!")
            elif current_position <= len(all_performances)//3:
                st.info("📈 Över genomsnitt")
            else:
                st.warning("🔧 Förbättringspotential")
        with col3:
            percentile = ((len(all_performances) - current_position + 1) / len(all_performances)) * 100
            st.metric("Percentil", f"{percentile:.0f}%")
        
        # Performance interpretation
        st.markdown("### 🎯 Prestandatolkning")
        
        if index_value >= 75:
            st.success(f"""
            **Excellent prestanda! 🌟**
            
            Din BRF presterar i topp 25% av alla jämförbara fastigheter. 
            Fortsätt det utmärkta arbetet med kostnads- och energieffektivitet.
            """)
        elif index_value >= 50:
            st.warning(f"""
            **Genomsnittlig prestanda 📊**
            
            Din BRF presterar på marknadsnivå. Det finns möjligheter för förbättring
            inom både energi- och kostnadseffektivitet.
            """)
        else:
            st.error(f"""
            **Förbättringspotential 🔧**
            
            Din BRF presterar under marknadsgenomsnittet. Prioritera
            energieffektiviseringsåtgärder och kostnadsoptimering.
            """)
        
        # Rankings and percentiles
        st.markdown("### 📊 Ranking & Percentiler")
        
        # Calculate rankings
        performances = []
        for building in buildings_data:
            if building.get('total_cost') and building.get('total_cost') > 0:
                perf = survey_system.calculate_financial_performance_index(building)
                performances.append(perf['financial_performance_index'])
        
        performances.sort(reverse=True)
        rank = performances.index(index_value) + 1 if index_value in performances else len(performances)
        percentile = ((len(performances) - rank + 1) / len(performances)) * 100
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Ranking",
                f"#{rank} av {len(performances)}",
                help="Position bland alla BRF:er i datasetet"
            )
        
        with col2:
            st.metric(
                "Percentil",
                f"{percentile:.1f}%",
                help="Procentandel av BRF:er som du presterar bättre än"
            )
        
        with col3:
            # Performance category
            if percentile >= 75:
                category = "🏆 Topprestaterare"
                color = "success"
            elif percentile >= 50:
                category = "📊 Över genomsnitt"
                color = "info"
            elif percentile >= 25:
                category = "⚖️ Genomsnitt"
                color = "warning"
            else:
                category = "🔧 Förbättringspotential"
                color = "error"
            
            st.metric(
                "Kategori",
                category,
                help="Prestandakategori baserat på percentilranking"
            )

if __name__ == "__main__":
    main()