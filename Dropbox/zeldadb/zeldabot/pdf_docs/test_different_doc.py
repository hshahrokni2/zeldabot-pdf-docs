#!/usr/bin/env python3
"""
Test different document to verify twin agent consistency
"""
import os
import sys
import json
import psycopg2
import tempfile

# Add current directory to path
sys.path.insert(0, '/workspace/brf_extraction/src')

from agents.qwen_agent import QwenAgent

# Import our resilient Gemini agent
sys.path.insert(0, '/tmp')
from h100_twin_resilient_test import ResilientGeminiAgent, simple_governance_prompt

def test_different_document():
    print("🔍 TEST 4: Testing different document for consistency verification")
    
    # Connect to H100 database
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    cursor = conn.cursor()
    
    # Get a different document (second in list)
    cursor.execute("""
        SELECT id, filename, pdf_binary 
        FROM arsredovisning_documents 
        WHERE pdf_binary IS NOT NULL 
        ORDER BY created_at DESC 
        LIMIT 1 OFFSET 1
    """)
    
    doc = cursor.fetchone()
    if not doc:
        print("❌ No second document found")
        return
        
    doc_id, filename, pdf_binary = doc
    print(f"📄 Testing different document: {filename}")
    
    # Initialize agents
    qwen_agent = QwenAgent()
    gemini_agent = ResilientGeminiAgent()
    
    # Create temp PDF file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        tmp_file.write(pdf_binary)
        tmp_path = tmp_file.name
    
    prompt = simple_governance_prompt()
    
    # Test both agents
    print("🔍 Testing Qwen on different document...")
    qwen_result = qwen_agent.extract_section("governance", prompt, [1, 2, 3, 4, 5], tmp_path)
    
    print("🔍 Testing Gemini on different document...")
    gemini_result = gemini_agent.extract_section("governance", prompt, [1, 2, 3, 4, 5], tmp_path)
    
    # Cleanup
    os.unlink(tmp_path)
    
    # Show results
    print("\n=== DIFFERENT DOCUMENT TEST RESULTS ===")
    print(f"Document: {filename}")
    
    print(f"Qwen Success: {qwen_result.get('success', False)}")
    if qwen_result.get('success'):
        qwen_data = qwen_result.get('data', {})
        print(f"Qwen Chairman: {qwen_data.get('chairman', 'None')}")
        print(f"Qwen Board: {len(qwen_data.get('board_members', []))} members")
        print(f"Qwen Auditor: {qwen_data.get('auditor_name', 'None')}")
    else:
        print(f"Qwen Error: {qwen_result.get('receipt', {}).get('error', 'Unknown')}")
    
    print(f"Gemini Success: {gemini_result.get('success', False)}")
    if gemini_result.get('success'):
        gemini_data = gemini_result.get('data', {})
        print(f"Gemini Chairman: {gemini_data.get('chairman', 'None')}")
        print(f"Gemini Board: {len(gemini_data.get('board_members', []))} members") 
        print(f"Gemini Auditor: {gemini_data.get('auditor_name', 'None')}")
        print(f"Gemini Board Members: {gemini_data.get('board_members', [])}")
    else:
        print(f"Gemini Error: {gemini_result.get('receipt', {}).get('error', 'Unknown')}")
        
    conn.close()
    
    # Truth check
    both_successful = qwen_result.get('success', False) and gemini_result.get('success', False)
    print(f"\n🎯 TRUTH CHECK: Both agents successful on different document: {both_successful}")
    
    return both_successful

if __name__ == "__main__":
    test_different_document()