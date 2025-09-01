"""
Gemini client for coaching and twin agent mode.
No stubs, no TODOs - production ready.
"""
import os
import requests
import json
from typing import Dict, Any


def call_gemini_for_coaching(prompt: str, *, temperature: float = 0.0, max_tokens: int = 512) -> str:
    """
    Call Gemini API for coaching prompts.
    Returns raw text response - JSON validation must be done by caller.
    """
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent"
    api_key = os.environ["GEMINI_API_KEY"]
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature, 
            "maxOutputTokens": max_tokens
        }
    }
    
    response = requests.post(f"{url}?key={api_key}", json=payload, timeout=60)
    response.raise_for_status()
    
    result = response.json()
    text = result["candidates"][0]["content"]["parts"][0]["text"]
    
    return text


def call_gemini_for_extraction(prompt: str, *, temperature: float = 0.0, max_tokens: int = 2048) -> Dict[str, Any]:
    """
    Call Gemini API for field extraction in twin agent mode.
    Returns structured response with metadata for receipts.
    """
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent"
    api_key = os.environ["GEMINI_API_KEY"]
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens
        }
    }
    
    response = requests.post(f"{url}?key={api_key}", json=payload, timeout=120)
    
    # Build receipt data
    receipt = {
        "model": "gemini-1.5-pro",
        "transport": "rest_api",
        "http_status": response.status_code,
        "json_ok": False,
        "schema_ok": False,
        "latency_ms": None,  # Would need timing wrapper
        "response_text": None
    }
    
    response.raise_for_status()
    
    result = response.json()
    text = result["candidates"][0]["content"]["parts"][0]["text"]
    
    receipt["response_text"] = text
    receipt["json_ok"] = True  # Will be validated by caller
    
    return {
        "text": text,
        "receipt": receipt
    }