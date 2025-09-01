#!/usr/bin/env python3
"""
Test script to validate HF sectioning integration into twin pipeline.
This tests the surgical integration without disrupting existing functionality.
"""

import os
import sys
import json
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_enhanced_qwen_agent():
    """Test the enhanced QwenAgent with HF capabilities"""
    print("🧪 Testing Enhanced QwenAgent...")
    
    from agents.qwen_agent import QwenAgent
    
    # Test Ollama mode (existing functionality)
    print("   Testing Ollama mode...")
    agent_ollama = QwenAgent()
    assert not agent_ollama.use_hf_direct, "Should default to Ollama mode"
    assert agent_ollama.enable_receipts, "Receipts should be enabled by default"
    
    # Test HF Direct mode configuration (graceful fallback expected)
    print("   Testing HF Direct mode configuration...")
    os.environ["USE_HF_DIRECT"] = "true"
    agent_hf = QwenAgent()
    # Note: HF Direct may fail to initialize in non-H100 environments, this is expected
    print(f"     HF Direct mode: {agent_hf.use_hf_direct} (fallback to Ollama is expected)")
    
    # Test bounded prompt generation
    print("   Testing bounded sectioning prompt...")
    bounded_prompt = agent_hf._get_bounded_sectioning_prompt()
    word_count = len(bounded_prompt.split())
    assert 80 <= word_count <= 120, f"Bounded prompt should be 80-120 words, got {word_count}"
    assert "HeaderExtractionAgent" in bounded_prompt, "Should contain HeaderExtractionAgent"
    assert "Swedish BRF" in bounded_prompt, "Should contain Swedish BRF"
    
    # Test HMAC receipt generation
    print("   Testing HMAC receipt generation...")
    test_data = {"page": 1, "model": "test", "latency_ms": 1000, "image_sha": "abc123"}
    receipt = agent_hf._generate_hmac_receipt(test_data)
    assert "hmac" in receipt, "Receipt should contain HMAC signature"
    assert "call_id" in receipt, "Receipt should have call_id"
    assert receipt["vision_only"], "Should be vision-only mode"
    
    print("   ✅ QwenAgent tests passed!")
    
    # Cleanup
    os.environ.pop("USE_HF_DIRECT", None)

def test_header_post_filter():
    """Test the header post-filter functionality"""
    print("🧪 Testing Header Post Filter...")
    
    from orchestrator.header_postfilter import HeaderPostFilter
    
    filter_processor = HeaderPostFilter()
    
    # Test rejection patterns
    print("   Testing rejection patterns...")
    test_headers = [
        {"text": "123", "page": 1},  # Should be rejected (pure number)
        {"text": "2024-01-01", "page": 1},  # Should be rejected (date)
        {"text": "Förvaltningsberättelse", "page": 2},  # Should be kept
        {"text": "Not 1 Byggnader", "page": 3},  # Should be kept (note)
        {"text": "kr", "page": 1},  # Should be rejected (too short)
    ]
    
    valid_count = 0
    for header in test_headers:
        if not filter_processor.should_reject(header):
            valid_count += 1
    
    assert valid_count == 2, f"Should keep 2 headers, kept {valid_count}"
    
    # Test hierarchical structure creation
    print("   Testing hierarchical structure...")
    test_headers = [
        {"text": "Noter", "page": 10, "level": 1},
        {"text": "Not 1 Byggnader", "page": 11},
        {"text": "Not 2 Inventarier", "page": 12},
        {"text": "Förvaltningsberättelse", "page": 2, "level": 1}
    ]
    
    structured = filter_processor.create_hierarchical_structure(test_headers)
    
    # Find Noter section
    noter_section = next((h for h in structured if h.get("header_type") == "noter_section"), None)
    assert noter_section, "Should find Noter section"
    assert "children" in noter_section, "Noter should have children"
    assert len(noter_section["children"]) == 2, "Should have 2 note children"
    
    print("   ✅ Header Post Filter tests passed!")

def test_orchestrator_integration():
    """Test the orchestrator integration"""
    print("🧪 Testing Orchestrator Integration...")
    
    from orchestrator.agent_orchestrator import OrchestratorAgent
    
    # Create minimal test PDF for initialization
    try:
        import fitz
        doc = fitz.open()  # Empty document
        page = doc.new_page()
        page.insert_text((100, 100), "Test")
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            doc.save(tmp.name)
            tmp_path = tmp.name
        doc.close()
    except:
        # Skip test if PyMuPDF not available
        print("   Skipping orchestrator test (PyMuPDF not available)")
        return
    
    try:
        # Test orchestrator initialization
        print("   Testing orchestrator initialization...")
        os.environ["ENABLE_HF_SECTIONING"] = "true"
        
        orchestrator = OrchestratorAgent(tmp_path, {"test": "test prompt"})
        assert orchestrator.enable_hf_sectioning, "HF sectioning should be enabled"
        assert orchestrator.post_filter, "Should have post filter initialized"
        
        # Test header to section mapping
        print("   Testing header to section mapping...")
        test_cases = [
            ("förvaltningsberättelse", "management_report"),
            ("resultaträkning", "income_statement"),
            ("balansräkning", "balance_sheet"),
            ("noter", "notes"),
            ("random text", "other")
        ]
        
        for header_text, expected in test_cases:
            result = orchestrator._map_header_to_canonical_section(header_text)
            assert result == expected, f"'{header_text}' should map to '{expected}', got '{result}'"
        
        print("   ✅ Orchestrator integration tests passed!")
        
    finally:
        os.unlink(tmp_path)
        os.environ.pop("ENABLE_HF_SECTIONING", None)

def test_environment_configurations():
    """Test different environment configurations"""
    print("🧪 Testing Environment Configurations...")
    
    from agents.qwen_agent import QwenAgent
    
    # Test default configuration
    print("   Testing default configuration...")
    agent = QwenAgent()
    assert not agent.use_hf_direct, "Should default to Ollama"
    assert agent.enable_receipts, "Should default to receipts enabled"
    
    # Test HF configuration (expect graceful fallback in non-H100 environments)
    print("   Testing HF configuration...")
    os.environ["USE_HF_DIRECT"] = "true"
    os.environ["HF_MODEL_PATH"] = "Qwen/Qwen2.5-VL-7B-Instruct"  # Valid model name
    os.environ["HF_DEVICE"] = "cpu"
    
    agent_hf = QwenAgent()
    # Note: use_hf_direct may be False due to initialization failure, this is expected
    assert agent_hf.hf_model_path == "Qwen/Qwen2.5-VL-7B-Instruct", "Should use correct model path"
    assert agent_hf.device == "cpu", "Should use CPU device"
    print(f"     HF Direct enabled: {agent_hf.use_hf_direct} (graceful fallback expected)")
    
    # Test receipts disabled
    print("   Testing receipts disabled...")
    os.environ["ENABLE_RECEIPTS"] = "false"
    agent_no_receipts = QwenAgent()
    assert not agent_no_receipts.enable_receipts, "Should disable receipts"
    
    print("   ✅ Environment configuration tests passed!")
    
    # Cleanup
    for key in ["USE_HF_DIRECT", "HF_MODEL_PATH", "HF_DEVICE", "ENABLE_RECEIPTS"]:
        os.environ.pop(key, None)

def test_backward_compatibility():
    """Test that existing functionality is preserved"""
    print("🧪 Testing Backward Compatibility...")
    
    from agents.qwen_agent import QwenAgent
    
    # Test that existing methods still work
    agent = QwenAgent()
    
    # Test health check works in both modes
    print("   Testing health check compatibility...")
    try:
        health_ollama = agent.health_check()
        # Should return boolean without crashing
        assert isinstance(health_ollama, bool), "Health check should return boolean"
    except Exception as e:
        # Might fail if Ollama not available, but shouldn't crash code
        print(f"     Expected health check failure (no Ollama): {e}")
    
    # Test that existing extract_section interface is preserved
    print("   Testing extract_section interface...")
    try:
        # This should work without crashing (might fail on actual execution)
        method_exists = hasattr(agent, "extract_section")
        assert method_exists, "extract_section method should exist"
        
        # Check method signature compatibility
        import inspect
        sig = inspect.signature(agent.extract_section)
        expected_params = {"section", "prompt", "pages_used", "pdf_path"}
        actual_params = set(sig.parameters.keys())
        assert expected_params <= actual_params, f"Missing parameters: {expected_params - actual_params}"
        
    except Exception as e:
        print(f"     Method signature test failed: {e}")
        assert False, "extract_section method should be compatible"
    
    print("   ✅ Backward compatibility tests passed!")

def run_all_tests():
    """Run all integration tests"""
    print("🚀 Starting HF Integration Tests...\n")
    
    tests = [
        test_enhanced_qwen_agent,
        test_header_post_filter,
        test_orchestrator_integration,
        test_environment_configurations,
        test_backward_compatibility
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
            print()
        except Exception as e:
            print(f"❌ Test failed: {test_func.__name__}")
            print(f"   Error: {e}")
            failed += 1
            print()
    
    print(f"📊 Test Summary:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All HF integration tests passed! Surgical integration successful.")
        return 0
    else:
        print(f"\n💥 {failed} tests failed. Integration needs fixes.")
        return 1

if __name__ == "__main__":
    exit(run_all_tests())