#!/usr/bin/env python3
"""
H100 Twin test with resilient Gemini agent (Vertex AI + REST API fallback)
Implements systems architect recommended dual authentication approach
"""
import os
import sys
import json
import psycopg2
import tempfile
import time

# Add current directory to path
sys.path.insert(0, '/workspace/brf_extraction/src')

from agents.qwen_agent import QwenAgent

# Create resilient Gemini agent with dual authentication
import requests
import base64
import fitz
from google.auth.transport.requests import Request
from google.oauth2 import service_account

class ResilientGeminiAgent:
    def __init__(self):
        self.api_key = "AIzaSyD0y92BjcnvUgRlWsA1oPSIWV5QaJcCrNw"
        self.project_id = "brf-graphrag-swedish"
        self.location = "europe-west4" 
        self.model = "gemini-2.5-pro"
        
        # Primary: Vertex AI endpoint
        self.vertex_endpoint = f"https://{self.location}-aiplatform.googleapis.com/v1/projects/{self.project_id}/locations/{self.location}/publishers/google/models/{self.model}:generateContent"
        
        # Fallback: REST API endpoint (use correct model)
        self.rest_endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent"
        
        # Try to load service account credentials
        self.vertex_available = False
        self.access_token = None
        
        try:
            credentials_path = "/workspace/brf_extraction/brf-graphrag-swedish-aug27.json"
            if os.path.exists(credentials_path):
                credentials = service_account.Credentials.from_service_account_file(
                    credentials_path,
                    scopes=["https://www.googleapis.com/auth/cloud-platform"]
                )
                credentials.refresh(Request())
                self.access_token = credentials.token
                self.vertex_available = True
                print("✅ Vertex AI credentials loaded successfully")
            else:
                print("⚠️ Service account file not found, will use REST API fallback")
        except Exception as e:
            print(f"⚠️ Vertex AI setup failed ({str(e)[:50]}...), will use REST API fallback")
    
    def _pdf_pages_to_base64_images(self, pdf_path: str, page_nums: list) -> list:
        """Convert PDF pages to optimized base64 JPEGs for Gemini API (50-70% size reduction)."""
        doc = fitz.open(pdf_path)
        images = []
        for p in page_nums:
            if p-1 < 0 or p-1 >= len(doc): 
                continue
            page = doc.load_page(p-1)
            pix = page.get_pixmap(dpi=72)  # Lower DPI from 150 to 72 to reduce size (still readable)
            import io
            buf = io.BytesIO(pix.tobytes(output="jpeg"))
            data = base64.b64encode(buf.getvalue()).decode()
            images.append(data)
        doc.close()
        return images
    
    def _try_vertex_ai(self, section: str, prompt: str, images: list, t0: float):
        """Try Vertex AI authentication first."""
        if not self.vertex_available or not self.access_token:
            return None
            
        parts = [{"text": prompt + "\n\nReturn strictly JSON. Do not include any prose. If a field is unknown, use null. Keys MUST be snake_case."}]
        for img in images:
            parts.append({"inline_data": {"mime_type": "image/jpeg", "data": img}})
        
        body = {
            "contents": [{"role": "user", "parts": parts}],
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
            response = requests.post(self.vertex_endpoint, headers=headers, json=body, timeout=120)
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
                                    "json_ok": True,
                                    "fallback_used": False
                                }
                            }
                        except json.JSONDecodeError:
                            # JSON error - try fallback
                            print("⚠️ Vertex AI returned invalid JSON, trying REST API fallback")
                            return None
                            
            # HTTP error - check if JWT related
            error_text = response.text
            if "JWT" in error_text or "invalid_grant" in error_text or "reasonable timeframe" in error_text:
                print(f"⚠️ Vertex AI JWT authentication failed (HTTP {response.status_code}), trying REST API fallback")
                return None
            
            # Other HTTP error - still try fallback
            print(f"⚠️ Vertex AI returned HTTP {response.status_code}, trying REST API fallback")
            return None
            
        except Exception as e:
            print(f"⚠️ Vertex AI request failed ({str(e)[:50]}...), trying REST API fallback")
            return None
    
    def _try_rest_api(self, section: str, prompt: str, images: list, t0: float):
        """Fallback to REST API with API key."""
        parts = [{"text": prompt + "\n\nReturn strictly JSON. Do not include any prose. If a field is unknown, use null. Keys MUST be snake_case."}]
        for img in images:
            parts.append({"inline_data": {"mime_type": "image/jpeg", "data": img}})
        
        body = {
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {
                "temperature": 0,
                "response_mime_type": "application/json"
            }
        }
        
        headers = {"x-goog-api-key": self.api_key}
        
        # Add retry logic for HTTP 503 transient errors
        response = None
        for attempt in range(3):  # 3 attempts total
            try:
                response = requests.post(self.rest_endpoint, headers=headers, json=body, timeout=240)
                if response.status_code != 503:
                    break  # Success or non-retryable error
                
                if attempt < 2:  # Don't sleep on last attempt
                    wait_time = 5 * (2 ** attempt)  # 5s, 10s backoff
                    print(f"⚠️ HTTP 503 - retrying in {wait_time}s (attempt {attempt + 1}/3)")
                    time.sleep(wait_time)
            except requests.RequestException as e:
                if attempt == 2:  # Last attempt
                    raise e
                print(f"⚠️ Request failed - retrying in 5s (attempt {attempt + 1}/3)")
                time.sleep(5)
        
        try:            
            latency_ms = int((time.time() - t0) * 1000)
            
            if response.status_code == 200:
                result = response.json()
                parts = result.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                content = parts[0].get("text", "{}") if parts else "{}"
                
                try:
                    data = json.loads(content)
                    print(f"🔍 GEMINI PARSED JSON: {json.dumps(data, ensure_ascii=False)}")
                    return {
                        "success": True,
                        "data": data,
                        "receipt": {
                            "section": section,
                            "model": "gemini-2.5-pro",
                            "transport": "rest-api",
                            "http_status": 200,
                            "latency_ms": latency_ms,
                            "json_ok": True,
                            "fallback_used": True
                        }
                    }
                except json.JSONDecodeError as e:
                    print(f"🔍 GEMINI RAW RESPONSE (JSON parse failed): {content[:500]}...")
                    return {
                        "success": False,
                        "receipt": {
                            "section": section,
                            "model": "gemini-2.5-pro", 
                            "transport": "rest-api",
                            "http_status": 200,
                            "latency_ms": latency_ms,
                            "json_ok": False,
                            "error": f"Invalid JSON response: {str(e)}",
                            "fallback_used": True
                        },
                        "raw_response": content
                    }
            else:
                return {
                    "success": False,
                    "receipt": {
                        "section": section,
                        "model": "gemini-2.5-pro",
                        "transport": "rest-api", 
                        "http_status": response.status_code,
                        "latency_ms": latency_ms,
                        "json_ok": False,
                        "error": f"HTTP {response.status_code}",
                        "fallback_used": True
                    }
                }
        except Exception as e:
            return {
                "success": False,
                "receipt": {
                    "section": section,
                    "model": "gemini-2.5-pro",
                    "transport": "rest-api",
                    "http_status": 0,
                    "latency_ms": int((time.time() - t0) * 1000),
                    "json_ok": False,
                    "error": str(e),
                    "fallback_used": True
                }
            }
    
    def extract_section(self, section: str, prompt: str, pages_used: list, pdf_path: str):
        t0 = time.time()
        
        # Limit to 4 pages and optimize for payload size
        images = self._pdf_pages_to_base64_images(pdf_path, pages_used[:4])  # Limit to 4 pages
        
        # Try Vertex AI first
        result = self._try_vertex_ai(section, prompt, images, t0)
        if result is not None:
            return result
        
        # Fall back to REST API
        print("🔄 Using REST API fallback for Gemini...")
        return self._try_rest_api(section, prompt, images, t0)

def simple_governance_prompt():
    return """Extrahera styrelseinformation från denna svenska BRF årsredovisning.
Sök efter styrelserelaterade termer: styrelseordförande, styrelseledamöter, suppleanter, revisor, revisionsföretag, årsstämma.
Identifiera namn på personer och företag.

ENDAST JSON - Respond ONLY with a SINGLE minified JSON object:
{"chairman": "", "board_members": [], "auditor_name": "", "audit_firm": "", "annual_meeting_date": ""}"""

def test_h100_resilient_twins():
    print("🚀 H100 RESILIENT TWIN TEST - QWEN + GEMINI (WITH FALLBACK)")
    
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
    gemini_agent = ResilientGeminiAgent()
    
    # Create temp PDF file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
        tmp_file.write(pdf_binary)
        tmp_path = tmp_file.name
    
    prompt = simple_governance_prompt()
    
    # Test both agents
    print("🔍 Testing Qwen (multimodal)...")
    qwen_result = qwen_agent.extract_section("governance", prompt, [1, 2, 3, 4, 5], tmp_path)
    
    print("🔍 Testing Gemini (resilient with fallback)...")
    gemini_result = gemini_agent.extract_section("governance", prompt, [1, 2, 3, 4, 5], tmp_path)
    
    # Cleanup
    os.unlink(tmp_path)
    
    # Show results
    print("\n=== RESILIENT TWIN AGENTS RESULTS ===")
    
    print(f"Qwen Success: {qwen_result.get('success', False)}")
    print(f"Qwen HTTP: {qwen_result.get('receipt', {}).get('http_status', 0)}")
    if qwen_result.get('success'):
        qwen_data = qwen_result.get('data', {})
        print(f"Qwen Chairman: {qwen_data.get('chairman', 'None')}")
        print(f"Qwen Board: {len(qwen_data.get('board_members', []))} members")
        print(f"Qwen Auditor: {qwen_data.get('auditor_name', 'None')}")
    
    print(f"Gemini Success: {gemini_result.get('success', False)}")
    print(f"Gemini HTTP: {gemini_result.get('receipt', {}).get('http_status', 0)}")
    print(f"Gemini Transport: {gemini_result.get('receipt', {}).get('transport', 'unknown')}")
    print(f"Gemini Fallback Used: {gemini_result.get('receipt', {}).get('fallback_used', False)}")
    
    if gemini_result.get('success'):
        gemini_data = gemini_result.get('data', {})
        print(f"Gemini Chairman: {gemini_data.get('chairman', 'None')}")
        print(f"Gemini Board: {len(gemini_data.get('board_members', []))} members") 
        print(f"Gemini Auditor: {gemini_data.get('auditor_name', 'None')}")
    else:
        print(f"Gemini Error: {gemini_result.get('receipt', {}).get('error', 'Unknown')}")
        
    conn.close()
    
    if qwen_result.get('success') and gemini_result.get('success'):
        transport = gemini_result.get('receipt', {}).get('transport', 'unknown')
        fallback = gemini_result.get('receipt', {}).get('fallback_used', False)
        if fallback:
            print(f"\n🎉 BOTH TWIN AGENTS OPERATIONAL (Gemini via {transport} fallback)! 🎉")
        else:
            print(f"\n🎉 BOTH TWIN AGENTS OPERATIONAL (Gemini via {transport})! 🎉")
    elif qwen_result.get('success'):
        print("\n✅ QWEN WORKING, Gemini had issues despite fallback")
    else:
        print("\n❌ Issues with both agents")

if __name__ == "__main__":
    test_h100_resilient_twins()