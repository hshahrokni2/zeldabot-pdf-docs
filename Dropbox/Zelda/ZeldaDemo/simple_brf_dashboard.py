#!/usr/bin/env python3
"""
Simple BRF Performance Dashboard
===============================
"""

import json
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import numpy as np

def create_dashboard():
    """Create BRF performance dashboard."""
    
    # Load data
    with open('/Users/hosseins/Dropbox/Zelda/ZeldaDemo/brf_comprehensive_analysis.json', 'r') as f:
        data = json.load(f)
    
    cost_df = pd.read_csv('/Users/hosseins/Dropbox/Zelda/ZeldaDemo/brf_cost_breakdown.csv')
    
    # Create figure
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('BRF Performance Analysis Dashboard', fontsize=16, fontweight='bold')
    
    # 1. Performance Rankings
    ax1 = axes[0, 0]
    performance_data = []
    for brf in data['brf_summary']:
        performance_data.append({
            'name': brf['brf_name'].replace('Brf ', ''),
            'performance': brf['financial_performance_index']
        })
    
    perf_df = pd.DataFrame(performance_data).sort_values('performance', ascending=True)
    
    colors = ['darkred' if x < 20 else 'red' if x < 40 else 'orange' if x < 60 else 'green' 
              for x in perf_df['performance']]
    
    bars = ax1.barh(range(len(perf_df)), perf_df['performance'], color=colors, alpha=0.7)
    ax1.set_yticks(range(len(perf_df)))
    ax1.set_yticklabels(perf_df['name'])
    ax1.set_xlabel('Performance Index')
    ax1.set_title('BRF Performance Rankings')
    
    # 2. Cost Categories Comparison
    ax2 = axes[0, 1]
    categories = ['Electricity_per_m2', 'Heating_per_m2', 'Water_per_m2']
    category_names = ['Electricity', 'Heating', 'Water']
    
    # Box plot
    box_data = [cost_df[cat].values for cat in categories]
    bp = ax2.boxplot(box_data, labels=category_names, patch_artist=True)
    
    colors = ['lightcoral', 'lightblue', 'lightgreen']
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
    
    ax2.set_ylabel('Cost (SEK/m²)')
    ax2.set_title('Cost Distribution by Category')
    
    # 3. Energy vs Cost Scatter
    ax3 = axes[1, 0]
    energy_perf = []
    total_costs = []
    names = []
    
    for brf in data['brf_summary']:
        energy_perf.append(brf['energy_performance'])
        total_costs.append(brf['costs']['total_per_m2'])
        names.append(brf['brf_name'].replace('Brf ', ''))
    
    ax3.scatter(energy_perf, total_costs, s=100, alpha=0.7, c='steelblue')
    
    for i, name in enumerate(names):
        ax3.annotate(name, (energy_perf[i], total_costs[i]), 
                    xytext=(5, 5), textcoords='offset points', fontsize=8)
    
    ax3.set_xlabel('Energy Performance (kWh/m²/år)')
    ax3.set_ylabel('Total Cost (SEK/m²)')
    ax3.set_title('Energy Performance vs Cost')
    
    # 4. Sjöstaden 2 Analysis
    ax4 = axes[1, 1]
    
    # Find Sjöstaden 2
    sjostaden_data = None
    for brf in data['brf_summary']:
        if 'Sjöstaden 2' in brf['brf_name']:
            sjostaden_data = brf
            break
    
    if sjostaden_data:
        categories = ['Electricity', 'Heating', 'Water']
        sjostaden_costs = [
            sjostaden_data['costs']['electricity_per_m2'],
            sjostaden_data['costs']['heating_per_m2'], 
            sjostaden_data['costs']['water_per_m2']
        ]
        market_avgs = [
            data['market_averages']['Electricity']['mean_per_m2'],
            data['market_averages']['Heating']['mean_per_m2'],
            data['market_averages']['Water']['mean_per_m2']
        ]
        
        x = np.arange(len(categories))
        width = 0.35
        
        ax4.bar(x - width/2, sjostaden_costs, width, label='Sjöstaden 2', 
               color='steelblue', alpha=0.7)
        ax4.bar(x + width/2, market_avgs, width, label='Market Average', 
               color='lightcoral', alpha=0.7)
        
        ax4.set_xlabel('Categories')
        ax4.set_ylabel('Cost (SEK/m²)')
        ax4.set_title('Sjöstaden 2 vs Market')
        ax4.set_xticks(x)
        ax4.set_xticklabels(categories)
        ax4.legend()
    
    plt.tight_layout()
    
    # Save
    output_path = '/Users/hosseins/Dropbox/Zelda/ZeldaDemo/brf_dashboard.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Dashboard saved to: {output_path}")
    
    return output_path

if __name__ == "__main__":
    print("Creating BRF Dashboard...")
    dashboard_path = create_dashboard()
    print("Dashboard complete!")