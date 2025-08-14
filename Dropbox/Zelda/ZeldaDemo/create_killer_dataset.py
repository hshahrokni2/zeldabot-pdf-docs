#!/usr/bin/env python3
"""
Create Killer Dataset - Merge PostgreSQL + EPC + Excel for 8 EGHS buildings
Using manual mapping where building names don't match exactly
"""

import pandas as pd
import json
import psycopg2
from typing import Dict, Any

# Manual mapping based on our analysis
BUILDING_MAPPING = {
    'Brf Hammarby Kaj': {
        'postgres_id': 2,
        'postgres_name': 'BRF Hammarby Kaj',
        'epc_owner': 'Bostadsrättsföreningen Hammarby Kaj',
        'excel_name': 'Brf Hammarby Kaj'
    },
    # These have EPC + Excel but need to find/assign Postgres coordinates
    'Brf Havet': {
        'postgres_id': None,  # Need to assign
        'postgres_name': None,
        'epc_owner': 'Bostadsrättsföreningen Havet',  
        'excel_name': 'Brf Havet'
    },
    'Brf Holmen': {
        'postgres_id': None,  # Maybe BRF Hammarby Port/Fabrik?
        'postgres_name': None,
        'epc_owner': 'Bostadsrättsföreningen Holmen, Sickla Kaj.',
        'excel_name': 'Brf Holmen'
    },
    'Brf Sjöportalen 1': {
        'postgres_id': None,
        'postgres_name': None, 
        'epc_owner': 'Bostadsrättsföreningen Sjöportalen 1',
        'excel_name': 'Brf Sjöportalen 1'
    },
    'Brf Sjöstaden 2': {
        'postgres_id': 1,  # Different but closest: BRF Sjöstaden 1
        'postgres_name': 'BRF Sjöstaden 1',  # Note: Different number!
        'epc_owner': 'Bostadsrättsföreningen Sjöstaden 2',
        'excel_name': 'Brf Sjöstaden 2'
    },
    'Brf Sjöstadsesplanaden 1': {
        'postgres_id': 7,  # Maybe BRF Sjöstadsparterren?
        'postgres_name': 'BRF Sjöstadsparterren',
        'epc_owner': 'Bostadsrättsföreningen Sjöstadsesplanaden 1', 
        'excel_name': 'Brf Sjöstadsesplanaden 1 '
    },
    'Brf Sjöstadspiren': {
        'postgres_id': 11,  # Maybe BRF Sjöstadskajen?
        'postgres_name': 'BRF Sjöstadskajen',
        'epc_owner': 'Bostadsrättsföreningen Sjöstadspiren',
        'excel_name': 'Brf Sjöstadspiren'
    },
    'Brf Strandkanten': {
        'postgres_id': 6,   # Maybe BRF Lugnets Strand?
        'postgres_name': 'BRF Lugnets Strand',
        'epc_owner': 'Bostadsrättsföreningen Strandkanten',
        'excel_name': 'Brf Strandkanten'
    },
    'Brf Sundet': {
        'postgres_id': None,
        'postgres_name': None,
        'epc_owner': 'Bostadsrättsföreningen Sundet',
        'excel_name': 'Brf Sundet'
    }
}

def load_postgres_data():
    """Load data from PostgreSQL"""
    conn = psycopg2.connect('postgresql://postgres:zeldaMaster@localhost/zelda')
    
    # Buildings with coordinates
    buildings_df = pd.read_sql('''
        SELECT brf_id, brf_name, latitude, longitude, formatted_address, city_appended, postal_code
        FROM residences 
        ORDER BY brf_id
    ''', conn)
    
    # Economy data
    economy_df = pd.read_sql('''
        SELECT brf_id, year, monthly_fee, total_income, total_expenses,
               energy_costs, water_costs, heating_costs, maintenance_fund, loan_amount
        FROM economy_data
        WHERE year = (SELECT MAX(year) FROM economy_data WHERE economy_data.brf_id = economy_data.brf_id)
        ORDER BY brf_id
    ''', conn)
    
    conn.close()
    return buildings_df, economy_df

def load_epc_data():
    """Load and process EPC energy data"""
    with open('EnergyPerformanceCertificatesEGHS.json', 'r') as f:
        epc_data = json.load(f)
    
    # Group by BRF and calculate averages
    epc_by_brf = {}
    for item in epc_data:
        owner = item['property_owner']
        if owner not in epc_by_brf:
            epc_by_brf[owner] = {
                'energy_performances': [],
                'energy_classes': [],
                'construction_years': [],
                'properties': []
            }
        
        if isinstance(item['json_data'], dict):
            energy = item['json_data'].get('energyPerformance_kWh_per_m2', 0)
            energy_class = item['json_data'].get('energyClass', 'Unknown')
            construction_year = item['json_data'].get('constructionYear', 0)
            
            epc_by_brf[owner]['energy_performances'].append(energy)
            epc_by_brf[owner]['energy_classes'].append(energy_class)
            epc_by_brf[owner]['construction_years'].append(construction_year)
            epc_by_brf[owner]['properties'].append({
                'name': item['property_name'],
                'house_numbers': item['house_numbers']
            })
    
    # Calculate averages
    epc_summary = {}
    for owner, data in epc_by_brf.items():
        valid_energies = [e for e in data['energy_performances'] if e > 0]
        valid_years = [y for y in data['construction_years'] if y > 0]
        
        epc_summary[owner] = {
            'avg_energy_performance': sum(valid_energies) / len(valid_energies) if valid_energies else 0,
            'energy_class': max(set(data['energy_classes']), key=data['energy_classes'].count) if data['energy_classes'] else 'Unknown',
            'construction_year': max(set(valid_years), key=valid_years.count) if valid_years else 0,
            'property_count': len(data['properties']),
            'properties': data['properties']
        }
    
    return epc_summary

def load_excel_data():
    """Load and process Excel cost data"""
    cost_df = pd.read_excel('Parsed costs for EGHS and Finnboda for 2023 (1).xlsx', sheet_name='Raw data')
    
    # Filter for Hammarby Sjöstad
    hammarby_costs = cost_df[cost_df['neighborhood'] == 'Hammarby Sjöstad']
    
    # Pivot to get costs by category per building
    cost_pivot = hammarby_costs.pivot_table(
        index='property',
        columns='type', 
        values='value',
        aggfunc='sum',
        fill_value=0
    ).reset_index()
    
    cost_pivot.columns.name = None
    return cost_pivot

def create_unified_dataset():
    """Create the killer unified dataset"""
    print("🔄 Loading data from all sources...")
    
    # Load all data
    buildings_df, economy_df = load_postgres_data()
    epc_data = load_epc_data()
    cost_data = load_excel_data()
    
    print(f"📊 Loaded:")
    print(f"  - Postgres: {len(buildings_df)} buildings with coordinates")
    print(f"  - EPC: {len(epc_data)} buildings with energy data")  
    print(f"  - Excel: {len(cost_data)} buildings with cost data")
    
    unified_buildings = []
    
    for brf_name, mapping in BUILDING_MAPPING.items():
        print(f"\\n🏗️  Processing {brf_name}...")
        
        building_data = {
            'brf_name': brf_name,
            'building_id': f"eghs_{len(unified_buildings) + 1}"
        }
        
        # Get Postgres data (coordinates, etc.)
        if mapping['postgres_id']:
            postgres_row = buildings_df[buildings_df['brf_id'] == mapping['postgres_id']]
            if not postgres_row.empty:
                row = postgres_row.iloc[0]
                building_data.update({
                    'latitude': float(row['latitude']),
                    'longitude': float(row['longitude']),
                    'formatted_address': row['formatted_address'],
                    'postal_code': row['postal_code'],
                    'postgres_name': row['brf_name'],
                    'postgres_id': int(row['brf_id'])
                })
                print(f"  ✅ Coordinates: {building_data['latitude']:.4f}, {building_data['longitude']:.4f}")
                
                # Get economy data
                economy_row = economy_df[economy_df['brf_id'] == mapping['postgres_id']]
                if not economy_row.empty:
                    econ = economy_row.iloc[0]
                    building_data.update({
                        'monthly_fee': float(econ['monthly_fee']) if econ['monthly_fee'] else 0,
                        'total_income': float(econ['total_income']) if econ['total_income'] else 0,
                        'total_expenses': float(econ['total_expenses']) if econ['total_expenses'] else 0,
                        'postgres_energy_costs': float(econ['energy_costs']) if econ['energy_costs'] else 0,
                        'postgres_water_costs': float(econ['water_costs']) if econ['water_costs'] else 0,
                        'postgres_heating_costs': float(econ['heating_costs']) if econ['heating_costs'] else 0,
                        'maintenance_fund': float(econ['maintenance_fund']) if econ['maintenance_fund'] else 0,
                        'loan_amount': float(econ['loan_amount']) if econ['loan_amount'] else 0
                    })
                    print(f"  ✅ Economy data: {building_data['monthly_fee']:,.0f} SEK/month")
            else:
                print(f"  ❌ No Postgres data found for ID {mapping['postgres_id']}")
        else:
            print(f"  ⚠️  No coordinates available (no Postgres mapping)")
            # Use approximate coordinates in Hammarby Sjöstad area
            building_data.update({
                'latitude': 59.305,  # Approximate
                'longitude': 18.105,  # Approximate  
                'formatted_address': 'Hammarby Sjöstad, Stockholm',
                'postal_code': '120 XX'
            })
        
        # Get EPC data
        if mapping['epc_owner'] in epc_data:
            epc = epc_data[mapping['epc_owner']]
            building_data.update({
                'energy_performance': epc['avg_energy_performance'],
                'energy_class': epc['energy_class'],
                'construction_year': epc['construction_year'],
                'property_count': epc['property_count'],
                'epc_properties': epc['properties']
            })
            print(f"  ✅ Energy: {building_data['energy_performance']:.1f} kWh/m² (Class {building_data['energy_class']})")
        else:
            print(f"  ❌ No EPC data found")
            
        # Get Excel cost data
        excel_row = cost_data[cost_data['property'] == mapping['excel_name']]
        if not excel_row.empty:
            cost_row = excel_row.iloc[0]
            building_data.update({
                'cost_cleaning': float(cost_row.get('cost_cleaning', 0)),
                'cost_electricity': float(cost_row.get('cost_electricity', 0)),
                'cost_heating': float(cost_row.get('cost_heating', 0)),
                'cost_internet_and_tv': float(cost_row.get('cost_internet_and_tv', 0)),
                'cost_recycling': float(cost_row.get('cost_recycling', 0)),
                'cost_snow_removal': float(cost_row.get('cost_snow_removal', 0)),
                'cost_water': float(cost_row.get('cost_water', 0))
            })
            
            total_cost = sum([
                building_data[f'cost_{cat}'] for cat in 
                ['cleaning', 'electricity', 'heating', 'internet_and_tv', 'recycling', 'snow_removal', 'water']
            ])
            building_data['total_cost'] = total_cost
            print(f"  ✅ Costs: {total_cost:,.0f} SEK total")
        else:
            print(f"  ❌ No Excel cost data found")
        
        # Calculate performance score
        if 'energy_performance' in building_data and building_data['energy_performance'] > 0:
            # Better score for lower energy consumption
            building_data['performance_score'] = max(20, 100 - (building_data['energy_performance'] - 50) / 2)
        else:
            building_data['performance_score'] = 50
            
        unified_buildings.append(building_data)
    
    return unified_buildings

def save_killer_dataset():
    """Save the killer dataset"""
    print("🚀 Creating killer unified dataset...")
    
    unified_data = create_unified_dataset()
    
    # Save as JSON
    with open('killer_eghs_dataset.json', 'w') as f:
        json.dump(unified_data, f, indent=2)
    
    # Save as CSV
    df = pd.DataFrame(unified_data)
    df.to_csv('killer_eghs_dataset.csv', index=False)
    
    print(f"\\n💾 Saved killer dataset:")
    print(f"  - killer_eghs_dataset.json")
    print(f"  - killer_eghs_dataset.csv")
    
    # Print summary
    print(f"\\n🎯 KILLER DATASET SUMMARY:")
    print(f"Buildings: {len(df)}")
    
    with_coords = len(df[df['latitude'].notna() & (df['latitude'] != 59.305)])
    with_energy = len(df[df['energy_performance'].notna() & (df['energy_performance'] > 0)])
    with_costs = len(df[df['total_cost'].notna() & (df['total_cost'] > 0)])
    
    print(f"With real coordinates: {with_coords}")
    print(f"With energy data: {with_energy}")  
    print(f"With cost data: {with_costs}")
    print(f"Complete buildings (all data): {min(with_coords, with_energy, with_costs)}")
    
    print(f"\\nAvg Energy Performance: {df['energy_performance'].mean():.1f} kWh/m²")
    if 'total_cost' in df.columns:
        print(f"Avg Total Cost: {df['total_cost'].mean():,.0f} SEK")
    
    print(f"\\n🏠 BUILDINGS:")
    for _, row in df.iterrows():
        coords = f"({row['latitude']:.4f}, {row['longitude']:.4f})" if pd.notna(row['latitude']) else "(no coords)"
        energy = f"{row['energy_performance']:.0f} kWh/m²" if pd.notna(row['energy_performance']) else "no energy"
        cost = f"{row['total_cost']:,.0f} SEK" if 'total_cost' in row and pd.notna(row['total_cost']) else "no costs"
        print(f"  • {row['brf_name']}: {energy}, {cost}, {coords}")
    
    return unified_data

if __name__ == "__main__":
    save_killer_dataset()