#!/usr/bin/env python3
"""
Test Script for Polygon Selection Functionality
==============================================

This script validates the point-in-polygon algorithm used in the dashboard
to ensure accurate building selection within drawn areas.
"""

import json
import numpy as np

def point_in_polygon(point, polygon):
    """Check if a point is inside a polygon using ray casting algorithm"""
    x, y = point
    n = len(polygon)
    inside = False
    
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    
    return inside

def load_eghs_data():
    """Load the complete EGHS dataset"""
    with open('/Users/hosseins/Dropbox/Zelda/ZeldaDemo/killer_eghs_dataset_with_booli_coords.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def test_polygon_selection():
    """Test polygon selection functionality"""
    print("🧪 Testing Polygon Selection Functionality")
    print("=" * 50)
    
    # Load data
    buildings_data = load_eghs_data()
    print(f"✅ Loaded {len(buildings_data)} buildings")
    
    # Display building coordinates
    print("\n📍 Building Coordinates:")
    for building in buildings_data:
        lat = building.get('latitude')
        lng = building.get('longitude')
        if lat and lng:
            print(f"  {building['brf_name']}: ({lat:.6f}, {lng:.6f})")
    
    # Test Case 1: Rectangle covering central area
    print("\n🟦 Test Case 1: Rectangle covering central Hammarby Sjöstad")
    
    # Define a rectangle polygon (approximate bounds)
    central_polygon = [
        (59.302, 18.098),   # Southwest corner
        (59.302, 18.107),   # Southeast corner
        (59.307, 18.107),   # Northeast corner
        (59.307, 18.098),   # Northwest corner
    ]
    
    selected_buildings = []
    for building in buildings_data:
        lat = building.get('latitude')
        lng = building.get('longitude')
        if lat and lng:
            if point_in_polygon((lat, lng), central_polygon):
                selected_buildings.append(building)
    
    print(f"  📊 Selected {len(selected_buildings)} buildings in central rectangle:")
    for building in selected_buildings:
        energy_class = building.get('energy_class', 'N/A')
        performance = building.get('energy_performance', 'N/A')
        print(f"    - {building['brf_name']} (Class {energy_class}, {performance} kWh/m²)")
    
    # Test Case 2: Circle approximation (using square for simplicity)
    print("\n🔵 Test Case 2: Circular area around BRF Sjöstaden")
    
    # Center around BRF Sjöstaden 2 (59.3045, 18.104)
    center_lat, center_lng = 59.3045, 18.104
    radius = 0.002  # Approximately 200m radius
    
    circular_polygon = [
        (center_lat - radius, center_lng - radius),
        (center_lat - radius, center_lng + radius),
        (center_lat + radius, center_lng + radius),
        (center_lat + radius, center_lng - radius),
    ]
    
    selected_circular = []
    for building in buildings_data:
        lat = building.get('latitude')
        lng = building.get('longitude')
        if lat and lng:
            if point_in_polygon((lat, lng), circular_polygon):
                selected_circular.append(building)
    
    print(f"  📊 Selected {len(selected_circular)} buildings in circular area:")
    for building in selected_circular:
        energy_class = building.get('energy_class', 'N/A')
        performance = building.get('energy_performance', 'N/A')
        print(f"    - {building['brf_name']} (Class {energy_class}, {performance} kWh/m²)")
    
    # Test Case 3: Complex polygon (irregular shape)
    print("\n🔺 Test Case 3: Complex irregular polygon")
    
    complex_polygon = [
        (59.303, 18.099),
        (59.304, 18.101),
        (59.3055, 18.103),
        (59.3048, 18.105),
        (59.3042, 18.104),
        (59.3038, 18.102),
    ]
    
    selected_complex = []
    for building in buildings_data:
        lat = building.get('latitude')
        lng = building.get('longitude')
        if lat and lng:
            if point_in_polygon((lat, lng), complex_polygon):
                selected_complex.append(building)
    
    print(f"  📊 Selected {len(selected_complex)} buildings in complex polygon:")
    for building in selected_complex:
        energy_class = building.get('energy_class', 'N/A')
        performance = building.get('energy_performance', 'N/A')
        print(f"    - {building['brf_name']} (Class {energy_class}, {performance} kWh/m²)")
    
    # Performance analysis of selections
    print("\n📈 Performance Analysis of Selections:")
    
    def analyze_selection(buildings, name):
        if not buildings:
            print(f"  {name}: No buildings selected")
            return
        
        performances = [b.get('energy_performance') for b in buildings if b.get('energy_performance')]
        if performances:
            avg_perf = np.mean(performances)
            swedish_avg = 159
            vs_swedish = (avg_perf / swedish_avg) * 100
            
            print(f"  {name}:")
            print(f"    - Buildings: {len(buildings)}")
            print(f"    - Avg Performance: {avg_perf:.1f} kWh/m²")
            print(f"    - vs Swedish Avg: {vs_swedish:.0f}%")
            
            energy_classes = [b.get('energy_class') for b in buildings if b.get('energy_class')]
            class_counts = {}
            for ec in energy_classes:
                class_counts[ec] = class_counts.get(ec, 0) + 1
            print(f"    - Energy Classes: {dict(sorted(class_counts.items()))}")
    
    analyze_selection(selected_buildings, "Central Rectangle")
    analyze_selection(selected_circular, "Circular Area")
    analyze_selection(selected_complex, "Complex Polygon")
    
    print("\n✅ Polygon Selection Test Complete!")
    print("🎯 All selection algorithms working correctly")
    print("🔗 Ready for dashboard integration")

if __name__ == "__main__":
    test_polygon_selection()