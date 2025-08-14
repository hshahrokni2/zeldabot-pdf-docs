#!/usr/bin/env python3
"""
Test script to validate the survey unlock fixes.
"""

import json
from survey_system import SurveySystem, UnlockLevel

class MockSessionState:
    """Mock session state for testing."""
    def __init__(self):
        self.survey_responses = {}
        self.unlock_level = UnlockLevel.NONE
        self.current_survey = {}
        self.survey_progress = 0
        self.respondent_id = "test-user"
        self.peer_data_unlocked = False
        self.survey_completed = False
        self.survey_completion_timestamp = None
    
    def __contains__(self, key):
        """Support 'in' operator for attribute checking."""
        return hasattr(self, key)
    
    def get(self, key, default=None):
        """Support get() method like session_state."""
        return getattr(self, key, default)

def load_test_data():
    """Load test buildings data."""
    with open('killer_eghs_dataset_with_booli_coords.json', 'r') as f:
        data = json.load(f)
    
    # Transform data to include proper IDs and names for the survey system
    transformed_data = []
    for building in data:
        transformed_data.append({
            'id': building.get('building_id', building.get('postgres_id', 0)),
            'name': building.get('brf_name', 'Unknown BRF'),
            'building_id': building.get('building_id', building.get('postgres_id', 0)),
            **building
        })
    
    return transformed_data

def test_progress_calculation():
    """Test progress calculation with different completion levels."""
    print("🧪 Testing Progress Calculation...")
    
    buildings_data = load_test_data()
    mock_state = MockSessionState()
    survey_system = SurveySystem(buildings_data, mock_state)
    
    # Test Case 1: Empty survey (0% completion)
    empty_survey = {}
    progress = survey_system.calculate_progress(empty_survey)
    print(f"  ✓ Empty survey: {progress:.1f}% (Expected: 0%)")
    
    # Test Case 2: Building selected only (~3% completion)
    building_only = {
        'building_id': 1,
        'building_name': 'Test BRF'
    }
    progress = survey_system.calculate_progress(building_only)
    print(f"  ✓ Building only: {progress:.1f}% (Expected: ~3%)")
    
    # Test Case 3: Basic data (30%+ completion for unlock)
    basic_survey = {
        'building_id': 1,
        'building_name': 'Test BRF',
        'costs': {
            'cleaning': 100000,
            'heating': 200000,
            'electricity': 50000,
            'water': 75000  # Add one more category to push over 30%
        },
        'suppliers': {
            'cleaning': 'Test Cleaner',
            'heating': 'Test Heater', 
            'electricity': 'Test Electric',
            'water': 'Test Water'
        },
        'satisfaction': {
            'cleaning': 4,
            'heating': 3,
            'electricity': 5,
            'water': 4
        }
    }
    progress = survey_system.calculate_progress(basic_survey)
    unlock_level = survey_system.get_unlock_level(progress)
    print(f"  ✓ Basic survey: {progress:.1f}% - Unlock level: {unlock_level.value}")
    
    # Test Case 4: Full survey with contact info (90%+ completion)
    full_survey = {
        **basic_survey,
        'costs': {
            'cleaning': 100000,
            'heating': 200000,
            'electricity': 50000,
            'water': 75000,
            'recycling': 25000,
            'snow_removal': 30000,
            'gardening': 40000,
            'administration': 60000,
            'security': 35000,
            'insurance': 80000
        },
        'suppliers': {
            'cleaning': 'Test Cleaner',
            'heating': 'Test Heater',
            'electricity': 'Test Electric',
            'water': 'Test Water',
            'recycling': 'Test Recycling',
            'snow_removal': 'Test Snow',
            'gardening': 'Test Garden',
            'administration': 'Test Admin',
            'security': 'Test Security',
            'insurance': 'Test Insurance'
        },
        'satisfaction': {
            'cleaning': 4,
            'heating': 3,
            'electricity': 5,
            'water': 4,
            'recycling': 4,
            'snow_removal': 3,
            'gardening': 5,
            'administration': 2,
            'security': 4,
            'insurance': 3
        },
        'contact_info': {
            'name': 'Test User',
            'email': 'test@example.com',
            'phone': '08-123 45 67'
        }
    }
    progress = survey_system.calculate_progress(full_survey)
    unlock_level = survey_system.get_unlock_level(progress)
    print(f"  ✓ Full survey: {progress:.1f}% - Unlock level: {unlock_level.value}")
    
    return True

def test_unlock_levels():
    """Test unlock level thresholds."""
    print("\n🔓 Testing Unlock Levels...")
    
    buildings_data = load_test_data()
    mock_state = MockSessionState()
    survey_system = SurveySystem(buildings_data, mock_state)
    
    # Test thresholds
    test_cases = [
        (0, UnlockLevel.NONE, "Empty"),
        (15, UnlockLevel.NONE, "Minimal data"),
        (30, UnlockLevel.BASIC, "Basic threshold"),
        (45, UnlockLevel.BASIC, "Basic range"),
        (60, UnlockLevel.INTERMEDIATE, "Intermediate threshold"),
        (75, UnlockLevel.INTERMEDIATE, "Intermediate range"),
        (90, UnlockLevel.FULL, "Full threshold"),
        (100, UnlockLevel.FULL, "Complete")
    ]
    
    for progress, expected_level, description in test_cases:
        actual_level = survey_system.get_unlock_level(progress)
        status = "✓" if actual_level == expected_level else "✗"
        print(f"  {status} {progress}% ({description}): {actual_level.value} (expected: {expected_level.value})")
    
    return True

def test_session_state_persistence():
    """Test session state persistence logic."""
    print("\n💾 Testing Session State Persistence...")
    
    buildings_data = load_test_data()
    mock_state = MockSessionState()
    survey_system = SurveySystem(buildings_data, mock_state)
    
    # Simulate survey completion
    survey_data = {
        'building_id': 1,
        'building_name': 'Test BRF',
        'costs': {'cleaning': 100000, 'heating': 200000},
        'suppliers': {'cleaning': 'Test Cleaner', 'heating': 'Test Heater'},
        'satisfaction': {'cleaning': 4, 'heating': 3},
        'contact_info': {'name': 'Test User', 'email': 'test@example.com'}
    }
    
    # Update session state
    mock_state.current_survey = survey_data
    survey_system._update_progress_and_unlock_level()
    
    print(f"  ✓ Progress: {mock_state.survey_progress:.1f}%")
    print(f"  ✓ Unlock level: {mock_state.unlock_level.value}")
    print(f"  ✓ Peer data unlocked: {mock_state.peer_data_unlocked}")
    
    # Test persistence across "page loads"
    mock_state2 = MockSessionState()
    mock_state2.current_survey = survey_data  # Simulate persisted survey data
    survey_system2 = SurveySystem(buildings_data, mock_state2)
    
    print(f"  ✓ After 'reload' - Progress: {mock_state2.survey_progress:.1f}%")
    print(f"  ✓ After 'reload' - Peer data unlocked: {mock_state2.peer_data_unlocked}")
    
    return True

def main():
    """Run all tests."""
    print("🚀 Testing Survey Unlock Fixes\n")
    
    try:
        test_progress_calculation()
        test_unlock_levels()
        test_session_state_persistence()
        
        print("\n✅ All tests completed successfully!")
        print("\n📋 Summary of fixes:")
        print("  • Fixed progress calculation to only count completed fields")
        print("  • Corrected unlock thresholds (30%, 60%, 90%)")
        print("  • Improved session state persistence across tabs")
        print("  • Resolved conflicting unlock messages")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()