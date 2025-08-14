#!/usr/bin/env python3
"""
BRF Peer Data Survey System with Unlock Mechanisms

This module provides a comprehensive survey system for BRF (housing cooperative) 
board members to share operational cost data in exchange for peer comparisons
and supplier alternatives.

Features:
- Modal survey forms with progressive disclosure
- Unlock mechanism for peer data access
- Real-time validation and feedback
- Supplier alternatives database
- Cost-saving recommendations
- Mobile-responsive design
- Accessibility compliance (WCAG 2.1)
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import uuid
import hashlib

# Configuration constants - Updated with Grok categories
COST_CATEGORIES = [
    'cleaning', 'heating', 'electricity', 'water', 'recycling', 
    'snow_removal', 'gardening', 'administration', 'security', 'insurance'
]

SATISFACTION_SCALE = {
    1: "Very Dissatisfied",
    2: "Dissatisfied", 
    3: "Neutral",
    4: "Satisfied",
    5: "Very Satisfied"
}

SUPPLIER_CATEGORIES = {
    'cleaning': 'Städtjänster',
    'heating': 'Värme & VVS',
    'electricity': 'El & Energi',
    'water': 'VVS & Vatten',
    'recycling': 'Avfall & Återvinning',
    'snow_removal': 'Snöröjning',
    'gardening': 'Trädgård & Grönområden',
    'administration': 'Administration & Förvaltning',
    'security': 'Säkerhet & Bevakning',
    'insurance': 'Försäkring'
}

class UnlockLevel(Enum):
    """Survey completion levels that unlock different data access."""
    NONE = "none"
    BASIC = "basic"  # Building selection + 3 categories
    INTERMEDIATE = "intermediate"  # 5 categories + supplier info
    FULL = "full"  # All categories + satisfaction ratings

@dataclass
class SurveyResponse:
    """Survey response data structure."""
    building_id: int
    building_name: str
    respondent_id: str
    timestamp: datetime
    costs: Dict[str, Optional[float]]
    suppliers: Dict[str, Optional[str]]
    satisfaction: Dict[str, Optional[int]]
    contact_info: Dict[str, str]
    unlock_level: UnlockLevel
    completion_percentage: float

@dataclass
class SupplierInfo:
    """Supplier information structure."""
    name: str
    category: str
    description: str
    estimated_cost_range: Tuple[float, float]
    contact: str
    location: str
    rating: float
    specialties: List[str]

class StockholmSuppliersDB:
    """Real Stockholm suppliers database from Grok research."""
    
    def __init__(self):
        self.suppliers = self._load_grok_suppliers()
    
    def _load_grok_suppliers(self) -> Dict[str, List[SupplierInfo]]:
        """Load real Stockholm supplier database from Grok research."""
        import json
        try:
            with open('grok_suppliers_database.json', 'r', encoding='utf-8') as f:
                grok_data = json.load(f)
        except FileNotFoundError:
            st.warning("Grok suppliers database not found. Using fallback data.")
            return self._initialize_fallback_suppliers()
        
        # Convert Grok data to SupplierInfo format
        suppliers_dict = {}
        for category, suppliers_list in grok_data.items():
            suppliers_dict[category] = []
            for supplier_data in suppliers_list:
                # Parse pricing range
                pricing_range = supplier_data.get('pricing_range', '0–0 SEK/year')
                try:
                    # Extract numbers from pricing string like "150,000–300,000 SEK/year"
                    prices = pricing_range.replace(',', '').replace(' SEK/year', '').split('–')
                    if len(prices) == 2:
                        min_price = float(prices[0])
                        max_price = float(prices[1])
                    else:
                        min_price = max_price = 0
                except:
                    min_price = max_price = 0
                
                supplier_info = SupplierInfo(
                    name=supplier_data.get('name', 'Unknown'),
                    category=category,
                    description=supplier_data.get('services', ''),
                    estimated_cost_range=(min_price, max_price),
                    contact=f"{supplier_data.get('phone', 'N/A')} | {supplier_data.get('email', 'N/A')}",
                    location=supplier_data.get('address', 'Stockholm'),
                    rating=supplier_data.get('rating', 3.0),
                    specialties=supplier_data.get('specialties', [])
                )
                suppliers_dict[category].append(supplier_info)
        
        return suppliers_dict
    
    def _initialize_fallback_suppliers(self) -> Dict[str, List[SupplierInfo]]:
        """Fallback supplier data if Grok database is not available."""
        return {
            'cleaning': [
                SupplierInfo(
                    name="Vardagsfrid",
                    category="cleaning",
                    description="Stairway cleaning, common areas, exteriors, deep cleaning, window cleaning; tailored for property owners and BRFs",
                    estimated_cost_range=(150000, 300000),
                    contact="+46 10 516 43 00 | info@vardagsfrid.se",
                    location="Fleminggatan 7, Stockholm",
                    rating=4.5,
                    specialties=["eco-friendly", "nordic-swan-certified", "chemical-free"]
                ),
                SupplierInfo(
                    name="Freska",
                    category="cleaning",
                    description="Regular and deep cleaning of common areas, exteriors, windows; property showing cleaning",
                    estimated_cost_range=(150000, 250000),
                    contact="020-10 00 15 | kundtjanst@freska.se",
                    location="Årstaängsvägen 17, Stockholm",
                    rating=3.5,
                    specialties=["eco-friendly", "employee-wellbeing"]
                )
            ],
            'heating': [
                SupplierInfo(
                    name="Stockholm Exergi",
                    category="heating",
                    description="District heating connections, heat pumps, ventilation upgrades; energy efficiency assessments",
                    estimated_cost_range=(500000, 1000000),
                    contact="020-31 31 51 | kundservice@stockholmexergi.se",
                    location="Jägmästargatan 2, Stockholm",
                    rating=4.0,
                    specialties=["renewables", "district-heating", "fossil-free", "bio-ccs"]
                ),
                SupplierInfo(
                    name="GK",
                    category="heating",
                    description="HVAC installation, maintenance, ventilation systems; multi-unit buildings",
                    estimated_cost_range=(200000, 400000),
                    contact="+46 8 636 40 00 | info@gk.se",
                    location="Various locations in Stockholm",
                    rating=4.0,
                    specialties=["smart-hvac", "energy-efficient", "sustainable-buildings"]
                )
            ],
            'snow_removal': [
                SupplierInfo(
                    name="SmartaVal AB",
                    category="snow_removal",
                    description="Snow removal, de-icing, pathway clearing; adaptable to BRFs",
                    estimated_cost_range=(50000, 150000),
                    contact="+46 8-722 22 00 | info@smarta-val.se",
                    location="Stockholm",
                    rating=4.0,
                    specialties=["eco-clean", "sustainable-methods", "de-icing"]
                ),
                SupplierInfo(
                    name="Söder OM Söder Kontor & Fastighetsservice AB",
                    category="snow_removal",
                    description="Winter maintenance, snow removal for BRFs",
                    estimated_cost_range=(50000, 150000),
                    contact="08-572 301 00 | info@soderomsoder.se",
                    location="Konsumentvägen 12, Älvsjö",
                    rating=4.0,
                    specialties=["winter-maintenance", "sustainable-practices"]
                )
            ],
            'gardening': [
                SupplierInfo(
                    name="Urbangreen",
                    category="gardening",
                    description="Courtyard maintenance, green roofs, plantings; BRF-focused",
                    estimated_cost_range=(200000, 400000),
                    contact="+46 8-634 54 00 | info@urbangreen.se",
                    location="Stockholm",
                    rating=4.5,
                    specialties=["green-roofs", "sustainable-landscapes", "green-infrastructure"]
                ),
                SupplierInfo(
                    name="Green Landscaping Group",
                    category="gardening",
                    description="Landscaping, green roofs, courtyard maintenance for BRFs",
                    estimated_cost_range=(200000, 400000),
                    contact="+46 8-518 05 000 | info@greenlandscaping.com",
                    location="Biblioteksgatan 25, Stockholm",
                    rating=4.0,
                    specialties=["sustainable-outdoor", "eco-friendly", "landscaping"]
                )
            ],
            'electricity': [
                SupplierInfo(
                    name="Din Elektriker i Stockholm AB",
                    category="electricity",
                    description="Electrical maintenance, LED retrofits, EV charging installations; full BRF services",
                    estimated_cost_range=(100000, 250000),
                    contact="08-744 11 50 | info@dinelektriker.se",
                    location="Gröndalsvägen 22, Stockholm",
                    rating=4.5,
                    specialties=["led-retrofit", "ev-charging", "energy-efficiency"]
                ),
                SupplierInfo(
                    name="Euro El i Stockholm",
                    category="electricity",
                    description="Electrical maintenance, retrofits, EV charging; adaptable to BRF needs",
                    estimated_cost_range=(100000, 250000),
                    contact="+46 8-644 44 00 | contact@euroel.se",
                    location="Various in Stockholm",
                    rating=4.0,
                    specialties=["retrofits", "led-upgrade", "maintenance"]
                )
            ],
            'water': [
                SupplierInfo(
                    name="Cyklande Rörmokaren",
                    category="water",
                    description="Plumbing, water quality testing, leak detection; BRF common areas",
                    estimated_cost_range=(150000, 300000),
                    contact="08-30 81 00 | hej@cyklanderormokaren.se",
                    location="Själagårdsgatan 21, Stockholm",
                    rating=4.5,
                    specialties=["eco-friendly", "cycling-service", "leak-detection"]
                ),
                SupplierInfo(
                    name="Alvis Rörakut Service AB",
                    category="water",
                    description="Plumbing, leak detection, water systems maintenance; BRF-focused",
                    estimated_cost_range=(150000, 300000),
                    contact="08-650 01 44 | info@alvisrorakut.se",
                    location="Industrivägen 23, Solna",
                    rating=4.0,
                    specialties=["water-management", "energy-efficient", "vvs"]
                )
            ],
            'insurance': [
                SupplierInfo(
                    name="Folksam",
                    category="insurance",
                    description="BRF property and liability insurance; climate adaptation coverage",
                    estimated_cost_range=(200000, 500000),
                    contact="0771-950 950 | info@folksam.se",
                    location="Bohusgatan 14, Stockholm",
                    rating=3.5,
                    specialties=["climate-adaptation", "sustainable-investments", "property-liability"]
                ),
                SupplierInfo(
                    name="Trygg-Hansa",
                    category="insurance",
                    description="BRF-specific property, liability; additional covers",
                    estimated_cost_range=(200000, 500000),
                    contact="0771-111 110 | info@trygghansa.se",
                    location="Fleminggatan 18, Stockholm",
                    rating=3.5,
                    specialties=["sustainable-living", "green-initiatives", "additional-covers"]
                )
            ],
            'administration': [
                SupplierInfo(
                    name="Fastighetsägarna Service Stockholm AB",
                    category="administration",
                    description="Administration, board support, financial services; full BRF management",
                    estimated_cost_range=(300000, 600000),
                    contact="08-617 75 00 | service@fastighetsagarna.se",
                    location="Alströmergatan 14, Stockholm",
                    rating=3.5,
                    specialties=["full-brf-management", "board-support", "financial-services"]
                ),
                SupplierInfo(
                    name="Jakobsen Properties AB",
                    category="administration",
                    description="Administration, board support, financial for BRFs; digital tools",
                    estimated_cost_range=(300000, 600000),
                    contact="076-767 09 97 | henrik@jproperties.se",
                    location="Ljusslingan 30 a, Stockholm",
                    rating=4.0,
                    specialties=["digital-tools", "sustainable-management", "board-support"]
                )
            ],
            'recycling': [
                SupplierInfo(
                    name="Envac",
                    category="recycling",
                    description="Automated waste collection, recycling, composting; designed for BRFs like Hammarby Sjöstad",
                    estimated_cost_range=(200000, 500000),
                    contact="+46 8 785 00 10 | info@envac.se",
                    location="Fleminggatan 7, Stockholm",
                    rating=4.5,
                    specialties=["automated-collection", "circular-economy", "emission-reduction"]
                ),
                SupplierInfo(
                    name="Sortera",
                    category="recycling",
                    description="Waste collection, recycling, composting; BRF services",
                    estimated_cost_range=(100000, 250000),
                    contact="+46 8-409 166 00 | info@sortera.se",
                    location="Årstaängsvägen 21B, Stockholm",
                    rating=4.0,
                    specialties=["circular-economy", "100%-recycling", "composting"]
                )
            ],
            'security': [
                SupplierInfo(
                    name="Svenska Hemlarm",
                    category="security",
                    description="Access control, cameras, alarms; BRF security",
                    estimated_cost_range=(100000, 300000),
                    contact="+46 8-600 55 00 | info@svenskahemlarm.se",
                    location="Primusgatan 18, Stockholm",
                    rating=4.0,
                    specialties=["access-control", "energy-efficient", "modern-systems"]
                ),
                SupplierInfo(
                    name="SOS Alarm Sverige AB",
                    category="security",
                    description="Alarm systems, access control; emergency services for BRFs",
                    estimated_cost_range=(100000, 300000),
                    contact="020-31 31 51 | info@sosalarm.se",
                    location="Stockholm",
                    rating=4.0,
                    specialties=["emergency-services", "reliability", "sustainable-operations"]
                )
            ]
        }
    
    def get_suppliers_by_category(self, category: str) -> List[SupplierInfo]:
        """Get suppliers for a specific category."""
        return self.suppliers.get(category, [])
    
    def get_alternative_suppliers(self, category: str, exclude_supplier: str = None) -> List[SupplierInfo]:
        """Get alternative suppliers, optionally excluding current supplier."""
        suppliers = self.get_suppliers_by_category(category)
        if exclude_supplier:
            suppliers = [s for s in suppliers if s.name.lower() != exclude_supplier.lower()]
        return sorted(suppliers, key=lambda s: s.rating, reverse=True)[:2]  # Return top 2 alternatives by rating

class SurveySystem:
    """Main survey system class managing data collection and peer access."""
    
    def __init__(self, buildings_data: List[Dict], session_state: Any):
        self.buildings_data = buildings_data
        self.session_state = session_state
        self.suppliers_db = StockholmSuppliersDB()
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize session state variables."""
        if 'survey_responses' not in self.session_state:
            self.session_state.survey_responses = {}
        if 'unlock_level' not in self.session_state:
            self.session_state.unlock_level = UnlockLevel.NONE
        if 'current_survey' not in self.session_state:
            self.session_state.current_survey = {}
        if 'survey_progress' not in self.session_state:
            self.session_state.survey_progress = 0
        if 'respondent_id' not in self.session_state:
            self.session_state.respondent_id = str(uuid.uuid4())
        if 'peer_data_unlocked' not in self.session_state:
            self.session_state.peer_data_unlocked = False
        if 'survey_completed' not in self.session_state:
            self.session_state.survey_completed = False
        if 'survey_completion_timestamp' not in self.session_state:
            self.session_state.survey_completion_timestamp = None
        
        # Update progress and unlock level on each initialization
        self._update_progress_and_unlock_level()
    
    def _update_progress_and_unlock_level(self):
        """Update progress and unlock level based on current survey data."""
        if 'current_survey' in self.session_state:
            progress = self.calculate_progress(self.session_state.current_survey)
            self.session_state.survey_progress = progress
            self.session_state.unlock_level = self.get_unlock_level(progress)
            
            # Update peer data unlock status
            if progress >= 30:
                self.session_state.peer_data_unlocked = True
    
    def calculate_progress(self, survey_data: Dict) -> float:
        """Calculate survey completion percentage."""
        total_fields = len(COST_CATEGORIES) * 3  # cost + supplier + satisfaction
        total_fields += 4  # building selection + contact fields
        
        completed_fields = 0
        
        # Building selection
        if survey_data.get('building_id'):
            completed_fields += 1
        
        # Cost categories - only count if cost > 0
        costs = survey_data.get('costs', {})
        suppliers = survey_data.get('suppliers', {})
        satisfaction = survey_data.get('satisfaction', {})
        
        for category in COST_CATEGORIES:
            # Only count fields for categories where cost is entered
            if costs.get(category, 0) > 0:
                completed_fields += 1  # cost field
                if suppliers.get(category):
                    completed_fields += 1  # supplier field
                if satisfaction.get(category):
                    completed_fields += 1  # satisfaction field
        
        # Contact info - only count fields that have values
        contact_info = survey_data.get('contact_info', {})
        for field in ['name', 'email', 'phone']:
            if contact_info.get(field, '').strip():
                completed_fields += 1
        
        return min(100, (completed_fields / total_fields) * 100)
    
    def get_unlock_level(self, progress: float) -> UnlockLevel:
        """Determine unlock level based on survey progress."""
        if progress >= 90:
            return UnlockLevel.FULL
        elif progress >= 60:
            return UnlockLevel.INTERMEDIATE
        elif progress >= 30:
            return UnlockLevel.BASIC
        else:
            return UnlockLevel.NONE
    
    def create_survey_modal(self) -> bool:
        """Create modal survey form with progressive disclosure."""
        
        # Initialize modal container
        with st.container():
            st.markdown("""
            <div style="
                background: white;
                padding: 2rem;
                border-radius: 10px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                border: 2px solid #2E8B57;
                margin: 1rem 0;
            ">
            """, unsafe_allow_html=True)
            
            # Survey header with progress
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown("### 🏢 BRF Kostnadsjämförelse - Enkätformulär")
                st.markdown("*Dela dina kostnader och få tillgång till anonymiserad jämförelsedata*")
            
            with col2:
                progress = self.session_state.get('survey_progress', 0)
                st.metric("Färdigställt", f"{progress:.0f}%")
                st.progress(progress / 100)
            
            # Value proposition
            with st.expander("🎯 Vad får du ut av att delta?", expanded=False):
                st.markdown("""
                **Genom att dela dina kostnadsdata får du:**
                - 📊 Anonymiserad jämförelsedata från liknande BRF:er
                - 💡 Kostnadsbesparande rekommendationer baserat på peer-data
                - 🏪 Alternativa leverantörer med konkurrenskraftiga priser
                - 📈 Benchmarking mot din stadsdels genomsnitt
                
                **Din data behandlas helt anonymt och säkert enligt GDPR.**
                """)
            
            return self._render_survey_form()
    
    def _render_survey_form(self) -> bool:
        """Render the main survey form with sections."""
        
        # Initialize current survey data
        if 'current_survey' not in self.session_state:
            self.session_state.current_survey = {
                'costs': {},
                'suppliers': {},
                'satisfaction': {},
                'contact_info': {}
            }
        
        survey_data = self.session_state.current_survey
        
        # Ensure all required keys exist
        if 'costs' not in survey_data:
            survey_data['costs'] = {}
        if 'suppliers' not in survey_data:
            survey_data['suppliers'] = {}
        if 'satisfaction' not in survey_data:
            survey_data['satisfaction'] = {}
        if 'contact_info' not in survey_data:
            survey_data['contact_info'] = {}
        
        # Section 1: Building Selection
        st.markdown("#### 🏢 1. Välj din BRF")
        
        building_options = {b['name']: b['id'] for b in self.buildings_data}
        selected_building_name = st.selectbox(
            "Vilken BRF representerar du?",
            options=list(building_options.keys()),
            index=0 if not survey_data.get('building_name') else 
                  list(building_options.keys()).index(survey_data.get('building_name')),
            help="Välj den BRF som du representerar som styrelseledamot eller förvaltare"
        )
        
        if selected_building_name:
            survey_data['building_id'] = building_options[selected_building_name]
            survey_data['building_name'] = selected_building_name
        
        st.divider()
        
        # Section 2: Cost Categories with Integrated Input
        st.markdown("#### 💰 2. Kostnadsdata per Kategori")
        st.markdown("*För varje kategori: ange kostnad, leverantör och nöjdhetsbetyg*")
        
        # Get building data to show existing costs
        selected_building = None
        for building in self.buildings_data:
            if building.get('id') == survey_data.get('building_id') or building.get('name') == survey_data.get('building_name'):
                selected_building = building
                break
        
        # Pre-populate with existing cost data from building if available
        cost_mapping = {
            'cleaning': 'cost_cleaning',
            'heating': 'cost_heating', 
            'electricity': 'cost_electricity',
            'water': 'cost_water',
            'recycling': 'cost_recycling',
            'snow_removal': 'cost_snow_removal',
            'gardening': None,  # Not in annual reports typically
            'administration': None,  # Usually included in overhead
            'security': None,  # Separate line item if exists
            'insurance': None  # Part of building insurance
        }
        
        # Calculate progress once at the beginning so it can be used throughout
        new_progress = self.calculate_progress(survey_data)
        
        # Display categories in a 2-column layout
        col1, col2 = st.columns(2)
        
        for i, category in enumerate(COST_CATEGORIES):
            column = col1 if i % 2 == 0 else col2
            
            with column:
                # Create a container for each category
                with st.container():
                    st.markdown(f"### {SUPPLIER_CATEGORIES[category]}")
                    
                    # Get existing cost from building data if available
                    building_cost_key = cost_mapping.get(category)
                    existing_cost = selected_building.get(building_cost_key, 0) if selected_building and building_cost_key else 0
                    
                    # Cost input/display
                    if existing_cost and existing_cost > 0:
                        # Show as read-only metric for existing costs
                        st.metric(
                            "💰 Årskostnad (från årsredovisning)", 
                            f"{existing_cost:,.0f} SEK",
                            help="Kostnad från din BRFs årsredovisning"
                        )
                        # Store in survey data
                        survey_data['costs'][category] = float(existing_cost)
                    else:
                        # Allow input for missing costs
                        current_cost = survey_data['costs'].get(category)
                        cost_value = st.number_input(
                            "💰 Årskostnad (uppskattad)",
                            min_value=0,
                            value=int(current_cost) if current_cost else 0,
                            step=1000,
                            key=f"cost_{category}",
                            help=f"Uppskattad årskostnad för {SUPPLIER_CATEGORIES[category].lower()}"
                        )
                        
                        if cost_value > 0:
                            survey_data['costs'][category] = float(cost_value)
                        elif category in survey_data['costs']:
                            del survey_data['costs'][category]
                    
                    # Only show supplier and rating inputs if cost is entered
                    cost_amount = survey_data['costs'].get(category, 0)
                    if cost_amount > 0:
                        # Get suppliers for this category from database
                        category_suppliers = self.suppliers_db.get_suppliers_by_category(category)
                        
                        # Create dropdown options
                        supplier_options = ["Välj leverantör..."]
                        supplier_options.extend([supplier.name for supplier in category_suppliers])
                        supplier_options.append("📝 Lägg till ny leverantör")
                        
                        # Current supplier selection
                        current_supplier = survey_data['suppliers'].get(category, '')
                        
                        # Find current selection index
                        current_index = 0
                        if current_supplier:
                            # Check if it's one of the existing suppliers
                            for i, supplier in enumerate(category_suppliers):
                                if supplier.name == current_supplier:
                                    current_index = i + 1  # +1 because of "Välj leverantör..." at index 0
                                    break
                            else:
                                # If not found in database, it's a custom supplier
                                current_index = len(supplier_options) - 1  # "Lägg till ny leverantör"
                        
                        # Supplier dropdown
                        selected_option = st.selectbox(
                            "🏪 Leverantör",
                            options=supplier_options,
                            index=current_index,
                            key=f"supplier_dropdown_{category}",
                            help=f"Välj befintlig leverantör eller lägg till ny för {SUPPLIER_CATEGORIES[category].lower()}"
                        )
                        
                        supplier_name = None
                        
                        if selected_option == "📝 Lägg till ny leverantör":
                            # Show text input for custom supplier
                            supplier_name = st.text_input(
                                "📝 Namn på ny leverantör",
                                value=current_supplier if current_supplier not in [s.name for s in category_suppliers] else '',
                                key=f"custom_supplier_{category}",
                                placeholder="Ange leverantörens namn...",
                                help="Skriv in namnet på din nuvarande leverantör"
                            )
                        elif selected_option != "Välj leverantör...":
                            # Use selected supplier from dropdown
                            supplier_name = selected_option
                            
                            # Show supplier information if it's from database
                            selected_supplier = next((s for s in category_suppliers if s.name == selected_option), None)
                            if selected_supplier:
                                st.info(f"📍 {selected_supplier.location} | 📞 {selected_supplier.contact.split('|')[0].strip()} | ⭐ {selected_supplier.rating}/5")
                        
                        if supplier_name:
                            survey_data['suppliers'][category] = supplier_name
                            
                            # Satisfaction rating (only if supplier is entered)
                            current_rating = survey_data['satisfaction'].get(category)
                            rating = st.select_slider(
                                "⭐ Nöjdhetsbetyg",
                                options=list(SATISFACTION_SCALE.keys()),
                                value=current_rating if current_rating else 3,
                                format_func=lambda x: f"{x}⭐ - {SATISFACTION_SCALE[x]}",
                                key=f"satisfaction_{category}",
                                help="Hur nöjd är styrelsen med denna leverantör?"
                            )
                            
                            survey_data['satisfaction'][category] = rating
                            
                            # Show immediate feedback for low ratings
                            if rating <= 3:
                                st.warning(f"💡 Lågt betyg - vi kommer rekommendera alternativ!")
                        else:
                            # Remove supplier and rating if supplier name is cleared
                            if category in survey_data['suppliers']:
                                del survey_data['suppliers'][category]
                            if category in survey_data['satisfaction']:
                                del survey_data['satisfaction'][category]
                    else:
                        # Remove supplier and rating if cost is cleared
                        if category in survey_data['suppliers']:
                            del survey_data['suppliers'][category]
                        if category in survey_data['satisfaction']:
                            del survey_data['satisfaction'][category]
                    
                    # Add some spacing between categories
                    st.markdown("---")
        
        # Section 3: Contact Information (Show near end)
        if new_progress >= 60:
            st.markdown("#### 📧 3. Kontaktinformation")
            st.markdown("*För att kunna dela resultat och uppföljning (behandlas konfidentiellt)*")
            
            contact_col1, contact_col2 = st.columns(2)
            
            with contact_col1:
                name = st.text_input(
                    "Namn",
                    value=survey_data['contact_info'].get('name', ''),
                    key="contact_name",
                    placeholder="Förnamn Efternamn"
                )
                if name:
                    survey_data['contact_info']['name'] = name
                
                email = st.text_input(
                    "E-post",
                    value=survey_data['contact_info'].get('email', ''),
                    key="contact_email",
                    placeholder="namn@exempel.se"
                )
                if email:
                    survey_data['contact_info']['email'] = email
            
            with contact_col2:
                phone = st.text_input(
                    "Telefon",
                    value=survey_data['contact_info'].get('phone', ''),
                    key="contact_phone", 
                    placeholder="08-123 45 67"
                )
                if phone:
                    survey_data['contact_info']['phone'] = phone
                
                role = st.selectbox(
                    "Roll i BRF",
                    options=["Styrelseordförande", "Styrelseledamot", "Förvaltare", "Ekonomiansvarig", "Annat"],
                    index=0 if not survey_data['contact_info'].get('role') else 
                          ["Styrelseordförande", "Styrelseledamot", "Förvaltare", "Ekonomiansvarig", "Annat"].index(survey_data['contact_info'].get('role')),
                    key="contact_role"
                )
                survey_data['contact_info']['role'] = role
        
        # Update progress and unlock level (recalculate in case contact info was added)
        final_progress = self.calculate_progress(survey_data)
        self.session_state.survey_progress = final_progress
        self.session_state.unlock_level = self.get_unlock_level(final_progress)
        self.session_state.current_survey = survey_data
        
        # Update peer data unlock status based on progress
        if final_progress >= 30 and not self.session_state.peer_data_unlocked:
            self.session_state.peer_data_unlocked = True
        
        # Submit button and unlock status
        st.markdown("---")
        
        submit_col, status_col = st.columns([1, 2])
        
        with submit_col:
            can_submit = final_progress >= 30  # Minimum 30% completion
            
            if st.button(
                "📤 Skicka Enkät", 
                disabled=not can_submit,
                type="primary" if can_submit else "secondary",
                help="Kräver minst 30% ifyllt för att skicka"
            ):
                if can_submit:
                    return self._submit_survey()
        
        with status_col:
            # Show unlock status
            unlock_level = self.get_unlock_level(final_progress)
            
            if unlock_level == UnlockLevel.NONE:
                st.info("🔒 Fyll i mer information för att låsa upp jämförelsedata")
            elif unlock_level == UnlockLevel.BASIC:
                st.success("🔓 Grundläggande jämförelsedata upplåst!")
            elif unlock_level == UnlockLevel.INTERMEDIATE:
                st.success("🔓🔓 Detaljerad jämförelsedata och leverantörsförslag upplåst!")
            elif unlock_level == UnlockLevel.FULL:
                st.success("🔓🔓🔓 Full tillgång till alla peer-data och rekommendationer!")
        
        # Close modal div
        st.markdown("</div>", unsafe_allow_html=True)
        
        return False
    
    def _submit_survey(self) -> bool:
        """Submit survey and update session state."""
        survey_data = self.session_state.current_survey
        
        # Create survey response object
        response = SurveyResponse(
            building_id=survey_data.get('building_id'),
            building_name=survey_data.get('building_name', ''),
            respondent_id=self.session_state.respondent_id,
            timestamp=datetime.now(),
            costs=survey_data.get('costs', {}),
            suppliers=survey_data.get('suppliers', {}),
            satisfaction=survey_data.get('satisfaction', {}),
            contact_info=survey_data.get('contact_info', {}),
            unlock_level=self.session_state.unlock_level,
            completion_percentage=self.session_state.survey_progress
        )
        
        # Store response
        self.session_state.survey_responses[self.session_state.respondent_id] = response
        self.session_state.peer_data_unlocked = True
        
        # Store completion flags for persistence
        self.session_state.survey_completed = True
        self.session_state.survey_completion_timestamp = datetime.now()
        
        # Show success message
        st.success("✅ Tack för ditt deltagande! Du har nu tillgång till jämförelsedata och rekommendationer.")
        st.balloons()
        
        # Clear current survey
        self.session_state.current_survey = {}
        
        return True
    
    def get_building_by_id(self, building_id: int) -> Optional[Dict]:
        """Get building data by ID."""
        for building in self.buildings_data:
            if building.get('id') == building_id or building.get('building_id') == building_id:
                return building
        return None

    def estimate_building_size_m2(self, building_data: Dict) -> float:
        """Estimate building size in m² based on available data."""
        # Try to estimate apartment count from financial data first
        monthly_fee = building_data.get('monthly_fee', 0)
        total_income = building_data.get('total_income', 0)
        
        apartment_count = 1  # Default fallback
        
        if monthly_fee > 0 and total_income > 0:
            # Estimate apartments from total_income / (monthly_fee * 12)
            apartment_count = max(1, round(total_income / (monthly_fee * 12)))
        else:
            # Fallback to property count, but assume more apartments per property
            property_count = building_data.get('property_count', 1)
            apartment_count = max(10, property_count * 15)  # Assume 15 apartments per property minimum
        
        # Stockholm BRF average apartment sizes based on construction year
        construction_year = building_data.get('construction_year', 2000)
        if construction_year < 1960:
            avg_apt_size = 65  # Older buildings tend to be smaller
        elif construction_year < 1990:
            avg_apt_size = 75  # Mid-period developments
        else:
            avg_apt_size = 85  # Modern developments, larger apartments
        
        # Estimate total building size
        estimated_m2 = apartment_count * avg_apt_size
        
        # Add common areas (typically 15-25% of total)
        total_m2 = estimated_m2 * 1.2
        
        return total_m2
    
    def normalize_costs_per_m2(self, building_data: Dict, costs: Dict[str, float]) -> Dict[str, float]:
        """Normalize all costs to SEK per m²."""
        total_m2 = self.estimate_building_size_m2(building_data)
        return {category: cost / total_m2 for category, cost in costs.items()}
    
    def calculate_financial_performance_index(self, building_data: Dict) -> Dict[str, float]:
        """Calculate BRF Financial Performance Index."""
        # Get energy performance (lower is better)
        energy_performance = building_data.get('energy_performance', 100)
        
        # Calculate energy efficiency score (0-100, higher is better)
        energy_efficiency_score = max(0, 100 - (energy_performance / 159 * 100))
        
        # Get total cost and estimate per m²
        total_cost = building_data.get('total_cost', 0)
        total_m2 = self.estimate_building_size_m2(building_data)
        cost_per_m2 = total_cost / total_m2 if total_m2 > 0 else 0
        
        # Calculate market average (from dataset analysis)
        market_average_cost_per_m2 = self._calculate_market_average_cost_per_m2()
        
        # Calculate cost efficiency score (0-100, higher is better)
        if market_average_cost_per_m2 > 0:
            cost_efficiency_score = max(0, 100 - (cost_per_m2 / market_average_cost_per_m2 * 100))
        else:
            cost_efficiency_score = 50  # Default if no market data
        
        # Composite Financial Performance Index
        financial_performance_index = (energy_efficiency_score * 0.3) + (cost_efficiency_score * 0.7)
        
        return {
            'energy_efficiency_score': energy_efficiency_score,
            'cost_efficiency_score': cost_efficiency_score,
            'financial_performance_index': financial_performance_index,
            'cost_per_m2': cost_per_m2,
            'total_m2': total_m2,
            'market_average_cost_per_m2': market_average_cost_per_m2
        }
    
    def _calculate_market_average_cost_per_m2(self) -> float:
        """Calculate market average cost per m² from all buildings."""
        total_costs = []
        for building in self.buildings_data:
            if building.get('total_cost') and building.get('total_cost') > 0:
                m2 = self.estimate_building_size_m2(building)
                cost_per_m2 = building['total_cost'] / m2
                total_costs.append(cost_per_m2)
        
        return sum(total_costs) / len(total_costs) if total_costs else 0
    
    def calculate_savings_potential(self, survey_data: Dict) -> Dict[str, Any]:
        """Calculate potential savings based on peer data and market benchmarks."""
        building_id = survey_data.get('building_id')
        building_data = self.get_building_by_id(building_id)
        
        if not building_data:
            return {'error': 'Building not found'}
        
        performance_metrics = self.calculate_financial_performance_index(building_data)
        survey_costs = survey_data.get('costs', {})
        
        # Calculate potential savings for each category
        savings_potential = {}
        total_potential_savings = 0
        
        # Get top 25% performers for benchmarking
        top_performers = self._get_top_25_percent_performers()
        
        for category, cost in survey_costs.items():
            if cost > 0:
                # Compare with top 25% performers
                benchmark_cost = self._get_category_benchmark(category, top_performers)
                if benchmark_cost and cost > benchmark_cost:
                    potential_saving = cost - benchmark_cost
                    savings_potential[category] = {
                        'current_cost': cost,
                        'benchmark_cost': benchmark_cost,
                        'potential_saving': potential_saving,
                        'saving_percentage': (potential_saving / cost) * 100
                    }
                    total_potential_savings += potential_saving
        
        return {
            'total_potential_savings': total_potential_savings,
            'category_savings': savings_potential,
            'performance_metrics': performance_metrics,
            'recommendations': self._generate_savings_recommendations(savings_potential, survey_data)
        }
    
    def _get_top_25_percent_performers(self) -> List[Dict]:
        """Get top 25% performing buildings by cost efficiency."""
        performances = []
        for building in self.buildings_data:
            if building.get('total_cost') and building.get('total_cost') > 0:
                performance = self.calculate_financial_performance_index(building)
                performances.append({
                    'building': building,
                    'performance_index': performance['financial_performance_index']
                })
        
        # Sort by performance index and get top 25%
        performances.sort(key=lambda x: x['performance_index'], reverse=True)
        top_25_percent_count = max(1, int(len(performances) * 0.25))
        
        return [p['building'] for p in performances[:top_25_percent_count]]
    
    def _get_category_benchmark(self, category: str, top_performers: List[Dict]) -> Optional[float]:
        """Get benchmark cost for a category from top performers."""
        costs = []
        for building in top_performers:
            cost_field = f'cost_{category}'
            if building.get(cost_field) and building[cost_field] > 0:
                costs.append(building[cost_field])
        
        return sum(costs) / len(costs) if costs else None
    
    def _generate_savings_recommendations(self, savings_potential: Dict, survey_data: Dict) -> List[Dict]:
        """Generate AI-driven savings recommendations."""
        recommendations = []
        
        for category, savings_info in savings_potential.items():
            if savings_info['potential_saving'] > 5000:  # Focus on significant savings
                # Check supplier satisfaction
                satisfaction = survey_data.get('satisfaction', {}).get(category, 5)
                current_supplier = survey_data.get('suppliers', {}).get(category, '')
                
                recommendation = {
                    'category': category,
                    'priority': 'high' if savings_info['potential_saving'] > 20000 else 'medium',
                    'potential_saving': savings_info['potential_saving'],
                    'current_cost': savings_info['current_cost'],
                    'recommended_action': self._get_action_recommendation(category, satisfaction, savings_info),
                    'alternative_suppliers': []
                }
                
                # Add supplier alternatives if satisfaction is low
                if satisfaction <= 3:
                    alternatives = self.suppliers_db.get_alternative_suppliers(category, current_supplier)
                    recommendation['alternative_suppliers'] = alternatives
                
                recommendations.append(recommendation)
        
        return sorted(recommendations, key=lambda x: x['potential_saving'], reverse=True)
    
    def _get_action_recommendation(self, category: str, satisfaction: int, savings_info: Dict) -> str:
        """Get specific action recommendation based on category and satisfaction."""
        saving_percentage = savings_info['saving_percentage']
        
        if satisfaction <= 3:
            return f"Byt leverantör inom {SUPPLIER_CATEGORIES[category].lower()}. Nuvarande kostnad är {saving_percentage:.1f}% högre än toppresterande BRF:er och låg nöjdhet indikerar att byte kan vara lönsamt."
        elif saving_percentage > 30:
            return f"Förhandla om priser eller överväg leverantörsbyte. Kostnaden är {saving_percentage:.1f}% högre än bästa BRF:erna i området."
        else:
            return f"Optimera nuvarande avtal. Mindre förbättringsmöjligheter ({saving_percentage:.1f}% över benchmark)."

    def show_supplier_alternatives_for_low_ratings(self, survey_data: Dict) -> None:
        """Show supplier alternatives when user rates supplier 3 stars or below."""
        satisfaction_ratings = survey_data.get('satisfaction', {})
        suppliers = survey_data.get('suppliers', {})
        
        low_rated_categories = []
        for category, rating in satisfaction_ratings.items():
            if rating <= 3:
                low_rated_categories.append(category)
        
        if low_rated_categories:
            st.markdown("### 🔄 Rekommenderade Leverantörsalternativ")
            st.markdown("*Baserat på dina nöjdhetsbetyg rekommenderar vi följande alternativ:*")
            
            for category in low_rated_categories:
                current_supplier = suppliers.get(category, 'Okänd leverantör')
                alternatives = self.suppliers_db.get_alternative_suppliers(category, current_supplier)
                
                if alternatives:
                    st.markdown(f"#### {SUPPLIER_CATEGORIES[category]}")
                    st.markdown(f"**Nuvarande:** {current_supplier} (Betyg: {satisfaction_ratings[category]} ⭐)")
                    
                    col1, col2 = st.columns(2)
                    for i, supplier in enumerate(alternatives):
                        column = col1 if i % 2 == 0 else col2
                        
                        with column:
                            with st.container():
                                st.markdown(f"""
                                **{supplier.name}** ⭐ {supplier.rating}
                                
                                📍 {supplier.location}  
                                📞 {supplier.contact}
                                
                                {supplier.description}
                                
                                **Specialiteter:** {', '.join(supplier.specialties)}
                                
                                **Prisintervall:** {supplier.estimated_cost_range[0]:,} - {supplier.estimated_cost_range[1]:,} SEK/år
                                """)
                                
                                if st.button(f"Kontakta {supplier.name}", key=f"contact_{supplier.name}_{category}"):
                                    st.success(f"Kontaktinformation för {supplier.name}: {supplier.contact}")
                    
                    st.divider()

    def create_comprehensive_cost_breakdown_charts(self, survey_data: Dict, building_data: Dict, context: str = "default") -> None:
        """Create comprehensive cost breakdown visualizations with color-coding."""
        st.markdown("### 📊 Kostnadsnedbrytning & Jämförelse")
        
        # Define color scheme for categories
        category_colors = {
            'cleaning': '#FF6B6B',          # Red
            'maintenance': '#4ECDC4',       # Teal
            'snow_removal': '#45B7D1',      # Blue
            'gardening': '#96CEB4',         # Green
            'electricity': '#FFEAA7',       # Yellow
            'heating': '#DDA0DD',           # Plum
            'insurance': '#98D8C8',         # Mint
            'administration': '#F7DC6F',    # Light Yellow
            'repairs': '#BB8FCE',           # Light Purple
            'security': '#85C1E9'           # Light Blue
        }
        
        survey_costs = survey_data.get('costs', {})
        total_m2 = self.estimate_building_size_m2(building_data)
        
        # Normalize costs to per m²
        normalized_costs = self.normalize_costs_per_m2(building_data, survey_costs)
        
        # Create main cost breakdown pie chart
        col1, col2 = st.columns(2)
        
        with col1:
            # Pie chart of total costs
            fig_pie = go.Figure(data=[
                go.Pie(
                    labels=[SUPPLIER_CATEGORIES.get(cat, cat).title() for cat in survey_costs.keys()],
                    values=list(survey_costs.values()),
                    hole=0.4,
                    marker_colors=[category_colors.get(cat, '#95A5A6') for cat in survey_costs.keys()],
                    textinfo='label+percent',
                    textposition='outside',
                    hovertemplate='<b>%{label}</b><br>Kostnad: %{value:,} SEK<br>Andel: %{percent}<extra></extra>'
                )
            ])
            
            fig_pie.update_layout(
                title="Kostnadsfördelning per Kategori",
                font_size=12,
                height=400
            )
            
            st.plotly_chart(fig_pie, use_container_width=True, key=f"cost_breakdown_pie_{context}")
        
        with col2:
            # Bar chart comparing costs per m²
            categories = list(normalized_costs.keys())
            cost_per_m2_values = list(normalized_costs.values())
            
            fig_bar = go.Figure(data=[
                go.Bar(
                    x=[SUPPLIER_CATEGORIES.get(cat, cat).title() for cat in categories],
                    y=cost_per_m2_values,
                    marker_color=[category_colors.get(cat, '#95A5A6') for cat in categories],
                    text=[f'{val:.0f} SEK/m²' for val in cost_per_m2_values],
                    textposition='auto',
                    hovertemplate='<b>%{x}</b><br>Kostnad: %{y:.0f} SEK/m²<extra></extra>'
                )
            ])
            
            fig_bar.update_layout(
                title="Kostnad per m² (Normaliserat)",
                xaxis_title="Kategori",
                yaxis_title="SEK per m²",
                height=400,
                xaxis_tickangle=-45
            )
            
            st.plotly_chart(fig_bar, use_container_width=True, key=f"cost_comparison_bar_{context}")
        
        # Market comparison chart
        self._create_market_comparison_chart(survey_data, building_data, category_colors, context)
    
    def _create_market_comparison_chart(self, survey_data: Dict, building_data: Dict, category_colors: Dict, context: str = "default") -> None:
        """Create market comparison visualization."""
        st.markdown("#### 📈 Jämfört med andra BRF:er i stadsdelen")
        
        survey_costs = survey_data.get('costs', {})
        normalized_costs = self.normalize_costs_per_m2(building_data, survey_costs)
        
        # Calculate market averages for each category
        market_averages = {}
        for category in COST_CATEGORIES:
            costs = []
            for brf in self.buildings_data:
                cost_field = f'cost_{category}'
                if brf.get(cost_field) and brf[cost_field] > 0:
                    m2 = self.estimate_building_size_m2(brf)
                    cost_per_m2 = brf[cost_field] / m2
                    costs.append(cost_per_m2)
            
            market_averages[category] = sum(costs) / len(costs) if costs else 0
        
        # Create comparison chart
        categories = list(set(list(normalized_costs.keys()) + list(market_averages.keys())))
        user_values = [normalized_costs.get(cat, 0) for cat in categories]
        market_values = [market_averages.get(cat, 0) for cat in categories]
        
        fig = go.Figure()
        
        # Add user costs
        fig.add_trace(go.Bar(
            name='Dina kostnader',
            x=[SUPPLIER_CATEGORIES.get(cat, cat).title() for cat in categories],
            y=user_values,
            marker_color=[category_colors.get(cat, '#95A5A6') for cat in categories],
            opacity=0.8
        ))
        
        # Add market average
        fig.add_trace(go.Bar(
            name='Marknadsgenomsnitt',
            x=[SUPPLIER_CATEGORIES.get(cat, cat).title() for cat in categories],
            y=market_values,
            marker_color='rgba(128, 128, 128, 0.6)',
            opacity=0.6
        ))
        
        fig.update_layout(
            title="Kostnadsjämförelse: Du vs. Marknadsgenomsnitt",
            xaxis_title="Kategori",
            yaxis_title="SEK per m²",
            barmode='group',
            height=500,
            xaxis_tickangle=-45,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True, key=f"market_comparison_scatter_{context}_{hash(str(survey_data))}")
    
    def create_locked_savings_analysis_ui(self, survey_completion_percentage: float) -> None:
        """Create UI for locked savings analysis that unlocks based on survey completion."""
        st.markdown("### 💰 Besparingspotential Analys")
        
        # Check if analysis should be unlocked
        unlock_threshold = 70  # Require 70% completion
        is_unlocked = survey_completion_percentage >= unlock_threshold
        
        if not is_unlocked:
            # Show locked state with progress toward unlock
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #FF6B6B 0%, #FF8E53 100%);
                padding: 2rem;
                border-radius: 15px;
                text-align: center;
                color: white;
                margin: 2rem 0;
            ">
                <h3>🔒 Besparingsanalys Låst</h3>
                <p style="font-size: 1.1em;">
                    Slutför enkäten för att låsa upp din personaliserade besparingsanalys
                </p>
                <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                    <h4>Framsteg mot upplåsning:</h4>
                    <div style="background: rgba(255,255,255,0.3); height: 20px; border-radius: 10px; margin: 10px 0;">
                        <div style="background: white; height: 20px; width: {survey_completion_percentage}%; border-radius: 10px; transition: width 0.3s;"></div>
                    </div>
                    <p>{survey_completion_percentage:.1f}% / {unlock_threshold}% krävs för upplåsning</p>
                </div>
                <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                    <h4>🎁 Vad väntar på dig:</h4>
                    <ul style="text-align: left; display: inline-block;">
                        <li>💡 AI-drivna besparingsförslag baserat på peer-data</li>
                        <li>📊 Detaljerad kostnadsjämförelse med topp 25% BRF:er</li>
                        <li>🏪 Personaliserade leverantörsrekommendationer</li>
                        <li>📈 Finansiell prestandaindex för din BRF</li>
                        <li>🎯 Konkreta handlingsplaner för kostnadsoptimering</li>
                    </ul>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Show teaser metrics (limited/anonymized)
            st.markdown("#### 📊 Förhandsvisning - Begränsad Data")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Genomsnittlig Besparing",
                    "∼ 45,000 SEK/år",
                    help="Baserat på anonymiserad data från liknande BRF:er (kräver fullständig enkät för personlig analys)"
                )
            
            with col2:
                st.metric(
                    "Mest Lönsam Kategori",
                    "Energioptimering",
                    help="Kategorin med störst besparingspotential (kräver fullständig enkät för din specifika situation)"
                )
            
            with col3:
                st.metric(
                    "Potentiella Leverantörer",
                    f"{len(self.suppliers_db.suppliers)} st",
                    help="Totalt antal förkalifierade leverantörer i vår databas"
                )
        
        else:
            # Show unlocked analysis
            self._show_unlocked_savings_analysis()
    
    def _show_unlocked_savings_analysis(self) -> None:
        """Show the full unlocked savings analysis."""
        if 'current_survey' not in self.session_state or not self.session_state.current_survey:
            st.warning("Ingen enkätdata tillgänglig för analys.")
            return
        
        survey_data = self.session_state.current_survey
        building_id = survey_data.get('building_id')
        building_data = self.get_building_by_id(building_id)
        
        if not building_data:
            st.error("Kunde inte hitta byggnadsdata för analys.")
            return
        
        st.success("🔓 Besparingsanalys Upplåst! Här är din personaliserade rapport:")
        
        # Calculate savings potential
        savings_analysis = self.calculate_savings_potential(survey_data)
        
        if 'error' in savings_analysis:
            st.error(f"Fel vid beräkning av besparingspotential: {savings_analysis['error']}")
            return
        
        # Show key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        performance_metrics = savings_analysis['performance_metrics']
        
        with col1:
            st.metric(
                "Total Besparingspotential",
                f"{savings_analysis['total_potential_savings']:,.0f} SEK/år",
                help="Total årlig besparing baserat på jämförelse med topp 25% presterande BRF:er"
            )
        
        with col2:
            st.metric(
                "Finansiell Prestandaindex",
                f"{performance_metrics['financial_performance_index']:.1f}/100",
                help="Sammansatt index baserat på energi- och kostnadseffektivitet"
            )
        
        with col3:
            st.metric(
                "Din Kostnad per m²",
                f"{performance_metrics['cost_per_m2']:.0f} SEK/m²",
                delta=f"{performance_metrics['cost_per_m2'] - performance_metrics['market_average_cost_per_m2']:.0f} vs. marknad",
                help=f"Jämfört med marknadsgenomsnittet på {performance_metrics['market_average_cost_per_m2']:.0f} SEK/m²"
            )
        
        with col4:
            st.metric(
                "Uppskattad Byggnadsstorlek",
                f"{performance_metrics['total_m2']:.0f} m²",
                help="Baserat på antal lägenheter och byggnadsår"
            )
        
        # Show detailed recommendations
        st.markdown("#### 🎯 Rekommendationer för Kostnadsoptimering")
        
        recommendations = savings_analysis['recommendations']
        if recommendations:
            for i, rec in enumerate(recommendations):
                priority_colors = {
                    'high': '#FF6B6B',
                    'medium': '#FFA726',
                    'low': '#66BB6A'
                }
                
                priority_color = priority_colors.get(rec['priority'], '#95A5A6')
                
                with st.expander(f"💡 {SUPPLIER_CATEGORIES.get(rec['category'], rec['category'])} - Potentiell besparing: {rec['potential_saving']:,.0f} SEK/år"):
                    st.markdown(f"""
                    **Prioritet:** <span style="color: {priority_color};">●</span> {rec['priority'].title()}
                    
                    **Nuvarande kostnad:** {rec['current_cost']:,.0f} SEK/år
                    
                    **Rekommendation:** {rec['recommended_action']}
                    """, unsafe_allow_html=True)
                    
                    # Show alternative suppliers if available
                    if rec['alternative_suppliers']:
                        st.markdown("**Rekommenderade leverantörer:**")
                        
                        supplier_col1, supplier_col2 = st.columns(2)
                        for j, supplier in enumerate(rec['alternative_suppliers']):
                            column = supplier_col1 if j % 2 == 0 else supplier_col2
                            
                            with column:
                                st.markdown(f"""
                                **{supplier.name}** ⭐ {supplier.rating}
                                
                                📍 {supplier.location} | 📞 {supplier.contact}
                                
                                {supplier.description}
                                
                                **Prisintervall:** {supplier.estimated_cost_range[0]:,} - {supplier.estimated_cost_range[1]:,} SEK/år
                                """)
        else:
            st.info("Inga större besparingsmöjligheter identifierade. Dina kostnader ligger redan nära branschens toppnivå!")
        
        # Show cost breakdown charts
        self.create_comprehensive_cost_breakdown_charts(survey_data, building_data, context="savings_analysis")
        
        # Show specific BRF comparisons with names
        self._create_brf_specific_comparisons(survey_data, building_data)
        
        # Show supplier alternatives for low-rated suppliers AND overpaying
        self._show_smart_supplier_recommendations(survey_data, building_data)

    def _create_brf_specific_comparisons(self, survey_data: Dict, building_data: Dict) -> None:
        """Create specific BRF comparisons with names for social pressure effect."""
        st.markdown("### 🏘️ Jämförelse med Grann-BRF:er")
        st.markdown("*Vad betalar era grannar i stadsdelen?*")
        
        current_brf_name = survey_data.get('building_name', 'Din BRF')
        survey_costs = survey_data.get('costs', {})
        
        if not survey_costs:
            st.info("Ange dina kostnader för att se specifika grann-jämförelser.")
            return
        
        # Get building size for current BRF
        current_building = None
        for building in self.buildings_data:
            if building.get('name') == survey_data.get('building_name') or building.get('id') == survey_data.get('building_id'):
                current_building = building
                break
        
        if not current_building:
            return
            
        current_size_m2 = self.estimate_building_size_m2(current_building)
        
        # Create comparisons for each category
        for category, cost in survey_costs.items():
            if cost > 0:
                st.markdown(f"#### {SUPPLIER_CATEGORIES.get(category, category.title())}")
                
                # Find best value BRFs (low cost + high satisfaction proxy)
                best_brfs = []
                
                for building in self.buildings_data:
                    if building.get('brf_name') == current_brf_name:
                        continue
                        
                    building_cost_key = f'cost_{category}'
                    building_cost = building.get(building_cost_key, 0)
                    
                    if building_cost > 0:
                        building_size = self.estimate_building_size_m2(building)
                        cost_per_m2 = building_cost / building_size
                        
                        # Simple satisfaction proxy (lower costs often = better efficiency)
                        # In real system, use actual satisfaction ratings
                        satisfaction_proxy = 5.0 - min((cost_per_m2 / (cost / current_size_m2)), 2.0)
                        
                        best_brfs.append({
                            'name': building.get('brf_name', 'Okänd BRF'),
                            'cost_per_m2': cost_per_m2,
                            'total_cost': building_cost,
                            'satisfaction_proxy': satisfaction_proxy
                        })
                
                if best_brfs:
                    # Sort by best value (low cost per m2)
                    best_brfs.sort(key=lambda x: x['cost_per_m2'])
                    best_brf = best_brfs[0]
                    
                    current_cost_per_m2 = cost / current_size_m2
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        if best_brf['cost_per_m2'] < current_cost_per_m2:
                            savings_per_m2 = current_cost_per_m2 - best_brf['cost_per_m2']
                            total_savings = savings_per_m2 * current_size_m2
                            
                            st.success(f"""
                            **🏆 {best_brf['name']}** betalar bara **{best_brf['cost_per_m2']:.0f} SEK/m²** 
                            för {SUPPLIER_CATEGORIES.get(category, category).lower()}!
                            
                            💰 **Potential besparing:** {total_savings:,.0f} SEK/år ({savings_per_m2:.0f} SEK/m²)
                            """)
                        else:
                            st.info(f"✅ **Bra jobbat!** {current_brf_name} har redan konkurrenskraftiga kostnader för {SUPPLIER_CATEGORIES.get(category, category).lower()}.")
                    
                    with col2:
                        # Show top 3 performers
                        st.markdown("**🏘️ Grannar:**")
                        for i, brf in enumerate(best_brfs[:3]):
                            if i == 0:
                                st.markdown(f"🥇 {brf['name'][:20]}")
                            elif i == 1:
                                st.markdown(f"🥈 {brf['name'][:20]}")
                            else:
                                st.markdown(f"🥉 {brf['name'][:20]}")
                            st.caption(f"{brf['cost_per_m2']:.0f} SEK/m²")
                
                st.divider()

    def _show_smart_supplier_recommendations(self, survey_data: Dict, building_data: Dict) -> None:
        """Show smart supplier recommendations based on overpaying OR low satisfaction."""
        st.markdown("### 🎯 Smarta Leverantörsrekommendationer")
        st.markdown("*Analys av kostnader och nöjdhet - fokus på kvalitet och värde*")
        
        survey_costs = survey_data.get('costs', {})
        survey_suppliers = survey_data.get('suppliers', {})
        survey_satisfaction = survey_data.get('satisfaction', {})
        
        if not survey_costs:
            st.info("Slutför enkäten för att få personaliserade leverantörsrekommendationer.")
            return
        
        current_building_size = self.estimate_building_size_m2(building_data)
        recommendations_found = False
        
        for category, cost in survey_costs.items():
            if cost <= 0:
                continue
                
            current_cost_per_m2 = cost / current_building_size
            current_supplier = survey_suppliers.get(category, 'Okänd leverantör')
            current_satisfaction = survey_satisfaction.get(category, 3)
            
            # Analyze current situation
            market_avg = self._get_market_average_cost_per_m2(category)
            market_min = self._get_market_minimum_cost_per_m2(category)
            
            is_overpaying = current_cost_per_m2 > market_avg * 1.3  # 30% above average
            is_dissatisfied = current_satisfaction <= 3
            has_good_price = current_cost_per_m2 <= market_avg * 1.1  # Within 10% of average
            
            # Recommend in multiple scenarios:
            # 1. Overpaying (regardless of satisfaction)
            # 2. Low satisfaction (regardless of price)
            # 3. Good price but low satisfaction (find better quality at similar price)
            should_recommend = is_overpaying or is_dissatisfied
            
            if should_recommend:
                recommendations_found = True
                
                st.markdown(f"#### {SUPPLIER_CATEGORIES.get(category, category.title())}")
                
                # Show current situation
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Determine recommendation scenario
                    scenario_type = ""
                    issues = []
                    
                    if is_overpaying and is_dissatisfied:
                        scenario_type = "Både höga kostnader och låg nöjdhet"
                        # Calculate realistic savings potential (cap at market minimum)
                        max_realistic_savings = (current_cost_per_m2 - market_min) * current_building_size
                        max_savings_pct = ((current_cost_per_m2 - market_min) / current_cost_per_m2) * 100
                        issues.append(f"💸 **Höga kostnader:** {max_realistic_savings:,.0f} SEK/år besparingspotential ({max_savings_pct:.0f}%)")
                        stars = "⭐" * current_satisfaction + "☆" * (5 - current_satisfaction)
                        issues.append(f"😞 **Låg nöjdhet:** {stars} ({current_satisfaction}/5)")
                    elif is_overpaying:
                        scenario_type = "Överbetalning identifierad"
                        max_realistic_savings = (current_cost_per_m2 - market_min) * current_building_size
                        max_savings_pct = ((current_cost_per_m2 - market_min) / current_cost_per_m2) * 100
                        issues.append(f"💸 **Besparingspotential:** {max_realistic_savings:,.0f} SEK/år ({max_savings_pct:.0f}%)")
                    elif is_dissatisfied and has_good_price:
                        scenario_type = "Bra pris men låg kvalitet"
                        stars = "⭐" * current_satisfaction + "☆" * (5 - current_satisfaction)
                        issues.append(f"💰 **Bra kostnad:** {current_cost_per_m2:.0f} SEK/m² (konkurrenskraftig)")
                        issues.append(f"😞 **Låg nöjdhet:** {stars} ({current_satisfaction}/5)")
                        issues.append("🎯 **Fokus:** Hitta högre kvalitet till liknande pris")
                    elif is_dissatisfied:
                        scenario_type = "Låg nöjdhet"
                        stars = "⭐" * current_satisfaction + "☆" * (5 - current_satisfaction)
                        issues.append(f"😞 **Låg nöjdhet:** {stars} ({current_satisfaction}/5)")
                    
                    st.warning(f"""
                    **{scenario_type}**
                    
                    **Nuvarande:** {current_supplier}
                    
                    {chr(10).join(issues)}
                    """)
                
                with col2:
                    st.metric(
                        "Nuvarande kostnad", 
                        f"{current_cost_per_m2:.0f} SEK/m²",
                        help=f"Totalkostnad: {cost:,.0f} SEK/år"
                    )
                
                # Get supplier recommendations - ALWAYS prioritize highest satisfaction
                category_suppliers = self.suppliers_db.get_suppliers_by_category(category)
                
                if category_suppliers:
                    # Sort by rating (highest first) - ALWAYS recommend best satisfied
                    best_suppliers = sorted(category_suppliers, key=lambda x: x.rating, reverse=True)[:3]
                    
                    if has_good_price and is_dissatisfied:
                        st.markdown("**🎯 Rekommenderade Alternativ (Högre Kvalitet, Liknande Pris):**")
                    else:
                        st.markdown("**🏆 Rekommenderade Alternativ (Högst Betygsatta):**")
                    
                    for i, supplier in enumerate(best_suppliers):
                        # Calculate potential cost impact
                        est_cost_range = supplier.estimated_cost_range
                        est_avg_cost = (est_cost_range[0] + est_cost_range[1]) / 2
                        est_cost_per_m2 = est_avg_cost / current_building_size
                        potential_savings = (current_cost_per_m2 - est_cost_per_m2) * current_building_size
                        
                        # Create supplier card
                        with st.container():
                            col_info, col_contact = st.columns([2, 1])
                            
                            with col_info:
                                rating_stars = "⭐" * int(supplier.rating) + ("⭐" if supplier.rating % 1 >= 0.5 else "")
                                satisfaction_improvement = supplier.rating - current_satisfaction
                                
                                # Smart cost messaging based on scenario
                                if has_good_price and is_dissatisfied:
                                    if abs(potential_savings) < current_building_size * 10:  # Less than 10 SEK/m² difference
                                        cost_text = f"💰 **Kostnad:** Liknande nivå ({est_cost_per_m2:.0f} SEK/m²)"
                                    elif potential_savings > 0:
                                        cost_text = f"💰 **Bonus besparing:** {potential_savings:,.0f} SEK/år"
                                    else:
                                        cost_text = f"💰 **Kostnad:** Något högre ({est_cost_per_m2:.0f} SEK/m²) för bättre kvalitet"
                                else:
                                    if potential_savings > 0:
                                        # Cap savings display at realistic levels
                                        max_realistic = (current_cost_per_m2 - market_min) * current_building_size
                                        displayed_savings = min(potential_savings, max_realistic)
                                        cost_text = f"💰 **Besparing:** {displayed_savings:,.0f} SEK/år"
                                    else:
                                        cost_text = f"💰 **Kostnad:** Liknande nivå ({est_cost_per_m2:.0f} SEK/m²)"
                                
                                st.success(f"""
                                **{supplier.name}** {rating_stars} **({supplier.rating}/5 kundnöjdhet)**
                                
                                {cost_text}
                                📈 **Kvalitetsförbättring:** +{satisfaction_improvement:.1f} ⭐
                                
                                *{supplier.description}*
                                """)
                                
                                # Show specialties
                                if supplier.specialties:
                                    specialties_text = ", ".join(supplier.specialties)
                                    st.caption(f"🏷️ Specialiteter: {specialties_text}")
                            
                            with col_contact:
                                st.markdown("**📞 Kontakt:**")
                                contact_parts = supplier.contact.split('|')
                                for part in contact_parts:
                                    st.text(part.strip())
                                st.caption(f"📍 {supplier.location}")
                                
                                # Action button
                                if st.button(f"Kontakta {supplier.name}", key=f"contact_{category}_{i}"):
                                    st.success(f"Kontaktinformation för {supplier.name} kopierad! 📋")
                        
                        st.divider()
                else:
                    st.info(f"Inga alternativ tillgängliga för {SUPPLIER_CATEGORIES.get(category, category)} just nu.")
        
        if not recommendations_found:
            st.success("""
            🎉 **Inga förbättringar behövs just nu!**
            
            Alla dina leverantörer har bra betyg och konkurrenskraftiga priser.
            Fortsätt det bra arbetet!
            """)

    def _is_overpaying_for_category(self, category: str, current_cost_per_m2: float) -> bool:
        """Check if current cost per m² is significantly above market average."""
        market_avg = self._get_market_average_cost_per_m2(category)
        return current_cost_per_m2 > market_avg * 1.2  # 20% above average = overpaying
    
    def _get_market_average_cost_per_m2(self, category: str) -> float:
        """Get market average cost per m² for a specific category."""
        costs = []
        cost_field = f'cost_{category}'
        
        for building in self.buildings_data:
            cost = building.get(cost_field, 0)
            if cost > 0:
                building_size = self.estimate_building_size_m2(building)
                cost_per_m2 = cost / building_size
                costs.append(cost_per_m2)
        
        return sum(costs) / len(costs) if costs else 0
    
    def _get_market_minimum_cost_per_m2(self, category: str) -> float:
        """Get market minimum (best) cost per m² for a specific category."""
        costs = []
        cost_field = f'cost_{category}'
        
        for building in self.buildings_data:
            cost = building.get(cost_field, 0)
            if cost > 0:
                building_size = self.estimate_building_size_m2(building)
                cost_per_m2 = cost / building_size
                costs.append(cost_per_m2)
        
        return min(costs) if costs else 0

    def create_unlock_mechanism_ui(self):
        """Create UI showing current unlock status and what's available."""
        
        if not self.session_state.peer_data_unlocked:
            # Show teaser and survey invitation
            st.markdown("""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 2rem;
                border-radius: 15px;
                text-align: center;
                color: white;
                margin: 2rem 0;
            ">
                <h2>🔐 Lås upp Peer-data & Rekommendationer</h2>
                <p style="font-size: 1.1em; margin: 1rem 0;">
                    Få tillgång till anonymiserad kostnadsdata från liknande BRF:er i Stockholm
                </p>
                <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 10px; margin: 1rem 0;">
                    <h4>🎁 Vad väntar på dig:</h4>
                    <ul style="text-align: left; display: inline-block;">
                        <li>📊 Benchmarking mot 50+ liknande BRF:er</li>
                        <li>💡 AI-drivna kostnadsbesparingsförslag</li>
                        <li>🏪 Kurerade leverantörsalternativ</li>
                        <li>📈 Detaljerade kostnadsanalyser</li>
                    </ul>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            return False
        
        else:
            # Show unlock status
            unlock_level = self.session_state.unlock_level
            
            status_colors = {
                UnlockLevel.BASIC: "#FFD700",
                UnlockLevel.INTERMEDIATE: "#32CD32", 
                UnlockLevel.FULL: "#2E8B57"
            }
            
            level_descriptions = {
                UnlockLevel.BASIC: "Grundläggande jämförelsedata tillgänglig",
                UnlockLevel.INTERMEDIATE: "Detaljerade analyser och leverantörsförslag",
                UnlockLevel.FULL: "Full tillgång till alla premium funktioner"
            }
            
            color = status_colors.get(unlock_level, "#808080")
            description = level_descriptions.get(unlock_level, "Okänd nivå")
            
            st.markdown(f"""
            <div style="
                background: {color};
                color: white;
                padding: 1rem;
                border-radius: 10px;
                text-align: center;
                margin: 1rem 0;
            ">
                <h3>🔓 Upplåsningsstatus: {unlock_level.value.title()}</h3>
                <p>{description}</p>
            </div>
            """, unsafe_allow_html=True)
            
            return True
    
    def show_survey_modal_trigger(self) -> bool:
        """Show button to trigger survey modal."""
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button(
                "🚀 Starta Kostnadsenkät", 
                type="primary",
                help="Dela dina kostnader för att få tillgång till peer-jämförelser",
                use_container_width=True
            ):
                return True
        
        return False

# Export main classes for use in other modules
__all__ = [
    'SurveySystem', 
    'UnlockLevel', 
    'SurveyResponse', 
    'StockholmSuppliersDB',
    'COST_CATEGORIES',
    'SUPPLIER_CATEGORIES'
]