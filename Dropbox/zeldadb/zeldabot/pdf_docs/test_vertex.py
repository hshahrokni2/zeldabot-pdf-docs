#!/usr/bin/env python3
"""
Minimal Vertex AI authentication test
Tests if service account can access Gemini via Vertex AI endpoint
"""
import requests
import google.auth
import google.auth.transport.requests
import os
from google.oauth2 import service_account

def test_vertex_auth():
    """Test Vertex AI authentication with service account"""
    print("⏺ Testing Vertex AI Authentication")
    
    # Load service account credentials with explicit scope
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not credentials_path:
        print("❌ GOOGLE_APPLICATION_CREDENTIALS not set")
        return False
    
    print(f"📁 Credentials file: {credentials_path}")
    
    try:
        # Use service account credentials with cloud-platform scope
        creds = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        creds.refresh(google.auth.transport.requests.Request())
        
        print(f"✅ Token obtained: {creds.token[:20]}...")
        
        # Test Vertex AI endpoint with correct format
        headers = {"Authorization": f"Bearer {creds.token}", "Content-Type": "application/json"}
        body = {
            "contents": [
                {
                    "role": "user",  # Required role field for Vertex AI
                    "parts": [{"text": "Test Vertex AI access"}]
                }
            ]
        }
        # Try European region first (better for Swedish project)
        endpoint = "https://europe-west4-aiplatform.googleapis.com/v1/projects/brf-graphrag-swedish/locations/europe-west4/publishers/google/models/gemini-2.5-pro:generateContent"
        
        print(f"🌐 Testing endpoint: {endpoint[:80]}...")
        
        response = requests.post(endpoint, headers=headers, json=body, timeout=60)
        
        print(f"📊 Response Status: {response.status_code}")
        print(f"📄 Response Body: {response.text[:500]}...")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Vertex AI authentication working!")
            return True
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    # Ensure environment is loaded
    if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
        print("⚠️  Loading environment from Pure_LLM_Ftw/.env")
        # Note: This won't work in Python, need to source in shell first
        
    success = test_vertex_auth()
    exit(0 if success else 1)