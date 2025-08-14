#!/usr/bin/env python3
"""
Validation script to test core functionality without Streamlit.
"""

import json
import sys
from pathlib import Path

def test_data_loading():
    """Test if data file can be loaded."""
    try:
        data_file = "/Users/hosseins/Dropbox/Zelda/ZeldaDemo/hammarby_map_visualization_data.json"
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        buildings = data.get('buildings', [])
        print(f"✅ Data loaded successfully: {len(buildings)} buildings")
        return buildings
    except Exception as e:
        print(f"❌ Data loading failed: {e}")
        return None

def test_imports():
    """Test if all required modules can be imported."""
    modules_to_test = [
        ('streamlit', 'Streamlit web framework'),
        ('folium', 'Interactive maps'),
        ('plotly', 'Chart visualization'),
        ('pandas', 'Data processing'),
        ('numpy', 'Numerical computing'),
        ('shapely', 'Geometric operations'),
        ('streamlit_folium', 'Streamlit-Folium integration')
    ]
    
    all_good = True
    for module, description in modules_to_test:
        try:
            __import__(module.replace('-', '_'))
            print(f"✅ {module} - {description}")
        except ImportError as e:
            print(f"❌ {module} - {description} - {e}")
            all_good = False
    
    return all_good

def test_polygon_handler(buildings):
    """Test polygon selection functionality."""
    try:
        from polygon_selection_handler import PolygonSelectionHandler
        handler = PolygonSelectionHandler(buildings)
        
        # Test rectangle selection
        test_bounds = {
            'north': 59.308,
            'south': 59.302,
            'east': 18.110,
            'west': 18.080
        }
        
        selected = handler.select_buildings_in_rectangle(test_bounds)
        print(f"✅ Polygon handler working: {len(selected)} buildings selected in test area")
        
        # Test selection summary
        if selected:
            handler.add_selection(selected, "test")
            summary = handler.get_selection_summary()
            print(f"✅ Selection summary generated: {summary['selection_info']['total_buildings']} buildings")
        
        return True
    except Exception as e:
        print(f"❌ Polygon handler failed: {e}")
        return False

def test_folium_basic():
    """Test basic Folium map creation."""
    try:
        import folium
        
        # Create basic map
        m = folium.Map(location=[59.305, 18.085], zoom_start=14)
        
        # Add test marker
        folium.CircleMarker(
            location=[59.305, 18.085],
            radius=5,
            popup="Test marker"
        ).add_to(m)
        
        # Test if map can generate HTML
        html = m._repr_html_()
        if len(html) > 1000:  # Basic check that HTML is generated
            print("✅ Folium map creation and HTML generation working")
            return True
        else:
            print("❌ Folium map HTML generation seems insufficient")
            return False
            
    except Exception as e:
        print(f"❌ Folium basic test failed: {e}")
        return False

def test_file_structure():
    """Test if all required files are present."""
    required_files = [
        'hammarby_map_visualization_data.json',
        'hammarby_interactive_map.py',
        'polygon_selection_handler.py',
        'launch_interactive_map.py',
        'requirements.txt'
    ]
    
    base_path = Path("/Users/hosseins/Dropbox/Zelda/ZeldaDemo")
    all_present = True
    
    for file_name in required_files:
        file_path = base_path / file_name
        if file_path.exists():
            print(f"✅ {file_name}")
        else:
            print(f"❌ {file_name} - MISSING")
            all_present = False
    
    return all_present

def main():
    """Run all validation tests."""
    print("🔍 Hammarby Sjöstad Interactive Map - Setup Validation")
    print("=" * 60)
    
    # Test file structure
    print("\n📁 File Structure:")
    files_ok = test_file_structure()
    
    # Test imports
    print("\n📦 Module Imports:")
    imports_ok = test_imports()
    
    # Test data loading
    print("\n📊 Data Loading:")
    buildings = test_data_loading()
    data_ok = buildings is not None
    
    # Test Folium basic functionality
    print("\n🗺️  Folium Basic Test:")
    folium_ok = test_folium_basic()
    
    # Test polygon handler
    print("\n🔺 Polygon Selection Handler:")
    polygon_ok = False
    if buildings:
        polygon_ok = test_polygon_handler(buildings)
    else:
        print("❌ Skipped due to data loading failure")
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 VALIDATION SUMMARY:")
    print("=" * 60)
    
    tests = [
        ("File Structure", files_ok),
        ("Module Imports", imports_ok),
        ("Data Loading", data_ok),
        ("Folium Maps", folium_ok),
        ("Polygon Selection", polygon_ok)
    ]
    
    all_passed = True
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! The interactive map is ready to run.")
        print("\nTo start the application:")
        print("  python launch_interactive_map.py")
        print("  OR")
        print("  streamlit run hammarby_interactive_map.py")
    else:
        print("⚠️  SOME TESTS FAILED. Please resolve issues before running the full application.")
    
    print("=" * 60)
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)