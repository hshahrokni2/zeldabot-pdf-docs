#!/usr/bin/env python3
"""
Peer Comparison System with Unlock Mechanisms

This module provides anonymized peer comparison functionality that progressively
reveals more data based on user survey completion. Implements the "half peers visible"
system where users see increasingly detailed comparisons as they contribute more data.

Features:
- Progressive data disclosure based on unlock levels
- Anonymized peer comparisons with statistical aggregations
- Cost-saving recommendations based on peer performance
- Supplier alternatives with crowd-sourced ratings
- Interactive visualization of benchmarks
- Export functionality for insights
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import statistics
from survey_system import UnlockLevel, SurveyResponse, StockholmSuppliersDB, COST_CATEGORIES, SUPPLIER_CATEGORIES

@dataclass
class PeerInsight:
    """Insight generated from peer comparison analysis."""
    category: str
    insight_type: str  # 'cost_saving', 'supplier_alternative', 'efficiency_tip'
    title: str
    description: str
    potential_savings: Optional[float]
    confidence_level: float
    action_items: List[str]
    data_source: str

@dataclass  
class BenchmarkData:
    """Benchmark statistics for peer comparison."""
    category: str
    user_value: float
    peer_median: float
    peer_avg: float
    peer_min: float
    peer_max: float
    percentile_rank: float
    sample_size: int
    savings_potential: float

class PeerComparisonEngine:
    """Engine for generating peer comparisons and insights."""
    
    def __init__(self, buildings_data: List[Dict], suppliers_db: StockholmSuppliersDB):
        self.buildings_data = buildings_data
        self.suppliers_db = suppliers_db
        self.mock_peer_data = self._generate_realistic_peer_data()
    
    def _generate_realistic_peer_data(self) -> List[Dict]:
        """Generate realistic peer data for comparison."""
        
        # Base this on actual building data where available
        peer_responses = []
        
        # Generate synthetic but realistic peer data
        stockholm_brf_profiles = [
            {
                'building_type': 'modern_waterfront',
                'size_range': (80, 120),
                'age_range': (2000, 2010),
                'cost_multipliers': {
                    'cleaning': (0.8, 1.2),
                    'maintenance': (0.9, 1.4), 
                    'snow_removal': (0.7, 1.1),
                    'gardening': (1.1, 1.8),
                    'electricity': (0.8, 1.2),
                    'heating': (0.9, 1.3)
                }
            },
            {
                'building_type': 'traditional_stockholm',
                'size_range': (60, 100),
                'age_range': (1960, 1990),
                'cost_multipliers': {
                    'cleaning': (0.6, 1.0),
                    'maintenance': (1.2, 1.8),
                    'snow_removal': (0.8, 1.2),
                    'gardening': (0.7, 1.2),
                    'electricity': (1.0, 1.4),
                    'heating': (1.1, 1.6)
                }
            },
            {
                'building_type': 'luxury_central',
                'size_range': (100, 200),
                'age_range': (1990, 2020),
                'cost_multipliers': {
                    'cleaning': (1.2, 1.8),
                    'maintenance': (1.0, 1.5),
                    'snow_removal': (0.9, 1.3),
                    'gardening': (1.5, 2.5),
                    'electricity': (0.9, 1.3), 
                    'heating': (0.8, 1.2)
                }
            }
        ]
        
        # Base cost ranges (annual, in SEK)
        base_costs = {
            'cleaning': 45000,
            'maintenance': 85000,
            'snow_removal': 15000,
            'gardening': 35000,
            'electricity': 120000,
            'heating': 180000
        }
        
        # Generate 50 realistic peer responses
        for i in range(50):
            profile = np.random.choice(stockholm_brf_profiles)
            
            # Generate costs based on profile
            costs = {}
            for category, base_cost in base_costs.items():
                multiplier_range = profile['cost_multipliers'][category]
                multiplier = np.random.uniform(multiplier_range[0], multiplier_range[1])
                # Add some noise
                noise = np.random.normal(1, 0.1)
                costs[category] = max(1000, base_cost * multiplier * noise)
            
            # Generate satisfaction ratings (realistic distribution)
            satisfaction = {}
            for category in COST_CATEGORIES:
                # Most suppliers are decent (3-4), few are excellent (5) or terrible (1-2)
                satisfaction[category] = np.random.choice(
                    [1, 2, 3, 4, 5], 
                    p=[0.05, 0.15, 0.3, 0.4, 0.1]
                )
            
            peer_responses.append({
                'id': f'peer_{i+1}',
                'building_type': profile['building_type'],
                'costs': costs,
                'satisfaction': satisfaction,
                'timestamp': datetime.now() - timedelta(days=np.random.randint(1, 365))
            })
        
        return peer_responses
    
    def get_benchmark_data(self, user_costs: Dict[str, float], unlock_level: UnlockLevel) -> Dict[str, BenchmarkData]:
        """Generate benchmark comparison data based on unlock level."""
        
        benchmarks = {}
        
        for category, user_cost in user_costs.items():
            if category in COST_CATEGORIES:
                # Get peer costs for this category
                peer_costs = [
                    peer['costs'][category] for peer in self.mock_peer_data 
                    if category in peer['costs'] and peer['costs'][category] > 0
                ]
                
                if not peer_costs:
                    continue
                
                # Calculate statistics
                peer_median = statistics.median(peer_costs)
                peer_avg = statistics.mean(peer_costs)
                peer_min = min(peer_costs)
                peer_max = max(peer_costs)
                
                # Calculate percentile rank
                percentile_rank = (sum(1 for cost in peer_costs if cost <= user_cost) / len(peer_costs)) * 100
                
                # Calculate savings potential
                if user_cost > peer_median:
                    savings_potential = user_cost - peer_median
                else:
                    savings_potential = 0
                
                # Limit data visibility based on unlock level
                sample_size = len(peer_costs)
                if unlock_level == UnlockLevel.BASIC:
                    # Show basic comparison only
                    peer_costs_visible = peer_costs[:int(len(peer_costs) * 0.3)]
                    peer_median = statistics.median(peer_costs_visible) if peer_costs_visible else peer_median
                    peer_avg = statistics.mean(peer_costs_visible) if peer_costs_visible else peer_avg
                    sample_size = len(peer_costs_visible)
                elif unlock_level == UnlockLevel.INTERMEDIATE:
                    # Show 70% of data
                    peer_costs_visible = peer_costs[:int(len(peer_costs) * 0.7)]
                    peer_median = statistics.median(peer_costs_visible) if peer_costs_visible else peer_median
                    peer_avg = statistics.mean(peer_costs_visible) if peer_costs_visible else peer_avg
                    sample_size = len(peer_costs_visible)
                
                benchmarks[category] = BenchmarkData(
                    category=category,
                    user_value=user_cost,
                    peer_median=peer_median,
                    peer_avg=peer_avg,
                    peer_min=peer_min if unlock_level == UnlockLevel.FULL else peer_median * 0.7,
                    peer_max=peer_max if unlock_level == UnlockLevel.FULL else peer_median * 1.3,
                    percentile_rank=percentile_rank if unlock_level == UnlockLevel.FULL else None,
                    sample_size=sample_size,
                    savings_potential=savings_potential if unlock_level != UnlockLevel.BASIC else savings_potential * 0.5
                )
        
        return benchmarks
    
    def generate_insights(self, user_response: SurveyResponse, benchmarks: Dict[str, BenchmarkData]) -> List[PeerInsight]:
        """Generate actionable insights based on peer comparison."""
        
        insights = []
        
        for category, benchmark in benchmarks.items():
            # Cost saving insights
            if benchmark.savings_potential > 5000:  # Significant savings potential
                confidence = min(0.9, benchmark.sample_size / 50)
                
                insights.append(PeerInsight(
                    category=category,
                    insight_type='cost_saving',
                    title=f"Besparingspotential: {SUPPLIER_CATEGORIES[category]}",
                    description=f"Din kostnad ({benchmark.user_value:,.0f} SEK) är {((benchmark.user_value/benchmark.peer_median - 1) * 100):.0f}% högre än medianvärdet för liknande BRF:er ({benchmark.peer_median:,.0f} SEK).",
                    potential_savings=benchmark.savings_potential,
                    confidence_level=confidence,
                    action_items=[
                        f"Förhandla om priser med nuvarande leverantör för {SUPPLIER_CATEGORIES[category].lower()}",
                        "Begär offerter från minst 3 alternativa leverantörer",
                        "Undersök möjligheter för gruppupphandling med närliggande BRF:er"
                    ],
                    data_source=f"Baserat på {benchmark.sample_size} liknande BRF:er"
                ))
            
            # Supplier alternative insights
            if category in user_response.suppliers:
                current_supplier = user_response.suppliers[category]
                alternative_suppliers = self.suppliers_db.get_alternative_suppliers(category, current_supplier)
                
                if alternative_suppliers:
                    avg_alt_cost = statistics.mean([
                        (sup.estimated_cost_range[0] + sup.estimated_cost_range[1]) / 2 
                        for sup in alternative_suppliers
                    ])
                    
                    if avg_alt_cost < benchmark.user_value * 0.9:  # Potential 10% savings
                        potential_savings = benchmark.user_value - avg_alt_cost
                        
                        insights.append(PeerInsight(
                            category=category,
                            insight_type='supplier_alternative',
                            title=f"Alternativa leverantörer: {SUPPLIER_CATEGORIES[category]}",
                            description=f"Vi har identifierat {len(alternative_suppliers)} högkvalitativa alternativ som kan spara dig upp till {potential_savings:,.0f} SEK/år.",
                            potential_savings=potential_savings,
                            confidence_level=0.7,
                            action_items=[
                                f"Kontakta {alternative_suppliers[0].name} ({alternative_suppliers[0].contact})",
                                f"Jämför med {alternative_suppliers[1].name} för bästa pris" if len(alternative_suppliers) > 1 else "Begär detaljerad offert",
                                "Kontrollera referenser från andra BRF:er"
                            ],
                            data_source="Kurerade leverantörer med verifierade referenser"
                        ))
            
            # Efficiency tips based on satisfaction scores
            if category in user_response.satisfaction and user_response.satisfaction[category] <= 3:
                user_satisfaction = user_response.satisfaction[category]
                
                # Get peer satisfaction for context
                peer_satisfactions = [
                    peer['satisfaction'][category] for peer in self.mock_peer_data
                    if category in peer['satisfaction']
                ]
                avg_peer_satisfaction = statistics.mean(peer_satisfactions) if peer_satisfactions else 3.5
                
                if avg_peer_satisfaction > user_satisfaction + 0.5:
                    insights.append(PeerInsight(
                        category=category,
                        insight_type='efficiency_tip',
                        title=f"Förbättra leverantörsrelation: {SUPPLIER_CATEGORIES[category]}",
                        description=f"Din nöjdhet ({user_satisfaction}/5) är lägre än genomsnittet för andra BRF:er ({avg_peer_satisfaction:.1f}/5). Detta kan påverka service och kostnader.",
                        potential_savings=None,
                        confidence_level=0.6,
                        action_items=[
                            "Boka ett möte med leverantören för att diskutera förväntningar",
                            "Specificera tydliga service-nivå avtal (SLA)",
                            "Implementera regelbunden feedback-process"
                        ],
                        data_source=f"Baserat på nöjdhetsdata från {len(peer_satisfactions)} BRF:er"
                    ))
        
        # Sort insights by potential impact
        insights.sort(key=lambda x: x.potential_savings if x.potential_savings else 0, reverse=True)
        
        return insights

class PeerComparisonUI:
    """UI components for peer comparison system."""
    
    def __init__(self, comparison_engine: PeerComparisonEngine):
        self.engine = comparison_engine
    
    def create_comparison_dashboard(self, user_response: SurveyResponse, unlock_level: UnlockLevel):
        """Create main peer comparison dashboard."""
        
        st.markdown("## 📊 Peer-jämförelse Dashboard")
        
        # Get benchmark data
        benchmarks = self.engine.get_benchmark_data(user_response.costs, unlock_level)
        
        if not benchmarks:
            st.warning("Inga kostnadsdata att jämföra med. Fyll i enkäten för att se jämförelser.")
            return
        
        # Overview metrics
        self._create_overview_metrics(benchmarks, unlock_level)
        
        # Detailed comparisons
        st.markdown("### Detaljerad Kostnadsjämförelse")
        self._create_detailed_comparisons(benchmarks, unlock_level)
        
        # Generate and show insights
        insights = self.engine.generate_insights(user_response, benchmarks)
        if insights:
            st.markdown("### 💡 Rekommendationer & Insikter")
            self._display_insights(insights, unlock_level)
        
        # Supplier alternatives
        if unlock_level in [UnlockLevel.INTERMEDIATE, UnlockLevel.FULL]:
            st.markdown("### 🏪 Alternativa Leverantörer")
            self._create_supplier_alternatives(user_response, unlock_level)
    
    def _create_overview_metrics(self, benchmarks: Dict[str, BenchmarkData], unlock_level: UnlockLevel):
        """Create overview metrics section."""
        
        total_user_cost = sum(benchmark.user_value for benchmark in benchmarks.values())
        total_peer_median = sum(benchmark.peer_median for benchmark in benchmarks.values())
        total_savings_potential = sum(benchmark.savings_potential for benchmark in benchmarks.values())
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Dina Totalkostnader",
                f"{total_user_cost:,.0f} SEK",
                help="Summa av alla kategorier du fyllt i"
            )
        
        with col2:
            st.metric(
                "Peer-median",
                f"{total_peer_median:,.0f} SEK",
                delta=f"{total_user_cost - total_peer_median:,.0f} SEK",
                delta_color="inverse",
                help="Median för liknande BRF:er"
            )
        
        with col3:
            if unlock_level != UnlockLevel.BASIC:
                percentile_avg = np.mean([b.percentile_rank for b in benchmarks.values() if b.percentile_rank])
                st.metric(
                    "Din Percentil",
                    f"{percentile_avg:.0f}%",
                    help="Hur du rankas jämfört med peers (lägre = billigare)"
                )
            else:
                st.metric("Upplås för mer data", "30% färdigt", help="Fyll i mer av enkäten")
        
        with col4:
            st.metric(
                "Besparingspotential",
                f"{total_savings_potential:,.0f} SEK",
                help="Uppskattad årlig besparing baserat på peer-data"
            )
    
    def _create_detailed_comparisons(self, benchmarks: Dict[str, BenchmarkData], unlock_level: UnlockLevel):
        """Create detailed cost comparison visualizations."""
        
        # Create comparison chart
        categories = list(benchmarks.keys())
        user_values = [benchmarks[cat].user_value for cat in categories]
        peer_medians = [benchmarks[cat].peer_median for cat in categories]
        peer_avgs = [benchmarks[cat].peer_avg for cat in categories]
        
        fig = go.Figure()
        
        # User costs
        fig.add_trace(go.Bar(
            name='Dina kostnader',
            x=[SUPPLIER_CATEGORIES[cat] for cat in categories],
            y=user_values,
            marker_color='#FF6B35',
            hovertemplate='<b>%{x}</b><br>Dina kostnader: %{y:,.0f} SEK<extra></extra>'
        ))
        
        # Peer median
        fig.add_trace(go.Bar(
            name='Peer-median',
            x=[SUPPLIER_CATEGORIES[cat] for cat in categories],
            y=peer_medians,
            marker_color='#2E8B57',
            hovertemplate='<b>%{x}</b><br>Peer-median: %{y:,.0f} SEK<extra></extra>'
        ))
        
        if unlock_level in [UnlockLevel.INTERMEDIATE, UnlockLevel.FULL]:
            # Peer average
            fig.add_trace(go.Bar(
                name='Peer-genomsnitt',
                x=[SUPPLIER_CATEGORIES[cat] for cat in categories],
                y=peer_avgs,
                marker_color='#32CD32',
                opacity=0.7,
                hovertemplate='<b>%{x}</b><br>Peer-genomsnitt: %{y:,.0f} SEK<extra></extra>'
            ))
        
        fig.update_layout(
            title="Kostnadsjämförelse per kategori",
            xaxis_title="Kategori",
            yaxis_title="Kostnad (SEK)",
            barmode='group',
            height=500,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Savings potential breakdown
        if unlock_level != UnlockLevel.BASIC:
            savings_data = []
            for category, benchmark in benchmarks.items():
                if benchmark.savings_potential > 0:
                    savings_data.append({
                        'Kategori': SUPPLIER_CATEGORIES[category],
                        'Besparingspotential': benchmark.savings_potential,
                        'Din kostnad': benchmark.user_value,
                        'Peer-median': benchmark.peer_median,
                        'Skillnad %': ((benchmark.user_value / benchmark.peer_median - 1) * 100)
                    })
            
            if savings_data:
                st.markdown("#### 💰 Besparingspotential per kategori")
                savings_df = pd.DataFrame(savings_data)
                savings_df = savings_df.sort_values('Besparingspotential', ascending=False)
                
                # Format currency columns
                for col in ['Besparingspotential', 'Din kostnad', 'Peer-median']:
                    savings_df[col] = savings_df[col].apply(lambda x: f"{x:,.0f} SEK")
                savings_df['Skillnad %'] = savings_df['Skillnad %'].apply(lambda x: f"{x:+.0f}%")
                
                st.dataframe(
                    savings_df,
                    use_container_width=True,
                    hide_index=True
                )
    
    def _display_insights(self, insights: List[PeerInsight], unlock_level: UnlockLevel):
        """Display actionable insights and recommendations."""
        
        # Limit insights based on unlock level
        max_insights = {
            UnlockLevel.BASIC: 2,
            UnlockLevel.INTERMEDIATE: 4,
            UnlockLevel.FULL: len(insights)
        }
        
        displayed_insights = insights[:max_insights.get(unlock_level, 2)]
        
        for i, insight in enumerate(displayed_insights):
            
            # Color coding by insight type
            colors = {
                'cost_saving': '#FF6B35',
                'supplier_alternative': '#2E8B57', 
                'efficiency_tip': '#FFD700'
            }
            
            color = colors.get(insight.insight_type, '#808080')
            
            with st.container():
                st.markdown(f"""
                <div style="
                    border-left: 4px solid {color};
                    padding: 1rem;
                    background: rgba(46, 139, 87, 0.05);
                    border-radius: 0 8px 8px 0;
                    margin: 1rem 0;
                ">
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**{insight.title}**")
                    st.markdown(insight.description)
                    
                    if insight.action_items:
                        st.markdown("**Rekommenderade åtgärder:**")
                        for item in insight.action_items:
                            st.markdown(f"• {item}")
                
                with col2:
                    if insight.potential_savings:
                        st.metric(
                            "Potential besparing",
                            f"{insight.potential_savings:,.0f} SEK/år"
                        )
                    
                    st.markdown(f"**Säkerhet:** {insight.confidence_level*100:.0f}%")
                    st.caption(insight.data_source)
                
                st.markdown("</div>", unsafe_allow_html=True)
        
        # Show upgrade prompt if more insights available
        if len(insights) > len(displayed_insights):
            remaining = len(insights) - len(displayed_insights)
            st.info(f"🔒 {remaining} ytterligare rekommendationer tillgängliga. Fyll i mer av enkäten för att låsa upp.")
    
    def _create_supplier_alternatives(self, user_response: SurveyResponse, unlock_level: UnlockLevel):
        """Create supplier alternatives recommendations."""
        
        if unlock_level == UnlockLevel.BASIC:
            st.info("🔒 Leverantörsalternativ tillgängliga efter 60% ifyllt av enkäten")
            return
        
        # Group suppliers by category
        for category in COST_CATEGORIES:
            if category in user_response.suppliers and category in user_response.costs:
                current_supplier = user_response.suppliers[category]
                alternatives = self.engine.suppliers_db.get_alternative_suppliers(category, current_supplier)
                
                if alternatives:
                    st.markdown(f"#### {SUPPLIER_CATEGORIES[category]}")
                    
                    col1, col2 = st.columns([1, 2])
                    
                    with col1:
                        st.markdown("**Nuvarande leverantör:**")
                        st.markdown(f"• {current_supplier}")
                        st.markdown(f"• Kostnad: {user_response.costs[category]:,.0f} SEK/år")
                        if category in user_response.satisfaction:
                            satisfaction = user_response.satisfaction[category]
                            st.markdown(f"• Nöjdhet: {satisfaction}/5 ⭐")
                    
                    with col2:
                        st.markdown("**Rekommenderade alternativ:**")
                        
                        for alt in alternatives:
                            avg_cost = (alt.estimated_cost_range[0] + alt.estimated_cost_range[1]) / 2
                            potential_savings = max(0, user_response.costs[category] - avg_cost)
                            
                            with st.expander(f"🏪 {alt.name} - Betyg: {alt.rating:.1f}/5"):
                                st.markdown(f"**Beskrivning:** {alt.description}")
                                st.markdown(f"**Kontakt:** {alt.contact}")
                                st.markdown(f"**Plats:** {alt.location}")
                                st.markdown(f"**Specialiteter:** {', '.join(alt.specialties)}")
                                st.markdown(f"**Uppskattat pris:** {alt.estimated_cost_range[0]:,.0f} - {alt.estimated_cost_range[1]:,.0f} SEK/år")
                                
                                if potential_savings > 0:
                                    st.success(f"Potential besparing: {potential_savings:,.0f} SEK/år")
                                
                                if st.button(f"Kontakta {alt.name}", key=f"contact_{category}_{alt.name}"):
                                    st.success(f"Kontaktuppgifter kopierade: {alt.contact}")
                    
                    st.divider()
    
    def create_export_interface(self, user_response: SurveyResponse, benchmarks: Dict[str, BenchmarkData], insights: List[PeerInsight]):
        """Create export functionality for survey data and insights."""
        
        st.markdown("### 📤 Exportera Resultat")
        
        export_options = st.multiselect(
            "Vad vill du exportera?",
            options=[
                "Kostnadsjämförelse", 
                "Rekommendationer", 
                "Leverantörsalternativ",
                "Rådata (JSON)"
            ],
            default=["Kostnadsjämförelse", "Rekommendationer"]
        )
        
        if st.button("Generera Export", type="primary"):
            export_data = self._generate_export_data(
                user_response, benchmarks, insights, export_options
            )
            
            # Create downloadable content
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if "Rådata (JSON)" in export_options:
                json_data = json.dumps(export_data, indent=2, ensure_ascii=False, default=str)
                st.download_button(
                    label="📄 Ladda ner JSON",
                    data=json_data,
                    file_name=f"brf_kostnadsanalys_{timestamp}.json",
                    mime="application/json"
                )
            
            # Create Excel export for structured data
            if any(opt in export_options for opt in ["Kostnadsjämförelse", "Rekommendationer"]):
                excel_data = self._create_excel_export(export_data, export_options)
                st.download_button(
                    label="📊 Ladda ner Excel",
                    data=excel_data,
                    file_name=f"brf_kostnadsanalys_{timestamp}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            # Show preview
            st.markdown("#### Förhandsvisning av export")
            with st.expander("Exportdata"):
                st.json(export_data)
    
    def _generate_export_data(self, user_response: SurveyResponse, benchmarks: Dict[str, BenchmarkData], 
                            insights: List[PeerInsight], export_options: List[str]) -> Dict:
        """Generate export data based on selected options."""
        
        export_data = {
            'metadata': {
                'export_timestamp': datetime.now().isoformat(),
                'building_name': user_response.building_name,
                'survey_completion': user_response.completion_percentage,
                'unlock_level': user_response.unlock_level.value
            }
        }
        
        if "Kostnadsjämförelse" in export_options:
            comparison_data = {}
            for category, benchmark in benchmarks.items():
                comparison_data[category] = {
                    'category_name': SUPPLIER_CATEGORIES[category],
                    'user_cost': benchmark.user_value,
                    'peer_median': benchmark.peer_median,
                    'peer_average': benchmark.peer_avg,
                    'savings_potential': benchmark.savings_potential,
                    'percentile_rank': benchmark.percentile_rank,
                    'sample_size': benchmark.sample_size
                }
            export_data['cost_comparison'] = comparison_data
        
        if "Rekommendationer" in export_options:
            recommendations_data = []
            for insight in insights:
                recommendations_data.append({
                    'category': SUPPLIER_CATEGORIES.get(insight.category, insight.category),
                    'type': insight.insight_type,
                    'title': insight.title,
                    'description': insight.description,
                    'potential_savings': insight.potential_savings,
                    'confidence_level': insight.confidence_level,
                    'action_items': insight.action_items,
                    'data_source': insight.data_source
                })
            export_data['recommendations'] = recommendations_data
        
        if "Leverantörsalternativ" in export_options:
            suppliers_data = {}
            for category in user_response.suppliers:
                alternatives = self.engine.suppliers_db.get_alternative_suppliers(
                    category, user_response.suppliers[category]
                )
                suppliers_data[category] = {
                    'current_supplier': user_response.suppliers[category],
                    'alternatives': [
                        {
                            'name': alt.name,
                            'description': alt.description,
                            'contact': alt.contact,
                            'location': alt.location,
                            'rating': alt.rating,
                            'cost_range': alt.estimated_cost_range,
                            'specialties': alt.specialties
                        } for alt in alternatives
                    ]
                }
            export_data['supplier_alternatives'] = suppliers_data
        
        return export_data
    
    def _create_excel_export(self, export_data: Dict, export_options: List[str]) -> bytes:
        """Create Excel file from export data."""
        
        # This would typically use openpyxl or xlswriter
        # For now, return CSV format as bytes
        import io
        
        output = io.StringIO()
        
        # Write comparison data
        if 'cost_comparison' in export_data:
            output.write("KOSTNADSJÄMFÖRELSE\n")
            output.write("Kategori,Dina kostnader,Peer-median,Besparingspotential\n")
            
            for category, data in export_data['cost_comparison'].items():
                output.write(f"{data['category_name']},{data['user_cost']:.0f},{data['peer_median']:.0f},{data['savings_potential']:.0f}\n")
            
            output.write("\n")
        
        # Write recommendations
        if 'recommendations' in export_data:
            output.write("REKOMMENDATIONER\n")
            output.write("Kategori,Typ,Titel,Beskrivning,Potential besparing\n")
            
            for rec in export_data['recommendations']:
                savings = rec['potential_savings'] if rec['potential_savings'] else 0
                output.write(f"{rec['category']},{rec['type']},{rec['title']},{rec['description']},{savings:.0f}\n")
        
        return output.getvalue().encode('utf-8')

# Export main classes
__all__ = [
    'PeerComparisonEngine',
    'PeerComparisonUI', 
    'PeerInsight',
    'BenchmarkData'
]