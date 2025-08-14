#!/usr/bin/env python3
"""
Update killer dataset with real Booli.se coordinates
"""

import json
import pandas as pd

# Real coordinates from booli.se searches
BOOLI_COORDINATES = {
    'Brf Havet': {
        'latitude': 59.305129,
        'longitude': 18.10341,
        'address': 'Sickla Kanalgata 21-43',
        'postal_code': '12067'
    },
    'Brf Holmen': {
        'latitude': 59.30356573,
        'longitude': 18.09921582,
        'address': 'Hammarby Allé 119, 127, Babordsgatan 8, Korphoppsgatan 21-23',
        'postal_code': '12064'
    },
    'Brf Sjöportalen 1': {
        'latitude': 59.30478262,  # Average of the 3 buildings
        'longitude': 18.10124035,
        'address': 'Babordsgatan 20, 22, Korphoppsgatan 33',
        'postal_code': '12064'
    },
    'Brf Sundet': {
        'latitude': 59.30305859,
        'longitude': 18.10965754,
        'address': 'Sickla Kanalgata 60, 62, 64',
        'postal_code': '12067'
    }
}

def update_killer_dataset():
    """Update the killer dataset with real coordinates"""
    print("🔄 Updating killer dataset with real Booli.se coordinates...")
    
    # Load existing dataset
    with open('killer_eghs_dataset.json', 'r') as f:
        buildings = json.load(f)
    
    print(f"📊 Loaded {len(buildings)} buildings")
    
    # Update coordinates for buildings that were missing them
    updated_count = 0
    for building in buildings:
        brf_name = building['brf_name']
        
        if brf_name in BOOLI_COORDINATES:
            coords = BOOLI_COORDINATES[brf_name]
            
            # Only update if coordinates are approximate (59.305, 18.105)
            if (building.get('latitude') == 59.305 and 
                building.get('longitude') == 18.105):
                
                print(f"✅ Updating {brf_name}:")
                print(f"   Old: {building['latitude']:.6f}, {building['longitude']:.6f}")
                print(f"   New: {coords['latitude']:.6f}, {coords['longitude']:.6f}")
                
                building.update({
                    'latitude': coords['latitude'],
                    'longitude': coords['longitude'],
                    'formatted_address': coords['address'],
                    'postal_code': coords['postal_code'],
                    'coordinates_source': 'booli.se'
                })
                updated_count += 1
            else:
                print(f"🔧 {brf_name} already has real coordinates from Postgres")
    
    print(f"\\n🎯 Updated {updated_count} buildings with Booli.se coordinates")
    
    # Save updated dataset
    with open('killer_eghs_dataset_with_booli_coords.json', 'w') as f:
        json.dump(buildings, f, indent=2)
    
    # Save as CSV too
    df = pd.DataFrame(buildings)
    df.to_csv('killer_eghs_dataset_with_booli_coords.csv', index=False)
    
    print("💾 Saved updated dataset:")
    print("  - killer_eghs_dataset_with_booli_coords.json")
    print("  - killer_eghs_dataset_with_booli_coords.csv")
    
    # Print summary
    real_coords_count = len(df[(df['latitude'] != 59.305) | (df['longitude'] != 18.105)])
    print(f"\\n📍 COORDINATE SUMMARY:")
    print(f"Total buildings: {len(df)}")
    print(f"With real coordinates: {real_coords_count}")
    print(f"Coverage: {real_coords_count/len(df)*100:.1f}%")
    
    print(f"\\n🗺️  FINAL BUILDING LOCATIONS:")
    for _, row in df.iterrows():
        source = row.get('coordinates_source', 'postgres' if row['latitude'] != 59.305 else 'approximate')
        print(f"  • {row['brf_name']}: {row['latitude']:.6f}, {row['longitude']:.6f} ({source})")
    
    return buildings

if __name__ == "__main__":
    update_killer_dataset()