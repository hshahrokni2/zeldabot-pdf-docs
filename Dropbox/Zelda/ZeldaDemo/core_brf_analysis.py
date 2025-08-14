#!/usr/bin/env python3
"""
Core BRF Cost Analysis and Performance Metrics System
====================================================

Focused analysis without visualization to get core metrics.
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime

class CoreBRFAnalyzer:
    """Core BRF analysis system."""
    
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
            
        self.df = pd.DataFrame(self.raw_data)
        
        self.cost_columns = [
            'cost_cleaning', 'cost_electricity', 'cost_heating',
            'cost_internet_and_tv', 'cost_recycling', 'cost_snow_removal',
            'cost_water', 'total_cost'
        ]
        
        print(f"Loaded data for {len(self.df)} BRFs")
        
    def estimate_building_sizes(self):
        """Estimate building sizes in m²."""
        print("\n=== ESTIMATING BUILDING SIZES ===")
        
        def get_base_apartment_size(year: int, brf_name: str) -> float:
            if any(keyword in brf_name.lower() for keyword in ['sjöstaden', 'hammarby', 'sickla']):
                if year >= 2010:
                    return 75.0
                elif year >= 2000:
                    return 70.0
                else:
                    return 65.0
            else:
                if year >= 2010:
                    return 65.0
                elif year >= 2000:
                    return 60.0
                else:
                    return 55.0
        
        def estimate_apartments(row) -> int:
            total_apartments = 0
            
            for prop in row['epc_properties']:
                house_numbers = prop['house_numbers']
                
                if isinstance(house_numbers, str):
                    numbers_str = house_numbers.strip('{}')
                    if ',' in numbers_str:
                        numbers = numbers_str.split(',')
                    else:
                        numbers = [numbers_str]
                    
                    valid_numbers = [n.strip() for n in numbers if n.strip().isdigit()]
                    
                    if any(keyword in row['brf_name'].lower() for keyword in ['sjöstaden', 'hammarby']):
                        apartments_per_house = 25
                    else:
                        apartments_per_house = 15
                    
                    total_apartments += len(valid_numbers) * apartments_per_house
            
            cost_based_minimum = max(10, int(row['total_cost'] / 100000))
            return max(total_apartments, cost_based_minimum)
        
        self.df['estimated_apartments'] = self.df.apply(estimate_apartments, axis=1)
        self.df['base_apartment_size'] = self.df.apply(
            lambda x: get_base_apartment_size(x['construction_year'], x['brf_name']), axis=1
        )
        self.df['estimated_building_size_m2'] = (
            self.df['estimated_apartments'] * self.df['base_apartment_size']
        )
        
        print("Building Size Estimates:")
        print("=" * 80)
        for _, row in self.df.iterrows():
            print(f"{row['brf_name']:<30} | {row['construction_year']} | "
                  f"{row['estimated_apartments']:>3} apts | {row['base_apartment_size']:>4.0f} m²/apt | "
                  f"{row['estimated_building_size_m2']:>6,.0f} m² total")
        
    def normalize_costs(self):
        """Normalize costs to SEK/m²."""
        print("\n=== NORMALIZING COSTS TO SEK/m² ===")
        
        for cost_col in self.cost_columns:
            normalized_col = f"{cost_col}_per_m2"
            self.df[normalized_col] = self.df[cost_col] / self.df['estimated_building_size_m2']
        
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
            
            for category, cost in cost_categories.items():
                breakdown[f'{category}_SEK'] = cost
                breakdown[f'{category}_per_m2'] = cost / row['estimated_building_size_m2']
            
            breakdown['Total_SEK'] = total_cost
            breakdown['Total_per_m2'] = total_cost / row['estimated_building_size_m2']
            
            self.cost_breakdown.append(breakdown)
        
        self.cost_breakdown_df = pd.DataFrame(self.cost_breakdown)
        
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
        
        max_energy_performance = 159
        self.df['energy_efficiency_score'] = np.maximum(0, 100 - (self.df['energy_performance'] / max_energy_performance * 100))
        
        market_avg_cost_per_m2 = self.market_averages['Total']['mean_per_m2']
        self.df['cost_efficiency_score'] = np.maximum(0, 100 - (self.df['total_cost_per_m2'] / market_avg_cost_per_m2 * 100))
        
        self.df['financial_performance_index'] = (
            0.3 * self.df['energy_efficiency_score'] + 
            0.7 * self.df['cost_efficiency_score']
        )
        
        self.df['performance_percentile'] = self.df['financial_performance_index'].rank(pct=True) * 100
        self.df['energy_percentile'] = self.df['energy_efficiency_score'].rank(pct=True) * 100
        self.df['cost_percentile'] = self.df['cost_efficiency_score'].rank(pct=True) * 100
        
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
        """Personalized analysis for BRF Sjöstaden 2."""
        print("\n=== PERSONALIZED ANALYSIS: BRF SJÖSTADEN 2 ===")
        
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
        
        # Top 25% comparison
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
            
            if difference > 50:
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
        
        print(f"\nStrengths:")
        print("=" * 30)
        
        strengths = []
        for category in cost_categories:
            per_m2_col = f'{category}_per_m2'
            sjostaden_cost = sjostaden_breakdown[per_m2_col]
            market_avg = self.market_averages[category]['mean_per_m2']
            
            if sjostaden_cost < market_avg * 0.8:
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
            'savings_opportunities': savings_opportunities,
            'strengths': strengths
        }
    
    def export_analysis_data(self):
        """Export analysis data."""
        print("\n=== EXPORTING ANALYSIS DATA ===")
        
        export_data = {
            'metadata': {
                'analysis_date': datetime.now().isoformat(),
                'total_brfs': len(self.df),
                'total_building_area_m2': int(self.df['estimated_building_size_m2'].sum()),
                'analyst': 'Claudette-Analyst'
            },
            'market_averages': {},
            'brf_summary': []
        }
        
        # Convert numpy types for JSON serialization
        for category, stats in self.market_averages.items():
            export_data['market_averages'][category] = {
                'mean_per_m2': float(stats['mean_per_m2']),
                'median_per_m2': float(stats['median_per_m2']),
                'std_per_m2': float(stats['std_per_m2']),
                'min_per_m2': float(stats['min_per_m2']),
                'max_per_m2': float(stats['max_per_m2'])
            }
        
        for _, row in self.df.iterrows():
            brf_data = {
                'brf_name': row['brf_name'],
                'building_id': row['building_id'],
                'construction_year': int(row['construction_year']),
                'energy_performance': float(row['energy_performance']),
                'energy_class': row['energy_class'],
                'estimated_building_size_m2': float(row['estimated_building_size_m2']),
                'estimated_apartments': int(row['estimated_apartments']),
                'financial_performance_index': float(row['financial_performance_index']),
                'performance_percentile': float(row['performance_percentile'])
            }
            
            cost_breakdown = self.cost_breakdown_df[
                self.cost_breakdown_df['brf_name'] == row['brf_name']
            ].iloc[0]
            
            brf_data['costs'] = {
                'total_per_m2': float(cost_breakdown['Total_per_m2']),
                'electricity_per_m2': float(cost_breakdown['Electricity_per_m2']),
                'heating_per_m2': float(cost_breakdown['Heating_per_m2']),
                'water_per_m2': float(cost_breakdown['Water_per_m2'])
            }
            
            export_data['brf_summary'].append(brf_data)
        
        output_path = '/Users/hosseins/Dropbox/Zelda/ZeldaDemo/brf_comprehensive_analysis.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        csv_path = '/Users/hosseins/Dropbox/Zelda/ZeldaDemo/brf_cost_breakdown.csv'
        self.cost_breakdown_df.to_csv(csv_path, index=False)
        
        print(f"Analysis exported to: {output_path}")
        print(f"Cost breakdown CSV: {csv_path}")
        
        return export_data
    
    def generate_executive_summary(self):
        """Generate executive summary."""
        print("\n" + "="*80)
        print("EXECUTIVE SUMMARY - BRF COST ANALYSIS & PERFORMANCE METRICS")
        print("="*80)
        
        best_performer = self.df.loc[self.df['financial_performance_index'].idxmax()]
        worst_performer = self.df.loc[self.df['financial_performance_index'].idxmin()]
        
        print(f"\nKEY FINDINGS:")
        print(f"• Total analyzed: {len(self.df)} BRFs with {self.df['estimated_building_size_m2'].sum():,.0f} m² combined")
        print(f"• Best performer: {best_performer['brf_name']} (Index: {best_performer['financial_performance_index']:.1f})")
        print(f"• Most challenged: {worst_performer['brf_name']} (Index: {worst_performer['financial_performance_index']:.1f})")
        
        avg_total_cost = self.market_averages['Total']['mean_per_m2']
        min_total_cost = self.market_averages['Total']['min_per_m2']
        max_total_cost = self.market_averages['Total']['max_per_m2']
        
        print(f"\nCOST ANALYSIS:")
        print(f"• Average annual cost: {avg_total_cost:.0f} SEK/m²")
        print(f"• Cost range: {min_total_cost:.0f} - {max_total_cost:.0f} SEK/m² ({(max_total_cost-min_total_cost)/min_total_cost*100:.0f}% variation)")
        print(f"• Largest cost category: Electricity ({self.market_averages['Electricity']['mean_per_m2']:.0f} SEK/m² average)")
        
        avg_energy = self.df['energy_performance'].mean()
        print(f"\nENERGY PERFORMANCE:")
        print(f"• Average energy performance: {avg_energy:.0f} kWh/m²/år")
        print(f"• Energy class distribution: {dict(self.df['energy_class'].value_counts())}")
        
        sjostaden = self.df[self.df['brf_name'] == 'Brf Sjöstaden 2'].iloc[0]
        sjostaden_rank = self.df.sort_values('financial_performance_index', ascending=False).reset_index().index[
            self.df.sort_values('financial_performance_index', ascending=False)['brf_name'] == 'Brf Sjöstaden 2'
        ].tolist()[0] + 1
        
        print(f"\nBRF SJÖSTADEN 2 HIGHLIGHTS:")
        print(f"• Performance rank: #{sjostaden_rank} of {len(self.df)}")
        print(f"• Energy class: {sjostaden['energy_class']} ({sjostaden['energy_performance']:.0f} kWh/m²/år)")
        print(f"• Total cost: {sjostaden['total_cost_per_m2']:.0f} SEK/m² ({(sjostaden['total_cost_per_m2']/avg_total_cost-1)*100:+.0f}% vs market)")


def main():
    """Main execution function."""
    print("BRF COMPREHENSIVE COST ANALYSIS & PERFORMANCE METRICS SYSTEM")
    print("=" * 70)
    
    data_path = '/Users/hosseins/Dropbox/Zelda/ZeldaDemo/killer_eghs_dataset_with_booli_coords.json'
    analyzer = CoreBRFAnalyzer(data_path)
    
    analyzer.analyze_sjostaden_2()
    analyzer.export_analysis_data()
    analyzer.generate_executive_summary()
    
    print("\n" + "="*70)
    print("CORE ANALYSIS COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()