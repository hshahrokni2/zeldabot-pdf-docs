#!/usr/bin/env python3
"""
Test both Qwen and Gemini agents with the fixed configuration
Uses existing PDF to avoid DB connection issues
"""
import os
import sys
import time
from pathlib import Path

# Add paths for agent imports  
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_qwen_agent(pdf_path: str):
    """Test fixed Qwen agent"""
    print("🤖 Testing Fixed Qwen 2.5-VL Agent...")
    
    from agents.qwen_agent import QwenAgent
    
    agent = QwenAgent()
    
    prompt = """Extract key information from this Swedish BRF annual report.
Focus on:
1. Organization details (name, org number, address)
2. Board members (especially chairman)
3. Financial data (assets, liabilities, cash)
4. Auditor information

Return valid JSON only, no markdown."""
    
    try:
        start_time = time.time()
        
        result = agent.extract_section(
            section="governance",
            prompt=prompt,
            pages_used=[1, 2, 3],
            pdf_path=pdf_path
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        print(f"   Latency: {latency_ms}ms")
        
        if result.get("success"):
            extracted_data = result.get("data", {})
            print(f"   ✅ Qwen extraction successful")
            print(f"      Data keys: {list(extracted_data.keys())}")
            return {
                "success": True,
                "data": extracted_data,
                "latency_ms": latency_ms,
                "agent": "qwen"
            }
        else:
            print(f"   ❌ Qwen extraction failed: {result.get('error')}")
            return {"success": False, "error": result.get("error")}
            
    except Exception as e:
        print(f"   ❌ Qwen agent error: {e}")
        return {"success": False, "error": str(e)}

def test_gemini_agent(pdf_path: str):
    """Test Gemini agent"""
    print("🤖 Testing Gemini 2.5 Pro Agent...")
    
    from agents.gemini_agent import GeminiAgent
    
    agent = GeminiAgent()
    
    prompt = """Extract key information from this Swedish BRF annual report.
Focus on:
1. Organization details (name, org number, address)
2. Board members (especially chairman)
3. Financial data (assets, liabilities, cash)
4. Auditor information

Return valid JSON only, no markdown."""
    
    try:
        start_time = time.time()
        
        result = agent.extract_section(
            section="governance",
            prompt=prompt,
            pages_used=[1, 2, 3],
            pdf_path=pdf_path
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        print(f"   Latency: {latency_ms}ms")
        
        if result.get("success"):
            extracted_data = result.get("data", {})
            print(f"   ✅ Gemini extraction successful")
            print(f"      Data keys: {list(extracted_data.keys())}")
            return {
                "success": True,
                "data": extracted_data,
                "latency_ms": latency_ms,
                "agent": "gemini"
            }
        else:
            print(f"   ❌ Gemini extraction failed: {result.get('error')}")
            return {"success": False, "error": result.get("error")}
            
    except Exception as e:
        print(f"   ❌ Gemini agent error: {e}")
        return {"success": False, "error": str(e)}

def compare_results(qwen_result, gemini_result):
    """Compare twin agent results"""
    print("\n📊 TWIN AGENT COMPARISON:")
    
    qwen_success = qwen_result.get("success", False)
    gemini_success = gemini_result.get("success", False)
    qwen_latency = qwen_result.get("latency_ms", 0)
    gemini_latency = gemini_result.get("latency_ms", 0)
    
    print(f"   Qwen Status: {'✅ Success' if qwen_success else '❌ Failed'} ({qwen_latency}ms)")
    print(f"   Gemini Status: {'✅ Success' if gemini_success else '❌ Failed'} ({gemini_latency}ms)")
    
    success_rate = sum([qwen_success, gemini_success])
    print(f"   Twin Success Rate: {success_rate}/2 ({success_rate * 50}%)")
    
    if qwen_success and gemini_success:
        print("\n🔍 Data Comparison:")
        qwen_data = qwen_result.get("data", {})
        gemini_data = gemini_result.get("data", {})
        
        # Look for common fields
        all_fields = set(qwen_data.keys()) | set(gemini_data.keys())
        for field in sorted(all_fields):
            qwen_val = qwen_data.get(field, "N/A")
            gemini_val = gemini_data.get(field, "N/A")
            print(f"   {field}: Qwen='{qwen_val}' | Gemini='{gemini_val}'")
    
    return {
        "qwen_success": qwen_success,
        "gemini_success": gemini_success,
        "success_rate": success_rate,
        "total_latency": qwen_latency + gemini_latency
    }

def main():
    print("🎯 FIXED TWIN AGENTS TEST - H100 SYSTEM")
    print("=" * 50)
    
    # Set environment
    os.environ["OLLAMA_URL"] = "http://127.0.0.1:11434"
    os.environ["QWEN_MODEL_TAG"] = "qwen2.5vl:7b"
    os.environ["GEMINI_API_KEY"] = "AIzaSyD0y92BjcnvUgRlWsA1oPSIWV5QaJcCrNw"
    os.environ["GEMINI_MODEL"] = "gemini-2.5-pro"
    
    # Use existing PDF
    pdf_path = "/tmp/83659_årsredovisning_göteborg_brf_erik_dahlbergsgatan_12.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF not found: {pdf_path}")
        return 1
    
    print(f"📁 Testing with: {os.path.basename(pdf_path)}")
    print(f"   Size: {os.path.getsize(pdf_path)} bytes")
    
    # Test both agents
    qwen_result = test_qwen_agent(pdf_path)
    gemini_result = test_gemini_agent(pdf_path)
    
    # Compare results
    comparison = compare_results(qwen_result, gemini_result)
    
    print(f"\n🎉 TWIN AGENT TEST COMPLETE")
    print(f"   Success Rate: {comparison['success_rate']}/2")
    print(f"   Total Processing Time: {comparison['total_latency']}ms")
    
    # Return 0 if at least one agent succeeded
    return 0 if comparison['success_rate'] > 0 else 1

if __name__ == "__main__":
    sys.exit(main())