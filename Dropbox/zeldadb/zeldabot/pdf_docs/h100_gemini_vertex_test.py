#!/usr/bin/env python3
"""
H100 Twin test with Gemini via Vertex AI instead of generativelanguage
"""
import os
import sys
import json
import psycopg2
import tempfile

# Add current directory to path
sys.path.insert(0, '/workspace/brf_extraction/src')

from agents.qwen_agent import QwenAgent

# Create a Vertex AI Gemini agent
import requests
import base64
import fitz
from google.auth.transport.requests import Request
from google.oauth2 import service_account

class VertexAIGeminiAgent:
    def __init__(self):
        self.project_id = "brf-graphrag-swedish"
        self.location = "europe-west4" 
        self.model = "gemini-2.5-pro"
        
        # Load service account credentials
        credentials_path = "/workspace/brf_extraction/brf-graphrag-swedish-aug27.json"
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        
        # Refresh credentials to get access token
        credentials.refresh(Request())
        self.access_token = credentials.token
        
        self.endpoint = f"https://{self.location}-aiplatform.googleapis.com/v1/projects/{self.project_id}/locations/{self.location}/publishers/google/models/{self.model}:generateContent"
    
    def _pdf_pages_to_base64_images(self, pdf_path: str, page_nums: list) -> list:
        """Convert PDF pages to base64 JPEGs for multimodal input."""
        doc = fitz.open(pdf_path)
        images = []
        for p in page_nums:
            if 0 <= p - 1 < len(doc):
                pix = doc.load_page(p - 1).get_pixmap(dpi=150)
                import io
                buf = io.BytesIO(pix.tobytes(output="jpeg"))
                images.append(base64.b64encode(buf.getvalue()).decode())
        doc.close()
        return images
    
    def extract_section(self, section: str, prompt: str, pages_used: list, pdf_path: str):
        import time
        t0 = time.time()
        
        images = self._pdf_pages_to_base64_images(pdf_path, pages_used[:2])  # Limit to 2 pages
        
        # Build Vertex AI format request
        parts = [{"text": prompt + "\n\nReturn strictly JSON. Do not include any prose. If a field is unknown, use null. Keys MUST be snake_case."}]
        for img in images:
            parts.append({"inline_data": {"mime_type": "image/jpeg", "data": img}})
        
        body = {
            "contents": [{
                "role": "user",
                "parts": parts
            }],
            "generation_config": {
                "temperature": 0,
                "response_mime_type": "application/json"
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(self.endpoint, headers=headers, json=body, timeout=120)
            latency_ms = int((time.time() - t0) * 1000)
            
            if response.status_code == 200:
                result = response.json()
                candidates = result.get("candidates", [])
                if candidates:
                    content = candidates[0].get("content", {}).get("parts", [])
                    if content:
                        text = content[0].get("text", "{}")
                        
                        try:
                            data = json.loads(text)
                            return {
                                "success": True,
                                "data": data,
                                "receipt": {
                                    "section": section,
                                    "model": "gemini-2.5-pro",
                                    "transport": "vertex-ai",
                                    "http_status": 200,
                                    "latency_ms": latency_ms,
                                    "json_ok": True
                                }
                            }
                        except json.JSONDecodeError:
                            return {
                                "success": False,
                                "receipt": {
                                    "section": section,
                                    "model": "gemini-2.5-pro", 
                                    "transport": "vertex-ai",
                                    "http_status": 200,
                                    "latency_ms": latency_ms,
                                    "json_ok": False,
                                    "error": "Invalid JSON response"
                                },
                                "raw_response": text
                            }
                            
            return {
                "success": False,
                "receipt": {
                    "section": section,
                    "model": "gemini-2.5-pro",
                    "transport": "vertex-ai", 
                    "http_status": response.status_code,
                    "latency_ms": latency_ms,
                    "json_ok": False,
                    "error": f"HTTP {response.status_code}: {response.text[:200]}"
                }
            }
        except Exception as e:
            return {
                "success": False,
                "receipt": {
                    "section": section,
                    "model": "gemini-2.5-pro",
                    "transport": "vertex-ai",
                    "http_status": 0,
                    "latency_ms": int((time.time() - t0) * 1000),
                    "json_ok": False,
                    "error": str(e)
                }
            }

def simple_governance_prompt():
    return """Extrahera styrelseinformation från denna svenska BRF årsredovisning.
Sök efter styrelserelaterade termer: styrelseordförande, styrelseledamöter, suppleanter, revisor, revisionsföretag, årsstämma.
Identifiera namn på personer och företag.

ENDAST JSON - Respond ONLY with a SINGLE minified JSON object:
{"chairman": "", "board_members": [], "auditor_name": "", "audit_firm": "", "annual_meeting_date": ""}"""

def test_h100_twin_vertex():
    print("🚀 H100 TWIN TEST - QWEN + GEMINI VERTEX AI")
    
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
    gemini_agent = VertexAIGeminiAgent()
    
    # Create temp PDF file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        tmp_file.write(pdf_binary)
        tmp_path = tmp_file.name
    
    prompt = simple_governance_prompt()
    
    # Test both agents
    print("🔍 Testing Qwen (multimodal)...")
    qwen_result = qwen_agent.extract_section("governance", prompt, [1, 2, 3, 4, 5], tmp_path)
    
    print("🔍 Testing Gemini (Vertex AI)...")
    gemini_result = gemini_agent.extract_section("governance", prompt, [1, 2, 3, 4, 5], tmp_path)
    
    # Cleanup
    os.unlink(tmp_path)
    
    # Show results
    print("\n=== TWIN AGENTS RESULTS (VERTEX AI) ===")
    
    print(f"Qwen Success: {qwen_result.get('success', False)}")
    print(f"Qwen HTTP: {qwen_result.get('receipt', {}).get('http_status', 0)}")
    if qwen_result.get('success'):
        qwen_data = qwen_result.get('data', {})
        print(f"Qwen Chairman: {qwen_data.get('chairman', 'None')}")
        print(f"Qwen Board: {len(qwen_data.get('board_members', []))} members")
        print(f"Qwen Auditor: {qwen_data.get('auditor_name', 'None')}")
    
    print(f"Gemini Success: {gemini_result.get('success', False)}")
    print(f"Gemini HTTP: {gemini_result.get('receipt', {}).get('http_status', 0)}")
    if gemini_result.get('success'):
        gemini_data = gemini_result.get('data', {})
        print(f"Gemini Chairman: {gemini_data.get('chairman', 'None')}")
        print(f"Gemini Board: {len(gemini_data.get('board_members', []))} members") 
        print(f"Gemini Auditor: {gemini_data.get('auditor_name', 'None')}")
    else:
        print(f"Gemini Error: {gemini_result.get('receipt', {}).get('error', 'Unknown')}")
        
    conn.close()
    
    if qwen_result.get('success') and gemini_result.get('success'):
        print("\n🎉 BOTH TWIN AGENTS WORKING ON H100! 🎉")
    elif qwen_result.get('success'):
        print("\n✅ QWEN WORKING, Gemini Vertex AI had issues")
    else:
        print("\n❌ Issues with both agents")

if __name__ == "__main__":
    test_h100_twin_vertex()