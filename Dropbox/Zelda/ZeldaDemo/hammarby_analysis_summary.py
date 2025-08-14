#!/usr/bin/env python3
"""
Hammarby Sjöstad Analysis Summary
Creates visualization-ready summaries and insights from the integrated energy-cost dataset.
"""

import json
import pandas as pd
from typing import Dict, List
import numpy as np

def load_integrated_data(file_path: str) -> Dict:
    """Load the integrated dataset."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_map_visualization_data(data: Dict) -> Dict:
    """Create simplified data structure optimized for map visualization."""
    
    map_data = {
        'metadata': data['metadata'].copy(),
        'summary_statistics': data['statistics'].copy(),
        'buildings': []
    }
    
    for building in data['buildings']:
        # Extract key visualization data
        map_building = {
            'id': building['brf_id'],
            'name': building['brf_name'],
            'coordinates': {
                'lat': building['location']['latitude'],
                'lng': building['location']['longitude']
            },
            'address': building['location']['address'],
            'postal_code': building['location']['postal_code'],
            
            # Energy performance
            'energy_performance_kwh_m2': building.get('energy_performance_kwh_m2'),
            'energy_class': building.get('energy_class'),
            'efficiency_vs_swedish_avg': building.get('efficiency_vs_swedish_avg'),
            'efficiency_rating': building.get('efficiency_rating'),
            'construction_year': building.get('construction_year'),
            
            # Economic data
            'monthly_fee': building['economy']['monthly_fee'],
            'energy_costs': building['economy']['energy_costs'],
            'water_costs': building['economy']['water_costs'],
            'heating_costs': building['economy']['heating_costs'],
            
            # Performance metrics
            'performance_score': building.get('performance_score', 0),
            'bang_for_buck_overall': building.get('bang_for_buck', {}).get('overall', 0),
            
            # Cost breakdown ratios for visualization
            'cost_ratios': building.get('cost_metrics', {}).get('cost_ratios', {}),
            
            # Data quality indicators
            'epc_confidence': building.get('epc_confidence', 0),
            'cost_confidence': building.get('cost_confidence', 0),
            'has_energy_data': building.get('energy_performance_kwh_m2') is not None,
            'has_cost_data': building.get('cost_breakdown') is not None
        }
        
        map_data['buildings'].append(map_building)
    
    return map_data

def create_insights_report(data: Dict) -> Dict:
    """Generate key insights and analysis from the integrated data."""
    
    buildings = data['buildings']
    stats = data['statistics']
    
    insights = {
        'key_findings': [],
        'energy_analysis': {},
        'cost_analysis': {},
        'performance_analysis': {},
        'recommendations': []
    }
    
    # Energy Analysis
    energy_buildings = [b for b in buildings if b.get('energy_performance_kwh_m2')]
    if energy_buildings:
        avg_energy = np.mean([b['energy_performance_kwh_m2'] for b in energy_buildings])
        swedish_benchmark = data['metadata']['swedish_energy_benchmark']
        
        insights['energy_analysis'] = {
            'avg_performance_kwh_m2': round(avg_energy, 1),
            'vs_swedish_benchmark': round((avg_energy / swedish_benchmark) * 100, 1),
            'best_performer': min(energy_buildings, key=lambda x: x['energy_performance_kwh_m2']),
            'efficiency_distribution': {
                'excellent': len([b for b in energy_buildings if b.get('efficiency_vs_swedish_avg', 1) <= 0.7]),
                'good': len([b for b in energy_buildings if 0.7 < b.get('efficiency_vs_swedish_avg', 1) <= 0.9]),
                'average': len([b for b in energy_buildings if 0.9 < b.get('efficiency_vs_swedish_avg', 1) <= 1.1]),
                'below_average': len([b for b in energy_buildings if 1.1 < b.get('efficiency_vs_swedish_avg', 1) <= 1.3]),
                'poor': len([b for b in energy_buildings if b.get('efficiency_vs_swedish_avg', 1) > 1.3])
            }
        }
        
        if avg_energy < swedish_benchmark:
            insights['key_findings'].append(
                f"Hammarby Sjöstad performs {round(((swedish_benchmark - avg_energy) / swedish_benchmark) * 100, 1)}% "
                f"better than the Swedish average energy consumption of {swedish_benchmark} kWh/m²."
            )
    
    # Cost Analysis
    cost_buildings = [b for b in buildings if b.get('cost_breakdown')]
    if cost_buildings:
        # Analyze cost categories
        all_cost_ratios = {}
        for building in cost_buildings:
            ratios = building.get('cost_metrics', {}).get('cost_ratios', {})
            for category, ratio in ratios.items():
                if category not in all_cost_ratios:
                    all_cost_ratios[category] = []
                all_cost_ratios[category].append(ratio)
        
        avg_cost_ratios = {
            category: round(np.mean(ratios) * 100, 1)
            for category, ratios in all_cost_ratios.items()
        }
        
        insights['cost_analysis'] = {
            'buildings_with_cost_data': len(cost_buildings),
            'avg_cost_breakdown_percent': avg_cost_ratios,
            'highest_cost_category': max(avg_cost_ratios.items(), key=lambda x: x[1]) if avg_cost_ratios else None
        }
        
        if avg_cost_ratios:
            highest_category, highest_pct = max(avg_cost_ratios.items(), key=lambda x: x[1])
            insights['key_findings'].append(
                f"The largest cost category is {highest_category} at {highest_pct}% of total costs on average."
            )
    
    # Performance Analysis
    performance_scores = [b.get('performance_score', 0) for b in buildings if b.get('performance_score')]
    if performance_scores:
        insights['performance_analysis'] = {
            'avg_performance_score': round(np.mean(performance_scores), 1),
            'best_performer': max(buildings, key=lambda x: x.get('performance_score', 0)),
            'score_distribution': {
                'excellent': len([s for s in performance_scores if s >= 80]),
                'good': len([s for s in performance_scores if 60 <= s < 80]),
                'average': len([s for s in performance_scores if 40 <= s < 60]),
                'below_average': len([s for s in performance_scores if 20 <= s < 40]),
                'poor': len([s for s in performance_scores if s < 20])
            }
        }
    
    # Data Quality Assessment
    data_quality = stats.get('data_quality', {})
    insights['key_findings'].append(
        f"Data coverage: {data_quality.get('buildings_with_energy_data', 0)}/{data['metadata']['total_buildings']} "
        f"buildings have energy performance data, {data_quality.get('buildings_with_cost_data', 0)}/{data['metadata']['total_buildings']} have cost data."
    )
    
    # Recommendations
    if energy_buildings and len(energy_buildings) > 0:
        if avg_energy > swedish_benchmark:
            insights['recommendations'].append(
                "Consider energy efficiency improvements as average consumption exceeds Swedish benchmark."
            )
        else:
            insights['recommendations'].append(
                "Strong energy performance - consider sharing best practices with other buildings."
            )
    
    if cost_buildings and len(cost_buildings) > 0:
        insights['recommendations'].append(
            "Analyze cost optimization opportunities in the highest spending categories."
        )
    
    if data_quality.get('buildings_with_energy_data', 0) < data['metadata']['total_buildings']:
        insights['recommendations'].append(
            "Obtain EPC certificates for remaining buildings to enable comprehensive energy analysis."
        )
    
    return insights

def create_comparison_metrics(data: Dict) -> Dict:
    """Create metrics for building-to-building comparisons."""
    
    buildings = data['buildings']
    comparisons = {
        'energy_efficiency_ranking': [],
        'cost_efficiency_ranking': [],
        'overall_performance_ranking': [],
        'peer_groups': {}
    }
    
    # Energy efficiency ranking
    energy_buildings = [b for b in buildings if b.get('energy_performance_kwh_m2')]
    energy_buildings.sort(key=lambda x: x['energy_performance_kwh_m2'])
    
    for i, building in enumerate(energy_buildings):
        comparisons['energy_efficiency_ranking'].append({
            'rank': i + 1,
            'brf_name': building['brf_name'],
            'energy_performance_kwh_m2': building['energy_performance_kwh_m2'],
            'efficiency_rating': building.get('efficiency_rating', 'Unknown')
        })
    
    # Overall performance ranking
    performance_buildings = [b for b in buildings if b.get('performance_score')]
    performance_buildings.sort(key=lambda x: x['performance_score'], reverse=True)
    
    for i, building in enumerate(performance_buildings):
        comparisons['overall_performance_ranking'].append({
            'rank': i + 1,
            'brf_name': building['brf_name'],
            'performance_score': building['performance_score'],
            'monthly_fee': building['economy']['monthly_fee']
        })
    
    # Create peer groups by construction year
    construction_groups = {}
    for building in buildings:
        year = building.get('construction_year')
        if year:
            decade = (year // 10) * 10
            decade_key = f"{decade}s"
            if decade_key not in construction_groups:
                construction_groups[decade_key] = []
            construction_groups[decade_key].append({
                'name': building['brf_name'],
                'energy_performance': building.get('energy_performance_kwh_m2'),
                'performance_score': building.get('performance_score'),
                'monthly_fee': building['economy']['monthly_fee']
            })
    
    comparisons['peer_groups'] = construction_groups
    
    return comparisons

def main():
    """Main function to generate analysis outputs."""
    
    # Load integrated data
    input_file = "/Users/hosseins/Dropbox/Zelda/ZeldaDemo/hammarby_integrated_energy_cost_analysis.json"
    data = load_integrated_data(input_file)
    
    # Create map visualization data
    map_data = create_map_visualization_data(data)
    map_output_file = "/Users/hosseins/Dropbox/Zelda/ZeldaDemo/hammarby_map_visualization_data.json"
    with open(map_output_file, 'w', encoding='utf-8') as f:
        json.dump(map_data, f, indent=2, ensure_ascii=False)
    
    # Generate insights
    insights = create_insights_report(data)
    insights_output_file = "/Users/hosseins/Dropbox/Zelda/ZeldaDemo/hammarby_analysis_insights.json"
    with open(insights_output_file, 'w', encoding='utf-8') as f:
        json.dump(insights, f, indent=2, ensure_ascii=False)
    
    # Create comparison metrics
    comparisons = create_comparison_metrics(data)
    comparisons_output_file = "/Users/hosseins/Dropbox/Zelda/ZeldaDemo/hammarby_building_comparisons.json"
    with open(comparisons_output_file, 'w', encoding='utf-8') as f:
        json.dump(comparisons, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print("🏗️ Hammarby Sjöstad Analysis Summary")
    print("=" * 50)
    print(f"📊 Dataset processed: {data['metadata']['total_buildings']} buildings")
    print(f"🏠 Buildings with energy data: {data['statistics']['data_quality']['buildings_with_energy_data']}")
    print(f"💰 Buildings with cost data: {data['statistics']['data_quality']['buildings_with_cost_data']}")
    
    if data['statistics']['energy_performance']['avg_kwh_per_m2']:
        avg_energy = data['statistics']['energy_performance']['avg_kwh_per_m2']
        vs_swedish = (avg_energy / 159) * 100
        print(f"⚡ Average energy performance: {avg_energy} kWh/m² ({vs_swedish:.1f}% of Swedish avg)")
    
    print(f"📈 Average performance score: {data['statistics']['performance_scores']['avg_score']:.1f}/100")
    
    print(f"\n📁 Output files created:")
    print(f"   Map visualization: {map_output_file}")
    print(f"   Analysis insights: {insights_output_file}")
    print(f"   Building comparisons: {comparisons_output_file}")
    
    # Display key findings
    if insights['key_findings']:
        print(f"\n🔍 Key Findings:")
        for i, finding in enumerate(insights['key_findings'], 1):
            print(f"   {i}. {finding}")
    
    # Display recommendations
    if insights['recommendations']:
        print(f"\n💡 Recommendations:")
        for i, rec in enumerate(insights['recommendations'], 1):
            print(f"   {i}. {rec}")

if __name__ == "__main__":
    main()