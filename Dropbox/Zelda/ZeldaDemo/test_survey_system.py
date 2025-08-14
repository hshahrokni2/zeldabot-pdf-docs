#!/usr/bin/env python3
"""
Test script for the Survey System components

This script validates that all survey system components work correctly
and can generate realistic test data for development and demonstration.
"""

import sys
import json
from datetime import datetime
from survey_system import (
    SurveySystem, UnlockLevel, SurveyResponse, 
    StockholmSuppliersDB, COST_CATEGORIES, SUPPLIER_CATEGORIES
)
from peer_comparison_system import PeerComparisonEngine, PeerComparisonUI

class MockSessionState:
    """Mock session state for testing."""
    def __init__(self):
        self._data = {
            'survey_responses': {},
            'unlock_level': UnlockLevel.NONE,
            'current_survey': {},
            'survey_progress': 0,
            'respondent_id': "test_user_123",
            'peer_data_unlocked': False
        }
    
    def __contains__(self, key):
        return key in self._data
    
    def __getattr__(self, name):
        if name.startswith('_'):
            return super().__getattribute__(name)
        return self._data.get(name)
    
    def __setattr__(self, name, value):
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            if not hasattr(self, '_data'):
                super().__setattr__('_data', {})
            self._data[name] = value

def test_suppliers_database():
    """Test the Stockholm suppliers database."""
    print("🧪 Testing Stockholm Suppliers Database...")
    
    db = StockholmSuppliersDB()
    
    for category in COST_CATEGORIES:
        suppliers = db.get_suppliers_by_category(category)
        alternatives = db.get_alternative_suppliers(category, "Test Supplier")
        
        print(f"  {SUPPLIER_CATEGORIES[category]}:")
        print(f"    Total suppliers: {len(suppliers)}")
        print(f"    Alternatives available: {len(alternatives)}")
        
        if suppliers:
            example = suppliers[0]
            print(f"    Example: {example.name} ({example.rating:.1f}/5)")
    
    print("✅ Suppliers database test completed\n")

def test_survey_system():
    """Test the survey system functionality.""" 
    print("🧪 Testing Survey System...")
    
    # Mock building data
    mock_buildings = [
        {
            "id": 1,
            "name": "Test BRF 1", 
            "address": "Test Address 1",
            "coordinates": {"lat": 59.305, "lng": 18.085}
        },
        {
            "id": 2, 
            "name": "Test BRF 2",
            "address": "Test Address 2", 
            "coordinates": {"lat": 59.306, "lng": 18.086}
        }
    ]
    
    session_state = MockSessionState()
    survey_system = SurveySystem(mock_buildings, session_state)
    
    # Test progress calculation
    test_survey_data = {
        'building_id': 1,
        'building_name': 'Test BRF 1',
        'costs': {
            'cleaning': 45000,
            'maintenance': 85000,
            'electricity': 120000
        },
        'suppliers': {
            'cleaning': 'Test Cleaning Co',
            'maintenance': 'Test Maintenance Co'
        },
        'satisfaction': {
            'cleaning': 4,
            'maintenance': 3
        },
        'contact_info': {
            'name': 'Test User',
            'email': 'test@example.com'
        }
    }
    
    progress = survey_system.calculate_progress(test_survey_data)
    unlock_level = survey_system.get_unlock_level(progress)
    
    print(f"  Survey progress: {progress:.1f}%")
    print(f"  Unlock level: {unlock_level.value}")
    print("✅ Survey system test completed\n")

def test_comparison_engine():
    """Test the peer comparison engine."""
    print("🧪 Testing Peer Comparison Engine...")
    
    # Mock building data
    mock_buildings = [
        {"id": 1, "name": "Test BRF 1", "coordinates": {"lat": 59.305, "lng": 18.085}}
    ]
    
    suppliers_db = StockholmSuppliersDB()
    engine = PeerComparisonEngine(mock_buildings, suppliers_db)
    
    # Test benchmark generation
    user_costs = {
        'cleaning': 55000,  # Higher than average
        'maintenance': 70000,  # Lower than average
        'electricity': 140000  # About average
    }
    
    benchmarks = engine.get_benchmark_data(user_costs, UnlockLevel.FULL)
    
    print(f"  Generated benchmarks for {len(benchmarks)} categories:")
    for category, benchmark in benchmarks.items():
        print(f"    {SUPPLIER_CATEGORIES[category]}:")
        print(f"      User cost: {benchmark.user_value:,.0f} SEK")
        print(f"      Peer median: {benchmark.peer_median:,.0f} SEK") 
        print(f"      Savings potential: {benchmark.savings_potential:,.0f} SEK")
    
    # Test insight generation
    mock_response = SurveyResponse(
        building_id=1,
        building_name="Test BRF 1",
        respondent_id="test_123",
        timestamp=datetime.now(),
        costs=user_costs,
        suppliers={'cleaning': 'Test Cleaner', 'maintenance': 'Test Maintenance'},
        satisfaction={'cleaning': 2, 'maintenance': 4},
        contact_info={'name': 'Test User', 'email': 'test@example.com'},
        unlock_level=UnlockLevel.FULL,
        completion_percentage=95.0
    )
    
    insights = engine.generate_insights(mock_response, benchmarks)
    
    print(f"  Generated {len(insights)} insights:")
    for insight in insights[:3]:  # Show first 3
        print(f"    {insight.insight_type}: {insight.title}")
        if insight.potential_savings:
            print(f"      Savings: {insight.potential_savings:,.0f} SEK/year")
    
    print("✅ Comparison engine test completed\n")

def generate_sample_data():
    """Generate sample data for demonstration."""
    print("📝 Generating sample survey data...")
    
    # Create sample completed survey
    sample_response = {
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "system_version": "1.0.0",
            "test_data": True
        },
        "survey_response": {
            "building_id": 2,
            "building_name": "BRF Hammarby Kaj",
            "respondent_id": "demo_user_456", 
            "completion_percentage": 92.0,
            "unlock_level": "full",
            "costs": {
                "cleaning": 52000,
                "maintenance": 78000,
                "snow_removal": 18000,
                "gardening": 41000,
                "electricity": 135000,
                "heating": 195000
            },
            "suppliers": {
                "cleaning": "Stockholm Fastighetsstäd AB",
                "maintenance": "Hammarby Fastighetsservice", 
                "snow_removal": "Vinterstaden AB",
                "gardening": "Hammarby Trädgård & Park",
                "electricity": "Stockholm Energioptimering",
                "heating": "Hammarby VVS & Värme"
            },
            "satisfaction": {
                "cleaning": 4,
                "maintenance": 5,
                "snow_removal": 3,
                "gardening": 4,
                "electricity": 3, 
                "heating": 4
            },
            "contact_info": {
                "name": "Demo User",
                "email": "demo@example.com",
                "phone": "08-123 45 67",
                "role": "Styrelseordförande"
            }
        }
    }
    
    # Save sample data
    with open("sample_survey_data.json", "w", encoding="utf-8") as f:
        json.dump(sample_response, f, indent=2, ensure_ascii=False)
    
    print("  Sample data saved to: sample_survey_data.json")
    print("✅ Sample data generation completed\n")

def main():
    """Run all tests."""
    print("🚀 Survey System Component Tests")
    print("=" * 50)
    
    try:
        test_suppliers_database()
        test_survey_system()
        test_comparison_engine()
        generate_sample_data()
        
        print("🎉 All tests completed successfully!")
        print("\nYou can now run the main application:")
        print("  python run_survey_app.py")
        print("  or")
        print("  streamlit run integrated_survey_map_app.py")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()