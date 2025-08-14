#!/usr/bin/env python3
"""
BRF Performance Visualizations
==============================
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

def create_brf_visualizations():
    """Create key visualizations for BRF analysis."""
    
    # Load data
    with open('/Users/hosseins/Dropbox/Zelda/ZeldaDemo/brf_comprehensive_analysis.json', 'r') as f:
        data = json.load(f)
    
    cost_df = pd.read_csv('/Users/hosseins/Dropbox/Zelda/ZeldaDemo/brf_cost_breakdown.csv')
    
    # Set style
    plt.style.use('default')
    sns.set_palette("husl")
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('BRF Performance Analysis Dashboard', fontsize=16, fontweight='bold')
    
    # 1. Cost breakdown by BRF (top-left)
    ax1 = axes[0, 0]
    
    # Prepare data for stacked bar
    brf_names = [name.replace('Brf ', '') for name in cost_df['brf_name']]
    categories = ['Electricity_per_m2', 'Heating_per_m2', 'Water_per_m2', 
                 'Internet & TV_per_m2', 'Recycling_per_m2']
    
    # Stack the costs
    bottom = np.zeros(len(brf_names))
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
    
    for i, category in enumerate(categories):
        values = cost_df[category].values
        ax1.bar(brf_names, values, bottom=bottom, label=category.replace('_per_m2', '').replace(' & ', ' & '), 
               color=colors[i], alpha=0.8)
        bottom += values
    
    ax1.set_title('Annual Costs by Category (SEK/m²)', fontweight='bold')
    ax1.set_ylabel('Cost (SEK/m²)')
    ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
    plt.setp(ax1.get_xticklabels(), rotation=45, ha='right', fontsize=9)
    
    # 2. Performance vs Energy scatter (top-right)
    ax2 = axes[0, 1]
    
    # Extract performance data
    performance_data = []
    for brf in data['brf_summary']:
        performance_data.append({
            'name': brf['brf_name'].replace('Brf ', ''),
            'performance_index': brf['financial_performance_index'],
            'energy_performance': brf['energy_performance'],
            'total_cost': brf['costs']['total_per_m2'],
            'energy_class': brf['energy_class']
        })
    
    perf_df = pd.DataFrame(performance_data)
    
    # Color by energy class
    class_colors = {'A': 'green', 'B': 'lightgreen', 'C': 'yellow', 
                   'D': 'orange', 'E': 'red', 'F': 'darkred'}
    colors = [class_colors.get(ec, 'gray') for ec in perf_df['energy_class']]
    
    scatter = ax2.scatter(perf_df['energy_performance'], perf_df['total_cost'], 
                         c=colors, s=150, alpha=0.7, edgecolors='black')
    
    # Add BRF names as labels
    for _, row in perf_df.iterrows():
        ax2.annotate(row['name'], (row['energy_performance'], row['total_cost']),
                    xytext=(5, 5), textcoords='offset points', fontsize=8)
    
    ax2.set_xlabel('Energy Performance (kWh/m²/år)')
    ax2.set_ylabel('Total Cost (SEK/m²)')
    ax2.set_title('Energy Performance vs Annual Costs', fontweight='bold')
    
    # Add energy class legend
    legend_elements = [plt.scatter([], [], c=color, s=100, label=f'Class {cls}', alpha=0.7) 
                      for cls, color in class_colors.items() if cls in perf_df['energy_class'].values]
    ax2.legend(handles=legend_elements, loc='upper right', fontsize=8)
    
    # 3. Performance rankings (bottom-left)
    ax3 = axes[1, 0]
    
    # Sort by performance index
    perf_sorted = perf_df.sort_values('performance_index', ascending=True)
    
    # Color bars based on performance level
    bar_colors = ['darkred' if x < 20 else 'red' if x < 40 else 'orange' if x < 60 else 'lightgreen' 
                  for x in perf_sorted['performance_index']]
    
    bars = ax3.barh(range(len(perf_sorted)), perf_sorted['performance_index'], color=bar_colors, alpha=0.7)
    ax3.set_yticks(range(len(perf_sorted)))
    ax3.set_yticklabels(perf_sorted['name'], fontsize=9)
    ax3.set_xlabel('Financial Performance Index')
    ax3.set_title('BRF Performance Rankings', fontweight='bold')
    
    # Add performance values on bars
    for i, bar in enumerate(bars):
        width = bar.get_width()
        ax3.text(width + 1, bar.get_y() + bar.get_height()/2, f'{width:.1f}',
                ha='left', va='center', fontsize=8, fontweight='bold')
    
    # 4. Sjöstaden 2 comparison (bottom-right)
    ax4 = axes[1, 1]
    
    # Find Sjöstaden 2 data
    sjostaden_data = None
    for brf in data['brf_summary']:
        if 'Sjöstaden 2' in brf['brf_name']:
            sjostaden_data = brf
            break
    
    if sjostaden_data:
        # Compare major cost categories vs market average
        categories = ['electricity_per_m2', 'heating_per_m2', 'water_per_m2']
        sjostaden_costs = [sjostaden_data['costs'][cat] for cat in categories]
        market_averages = [data['market_averages']['Electricity']['mean_per_m2'],
                          data['market_averages']['Heating']['mean_per_m2'],
                          data['market_averages']['Water']['mean_per_m2']]
        
        x = np.arange(len(categories))
        width = 0.35
        
        bars1 = ax4.bar(x - width/2, sjostaden_costs, width, label='Sjöstaden 2', 
                       color='steelblue', alpha=0.7)
        bars2 = ax4.bar(x + width/2, market_averages, width, label='Market Average', 
                       color='lightcoral', alpha=0.7)
        
        ax4.set_xlabel('Cost Categories')
        ax4.set_ylabel('Cost (SEK/m²)')
        ax4.set_title('Sjöstaden 2 vs Market Averages', fontweight='bold')
        ax4.set_xticks(x)
        ax4.set_xticklabels(['Electricity', 'Heating', 'Water'])
        ax4.legend()
        
        # Add value labels on bars
        def autolabel(bars):
            for bar in bars:
                height = bar.get_height()
                ax4.annotate(f'{height:.0f}',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom', fontsize=8)
        
        autolabel(bars1)
        autolabel(bars2)
    
    plt.tight_layout()
    
    # Save the plot
    output_path = '/Users/hosseins/Dropbox/Zelda/ZeldaDemo/brf_performance_dashboard.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    
    print(f"Dashboard saved to: {output_path}")
    plt.show()

def create_sjostaden_savings_chart():
    """Create a detailed savings opportunity chart for Sjöstaden 2."""
    
    # Savings data from analysis
    savings_data = {
        'Electricity': 1321676,
        'Water': 389669
    }
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle('BRF Sjöstaden 2 - Savings Opportunities', fontsize=14, fontweight='bold')
    
    # 1. Savings by category
    categories = list(savings_data.keys())
    savings = list(savings_data.values())
    
    bars = ax1.bar(categories, savings, color=['#FF6B6B', '#4ECDC4'], alpha=0.8)
    ax1.set_ylabel('Annual Savings (SEK)')
    ax1.set_title('Potential Annual Savings by Category')
    
    # Add value labels
    for bar, saving in zip(bars, savings):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + saving*0.02,
                f'{saving:,.0f} SEK\n({saving/12:,.0f}/month)', 
                ha='center', va='bottom', fontweight='bold')
    
    # 2. Total impact visualization
    total_savings = sum(savings)
    current_cost = 2950357  # Total cost for Sjöstaden 2
    optimized_cost = current_cost - total_savings
    
    costs = [optimized_cost, total_savings]
    labels = [f'Optimized Annual Cost\n{optimized_cost:,.0f} SEK', 
              f'Potential Savings\n{total_savings:,.0f} SEK']
    colors = ['lightblue', 'lightcoral']
    
    wedges, texts, autotexts = ax2.pie(costs, labels=labels, colors=colors, autopct='%1.1f%%',
                                      startangle=90, textprops={'fontsize': 10})
    ax2.set_title('Cost Optimization Impact')
    
    plt.tight_layout()
    
    output_path = '/Users/hosseins/Dropbox/Zelda/ZeldaDemo/sjostaden_savings_analysis.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Savings analysis saved to: {output_path}")
    plt.show()

if __name__ == "__main__":
    print("Creating BRF Performance Visualizations...")
    create_brf_visualizations()
    create_sjostaden_savings_chart()
    print("Visualizations complete!")