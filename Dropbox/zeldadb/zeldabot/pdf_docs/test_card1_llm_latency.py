#!/usr/bin/env python3
"""
Card 1: TDD Test for LLM Latency
This test MUST be written FIRST before implementation
"""
import time
import json
import os
import sys
from typing import Dict, Any
import pytest

class TestLLMOrchestratorSelection:
    """Test suite for selecting best LLM for orchestration"""
    
    def test_llm_latency_for_orchestration(self):
        """Test that at least one LLM responds within acceptable latency"""
        from llm_orchestrator_selector import LLMOrchestratorSelector
        
        selector = LLMOrchestratorSelector()
        
        # Test orchestration prompt
        test_prompt = """Analyze this document structure and recommend extraction strategy:
        
        Sections found:
        1. Förvaltningsberättelse (pages 3-6)
           - Styrelsen (Board information)
           - Fastighetsfakta (Property facts)
        2. Resultaträkning (page 7)
        3. Balansräkning (pages 8-9)
        
        Return JSON with agents to use for each section."""
        
        # Test available LLMs
        results = selector.test_all_available_llms(test_prompt)
        
        # At least one model must be available
        assert len(results) > 0, "No LLM models available for orchestration"
        
        # Find working models
        working_models = [r for r in results if r["success"]]
        assert len(working_models) > 0, "No working LLM models found"
        
        # Check latency thresholds (relaxed for model loading)
        for result in working_models:
            if result["model"] == "gpt-oss":
                assert result["latency"] < 30, f"GPT-OSS too slow: {result['latency']}s"
            elif result["model"] == "qwen":
                assert result["latency"] < 60, f"Qwen too slow: {result['latency']}s (60s threshold for HF)"
            elif result["model"] == "gemini":
                assert result["latency"] < 30, f"Gemini too slow: {result['latency']}s"
        
        # Select best model
        best = selector.select_best_model(results)
        assert best is not None, "Failed to select best model"
        assert best["model"] in ["gpt-oss", "qwen", "gemini"], f"Unknown model selected: {best['model']}"
        
        print(f"\n✅ Selected {best['model']} for orchestration (latency: {best['latency']:.2f}s)")
    
    def test_llm_response_quality(self):
        """Test that selected LLM produces valid orchestration strategy"""
        from llm_orchestrator_selector import LLMOrchestratorSelector
        
        selector = LLMOrchestratorSelector()
        
        # Get best model
        best = selector.get_best_available_model()
        assert best is not None, "No model available"
        
        # Test orchestration response
        test_sections = {
            "Förvaltningsberättelse": {"pages": [3, 4, 5, 6], "subsections": ["Styrelsen", "Fastighetsfakta"]},
            "Resultaträkning": {"pages": [7]},
            "Balansräkning": {"pages": [8, 9]}
        }
        
        strategy = selector.create_extraction_strategy(test_sections, model=best["model"])
        
        # Verify response structure
        assert "agents_to_use" in strategy, "Missing agents_to_use in strategy"
        assert isinstance(strategy["agents_to_use"], dict), "agents_to_use should be a dict"
        
        # Verify correct agent selection
        assert "Förvaltningsberättelse" in strategy["agents_to_use"]
        agents_for_management = strategy["agents_to_use"]["Förvaltningsberättelse"]
        assert "governance_agent" in agents_for_management or "property_info_agent" in agents_for_management
        
        assert "Resultaträkning" in strategy["agents_to_use"]
        assert "income_statement_agent" in strategy["agents_to_use"]["Resultaträkning"]
        
        assert "Balansräkning" in strategy["agents_to_use"]
        assert "balance_sheet_agent" in strategy["agents_to_use"]["Balansräkning"]
        
        print(f"\n✅ {best['model']} produces valid orchestration strategy")
    
    def test_fallback_when_primary_unavailable(self):
        """Test that system falls back gracefully when primary model unavailable"""
        from llm_orchestrator_selector import LLMOrchestratorSelector
        
        selector = LLMOrchestratorSelector()
        
        # Should have fallback logic
        model = selector.get_model_with_fallback()
        assert model is not None, "No fallback model available"
        assert model["available"] is True
        assert model["model"] in ["gpt-oss", "qwen", "gemini"]
        
        print(f"\n✅ Fallback to {model['model']} successful")

def test_card1_requirements():
    """Main test runner for Card 1 TDD requirements"""
    print("=" * 60)
    print("CARD 1: TDD Test for LLM Orchestrator Selection")
    print("=" * 60)
    
    # This test should FAIL first (RED phase)
    # Then we implement LLMOrchestratorSelector to make it pass (GREEN phase)
    # Finally we refactor for production quality (REFACTOR phase)
    
    test_suite = TestLLMOrchestratorSelection()
    
    try:
        print("\n1. Testing LLM latency...")
        test_suite.test_llm_latency_for_orchestration()
        
        print("\n2. Testing response quality...")
        test_suite.test_llm_response_quality()
        
        print("\n3. Testing fallback mechanism...")
        test_suite.test_fallback_when_primary_unavailable()
        
        print("\n" + "=" * 60)
        print("✅ ALL CARD 1 TDD TESTS PASSED")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        print("\nThis is expected in RED phase of TDD.")
        print("Now implement LLMOrchestratorSelector to make tests pass.")
        return False
    except ImportError as e:
        print(f"\n❌ IMPORT ERROR: {e}")
        print("\nThis is expected - LLMOrchestratorSelector doesn't exist yet.")
        print("This confirms we're in RED phase of TDD.")
        return False

if __name__ == "__main__":
    success = test_card1_requirements()
    exit(0 if success else 1)