#!/usr/bin/env python3
"""
Comprehensive BRF Cost Analysis and Performance Metrics System
=============================================================

This system provides:
1. Cost normalization and analysis across all BRFs
2. Building size estimation from apartment counts and BRF characteristics
3. BRF Financial Performance Index calculation
4. Market benchmarking and percentile rankings
5. Personalized analysis for BRF Sjöstaden 2
6. Enhanced visualizations and data export

Author: Claudette-Analyst
Date: 2025-08-13
"""

import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from typing import Dict, List, Tuple, Any
import warnings
warnings.filterwarnings('ignore')

# Set plotting style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class BRFAnalyzer:
    """Comprehensive BRF analysis and benchmarking system."""
    
    def __init__(self, data_path: str):
        """Initialize the analyzer with BRF data."""
        self.data_path = data_path
        self.load_data()
        self.estimate_building_sizes()
        self.normalize_costs()
        self.calculate_performance_indices()
        
    def load_data(self):
        """Load and prepare the BRF dataset."""
        with open(self.data_path, 'r', encoding='utf-8') as f:
            self.raw_data = json.load(f)
            
        # Convert to DataFrame for easier analysis
        self.df = pd.DataFrame(self.raw_data)
        
        # Cost columns for analysis
        self.cost_columns = [
            'cost_cleaning', 'cost_electricity', 'cost_heating',
            'cost_internet_and_tv', 'cost_recycling', 'cost_snow_removal',
            'cost_water', 'total_cost'
        ]
        
        print(f"Loaded data for {len(self.df)} BRFs")
        print(f"BRFs: {', '.join(self.df['brf_name'].tolist())}")
        
    def estimate_building_sizes(self):
        """Estimate building sizes in m² using multiple methods."""
        print("\n=== ESTIMATING BUILDING SIZES ===")
        
        # Method 1: Base apartment size by construction year and BRF type
        def get_base_apartment_size(year: int, brf_name: str) -> float:
            """Estimate base apartment size based on year and location characteristics."""
            # Stockholm waterfront premium apartments (larger)
            if any(keyword in brf_name.lower() for keyword in ['sjöstaden', 'hammarby', 'sickla']):
                if year >= 2010:
                    return 75.0  # Modern waterfront
                elif year >= 2000:
                    return 70.0  # Early 2000s waterfront
                else:
                    return 65.0  # Older waterfront
            else:
                # More standard locations
                if year >= 2010:
                    return 65.0
                elif year >= 2000:
                    return 60.0
                else:
                    return 55.0
        
        # Method 2: Estimate apartments from property count and house numbers
        def estimate_apartments(row) -> int:
            """Estimate number of apartments from EPC properties."""
            total_apartments = 0
            
            for prop in row['epc_properties']:
                house_numbers = prop['house_numbers']
                
                # Parse house numbers string like "{1,2,3}" or "{1}"
                if isinstance(house_numbers, str):
                    # Clean and count numbers
                    numbers_str = house_numbers.strip('{}')
                    if ',' in numbers_str:
                        numbers = numbers_str.split(',')
                    else:
                        numbers = [numbers_str]
                    
                    # Estimate apartments per house number
                    valid_numbers = [n.strip() for n in numbers if n.strip().isdigit()]
                    
                    # For waterfront BRFs, assume more apartments per building
                    if any(keyword in row['brf_name'].lower() for keyword in ['sjöstaden', 'hammarby']):
                        apartments_per_house = 25  # High-rise waterfront
                    else:
                        apartments_per_house = 15  # Mid-rise
                    
                    total_apartments += len(valid_numbers) * apartments_per_house
            
            # Minimum apartments based on costs (higher costs suggest more apartments)
            cost_based_minimum = max(10, int(row['total_cost'] / 100000))  # 100k SEK per apartment
            
            return max(total_apartments, cost_based_minimum)
        
        # Calculate estimated apartments and building sizes
        self.df['estimated_apartments'] = self.df.apply(estimate_apartments, axis=1)
        self.df['base_apartment_size'] = self.df.apply(
            lambda x: get_base_apartment_size(x['construction_year'], x['brf_name']), axis=1
        )
        
        # Calculate total building area
        self.df['estimated_building_size_m2'] = (
            self.df['estimated_apartments'] * self.df['base_apartment_size']
        )
        
        # Display results
        size_summary = self.df[['brf_name', 'construction_year', 'estimated_apartments', 
                               'base_apartment_size', 'estimated_building_size_m2']].copy()
        
        print("\nBuilding Size Estimates:")
        print("=" * 80)
        for _, row in size_summary.iterrows():
            print(f"{row['brf_name']:<30} | {row['construction_year']} | "
                  f"{row['estimated_apartments']:>3} apts | {row['base_apartment_size']:>4.0f} m²/apt | "
                  f"{row['estimated_building_size_m2']:>6,.0f} m² total")
        
        print(f"\nTotal estimated building area: {self.df['estimated_building_size_m2'].sum():,.0f} m²")
        
    def normalize_costs(self):
        """Normalize all costs to SEK/m² for fair comparison."""
        print("\n=== NORMALIZING COSTS TO SEK/m² ===")
        
        # Calculate normalized costs per m²
        for cost_col in self.cost_columns:
            normalized_col = f"{cost_col}_per_m2"
            self.df[normalized_col] = self.df[cost_col] / self.df['estimated_building_size_m2']
        
        # Create comprehensive cost breakdown
        self.cost_breakdown = []
        
        for _, row in self.df.iterrows():
            breakdown = {
                'brf_name': row['brf_name'],
                'building_id': row['building_id'],
                'estimated_building_size_m2': row['estimated_building_size_m2'],
                'energy_performance': row['energy_performance'],
                'energy_class': row['energy_class'],
                'construction_year': row['construction_year']
            }
            
            # Add all cost categories (including zeros)
            cost_categories = {
                'Cleaning': row['cost_cleaning'],
                'Electricity': row['cost_electricity'],
                'Heating': row['cost_heating'],
                'Internet & TV': row['cost_internet_and_tv'],
                'Recycling': row['cost_recycling'],
                'Snow Removal': row['cost_snow_removal'],
                'Water': row['cost_water']
            }
            
            total_cost = sum(cost_categories.values())
            
            # Add absolute costs
            for category, cost in cost_categories.items():
                breakdown[f'{category}_SEK'] = cost
            breakdown['Total_SEK'] = total_cost
            
            # Add normalized costs per m²
            for category, cost in cost_categories.items():
                breakdown[f'{category}_per_m2'] = cost / row['estimated_building_size_m2']
            breakdown['Total_per_m2'] = total_cost / row['estimated_building_size_m2']
            
            self.cost_breakdown.append(breakdown)
        
        self.cost_breakdown_df = pd.DataFrame(self.cost_breakdown)
        
        # Calculate market averages
        self.market_averages = {}
        cost_categories = ['Cleaning', 'Electricity', 'Heating', 'Internet & TV', 
                          'Recycling', 'Snow Removal', 'Water', 'Total']
        
        for category in cost_categories:
            per_m2_col = f'{category}_per_m2'
            self.market_averages[category] = {
                'mean_per_m2': self.cost_breakdown_df[per_m2_col].mean(),
                'median_per_m2': self.cost_breakdown_df[per_m2_col].median(),
                'std_per_m2': self.cost_breakdown_df[per_m2_col].std(),
                'min_per_m2': self.cost_breakdown_df[per_m2_col].min(),
                'max_per_m2': self.cost_breakdown_df[per_m2_col].max()
            }
        
        print("Market Averages (SEK/m²):")
        print("=" * 60)
        for category, stats in self.market_averages.items():
            print(f"{category:<15} | Mean: {stats['mean_per_m2']:>6.0f} | "
                  f"Median: {stats['median_per_m2']:>6.0f} | Range: {stats['min_per_m2']:>4.0f}-{stats['max_per_m2']:>4.0f}")
    
    def calculate_performance_indices(self):
        """Calculate BRF Financial Performance Index."""
        print("\n=== CALCULATING PERFORMANCE INDICES ===")
        
        # Energy Efficiency Score (30% weight)
        # Formula: 100 - (energy_performance/159 × 100)
        # 159 is approximate worst case in Swedish building stock
        max_energy_performance = 159
        self.df['energy_efficiency_score'] = np.maximum(0, 100 - (self.df['energy_performance'] / max_energy_performance * 100))
        
        # Cost Efficiency Score (70% weight)  
        # Formula: 100 - (total_cost_per_m2/market_avg × 100)
        market_avg_cost_per_m2 = self.market_averages['Total']['mean_per_m2']
        self.df['cost_efficiency_score'] = np.maximum(0, 100 - (self.df['total_cost_per_m2'] / market_avg_cost_per_m2 * 100))
        
        # Combined Performance Index
        self.df['financial_performance_index'] = (
            0.3 * self.df['energy_efficiency_score'] + 
            0.7 * self.df['cost_efficiency_score']
        )
        
        # Calculate percentile rankings
        self.df['performance_percentile'] = self.df['financial_performance_index'].rank(pct=True) * 100
        self.df['energy_percentile'] = self.df['energy_efficiency_score'].rank(pct=True) * 100
        self.df['cost_percentile'] = self.df['cost_efficiency_score'].rank(pct=True) * 100
        
        # Sort by performance index
        performance_ranking = self.df.sort_values('financial_performance_index', ascending=False)
        
        print("BRF Performance Rankings:")
        print("=" * 100)
        print(f"{'Rank':<4} | {'BRF Name':<25} | {'Performance':<11} | {'Energy':<9} | {'Cost':<9} | {'Percentile':<10}")
        print("-" * 100)
        
        for i, (_, row) in enumerate(performance_ranking.iterrows(), 1):
            print(f"{i:<4} | {row['brf_name']:<25} | "
                  f"{row['financial_performance_index']:>8.1f}   | "
                  f"{row['energy_efficiency_score']:>6.1f}  | "
                  f"{row['cost_efficiency_score']:>6.1f}  | "
                  f"{row['performance_percentile']:>7.0f}%")
    
    def analyze_sjostaden_2(self):
        """Perform personalized analysis for BRF Sjöstaden 2."""
        print("\n=== PERSONALIZED ANALYSIS: BRF SJÖSTADEN 2 ===")
        
        # Find Sjöstaden 2
        sjostaden_2 = self.df[self.df['brf_name'] == 'Brf Sjöstaden 2'].iloc[0]
        sjostaden_breakdown = self.cost_breakdown_df[
            self.cost_breakdown_df['brf_name'] == 'Brf Sjöstaden 2'
        ].iloc[0]
        
        print(f"\nBRF: {sjostaden_2['brf_name']}")
        print(f"Building Size: {sjostaden_2['estimated_building_size_m2']:,.0f} m²")
        print(f"Energy Performance: {sjostaden_2['energy_performance']:.0f} kWh/m²/år (Class {sjostaden_2['energy_class']})")
        print(f"Construction Year: {sjostaden_2['construction_year']}")
        
        print(f"\nPerformance Scores:")
        print(f"Financial Performance Index: {sjostaden_2['financial_performance_index']:.1f} (Top {100-sjostaden_2['performance_percentile']:.0f}%)")
        print(f"Energy Efficiency Score: {sjostaden_2['energy_efficiency_score']:.1f} (Top {100-sjostaden_2['energy_percentile']:.0f}%)")
        print(f"Cost Efficiency Score: {sjostaden_2['cost_efficiency_score']:.1f} (Top {100-sjostaden_2['cost_percentile']:.0f}%)")
        
        # Compare against top 25% performers
        top_25_percent = self.cost_breakdown_df[
            self.cost_breakdown_df['brf_name'].isin(
                self.df[self.df['performance_percentile'] >= 75]['brf_name']
            )
        ]
        
        print(f"\nComparison vs Top 25% Performers:")
        print("=" * 50)
        
        cost_categories = ['Electricity', 'Heating', 'Water', 'Internet & TV', 'Recycling', 'Total']
        
        savings_opportunities = []
        
        for category in cost_categories:
            per_m2_col = f'{category}_per_m2'
            sjostaden_cost = sjostaden_breakdown[per_m2_col]
            top_25_avg = top_25_percent[per_m2_col].mean()
            
            difference = sjostaden_cost - top_25_avg
            difference_pct = (difference / sjostaden_cost * 100) if sjostaden_cost > 0 else 0
            
            print(f"{category:<15} | Sjöstaden 2: {sjostaden_cost:>6.0f} SEK/m² | "
                  f"Top 25%: {top_25_avg:>6.0f} SEK/m² | "
                  f"Diff: {difference:>+5.0f} SEK/m² ({difference_pct:>+4.0f}%)")
            
            if difference > 50:  # Significant savings opportunity
                annual_savings = difference * sjostaden_2['estimated_building_size_m2']
                savings_opportunities.append({
                    'category': category,
                    'current_cost_per_m2': sjostaden_cost,
                    'benchmark_cost_per_m2': top_25_avg,
                    'annual_savings_sek': annual_savings,
                    'savings_percentage': difference_pct
                })
        
        if savings_opportunities:
            print(f"\nIdentified Savings Opportunities:")
            print("=" * 60)
            total_potential_savings = 0
            
            for opp in savings_opportunities:
                print(f"{opp['category']:<15} | Potential savings: {opp['annual_savings_sek']:>8,.0f} SEK/year "
                      f"({opp['savings_percentage']:>4.0f}% reduction)")
                total_potential_savings += opp['annual_savings_sek']
            
            print(f"\nTotal Potential Annual Savings: {total_potential_savings:,.0f} SEK")
            print(f"Monthly Fee Impact: {total_potential_savings/12:,.0f} SEK/month")
        
        # Identify strengths
        print(f"\nStrengths:")
        print("=" * 30)
        
        strengths = []
        for category in cost_categories:
            per_m2_col = f'{category}_per_m2'
            sjostaden_cost = sjostaden_breakdown[per_m2_col]
            market_avg = self.market_averages[category]['mean_per_m2']
            
            if sjostaden_cost < market_avg * 0.8:  # 20% below market average
                difference_pct = (market_avg - sjostaden_cost) / market_avg * 100
                strengths.append(f"• {category}: {difference_pct:.0f}% below market average")
        
        if sjostaden_2['energy_efficiency_score'] > 80:
            strengths.append(f"• Excellent energy efficiency (Class {sjostaden_2['energy_class']})")
        
        if strengths:
            for strength in strengths:
                print(strength)
        else:
            print("• High overall performance ranking")
        
        return {
            'brf_data': sjostaden_2.to_dict(),
            'cost_breakdown': sjostaden_breakdown.to_dict(),
            'savings_opportunities': savings_opportunities,
            'strengths': strengths
        }
    
    def generate_market_benchmarking(self):
        """Generate comprehensive market benchmarking data."""
        print("\n=== MARKET BENCHMARKING ANALYSIS ===")
        
        # Best performers by category
        best_performers = {}
        cost_categories = ['Electricity', 'Heating', 'Water', 'Internet & TV', 'Recycling', 'Total']
        
        for category in cost_categories:
            per_m2_col = f'{category}_per_m2'
            best_idx = self.cost_breakdown_df[per_m2_col].idxmin()
            best_performer = self.cost_breakdown_df.iloc[best_idx]
            
            best_performers[category] = {
                'brf_name': best_performer['brf_name'],
                'cost_per_m2': best_performer[per_m2_col],
                'energy_class': best_performer['energy_class'],
                'construction_year': best_performer['construction_year']
            }
        
        print("Best Performers by Category:")
        print("=" * 70)
        for category, data in best_performers.items():
            print(f"{category:<15} | {data['brf_name']:<20} | "
                  f"{data['cost_per_m2']:>6.0f} SEK/m² | "
                  f"Class {data['energy_class']} ({data['construction_year']})")
        
        # Generate percentile data for survey system
        percentile_data = {}
        for category in cost_categories:
            per_m2_col = f'{category}_per_m2'
            costs = self.cost_breakdown_df[per_m2_col]
            
            percentile_data[category] = {
                'p10': costs.quantile(0.1),
                'p25': costs.quantile(0.25),
                'p50': costs.quantile(0.5),
                'p75': costs.quantile(0.75),
                'p90': costs.quantile(0.9),
                'mean': costs.mean(),
                'std': costs.std()
            }
        
        return {
            'best_performers': best_performers,
            'percentile_data': percentile_data,
            'market_averages': self.market_averages
        }
    
    def create_visualizations(self):
        """Create comprehensive visualizations."""
        print("\n=== CREATING VISUALIZATIONS ===")
        
        # Set up the plotting environment
        plt.rcParams['figure.figsize'] = (15, 10)
        fig = plt.figure(figsize=(20, 24))
        
        # 1. Cost Breakdown by BRF (Stacked Bar Chart)
        ax1 = plt.subplot(4, 2, 1)
        cost_categories = ['Electricity_per_m2', 'Heating_per_m2', 'Water_per_m2', 
                          'Internet & TV_per_m2', 'Recycling_per_m2', 'Snow Removal_per_m2']
        
        # Prepare data for stacked bar chart
        plot_data = []
        labels = []
        
        for _, row in self.cost_breakdown_df.iterrows():
            plot_data.append([row[cat] for cat in cost_categories])
            labels.append(row['brf_name'].replace('Brf ', ''))
        
        plot_data = np.array(plot_data).T
        
        # Create stacked bar chart
        bottom = np.zeros(len(labels))
        colors = plt.cm.Set3(np.linspace(0, 1, len(cost_categories)))
        
        for i, (category, color) in enumerate(zip(cost_categories, colors)):
            category_name = category.replace('_per_m2', '').replace('_', ' & ')
            ax1.bar(labels, plot_data[i], bottom=bottom, label=category_name, color=color)
            bottom += plot_data[i]
        
        ax1.set_title('Annual Costs by Category (SEK/m²)', fontsize=14, fontweight='bold')
        ax1.set_xlabel('BRF')
        ax1.set_ylabel('Cost (SEK/m²)')
        ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.setp(ax1.get_xticklabels(), rotation=45, ha='right')
        
        # 2. Performance Index Scatter Plot
        ax2 = plt.subplot(4, 2, 2)
        scatter = ax2.scatter(self.df['energy_efficiency_score'], 
                             self.df['cost_efficiency_score'],
                             s=200, c=self.df['financial_performance_index'], 
                             cmap='RdYlGn', alpha=0.7)
        
        # Add BRF names as labels
        for _, row in self.df.iterrows():
            ax2.annotate(row['brf_name'].replace('Brf ', ''), 
                        (row['energy_efficiency_score'], row['cost_efficiency_score']),
                        xytext=(5, 5), textcoords='offset points', fontsize=8)
        
        ax2.set_xlabel('Energy Efficiency Score')
        ax2.set_ylabel('Cost Efficiency Score')
        ax2.set_title('BRF Performance Matrix', fontsize=14, fontweight='bold')
        plt.colorbar(scatter, ax=ax2, label='Financial Performance Index')
        
        # 3. Energy Performance vs Total Cost
        ax3 = plt.subplot(4, 2, 3)
        ax3.scatter(self.df['energy_performance'], self.df['total_cost_per_m2'], 
                   s=150, alpha=0.7, c='steelblue')
        
        for _, row in self.df.iterrows():
            ax3.annotate(row['brf_name'].replace('Brf ', ''), 
                        (row['energy_performance'], row['total_cost_per_m2']),
                        xytext=(5, 5), textcoords='offset points', fontsize=8)
        
        ax3.set_xlabel('Energy Performance (kWh/m²/år)')
        ax3.set_ylabel('Total Cost (SEK/m²)')
        ax3.set_title('Energy Performance vs Annual Costs', fontsize=14, fontweight='bold')
        
        # 4. Cost Category Comparison (Box Plot)
        ax4 = plt.subplot(4, 2, 4)
        cost_categories_plot = ['Electricity_per_m2', 'Heating_per_m2', 'Water_per_m2']
        
        box_data = []
        box_labels = []
        
        for category in cost_categories_plot:
            box_data.append(self.cost_breakdown_df[category])
            box_labels.append(category.replace('_per_m2', '').replace('_', ' '))
        
        ax4.boxplot(box_data, labels=box_labels)
        ax4.set_title('Cost Distribution by Major Categories', fontsize=14, fontweight='bold')
        ax4.set_ylabel('Cost (SEK/m²)')
        
        # 5. BRF Rankings Bar Chart
        ax5 = plt.subplot(4, 2, 5)
        ranking_data = self.df.sort_values('financial_performance_index', ascending=True)
        
        bars = ax5.barh(range(len(ranking_data)), ranking_data['financial_performance_index'])
        ax5.set_yticks(range(len(ranking_data)))
        ax5.set_yticklabels([name.replace('Brf ', '') for name in ranking_data['brf_name']])
        ax5.set_xlabel('Financial Performance Index')
        ax5.set_title('BRF Performance Rankings', fontsize=14, fontweight='bold')
        
        # Color bars based on performance
        for i, bar in enumerate(bars):
            if ranking_data.iloc[i]['financial_performance_index'] >= 60:
                bar.set_color('green')
            elif ranking_data.iloc[i]['financial_performance_index'] >= 40:
                bar.set_color('orange')
            else:
                bar.set_color('red')
        
        # 6. Savings Opportunity Analysis for Sjöstaden 2
        ax6 = plt.subplot(4, 2, 6)
        sjostaden_analysis = self.analyze_sjostaden_2()
        
        if sjostaden_analysis['savings_opportunities']:
            categories = [opp['category'] for opp in sjostaden_analysis['savings_opportunities']]
            savings = [opp['annual_savings_sek'] for opp in sjostaden_analysis['savings_opportunities']]
            
            bars = ax6.bar(categories, savings, color='lightcoral')
            ax6.set_title('Savings Opportunities - BRF Sjöstaden 2', fontsize=14, fontweight='bold')
            ax6.set_ylabel('Potential Annual Savings (SEK)')
            plt.setp(ax6.get_xticklabels(), rotation=45, ha='right')
            
            # Add value labels on bars
            for bar, saving in zip(bars, savings):
                ax6.text(bar.get_x() + bar.get_width()/2, bar.get_height() + saving*0.01,
                        f'{saving:,.0f}', ha='center', va='bottom', fontsize=9)
        else:
            ax6.text(0.5, 0.5, 'No significant savings\nopportunities identified', 
                    transform=ax6.transAxes, ha='center', va='center', fontsize=12)
            ax6.set_title('Savings Opportunities - BRF Sjöstaden 2', fontsize=14, fontweight='bold')
        
        # 7. Energy Class Distribution
        ax7 = plt.subplot(4, 2, 7)
        energy_class_counts = self.df['energy_class'].value_counts()
        wedges, texts, autotexts = ax7.pie(energy_class_counts.values, 
                                          labels=energy_class_counts.index,
                                          autopct='%1.0f%%', startangle=90)
        ax7.set_title('Energy Class Distribution', fontsize=14, fontweight='bold')
        
        # 8. Cost vs Building Age
        ax8 = plt.subplot(4, 2, 8)
        ax8.scatter(self.df['construction_year'], self.df['total_cost_per_m2'], 
                   s=150, alpha=0.7, c='purple')
        
        for _, row in self.df.iterrows():
            ax8.annotate(row['brf_name'].replace('Brf ', ''), 
                        (row['construction_year'], row['total_cost_per_m2']),
                        xytext=(5, 5), textcoords='offset points', fontsize=8)
        
        ax8.set_xlabel('Construction Year')
        ax8.set_ylabel('Total Cost (SEK/m²)')
        ax8.set_title('Building Age vs Annual Costs', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig('/Users/hosseins/Dropbox/Zelda/ZeldaDemo/brf_comprehensive_analysis.png', 
                   dpi=300, bbox_inches='tight')
        plt.show()
        
        print("Visualizations saved to: /Users/hosseins/Dropbox/Zelda/ZeldaDemo/brf_comprehensive_analysis.png")
    
    def export_analysis_data(self):
        """Export comprehensive analysis data for dashboard integration."""
        print("\n=== EXPORTING ANALYSIS DATA ===")
        
        # Prepare comprehensive export data
        export_data = {
            'metadata': {
                'analysis_date': datetime.now().isoformat(),
                'total_brfs': len(self.df),
                'total_building_area_m2': self.df['estimated_building_size_m2'].sum(),
                'analyst': 'Claudette-Analyst'
            },
            'brf_summary': [],
            'market_benchmarks': self.generate_market_benchmarking(),
            'cost_categories': ['Cleaning', 'Electricity', 'Heating', 'Internet & TV', 
                              'Recycling', 'Snow Removal', 'Water'],
            'sjostaden_2_analysis': self.analyze_sjostaden_2()
        }
        
        # Add detailed BRF data
        for _, row in self.df.iterrows():
            brf_data = {
                'brf_name': row['brf_name'],
                'building_id': row['building_id'],
                'construction_year': row['construction_year'],
                'energy_performance': row['energy_performance'],
                'energy_class': row['energy_class'],
                'estimated_building_size_m2': row['estimated_building_size_m2'],
                'estimated_apartments': row['estimated_apartments'],
                'financial_performance_index': row['financial_performance_index'],
                'performance_percentile': row['performance_percentile'],
                'energy_efficiency_score': row['energy_efficiency_score'],
                'cost_efficiency_score': row['cost_efficiency_score']
            }
            
            # Add cost data
            cost_breakdown = self.cost_breakdown_df[
                self.cost_breakdown_df['brf_name'] == row['brf_name']
            ].iloc[0]
            
            brf_data['costs'] = {
                'cleaning_per_m2': cost_breakdown['Cleaning_per_m2'],
                'electricity_per_m2': cost_breakdown['Electricity_per_m2'],
                'heating_per_m2': cost_breakdown['Heating_per_m2'],
                'internet_tv_per_m2': cost_breakdown['Internet & TV_per_m2'],
                'recycling_per_m2': cost_breakdown['Recycling_per_m2'],
                'snow_removal_per_m2': cost_breakdown['Snow Removal_per_m2'],
                'water_per_m2': cost_breakdown['Water_per_m2'],
                'total_per_m2': cost_breakdown['Total_per_m2']
            }
            
            export_data['brf_summary'].append(brf_data)
        
        # Export to JSON
        output_path = '/Users/hosseins/Dropbox/Zelda/ZeldaDemo/brf_comprehensive_analysis.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        # Export cost breakdown to CSV for easy analysis
        csv_path = '/Users/hosseins/Dropbox/Zelda/ZeldaDemo/brf_cost_breakdown.csv'
        self.cost_breakdown_df.to_csv(csv_path, index=False)
        
        # Export performance summary to CSV
        performance_summary = self.df[[
            'brf_name', 'construction_year', 'energy_performance', 'energy_class',
            'estimated_building_size_m2', 'financial_performance_index',
            'performance_percentile', 'energy_efficiency_score', 'cost_efficiency_score'
        ]].copy()
        
        performance_csv_path = '/Users/hosseins/Dropbox/Zelda/ZeldaDemo/brf_performance_summary.csv'
        performance_summary.to_csv(performance_csv_path, index=False)
        
        print(f"Analysis data exported to:")
        print(f"• JSON: {output_path}")
        print(f"• Cost CSV: {csv_path}")
        print(f"• Performance CSV: {performance_csv_path}")
        
        return export_data
    
    def generate_executive_summary(self):
        """Generate executive summary of findings."""
        print("\n" + "="*80)
        print("EXECUTIVE SUMMARY - BRF COST ANALYSIS & PERFORMANCE METRICS")
        print("="*80)
        
        # Key findings
        best_performer = self.df.loc[self.df['financial_performance_index'].idxmax()]
        worst_performer = self.df.loc[self.df['financial_performance_index'].idxmin()]
        
        print(f"\nKEY FINDINGS:")
        print(f"• Total analyzed: {len(self.df)} BRFs with {self.df['estimated_building_size_m2'].sum():,.0f} m² combined")
        print(f"• Best performer: {best_performer['brf_name']} (Index: {best_performer['financial_performance_index']:.1f})")
        print(f"• Most challenged: {worst_performer['brf_name']} (Index: {worst_performer['financial_performance_index']:.1f})")
        
        # Cost insights
        avg_total_cost = self.market_averages['Total']['mean_per_m2']
        min_total_cost = self.market_averages['Total']['min_per_m2']
        max_total_cost = self.market_averages['Total']['max_per_m2']
        
        print(f"\nCOST ANALYSIS:")
        print(f"• Average annual cost: {avg_total_cost:.0f} SEK/m²")
        print(f"• Cost range: {min_total_cost:.0f} - {max_total_cost:.0f} SEK/m² ({(max_total_cost-min_total_cost)/min_total_cost*100:.0f}% variation)")
        print(f"• Largest cost category: Electricity ({self.market_averages['Electricity']['mean_per_m2']:.0f} SEK/m² average)")
        
        # Energy performance insights
        print(f"\nENERGY PERFORMANCE:")
        avg_energy = self.df['energy_performance'].mean()
        print(f"• Average energy performance: {avg_energy:.0f} kWh/m²/år")
        print(f"• Energy class distribution: {dict(self.df['energy_class'].value_counts())}")
        
        # BRF Sjöstaden 2 specific
        sjostaden = self.df[self.df['brf_name'] == 'Brf Sjöstaden 2'].iloc[0]
        print(f"\nBRF SJÖSTADEN 2 HIGHLIGHTS:")
        print(f"• Performance rank: #{self.df.sort_values('financial_performance_index', ascending=False).reset_index().index[self.df.sort_values('financial_performance_index', ascending=False)['brf_name'] == 'Brf Sjöstaden 2'].tolist()[0] + 1} of {len(self.df)}")
        print(f"• Energy class: {sjostaden['energy_class']} ({sjostaden['energy_performance']:.0f} kWh/m²/år)")
        print(f"• Total cost: {sjostaden['total_cost_per_m2']:.0f} SEK/m² ({(sjostaden['total_cost_per_m2']/avg_total_cost-1)*100:+.0f}% vs market)")


def main():
    """Main execution function."""
    print("BRF COMPREHENSIVE COST ANALYSIS & PERFORMANCE METRICS SYSTEM")
    print("=" * 70)
    print("Initializing analysis...")
    
    # Initialize analyzer
    data_path = '/Users/hosseins/Dropbox/Zelda/ZeldaDemo/killer_eghs_dataset_with_booli_coords.json'
    analyzer = BRFAnalyzer(data_path)
    
    # Perform personalized analysis for Sjöstaden 2
    analyzer.analyze_sjostaden_2()
    
    # Generate market benchmarking
    analyzer.generate_market_benchmarking()
    
    # Create visualizations
    analyzer.create_visualizations()
    
    # Export comprehensive data
    analyzer.export_analysis_data()
    
    # Generate executive summary
    analyzer.generate_executive_summary()
    
    print("\n" + "="*70)
    print("ANALYSIS COMPLETE")
    print("="*70)
    print("\nFiles generated:")
    print("• /Users/hosseins/Dropbox/Zelda/ZeldaDemo/brf_comprehensive_analysis.png")
    print("• /Users/hosseins/Dropbox/Zelda/ZeldaDemo/brf_comprehensive_analysis.json") 
    print("• /Users/hosseins/Dropbox/Zelda/ZeldaDemo/brf_cost_breakdown.csv")
    print("• /Users/hosseins/Dropbox/Zelda/ZeldaDemo/brf_performance_summary.csv")


if __name__ == "__main__":
    main()