#!/usr/bin/env python3
"""
H100 Qwen-only test - test the multimodal fix
"""
import os
import sys
import json
import psycopg2
import tempfile

# Add current directory to path
sys.path.insert(0, '/workspace/brf_extraction/src')

from agents.qwen_agent import QwenAgent

def simple_governance_prompt():
    return """Extrahera styrelseinformation från denna svenska BRF årsredovisning.
Sök efter styrelserelaterade termer: styrelseordförande, styrelseledamöter, suppleanter, revisor, revisionsföretag, årsstämma.
Identifiera namn på personer och företag.

ENDAST JSON - Respond ONLY with a SINGLE minified JSON object:
{"chairman": "", "board_members": [], "auditor_name": "", "audit_firm": "", "annual_meeting_date": ""}"""

def test_h100_qwen():
    print("🚀 H100 QWEN MULTIMODAL TEST")
    
    # Connect to H100 database
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cursor = conn.cursor()
    
    # Get a document
    cursor.execute("""
        SELECT id, filename, pdf_binary 
        FROM arsredovisning_documents 
        WHERE pdf_binary IS NOT NULL 
        ORDER BY created_at DESC 
        LIMIT 1
    """)
    
    doc = cursor.fetchone()
    if not doc:
        print("❌ No documents found")
        return
        
    doc_id, filename, pdf_binary = doc
    print(f"📄 Testing: {filename}")
    
    # Initialize Qwen agent
    qwen_agent = QwenAgent()
    
    # Create temp PDF file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        tmp_file.write(pdf_binary)
        tmp_path = tmp_file.name
    
    prompt = simple_governance_prompt()
    
    # Test Qwen (upgraded multimodal)
    print("🔍 Testing Qwen (upgraded multimodal)...")
    qwen_result = qwen_agent.extract_section("governance", prompt, [1, 2, 3, 4, 5], tmp_path)
    
    # Cleanup
    os.unlink(tmp_path)
    
    # Show results
    print("\n=== QWEN MULTIMODAL RESULTS ===")
    print(f"✅ Success: {qwen_result.get('success', False)}")
    print(f"📊 HTTP Status: {qwen_result.get('receipt', {}).get('http_status', 0)}")
    print(f"⏱️  Latency: {qwen_result.get('receipt', {}).get('latency_ms', 0)}ms")
    print(f"🎯 JSON OK: {qwen_result.get('receipt', {}).get('json_ok', False)}")
    
    if qwen_result.get('success'):
        data = qwen_result.get('data', {})
        print(f"👑 Chairman: {data.get('chairman', 'Not found')}")
        print(f"👥 Board Members: {len(data.get('board_members', []))} members")
        print(f"📋 Auditor: {data.get('auditor_name', 'Not found')}")
        print(f"🏢 Audit Firm: {data.get('audit_firm', 'Not found')}")
        print(f"📅 Annual Meeting: {data.get('annual_meeting_date', 'Not found')}")
        print(f"📄 Full Data: {json.dumps(data, ensure_ascii=False)}")
    else:
        print(f"❌ Error: {qwen_result.get('receipt', {}).get('error', 'Unknown')}")
        print(f"📄 Raw Response: {qwen_result.get('raw_response', 'No response')[:200]}...")
        
    conn.close()
    
    if qwen_result.get('success'):
        print("\n🎉 QWEN MULTIMODAL BREAKTHROUGH CONFIRMED ON H100! 🎉")
    else:
        print("\n❌ Qwen multimodal still has issues on H100")

if __name__ == "__main__":
    test_h100_qwen()
