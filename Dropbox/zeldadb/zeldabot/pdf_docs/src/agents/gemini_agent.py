#!/usr/bin/env python3
"""
Gemini agent for BRF extraction (twin mode).
- Calls gemini-2.5-pro via Google Generative Language API v1beta
- Forces JSON-only output (response_mime_type=application/json)
- Hardened parser for candidates/content/parts
"""
import os
import time
import json
import requests
import base64
import fitz
import io
from typing import Dict, Any, List
from google.auth.transport.requests import Request
from google.oauth2 import service_account


class GeminiAgent:
    def __init__(self):
        self.model = "gemini-2.5-pro"
        self.api_key = os.environ["GEMINI_API_KEY"]  # fail fast if missing
        
        # Support both Vertex AI and generativelanguage endpoints
        custom_endpoint = os.getenv("GEMINI_ENDPOINT")
        if custom_endpoint and "aiplatform.googleapis.com" in custom_endpoint:
            self.endpoint = custom_endpoint
            # Vertex AI uses service account authentication
            self.use_vertex = True
            self._setup_vertex_auth()
        else:
            self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
            self.use_vertex = False
            
        self.session = requests.Session()
        self.timeout = float(os.getenv("GEMINI_TIMEOUT", "120"))
    
    def _setup_vertex_auth(self):
        """Set up Vertex AI service account authentication"""
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not credentials_path:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS required for Vertex AI")
        
        # Load service account credentials
        self.credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
    
    def _get_vertex_token(self):
        """Get fresh OAuth token for Vertex AI with explicit scopes"""
        # Use explicit service account credentials with cloud-platform scope
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not credentials_path:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS required for Vertex AI")
        
        creds = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/cloud-platform']  # Broad scope for Vertex AI
        )
        creds.refresh(Request())
        
        return creds.token

    def _json_guard_prompt(self, section: str, user_prompt: str) -> str:
        return (
            f"{user_prompt.strip()}\n\n"
            "Return strictly JSON. Do not include any prose. "
            "If a field is unknown, use null. Keys MUST be snake_case."
        )

    def _pdf_pages_to_inline_images(self, pdf_path: str, page_nums: List[int]) -> List[Dict[str, Any]]:
        """Convert PDF pages to inline base64 images for Gemini API"""
        doc = fitz.open(pdf_path)
        images = []
        for p in page_nums:
            if p-1 < 0 or p-1 >= len(doc): 
                continue
            pix = doc.load_page(p-1).get_pixmap(dpi=150)
            buf = io.BytesIO(pix.tobytes(output="jpeg"))
            data = base64.b64encode(buf.getvalue()).decode()
            images.append({"inline_data": {"mime_type": "image/jpeg", "data": data}})
        doc.close()
        return images

    def extract_section(
        self,
        section: str,
        prompt: str,
        pages_used: List[int],
        pdf_path: str
    ) -> Dict[str, Any]:
        t0 = time.time()
        
        # Set headers based on endpoint type
        if self.use_vertex:
            token = self._get_vertex_token()
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        else:
            headers = {"x-goog-api-key": self.api_key}
        
        # Convert PDF pages to images (limit to pages 1-2 for testing)
        # Text-only toggle for testing
        if os.getenv('GEMINI_TEXT_ONLY', '0') == '1':
            images = []  # Skip images for text-only testing
        else:
            images = self._pdf_pages_to_inline_images(pdf_path, pages_used or [1, 2])
        parts = [{"text": self._json_guard_prompt(section, prompt)}] + images
        
        body = {
            "contents": [
                {"role": "user", "parts": parts}
            ],
            "generationConfig": {
                "temperature": 0,
                "topP": 0.95,
                "response_mime_type": "application/json"
            }
        }
        
        # Vertex AI format is already correct with role: "user"
        
        try:
            r = self.session.post(self.endpoint, headers=headers, json=body, timeout=240)
            r.raise_for_status()
            latency_ms = int((time.time() - t0) * 1000)

            receipt = {
                "section": section,
                "model": self.model,
                "transport": "google_gls_v1beta",
                "http_status": r.status_code,
                "latency_ms": latency_ms,
                "pages_used": pages_used,
                "json_ok": False,
                "schema_ok": False
            }

            result = r.json()
            # Robust text extraction
            parts = result.get("candidates", [{}])[0].get("content", {}).get("parts", [])
            content = parts[0].get("text", "{}") if parts else "{}"
            
            if not content.strip():
                return {
                    "receipt": {**receipt, "error": "No parts/text in Gemini response", "raw": json.dumps(result)[:1000]},
                    "success": False
                }
            
            data = json.loads(content)
            receipt["json_ok"] = True
            return {"receipt": receipt, "success": True, "data": data}
            
        except requests.HTTPError as e:
            latency_ms = int((time.time() - t0) * 1000)
            receipt = {
                "section": section,
                "model": self.model,
                "transport": "google_gls_v1beta",
                "http_status": getattr(e.response, 'status_code', 0),
                "latency_ms": latency_ms,
                "pages_used": pages_used,
                "json_ok": False,
                "schema_ok": False
            }
            # Fallback once if 500/429 by retrying 1.5-pro-latest
            if e.response is not None and e.response.status_code in (429, 500) and self.model != "gemini-1.5-pro-latest":
                self.model = "gemini-1.5-pro-latest"
                self.endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
                return self.extract_section(section, prompt, pages_used, pdf_path)
            return {"receipt": {**receipt, "error": str(e)}, "success": False}
        except Exception as e:
            latency_ms = int((time.time() - t0) * 1000)
            receipt = {
                "section": section,
                "model": self.model,
                "transport": "google_gls_v1beta",
                "http_status": 0,
                "latency_ms": latency_ms,
                "pages_used": pages_used,
                "json_ok": False,
                "schema_ok": False
            }
            return {"receipt": {**receipt, "error": str(e)}, "success": False}
    
    def health_check(self) -> bool:
        """Check if Gemini API is accessible."""
        try:
            headers = {"x-goog-api-key": self.api_key}
            test_payload = {
                "contents": [{"role": "user", "parts": [{"text": "Return JSON: {\"status\": \"ok\"}"}]}],
                "generationConfig": {
                    "maxOutputTokens": 20,
                    "response_mime_type": "application/json"
                }
            }
            
            response = self.session.post(
                self.endpoint,
                headers=headers,
                json=test_payload,
                timeout=10
            )
            
            return response.status_code == 200
            
        except:
            return False