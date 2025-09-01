#!/usr/bin/env python3
"""
Card 4: TDD Test for LLM Orchestrator
Test that orchestrator uses LLM (Qwen HF-Direct) instead of pure logic
"""
import json
import sys
import os
from typing import Dict, Any

class TestLLMOrchestrator:
    """Test suite for LLM-based orchestrator"""
    
    def test_orchestrator_uses_llm_not_logic(self):
        """Test that orchestrator makes LLM-based decisions"""
        sys.path.insert(0, '/tmp/zeldabot/pdf_docs')
        sys.path.insert(0, '/tmp/zeldabot/pdf_docs/src')
        
        from src.orchestrator.llm_orchestrator import LLMOrchestrator
        
        orchestrator = LLMOrchestrator(use_hf_direct=True)
        
        # Test with hierarchical section map from EnhancedSectionizerV2
        section_map = {
            "sections": [
                {
                    "name": "Förvaltningsberättelse",
                    "start_page": 3,
                    "end_page": 6,
                    "level": 1,
                    "subsections": [
                        {"name": "Styrelsen", "level": 2, "description": "Board information"},
                        {"name": "Fastighetsfakta", "level": 2, "description": "Property facts"}
                    ]
                },
                {
                    "name": "Resultaträkning",
                    "start_page": 7,
                    "end_page": 7,
                    "level": 1,
                    "subsections": []
                }
            ]
        }
        
        # LLM should analyze structure and decide agents
        strategy = orchestrator.create_extraction_strategy(section_map)
        
        # Verify it returns intelligent strategy
        assert "agents_to_use" in strategy, "Missing agents_to_use in strategy"
        assert isinstance(strategy["agents_to_use"], dict), "agents_to_use should be dict"
        
        # Should have reasoning from LLM
        assert "reasoning" in strategy, "Missing LLM reasoning"
        assert len(strategy["reasoning"]) > 50, "Reasoning too short - not from LLM"
        
        # Should map sections to appropriate agents
        assert "Förvaltningsberättelse" in strategy["agents_to_use"]
        assert "Resultaträkning" in strategy["agents_to_use"]
        
        print("✅ Orchestrator uses LLM for decisions")
    
    def test_orchestrator_adapts_to_structure(self):
        """Test that orchestrator adapts to different structures"""
        from src.orchestrator.llm_orchestrator import LLMOrchestrator
        
        orchestrator = LLMOrchestrator(use_hf_direct=True)
        
        # Test with unusual structure
        unusual_map = {
            "sections": [
                {
                    "name": "Noter",
                    "start_page": 15,
                    "end_page": 25,
                    "level": 1,
                    "subsections": [
                        {"name": "Not 1", "level": 3, "description": "Accounting principles"},
                        {"name": "Not 2", "level": 3, "description": "Property valuation"},
                        {"name": "Not 15", "level": 3, "description": "Board compensation"}
                    ]
                }
            ]
        }
        
        strategy = orchestrator.create_extraction_strategy(unusual_map)
        
        # Should recognize Noter needs special handling
        assert "Noter" in strategy["agents_to_use"]
        notes_agents = strategy["agents_to_use"]["Noter"]
        assert "notes_agent" in notes_agents or "noter_agent" in notes_agents
        
        # Should understand subsection context
        assert strategy.get("understands_subsections", False), "Should understand subsection context"
        
        print("✅ Orchestrator adapts to document structure")
    
    def test_orchestrator_no_hardcoded_logic(self):
        """Test that orchestrator doesn't use hardcoded mappings"""
        from src.orchestrator.llm_orchestrator import LLMOrchestrator
        
        orchestrator = LLMOrchestrator(use_hf_direct=True)
        
        # Check implementation doesn't have hardcoded section mappings
        assert not hasattr(orchestrator, 'SECTION_MAPPING'), "Should not have hardcoded mappings"
        assert hasattr(orchestrator, 'llm_analyze'), "Should have LLM analysis method"
        
        print("✅ No hardcoded logic found")

def test_card4_requirements():
    """Main test runner for Card 4 TDD requirements"""
    print("=" * 60)
    print("CARD 4: TDD Test for LLM Orchestrator")
    print("=" * 60)
    
    test_suite = TestLLMOrchestrator()
    
    try:
        print("\n1. Testing LLM-based decisions...")
        test_suite.test_orchestrator_uses_llm_not_logic()
        
        print("\n2. Testing adaptation to structure...")
        test_suite.test_orchestrator_adapts_to_structure()
        
        print("\n3. Testing no hardcoded logic...")
        test_suite.test_orchestrator_no_hardcoded_logic()
        
        print("\n" + "=" * 60)
        print("✅ ALL CARD 4 TDD TESTS PASSED")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        print("\nThis is expected in RED phase of TDD.")
        print("Now implement LLMOrchestrator to make tests pass.")
        return False
    except ImportError as e:
        print(f"\n❌ IMPORT ERROR: {e}")
        print("\nNeed to create llm_orchestrator.py")
        return False

if __name__ == "__main__":
    success = test_card4_requirements()
    exit(0 if success else 1)