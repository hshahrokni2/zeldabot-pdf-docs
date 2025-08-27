#!/usr/bin/env python3
"""
Direct H100 Twin Agent Pipeline - Bypasses orchestrator
Direct Qwen via Ollama + Gemini with side-by-side governance extraction
"""
import os
import sys
import json
import psycopg2
import tempfile
import base64
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.qwen_agent import QwenAgent
from agents.gemini_agent import GeminiAgent
from utils.acceptance_tests import run_acceptance_gates, CANARY_GATES

def load_governance_prompt() -> str:
    """Load Swedish governance prompt template"""
    prompt_path = Path(__file__).parent.parent / "prompts/sections/governance.sv.tpl"
    if prompt_path.exists():
        return prompt_path.read_text(encoding='utf-8')
    else:
        # Fallback Swedish governance prompt
        return """Extrahera styrelseinformation från denna svenska BRF årsredovisning.
Sök efter styrelserelaterade termer: styrelseordförande, styrelseledamöter, suppleanter, revisor, revisionsföretag, årsstämma.
Identifiera namn på personer och företag.

ENDAST JSON - Respond ONLY with a SINGLE minified JSON object:
{"chairman": "", "board_members": [], "auditor_name": "", "audit_firm": "", "annual_meeting_date": ""}"""

def pdf_to_images(pdf_binary: bytes) -> List[str]:
    """Convert PDF to base64 encoded images"""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=pdf_binary, filetype="pdf")
        images = []
        
        for page_num in range(min(5, len(doc))):  # First 5 pages
            page = doc[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))  # 2x zoom
            img_data = pix.tobytes("png")
            b64_img = base64.b64encode(img_data).decode()
            images.append(b64_img)
        
        doc.close()
        return images
    except Exception as e:
        print(f"❌ PDF conversion error: {e}")
        return []

def extract_governance_twin(pdf_binary: bytes, filename: str) -> Dict[str, Any]:
    """Extract governance using twin agents (Qwen + Gemini)"""
    print(f"🎯 Twin governance extraction: {filename}")
    
    # Convert PDF to images
    images = pdf_to_images(pdf_binary)
    if not images:
        return {"error": "PDF conversion failed"}
    
    # Load governance prompt
    prompt = load_governance_prompt()
    
    # Initialize agents
    qwen_agent = QwenAgent()
    gemini_agent = GeminiAgent()
    
    results = {"qwen": {}, "gemini": {}, "comparison": {}}
    
    # Extract with Qwen
    try:
        print("🔍 Qwen extraction...")
        # Need to create temporary PDF file for agent interface
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(pdf_binary)
            tmp_path = tmp_file.name
        
        qwen_result = qwen_agent.extract_section("governance", prompt, [1, 2, 3, 4, 5], tmp_path)
        # Extract the data part from agent response  
        if "extracted_data" in qwen_result:
            results["qwen"] = qwen_result["extracted_data"]
        elif "data" in qwen_result:
            results["qwen"] = qwen_result["data"]
        else:
            results["qwen"] = qwen_result
        print(f"✅ Qwen raw: {json.dumps(qwen_result, ensure_ascii=False)[:200]}...")
        print(f"✅ Qwen extracted: {json.dumps(results['qwen'], ensure_ascii=False)[:100]}...")
        
        # Cleanup
        os.unlink(tmp_path)
    except Exception as e:
        print(f"❌ Qwen failed: {e}")
        results["qwen"] = {"error": str(e)}
    
    # Extract with Gemini  
    try:
        print("🔍 Gemini extraction...")
        # Need to create temporary PDF file for agent interface
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(pdf_binary)
            tmp_path = tmp_file.name
        
        gemini_result = gemini_agent.extract_section("governance", prompt, [1, 2, 3, 4, 5], tmp_path)
        # Extract the data part from agent response (Gemini wraps in receipt)
        if "extracted_data" in gemini_result:
            results["gemini"] = gemini_result["extracted_data"]
        elif "data" in gemini_result:
            results["gemini"] = gemini_result["data"]
        else:
            results["gemini"] = gemini_result
        print(f"✅ Gemini raw: {json.dumps(gemini_result, ensure_ascii=False)[:200]}...")
        print(f"✅ Gemini extracted: {json.dumps(results['gemini'], ensure_ascii=False)[:100]}...")
        
        # Cleanup
        os.unlink(tmp_path)
    except Exception as e:
        print(f"❌ Gemini failed: {e}")
        results["gemini"] = {"error": str(e)}
    
    # Side-by-side comparison
    qwen_data = results["qwen"] if "error" not in results["qwen"] else {}
    gemini_data = results["gemini"] if "error" not in results["gemini"] else {}
    
    results["comparison"] = {
        "chairman_match": qwen_data.get("chairman", "") == gemini_data.get("chairman", ""),
        "auditor_match": qwen_data.get("auditor_name", "") == gemini_data.get("auditor_name", ""),
        "qwen_board_count": len(qwen_data.get("board_members", [])),
        "gemini_board_count": len(gemini_data.get("board_members", []))
    }
    
    return results

def run_direct_twin_test(run_id: str, limit: int = 1) -> Dict[str, Any]:
    """Run direct twin agent test on H100 database"""
    print(f"🚀 DIRECT H100 TWIN PIPELINE: {run_id}")
    
    # Connect to H100 database
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cursor = conn.cursor()
    
    # Get documents
    cursor.execute("""
        SELECT id, filename, pdf_binary 
        FROM arsredovisning_documents 
        WHERE pdf_binary IS NOT NULL 
        ORDER BY created_at DESC 
        LIMIT %s
    """, (limit,))
    
    docs = cursor.fetchall()
    if not docs:
        print("❌ No documents found")
        return {"error": "No documents found"}
    
    print(f"📊 Processing {len(docs)} documents")
    
    results = []
    for doc_id, filename, pdf_binary in docs:
        print(f"\n🔍 Processing: {filename}")
        
        # Extract governance with twin agents
        governance_result = extract_governance_twin(pdf_binary, filename)
        
        # Store results in database
        cursor.execute("""
            UPDATE arsredovisning_documents 
            SET extraction_data = COALESCE(extraction_data, '{}') || %s::jsonb
            WHERE id = %s
        """, (json.dumps({"governance": governance_result}), doc_id))
        
        results.append({
            "doc_id": doc_id,
            "filename": filename,
            "governance": governance_result
        })
    
    conn.commit()
    conn.close()
    
    return {"run_id": run_id, "results": results}

def print_governance_side_by_side(results: List[Dict[str, Any]]):
    """Print governance extraction side-by-side"""
    for result in results:
        print(f"\n=== GOVERNANCE — SIDE BY SIDE: {result['filename']} ===")
        gov = result["governance"]
        
        qwen = gov.get("qwen", {})
        gemini = gov.get("gemini", {})
        
        def pick(d, k): 
            return str(d.get(k) or "")
        
        print(f"Chair:    Qwen: {pick(qwen,'chairman'):30} | Gemini: {pick(gemini,'chairman')}")
        print(f"Auditor:  Qwen: {pick(qwen,'auditor_name'):30} | Gemini: {pick(gemini,'auditor_name')}")
        print(f"AuditCo:  Qwen: {pick(qwen,'audit_firm'):30} | Gemini: {pick(gemini,'audit_firm')}")
        print(f"Board:    Qwen: {len(qwen.get('board_members',[])):>2} members   | Gemini: {len(gemini.get('board_members',[])):>2} members")
        
        # Show comparison
        comp = gov.get("comparison", {})
        print(f"Matches:  Chair: {comp.get('chairman_match', False)} | Auditor: {comp.get('auditor_match', False)}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Direct H100 twin agent pipeline")
    parser.add_argument("--run-id", required=True, help="Run ID for tracking")
    parser.add_argument("--limit", type=int, default=1, help="Number of documents to process")
    
    args = parser.parse_args()
    
    # Validate environment
    required_env = ["DATABASE_URL", "OLLAMA_URL", "QWEN_MODEL_TAG", "GEMINI_API_KEY"]
    for env_var in required_env:
        if not os.environ.get(env_var):
            print(f"❌ Missing {env_var}")
            sys.exit(1)
    
    # Run twin test
    results = run_direct_twin_test(args.run_id, args.limit)
    
    if "error" in results:
        print(f"❌ Pipeline failed: {results['error']}")
        sys.exit(1)
    
    # Print side-by-side governance
    print_governance_side_by_side(results["results"])
    
    # Run acceptance gates (will likely fail since we're not using Sjöstaden 2)
    for result in results["results"]:
        gov_data = result["governance"].get("qwen", {})  # Use Qwen data for gates
        gates = run_acceptance_gates({"governance": gov_data})
        
        if gates["gates_passed"]:
            print("✅ Acceptance gates PASSED")
        else:
            print("⚠️  Acceptance gates failed (expected for non-Sjöstaden docs):")
            for failure in gates["failures"][:3]:  # Show first 3 failures
                print(f"   • {failure}")
    
    print(f"\n🎯 Direct twin test completed: {args.run_id}")

if __name__ == "__main__":
    main()