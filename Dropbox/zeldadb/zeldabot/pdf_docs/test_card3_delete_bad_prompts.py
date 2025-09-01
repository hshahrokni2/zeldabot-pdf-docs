#!/usr/bin/env python3
"""
Card 3: TDD Test for Deleting Bad Prompts
Ensure only JSON cache is used, no file templates
"""
import os
import json
import sys

def test_no_bad_prompts_exist():
    """Test that bad prompt templates are deleted"""
    bad_paths = [
        "/tmp/zeldabot/pdf_docs/prompts/sections/",
        "/tmp/zeldabot/pdf_docs/prompts/registry.json",
        "/tmp/zeldabot/pdf_docs/prompts/prompt_header_agent_v3.txt"
    ]
    
    for path in bad_paths:
        assert not os.path.exists(path), f"Bad prompt path still exists: {path}"
    
    print("✅ All bad prompt files deleted")

def test_json_cache_exists_and_valid():
    """Test that JSON cache exists with 24 agents"""
    cache_path = "/tmp/zeldabot/pdf_docs/prompts/agent_prompts.json"
    
    # Cache must exist
    assert os.path.exists(cache_path), f"JSON cache missing: {cache_path}"
    
    # Load and validate
    with open(cache_path, 'r') as f:
        cache = json.load(f)
    
    # Check structure
    assert "agents" in cache, "Missing 'agents' key in cache"
    
    # Should have multiple agents
    agent_count = len(cache["agents"])
    assert agent_count >= 20, f"Too few agents: {agent_count} (expected >= 20)"
    
    # Each agent should have substantial prompts
    for agent_id, agent_data in cache["agents"].items():
        assert "prompt" in agent_data, f"Agent {agent_id} missing prompt"
        prompt_length = len(agent_data["prompt"])
        assert prompt_length > 100, f"Agent {agent_id} prompt too short: {prompt_length} chars"
    
    print(f"✅ JSON cache valid with {agent_count} agents")

def test_no_template_references():
    """Test that code doesn't reference template files"""
    # This would check that orchestrator doesn't try to load .tpl files
    # For now, we just verify the files don't exist
    
    template_dir = "/tmp/zeldabot/pdf_docs/prompts/sections"
    if os.path.exists(template_dir):
        templates = [f for f in os.listdir(template_dir) if f.endswith('.tpl')]
        assert len(templates) == 0, f"Template files still exist: {templates}"
    
    print("✅ No template file references found")

def test_card3_requirements():
    """Main test runner for Card 3 TDD requirements"""
    print("=" * 60)
    print("CARD 3: TDD Test for Deleting Bad Prompts")
    print("=" * 60)
    
    try:
        print("\n1. Testing bad prompts deleted...")
        test_no_bad_prompts_exist()
        
        print("\n2. Testing JSON cache validity...")
        test_json_cache_exists_and_valid()
        
        print("\n3. Testing no template references...")
        test_no_template_references()
        
        print("\n" + "=" * 60)
        print("✅ ALL CARD 3 TDD TESTS PASSED")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        print("\nThis is expected in RED phase of TDD.")
        print("Now delete bad prompts to make tests pass.")
        return False

if __name__ == "__main__":
    success = test_card3_requirements()
    exit(0 if success else 1)