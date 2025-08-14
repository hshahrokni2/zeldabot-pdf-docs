#!/usr/bin/env python3
"""
Integrated Survey & Map Application

This is the main application that combines the interactive map with the 
peer survey system, creating a comprehensive BRF analysis platform with
unlock mechanisms for peer data access.

Features:
- Interactive map with building performance data
- Progressive survey system with unlock mechanisms  
- Peer comparison with "half peers visible" system
- Supplier alternatives and recommendations
- Mobile-responsive design with accessibility
- Export functionality for insights and data
"""

import streamlit as st
import sys
import os
from typing import Dict, List, Optional
import json
import pandas as pd
import plotly.graph_objects as go

# Import our modules
from survey_system import SurveySystem, UnlockLevel, COST_CATEGORIES, SUPPLIER_CATEGORIES
from peer_comparison_system import PeerComparisonEngine, PeerComparisonUI
from hammarby_interactive_map import HammarbyMapInterface

# Page configuration
st.set_page_config(
    page_title="BRF Peer Survey & Map Analysis",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for mobile responsiveness and accessibility
st.markdown("""
<style>
    /* Mobile-first responsive design */
    @media (max-width: 768px) {
        .stColumns > div {
            width: 100% !important;
            flex: none !important;
        }
        
        .stSelectbox label, .stTextInput label, .stNumberInput label {
            font-size: 14px !important;
        }
        
        .metric-card {
            padding: 0.5rem !important;
            margin: 0.25rem 0 !important;
        }
    }
    
    /* Accessibility improvements */
    .stButton > button {
        border-radius: 8px;
        border: 2px solid transparent;
        transition: all 0.3s ease;
    }
    
    .stButton > button:focus {
        border-color: #2E8B57;
        box-shadow: 0 0 0 2px rgba(46, 139, 87, 0.2);
        outline: none;
    }
    
    /* High contrast mode support */
    @media (prefers-contrast: high) {
        .stApp {
            background-color: #ffffff;
            color: #000000;
        }
    }
    
    /* Survey modal styling */
    .survey-modal {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.12);
        border: 2px solid #2E8B57;
        margin: 1rem 0;
        position: relative;
    }
    
    .unlock-status {
        background: linear-gradient(135deg, #2E8B57 0%, #32CD32 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 1rem 0;
    }
    
    .peer-insight {
        border-left: 4px solid #2E8B57;
        padding: 1rem;
        background: rgba(46, 139, 87, 0.05);
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
    }
    
    /* Progress indicator */
    .progress-container {
        background: #f0f2f6;
        border-radius: 10px;
        padding: 0.5rem;
        margin: 0.5rem 0;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        border-radius: 8px 8px 0 0;
    }
</style>
""", unsafe_allow_html=True)

class IntegratedSurveyMapApp:
    """Main application class integrating survey and map functionality."""
    
    def __init__(self):
        self.data_file = "/Users/hosseins/Dropbox/Zelda/ZeldaDemo/hammarby_map_visualization_data.json"
        self.map_interface = None
        self.survey_system = None
        self.comparison_engine = None
        self.comparison_ui = None
        
        self._initialize_app()
    
    def _initialize_app(self):
        """Initialize all app components."""
        
        # Load map data and initialize map interface
        try:
            self.map_interface = HammarbyMapInterface(self.data_file)
            buildings_data = self.map_interface.buildings
            
            if not buildings_data:
                st.error("Kunde inte ladda byggnadsdata. Kontrollera att datafilen existerar.")
                return
            
            # Initialize survey system
            self.survey_system = SurveySystem(buildings_data, st.session_state)
            
            # Initialize comparison engine
            self.comparison_engine = PeerComparisonEngine(
                buildings_data, 
                self.survey_system.suppliers_db
            )
            
            # Initialize comparison UI
            self.comparison_ui = PeerComparisonUI(self.comparison_engine)
            
        except Exception as e:
            st.error(f"Fel vid initialisering av applikationen: {e}")
            st.stop()
    
    def run(self):
        """Run the main application."""
        
        # App header
        self._render_header()
        
        # Main navigation
        tab1, tab2, tab3, tab4 = st.tabs([
            "🗺️ Interaktiv Karta", 
            "📝 Kostnadsenkät", 
            "📊 Peer-jämförelse", 
            "📤 Export & Resultat"
        ])
        
        with tab1:
            self._render_map_tab()
        
        with tab2:
            self._render_survey_tab()
        
        with tab3:
            self._render_comparison_tab()
        
        with tab4:
            self._render_export_tab()
        
        # Footer
        self._render_footer()
    
    def _render_header(self):
        """Render application header."""
        
        # Main title with responsive layout
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown("""
            # 🏢 BRF Kostnadsjämförelse Hammarby Sjöstad
            ### Upptäck besparingsmöjligheter genom peer-jämförelser och leverantörsalternativ
            """)
        
        with col2:
            # Show unlock status if survey started
            if hasattr(st.session_state, 'survey_progress') and st.session_state.survey_progress > 0:
                unlock_level = getattr(st.session_state, 'unlock_level', UnlockLevel.NONE)
                progress = getattr(st.session_state, 'survey_progress', 0)
                
                # Status indicator
                level_colors = {
                    UnlockLevel.NONE: "#808080",
                    UnlockLevel.BASIC: "#FFD700", 
                    UnlockLevel.INTERMEDIATE: "#32CD32",
                    UnlockLevel.FULL: "#2E8B57"
                }
                
                color = level_colors.get(unlock_level, "#808080")
                
                st.markdown(f"""
                <div style="
                    background: {color};
                    color: white;
                    padding: 1rem;
                    border-radius: 10px;
                    text-align: center;
                ">
                    <h4 style="margin: 0; color: white;">Upplåsningsstatus</h4>
                    <p style="margin: 0; color: white;">{unlock_level.value.title()}</p>
                    <small style="color: rgba(255,255,255,0.8);">{progress:.0f}% färdigt</small>
                </div>
                """, unsafe_allow_html=True)
        
        # Value proposition banner
        if not getattr(st.session_state, 'peer_data_unlocked', False):
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 1.5rem;
                border-radius: 15px;
                text-align: center;
                color: white;
                margin: 1rem 0;
            ">
                <h3 style="margin: 0; color: white;">🎯 Dela dina kostnader - Få värdefulla insikter</h3>
                <p style="margin: 0.5rem 0 0 0; color: rgba(255,255,255,0.9);">
                    Jämför med 50+ BRF:er • Få leverantörsalternativ • Upptäck besparingsmöjligheter
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    def _render_map_tab(self):
        """Render interactive map tab."""
        
        st.markdown("### 🗺️ Utforska BRF:er i Hammarby Sjöstad")
        
        # Map controls in sidebar
        with st.sidebar:
            st.header("Kartkontroller")
            
            # Color scheme selection
            color_scheme = st.selectbox(
                "Färgkoda byggnader:",
                options=['energy', 'performance', 'cost'],
                format_func=lambda x: {
                    'energy': 'Energieffektivitet',
                    'performance': 'Prestationspoäng',
                    'cost': 'Kostnadseffektivitet'
                }[x],
                index=0
            )
            
            # Show survey progress for current building
            if hasattr(st.session_state, 'current_survey') and st.session_state.current_survey.get('building_id'):
                building_id = st.session_state.current_survey['building_id']
                building = self.survey_system.get_building_by_id(building_id)
                if building:
                    st.markdown("### 🎯 Vald BRF")
                    st.info(f"**{building['name']}**\nAdress: {building.get('address', 'N/A')}")
                    
                    # Show quick stats
                    if building.get('monthly_fee'):
                        st.metric("Månadsavgift", f"{building['monthly_fee']:,.0f} SEK")
                    if building.get('performance_score'):
                        st.metric("Prestationspoäng", f"{building['performance_score']:.1f}/100")
        
        # Create map interface
        try:
            # Map display area
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Create and display map
                m = self.map_interface.create_base_map()
                m = self.map_interface.add_building_markers(m, color_by=color_scheme)
                m = self.map_interface.add_legend(m, color_by=color_scheme)
                
                # Display map
                try:
                    from streamlit_folium import st_folium
                    map_data = st_folium(m, width=700, height=500, returned_objects=["last_clicked"])
                    
                    # Handle building selection from map
                    if map_data.get('last_object_clicked_tooltip'):
                        building_name = map_data['last_object_clicked_tooltip'].split(' - ')[0]
                        # Find building by name
                        for building in self.map_interface.buildings:
                            if building['name'] == building_name:
                                if 'current_survey' not in st.session_state:
                                    st.session_state.current_survey = {}
                                st.session_state.current_survey['building_id'] = building['id']
                                st.session_state.current_survey['building_name'] = building['name']
                                st.success(f"Valde {building_name} för enkäten!")
                                break
                                
                except ImportError:
                    st.warning("Installera streamlit-folium för full interaktivitet")
                    st.components.v1.html(m._repr_html_(), height=500)
            
            with col2:
                st.markdown("### 📊 Statistik")
                
                # Summary stats
                total_buildings = len(self.map_interface.buildings)
                energy_buildings = len([b for b in self.map_interface.buildings if b.get('energy_performance_kwh_m2')])
                
                st.metric("Totalt antal BRF", total_buildings)
                st.metric("Med energidata", f"{energy_buildings}/{total_buildings}")
                
                # Quick survey trigger
                st.markdown("---")
                st.markdown("### 🚀 Börja här")
                
                if st.button("Starta Kostnadsenkät", type="primary", use_container_width=True):
                    st.switch_page("📝 Kostnadsenkät")  # This would switch to survey tab
                    
                st.markdown("""
                <div style="
                    background: #f8f9fa;
                    padding: 1rem;
                    border-radius: 8px;
                    margin: 1rem 0;
                    font-size: 0.9em;
                ">
                    <b>Tips:</b> Klicka på en byggnad i kartan för att välja den för din enkät!
                </div>
                """, unsafe_allow_html=True)
        
        except Exception as e:
            st.error(f"Fel vid laddning av kartan: {e}")
    
    def _render_survey_tab(self):
        """Render survey tab."""
        
        st.markdown("### 📝 BRF Kostnadsenkät")
        
        # Check if survey is already submitted
        if getattr(st.session_state, 'peer_data_unlocked', False):
            st.success("✅ Enkät redan skickad! Se dina resultat i 'Peer-jämförelse' fliken.")
            
            # Show option to start new survey
            if st.button("Starta ny enkät", type="secondary"):
                # Reset survey state
                st.session_state.current_survey = {}
                st.session_state.survey_progress = 0
                st.session_state.peer_data_unlocked = False
                st.rerun()
            
            return
        
        # Show unlock mechanism UI
        unlocked = self.survey_system.create_unlock_mechanism_ui()
        
        if not unlocked:
            # Show survey trigger
            if self.survey_system.show_survey_modal_trigger():
                st.session_state.show_survey_modal = True
        
        # Show survey modal if triggered
        if getattr(st.session_state, 'show_survey_modal', False):
            completed = self.survey_system.create_survey_modal()
            
            if completed:
                st.session_state.show_survey_modal = False
                st.rerun()
        
        # Show current progress if survey started
        elif hasattr(st.session_state, 'survey_progress') and st.session_state.survey_progress > 0:
            progress = st.session_state.survey_progress
            
            # Progress indicator
            st.markdown("#### 📊 Enkätprogress")
            progress_col1, progress_col2 = st.columns([3, 1])
            
            with progress_col1:
                st.progress(progress / 100)
            
            with progress_col2:
                st.metric("Färdigt", f"{progress:.0f}%")
            
            # Continue survey button
            if st.button("Fortsätt enkät", type="primary"):
                st.session_state.show_survey_modal = True
                st.rerun()
            
            # Show preview of current data
            if hasattr(st.session_state, 'current_survey'):
                current_data = st.session_state.current_survey
                
                with st.expander("Förhandsvisa ifyllda data"):
                    if current_data.get('building_name'):
                        st.write(f"**BRF:** {current_data['building_name']}")
                    
                    if current_data.get('costs'):
                        st.write("**Kostnader:**")
                        for category, cost in current_data['costs'].items():
                            st.write(f"- {SUPPLIER_CATEGORIES.get(category, category)}: {cost:,.0f} SEK")
                    
                    if current_data.get('suppliers'):
                        st.write("**Leverantörer:**")
                        for category, supplier in current_data['suppliers'].items():
                            st.write(f"- {SUPPLIER_CATEGORIES.get(category, category)}: {supplier}")
    
    def _render_comparison_tab(self):
        """Render peer comparison tab."""
        
        st.markdown("### 📊 Peer-jämförelse & Rekommendationer")
        
        # Check if peer data is unlocked
        if not getattr(st.session_state, 'peer_data_unlocked', False):
            st.warning("🔒 Fyll i enkäten för att låsa upp peer-jämförelser")
            
            unlock_progress = getattr(st.session_state, 'survey_progress', 0)
            
            if unlock_progress > 0:
                st.info(f"Du är {unlock_progress:.0f}% färdig med enkäten. Fortsätt för att låsa upp mer data!")
                
                if st.button("Gå till enkät", type="primary"):
                    st.switch_page("📝 Kostnadsenkät")
            else:
                st.info("Starta enkäten för att börja låsa upp peer-jämförelser!")
            
            # Show teaser of what's available
            st.markdown("""
            ### 🎁 Vad väntar på dig:
            
            **Grundnivå (30% ifyllt):**
            - Grundläggande kostnadsjämförelser med liknande BRF:er
            - Översikt av besparingsmöjligheter
            
            **Mellannivå (60% ifyllt):**
            - Detaljerad benchmarking
            - Leverantörsalternativ med kontaktuppgifter
            - Specifika kostnadsbesparingsförslag
            
            **Full tillgång (90% ifyllt):**
            - Komplett peer-analys med percentiler
            - AI-drivna rekommendationer
            - Prioriterade åtgärdslistor
            - Premium leverantörsförslag
            """)
            
            return
        
        # Get user survey response
        respondent_id = getattr(st.session_state, 'respondent_id', '')
        user_responses = getattr(st.session_state, 'survey_responses', {})
        
        if respondent_id not in user_responses:
            st.error("Kunde inte hitta dina enkätdata. Vänligen fyll i enkäten igen.")
            return
        
        user_response = user_responses[respondent_id]
        unlock_level = getattr(st.session_state, 'unlock_level', UnlockLevel.BASIC)
        
        # Create comparison dashboard
        self.comparison_ui.create_comparison_dashboard(user_response, unlock_level)
    
    def _render_export_tab(self):
        """Render export and results tab."""
        
        st.markdown("### 📤 Export & Resultat")
        
        # Check if data is available for export
        if not getattr(st.session_state, 'peer_data_unlocked', False):
            st.warning("🔒 Inga resultat att exportera än. Fyll i enkäten först!")
            return
        
        # Get user data
        respondent_id = getattr(st.session_state, 'respondent_id', '')
        user_responses = getattr(st.session_state, 'survey_responses', {})
        
        if respondent_id not in user_responses:
            st.error("Kunde inte hitta dina enkätdata.")
            return
        
        user_response = user_responses[respondent_id]
        unlock_level = getattr(st.session_state, 'unlock_level', UnlockLevel.BASIC)
        
        # Generate data for export
        benchmarks = self.comparison_engine.get_benchmark_data(
            user_response.costs, unlock_level
        )
        insights = self.comparison_engine.generate_insights(user_response, benchmarks)
        
        # Create export interface
        self.comparison_ui.create_export_interface(user_response, benchmarks, insights)
        
        # Summary of results
        st.markdown("---")
        st.markdown("### 📋 Sammanfattning av resultat")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_costs = sum(user_response.costs.values())
            st.metric("Dina totalkostnader", f"{total_costs:,.0f} SEK/år")
        
        with col2:
            total_savings = sum(b.savings_potential for b in benchmarks.values())
            st.metric("Besparingspotential", f"{total_savings:,.0f} SEK/år")
        
        with col3:
            st.metric("Antal rekommendationer", len(insights))
        
        # Show key insights summary
        if insights:
            st.markdown("#### 🔑 Viktigaste rekommendationerna:")
            
            top_insights = sorted(
                [i for i in insights if i.potential_savings], 
                key=lambda x: x.potential_savings, 
                reverse=True
            )[:3]
            
            for i, insight in enumerate(top_insights, 1):
                st.markdown(f"""
                **{i}. {insight.title}**
                - Potential besparing: {insight.potential_savings:,.0f} SEK/år
                - Säkerhetsnivå: {insight.confidence_level*100:.0f}%
                """)
    
    def _render_footer(self):
        """Render application footer."""
        
        st.markdown("---")
        
        footer_col1, footer_col2, footer_col3 = st.columns(3)
        
        with footer_col1:
            st.markdown("""
            **🏢 BRF Kostnadsjämförelse**  
            Hammarby Sjöstad Edition
            """)
        
        with footer_col2:
            st.markdown("""
            **📊 Data & Säkerhet**  
            All data behandlas anonymt enligt GDPR
            """)
        
        with footer_col3:
            st.markdown("""
            **💡 Feedback**  
            Hjälp oss förbättra verktyget
            """)
        
        # Data source information
        st.caption(f"""
        Dataunderlag: {len(self.map_interface.buildings)} BRF:er i Hammarby Sjöstad  
        Leverantörsdatabas: {sum(len(suppliers) for suppliers in self.survey_system.suppliers_db.suppliers.values())} verifierade leverantörer  
        Senast uppdaterad: {self.map_interface.data.get('metadata', {}).get('created_at', 'Okänd')}
        """)

def main():
    """Main application entry point."""
    
    # Initialize and run the integrated app
    app = IntegratedSurveyMapApp()
    app.run()

if __name__ == "__main__":
    main()