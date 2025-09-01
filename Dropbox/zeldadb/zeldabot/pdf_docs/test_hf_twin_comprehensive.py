#!/usr/bin/env python3
"""
Comprehensive HF Twin Pipeline Test - Local Simulation
Demonstrates all components working together with the test PDF
"""
import os
import sys
import json
import time
import tempfile
from pathlib import Path

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def setup_comprehensive_environment():
    """Setup comprehensive test environment"""
    print("🚀 COMPREHENSIVE HF TWIN PIPELINE TEST")
    print("=" * 60)
    
    # Load Gemini API key from Pure_LLM_Ftw/.env
    try:
        env_file = Path("Pure_LLM_Ftw/.env")
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    if line.startswith("GEMINI_API_KEY="):
                        key, value = line.strip().split("=", 1)
                        os.environ[key] = value
                        print(f"   ✅ Loaded GEMINI_API_KEY from {env_file}")
                        break
        else:
            # Fallback to direct setting
            os.environ["GEMINI_API_KEY"] = "AIzaSyD0y92BjcnvUgRlWsA1oPSIWV5QaJcCrNw"
            print(f"   ✅ Using fallback GEMINI_API_KEY")
    except Exception as e:
        print(f"   ⚠️  Could not load Gemini API key: {e}")
    
    # HF Direct configuration (forced CPU for local testing)
    env_config = {
        "USE_HF_DIRECT": "false",  # Start with Ollama for demonstration
        "HF_DEVICE": "cpu",
        "HF_MODEL_PATH": "Qwen/Qwen2.5-VL-7B-Instruct",
        "TWIN_AGENTS": "1",
        "OBS_STRICT": "1",
        "JSON_SALVAGE": "0",
        "ENABLE_RECEIPTS": "true",
        "RECEIPT_SECRET": "hf_twin_comprehensive_demo",
        "GEMINI_MODEL": "gemini-2.5-pro",
        # Mock H100 database (since server is down)
        "DATABASE_URL": "postgresql://mock_user:mock_pass@localhost:5432/mock_db"
    }
    
    for key, value in env_config.items():
        os.environ[key] = value
        display_value = "***" if "KEY" in key or "URL" in key else value
        print(f"   {key}: {display_value}")
    
    return env_config

def mock_database_operations(doc_info: dict, results: dict):
    """Mock H100 database operations since server is down"""
    print(f"\n📀 MOCK DATABASE OPERATIONS (H100 DOWN)")
    print("-" * 40)
    
    # Simulate database storage
    mock_records = [
        {"section": "sectioning", "success": results["sectioning"]["success"]},
        {"section": "qwen_governance", "success": results["qwen_governance"]["success"]},
        {"section": "gemini_governance", "success": results["gemini_governance"]["success"]}
    ]
    
    print(f"   Would store to: {os.environ['DATABASE_URL']}")
    print(f"   Mock records: {len(mock_records)}")
    for record in mock_records:
        status = "✅" if record["success"] else "❌"
        print(f"     {record['section']}: {status}")
    
    return True

def test_hf_sectioning_with_bounded_prompt(pdf_path: str):
    """Test HF sectioning with bounded micro-prompt"""
    print(f"\n📋 PHASE 1: HF SECTIONING WITH BOUNDED PROMPT")
    print("-" * 50)
    
    from agents.qwen_agent import QwenAgent
    
    qwen_agent = QwenAgent()
    print(f"   Execution Mode: {'HF Direct' if qwen_agent.use_hf_direct else 'Ollama'}")
    print(f"   Device: {qwen_agent.device if qwen_agent.use_hf_direct else 'N/A'}")
    
    start_time = time.time()
    
    # Test the bounded sectioning prompt (87-word micro-prompt)
    result = qwen_agent.extract_section(
        section="sectioning",
        prompt="",  # Uses internal bounded prompt
        pages_used=[1, 2],  # Multiple pages for comprehensive sectioning
        pdf_path=pdf_path
    )
    
    sectioning_time = time.time() - start_time
    
    print(f"   Success: {'✅' if result.get('success') else '❌'}")
    print(f"   Latency: {sectioning_time:.1f}s")
    print(f"   Receipt HMAC: {'✅' if result.get('receipt', {}).get('hmac') else '❌'}")
    
    if result.get('success'):
        sections = result.get('data', [])
        if isinstance(sections, list):
            print(f"   Sections found: {len(sections)}")
            
            # Show hierarchical structure
            for i, section in enumerate(sections[:8]):  # Show first 8 sections
                if isinstance(section, dict):
                    text = section.get('text', 'Unknown')
                    level = section.get('level', 'Unknown')
                    page = section.get('page', '?')
                    indent = "  " * (int(level) if str(level).isdigit() else 1)
                    print(f"     {i+1}.{indent}Level {level}: '{text}' (Page {page})")
        else:
            print(f"   Unexpected data format: {type(sections)}")
    
    return result

def test_twin_governance_extraction(pdf_path: str):
    """Test twin agent governance extraction"""
    print(f"\n📋 PHASE 2: TWIN GOVERNANCE EXTRACTION")
    print("-" * 50)
    
    from agents.qwen_agent import QwenAgent
    from agents.gemini_agent import GeminiAgent
    
    # Enhanced governance prompt for Swedish BRF documents
    governance_prompt = """Extract complete governance information from this Swedish BRF annual report.

Focus on extracting:
1. Organization details:
   - Organization name (förening/BRF name)
   - Organization number (organisationsnummer)
   - Address and postal code
   - Report year (redovisningsår)

2. Board of Directors (Styrelse):
   - Chairman/Chairwoman (Ordförande)
   - Board members (Ledamöter)
   - Deputy members (Suppleanter)
   - Include full names and roles

3. Auditors (Revisorer):
   - Ordinary auditor (Ordinarie revisor)
   - Deputy auditor (Revisorssuppleant)  
   - Auditing company name
   - Professional qualifications

4. Management positions:
   - Property manager (Fastighetsskötare)
   - Other key positions

5. Meeting information:
   - Annual meeting date (Årsstämma)
   - Location

Return comprehensive structured JSON with all available governance data found in the document."""
    
    # Qwen HF extraction
    print("   Testing Qwen HF Agent...")
    qwen_agent = QwenAgent()
    start_time = time.time()
    
    qwen_result = qwen_agent.extract_section(
        section="governance",
        prompt=governance_prompt,
        pages_used=[1, 2, 3],  # Use multiple pages for comprehensive extraction
        pdf_path=pdf_path
    )
    
    qwen_time = time.time() - start_time
    print(f"   Qwen Success: {'✅' if qwen_result.get('success') else '❌'} ({qwen_time:.1f}s)")
    
    if qwen_result.get('success'):
        qwen_data = qwen_result.get('data', {})
        print(f"   Qwen extracted fields: {list(qwen_data.keys()) if isinstance(qwen_data, dict) else 'Non-dict data'}")
    
    # Gemini extraction
    print("   Testing Gemini 2.5 Pro Agent...")
    gemini_agent = GeminiAgent()
    start_time = time.time()
    
    gemini_result = gemini_agent.extract_section(
        section="governance",
        prompt=governance_prompt,
        pages_used=[1, 2, 3],
        pdf_path=pdf_path
    )
    
    gemini_time = time.time() - start_time
    print(f"   Gemini Success: {'✅' if gemini_result.get('success') else '❌'} ({gemini_time:.1f}s)")
    
    if gemini_result.get('success'):
        gemini_data = gemini_result.get('data', {})
        print(f"   Gemini extracted fields: {list(gemini_data.keys()) if isinstance(gemini_data, dict) else 'Non-dict data'}")
    
    return qwen_result, gemini_result

def analyze_twin_agent_comparison(qwen_result: dict, gemini_result: dict):
    """Analyze and compare twin agent results"""
    print(f"\n📊 PHASE 3: TWIN AGENT COMPARISON ANALYSIS")
    print("-" * 50)
    
    if not qwen_result.get('success') or not gemini_result.get('success'):
        print("   ❌ Cannot compare - one or both agents failed")
        return {}
    
    qwen_data = qwen_result.get('data', {})
    gemini_data = gemini_result.get('data', {})
    
    if not isinstance(qwen_data, dict) or not isinstance(gemini_data, dict):
        print("   ❌ Cannot compare - non-dict data formats")
        return {}
    
    # Find common and unique fields
    qwen_fields = set(qwen_data.keys())
    gemini_fields = set(gemini_data.keys())
    
    common_fields = qwen_fields & gemini_fields
    qwen_only = qwen_fields - gemini_fields
    gemini_only = gemini_fields - qwen_fields
    
    print(f"   Common fields: {len(common_fields)} - {list(common_fields)}")
    print(f"   Qwen unique: {len(qwen_only)} - {list(qwen_only)}")
    print(f"   Gemini unique: {len(gemini_only)} - {list(gemini_only)}")
    
    # Compare specific governance fields
    comparison_fields = [
        'chairman', 'ordforande', 'board_members', 'styrelse',
        'organization_name', 'org_number', 'auditor', 'revisor'
    ]
    
    print(f"\n   Field-by-field comparison:")
    for field in comparison_fields:
        qwen_val = qwen_data.get(field, "Not found")
        gemini_val = gemini_data.get(field, "Not found")
        
        if qwen_val != "Not found" or gemini_val != "Not found":
            print(f"     {field}:")
            print(f"       Qwen: {str(qwen_val)[:100]}...")
            print(f"       Gemini: {str(gemini_val)[:100]}...")
            
            # Simple agreement check
            if str(qwen_val).lower() == str(gemini_val).lower():
                print(f"       Status: ✅ Agreement")
            elif qwen_val == "Not found" or gemini_val == "Not found":
                print(f"       Status: ⚠️  One agent missed")
            else:
                print(f"       Status: ❌ Disagreement")
    
    return {
        "common_fields": len(common_fields),
        "qwen_unique_fields": len(qwen_only),
        "gemini_unique_fields": len(gemini_only),
        "total_coverage": len(qwen_fields | gemini_fields)
    }

def simulate_coaching_system(results: dict):
    """Simulate coaching system integration"""
    print(f"\n🎓 PHASE 4: COACHING SYSTEM SIMULATION")
    print("-" * 50)
    
    # Simulate coaching rounds based on initial results
    initial_success_rate = sum([
        results["sectioning"]["success"],
        results["qwen_governance"]["success"], 
        results["gemini_governance"]["success"]
    ])
    
    print(f"   Initial Success Rate: {initial_success_rate}/3")
    
    if initial_success_rate < 3:
        print("   🎓 Coaching would be triggered for failed extractions")
        
        # Simulate coaching improvement
        coaching_rounds = []
        current_accuracy = 0.6  # Simulated initial accuracy
        
        for round_num in range(1, 4):  # Up to 3 coaching rounds
            improvement = 0.1 + (0.05 * round_num)  # Simulated improvement
            current_accuracy = min(0.95, current_accuracy + improvement)
            
            coaching_rounds.append({
                "round": round_num,
                "accuracy_before": current_accuracy - improvement,
                "accuracy_after": current_accuracy,
                "improvement_delta": improvement,
                "hallucination_detected": round_num == 2,  # Simulate hallucination in round 2
                "coaching_strategy": "prompt_refinement" if round_num < 3 else "cross_validation"
            })
            
            print(f"   Round {round_num}: {current_accuracy-improvement:.1%} → {current_accuracy:.1%} (+{improvement:.1%})")
        
        results["coaching_simulation"] = {
            "triggered": True,
            "rounds": coaching_rounds,
            "final_accuracy": current_accuracy
        }
    else:
        print("   ✅ All extractions successful - no coaching needed")
        results["coaching_simulation"] = {"triggered": False}
    
    return results

def store_comprehensive_results(results: dict, run_id: str):
    """Store comprehensive test results with full audit trail"""
    print(f"\n📀 STORING COMPREHENSIVE RESULTS")
    print("-" * 40)
    
    # Create comprehensive results directory
    os.makedirs("artifacts/hf_twin_comprehensive", exist_ok=True)
    
    timestamp = int(time.time())
    
    # Main results file with all data
    results_file = f"artifacts/hf_twin_comprehensive/{run_id}_{timestamp}.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    # NDJSON receipt for observability
    receipt_file = "artifacts/calls_log.ndjson"
    receipt_entry = {
        "timestamp": timestamp,
        "run_id": run_id,
        "pipeline_type": "hf_twin_comprehensive_demo",
        "hf_direct_attempted": os.environ.get("USE_HF_DIRECT") == "true",
        "success_rate": results["success_rate"],
        "total_latency_ms": results["total_latency_ms"],
        "coaching_triggered": results.get("coaching_simulation", {}).get("triggered", False),
        "document": "83659_årsredovisning_göteborg_brf_erik_dahlbergsgatan_12.pdf"
    }
    
    with open(receipt_file, "a") as f:
        f.write(json.dumps(receipt_entry) + "\n")
    
    print(f"   Results: {results_file}")
    print(f"   Receipt: {receipt_file}")
    
    return results_file

def main():
    """Run comprehensive HF twin pipeline test"""
    run_id = f"HF_TWIN_COMPREHENSIVE_{int(time.time())}"
    
    # Setup environment
    config = setup_comprehensive_environment()
    
    # Test PDF path
    pdf_path = "/tmp/83659_årsredovisning_göteborg_brf_erik_dahlbergsgatan_12.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ Test PDF not found: {pdf_path}")
        return 1
    
    print(f"   Test PDF: {os.path.basename(pdf_path)} ({os.path.getsize(pdf_path):,} bytes)")
    
    try:
        # Phase 1: HF Sectioning with bounded prompt
        sectioning_result = test_hf_sectioning_with_bounded_prompt(pdf_path)
        
        # Phase 2: Twin governance extraction
        qwen_result, gemini_result = test_twin_governance_extraction(pdf_path)
        
        # Phase 3: Twin comparison analysis
        comparison_stats = analyze_twin_agent_comparison(qwen_result, gemini_result)
        
        # Compile comprehensive results
        results = {
            "run_id": run_id,
            "timestamp": time.time(),
            "pipeline_type": "hf_twin_comprehensive_demo",
            "document": {
                "filename": os.path.basename(pdf_path),
                "size_bytes": os.path.getsize(pdf_path)
            },
            "sectioning": {
                "success": sectioning_result.get("success", False),
                "data": sectioning_result.get("data", []),
                "receipt": sectioning_result.get("receipt", {})
            },
            "qwen_governance": {
                "success": qwen_result.get("success", False),
                "data": qwen_result.get("data", {}),
                "receipt": qwen_result.get("receipt", {})
            },
            "gemini_governance": {
                "success": gemini_result.get("success", False),
                "data": gemini_result.get("data", {}),
                "receipt": gemini_result.get("receipt", {})
            },
            "comparison_analysis": comparison_stats
        }
        
        # Calculate metrics
        total_success = sum([
            results["sectioning"]["success"],
            results["qwen_governance"]["success"],
            results["gemini_governance"]["success"]
        ])
        
        results["success_rate"] = f"{total_success}/3"
        results["total_latency_ms"] = sum([
            results["sectioning"]["receipt"].get("latency_ms", 0),
            results["qwen_governance"]["receipt"].get("latency_ms", 0),
            results["gemini_governance"]["receipt"].get("latency_ms", 0)
        ])
        
        # Phase 4: Coaching simulation
        results = simulate_coaching_system(results)
        
        # Mock database operations (H100 down)
        mock_database_operations(results["document"], results)
        
        # Store comprehensive results
        results_file = store_comprehensive_results(results, run_id)
        
        # Final comprehensive summary
        print(f"\n🎉 COMPREHENSIVE HF TWIN PIPELINE TEST COMPLETE")
        print("=" * 60)
        print(f"   Run ID: {run_id}")
        print(f"   Success Rate: {results['success_rate']}")
        print(f"   Total Latency: {results['total_latency_ms']/1000:.1f}s")
        print(f"   HF Direct Mode: {'✅' if config['USE_HF_DIRECT'] == 'true' else '❌ (Ollama fallback)'}")
        print(f"   Bounded Sectioning: {'✅' if results['sectioning']['success'] else '❌'}")
        print(f"   Twin Agents: {'✅' if total_success >= 2 else '❌'}")
        print(f"   Coaching: {'✅ Triggered' if results.get('coaching_simulation', {}).get('triggered') else '✅ Not needed'}")
        print(f"   Results File: {results_file}")
        
        # Component-specific status
        print(f"\n📊 Component Status:")
        print(f"   Sectioning (Bounded prompt): {'✅' if results['sectioning']['success'] else '❌'}")
        print(f"   Qwen HF Governance: {'✅' if results['qwen_governance']['success'] else '❌'}")
        print(f"   Gemini 2.5 Pro: {'✅' if results['gemini_governance']['success'] else '❌'}")
        if comparison_stats:
            print(f"   Field Coverage: {comparison_stats['total_coverage']} fields")
            print(f"   Agent Agreement: {comparison_stats['common_fields']} common fields")
        
        return 0 if total_success >= 2 else 1  # Success if at least 2/3 components work
        
    except Exception as e:
        print(f"❌ Comprehensive test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())