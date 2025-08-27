#!/usr/bin/env python3
"""
Simple H100 twin test - bypassing import issues
"""
import os
import sys
import json
import psycopg2
import tempfile

# Add current directory to path
sys.path.insert(0, '/workspace/brf_extraction/src')

from agents.qwen_agent import QwenAgent
from agents.gemini_agent import GeminiAgent

def simple_governance_prompt():
    return """Extrahera styrelseinformation från denna svenska BRF årsredovisning.
Sök efter styrelserelaterade termer: styrelseordförande, styrelseledamöter, suppleanter, revisor, revisionsföretag, årsstämma.
Identifiera namn på personer och företag.

ENDAST JSON - Respond ONLY with a SINGLE minified JSON object:
{"chairman": "", "board_members": [], "auditor_name": "", "audit_firm": "", "annual_meeting_date": ""}"""

def test_h100_twin():
    print("🚀 H100 TWIN TEST - UPGRADED MULTIMODAL QWEN")
    
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
    
    # Initialize agents
    qwen_agent = QwenAgent()
    gemini_agent = GeminiAgent()
    
    # Create temp PDF file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        tmp_file.write(pdf_binary)
        tmp_path = tmp_file.name
    
    prompt = simple_governance_prompt()
    
    # Test Qwen (upgraded multimodal)
    print("🔍 Testing Qwen (multimodal)...")
    qwen_result = qwen_agent.extract_section("governance", prompt, [1, 2, 3, 4, 5], tmp_path)
    
    # Test Gemini 
    print("🔍 Testing Gemini (Vertex AI)...")
    gemini_result = gemini_agent.extract_section("governance", prompt, [1, 2, 3, 4, 5], tmp_path)
    
    # Cleanup
    os.unlink(tmp_path)
    
    # Show results
    print("\n=== RESULTS ===")
    print(f"Qwen Status: {qwen_result.get('success', False)}")
    print(f"Qwen HTTP: {qwen_result.get('receipt', {}).get('http_status', 0)}")
    if qwen_result.get('success'):
        print(f"Qwen Data: {json.dumps(qwen_result.get('data', {}))}")
    else:
        print(f"Qwen Error: {qwen_result.get('receipt', {}).get('error', 'Unknown')}")
    
    print(f"Gemini Status: {gemini_result.get('success', False)}")  
    print(f"Gemini HTTP: {gemini_result.get('receipt', {}).get('http_status', 0)}")
    if gemini_result.get('success'):
        print(f"Gemini Data: {json.dumps(gemini_result.get('data', {}))}")
    else:
        print(f"Gemini Error: {gemini_result.get('receipt', {}).get('error', 'Unknown')}")
        
    conn.close()

if __name__ == "__main__":
    test_h100_twin()
