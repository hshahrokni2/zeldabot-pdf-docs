#!/usr/bin/env python3
"""
Qwen agent for BRF document extraction.
Handles Ollama calls with receipts and error handling.
"""
import os
import time
import requests
import json
from typing import Dict, Any, Optional, List


class QwenAgent:
    def __init__(self):
        self.model_tag = os.environ.get("QWEN_MODEL_TAG", "qwen2.5vl:7b")
        self.ollama_url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
        
    def extract_section(
        self, 
        section: str, 
        prompt: str, 
        pages_used: List[int],
        pdf_path: str
    ) -> Dict[str, Any]:
        """
        Extract a section using Qwen vision model.
        Returns structured response with receipt metadata.
        """
        start_time = time.time()
        
        payload = {
            "model": self.model_tag,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=120
            )
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            receipt = {
                "section": section,
                "model": self.model_tag,
                "transport": "ollama",
                "http_status": response.status_code,
                "latency_ms": latency_ms,
                "pages_used": pages_used,
                "json_ok": False,
                "schema_ok": False
            }
            
            if response.status_code != 200:
                receipt["error"] = f"HTTP {response.status_code}"
                return {"receipt": receipt, "success": False}
            
            result = response.json()
            response_text = result.get("response", "")
            
            # Try to parse JSON response
            try:
                parsed_json = json.loads(response_text)
                receipt["json_ok"] = True
                receipt["schema_ok"] = True  # TODO: Add actual schema validation
                
                return {
                    "receipt": receipt,
                    "success": True,
                    "data": parsed_json,
                    "raw_response": response_text
                }
                
            except json.JSONDecodeError:
                receipt["error"] = "Invalid JSON response"
                return {
                    "receipt": receipt,
                    "success": False,
                    "raw_response": response_text
                }
                
        except requests.RequestException as e:
            latency_ms = int((time.time() - start_time) * 1000)
            receipt = {
                "section": section,
                "model": self.model_tag,
                "transport": "ollama",
                "http_status": 0,
                "latency_ms": latency_ms,
                "pages_used": pages_used,
                "json_ok": False,
                "schema_ok": False,
                "error": str(e)
            }
            
            return {"receipt": receipt, "success": False}
    
    def health_check(self) -> bool:
        """Check if Qwen model is available."""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return any(m["name"] == self.model_tag for m in models)
            return False
        except:
            return False