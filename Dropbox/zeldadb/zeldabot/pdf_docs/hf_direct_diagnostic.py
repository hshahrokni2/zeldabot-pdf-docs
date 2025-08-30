#!/usr/bin/env python3
"""
HF-Direct Diagnostic: Test environment and dependencies
Minimal test to verify HF-Direct readiness without full pipeline
"""
import os
import sys
import json
from pathlib import Path

def test_environment():
    """Test environment configuration"""
    print("🔍 ENVIRONMENT DIAGNOSTIC")
    print("=" * 40)
    
    # Test environment variables
    env_checks = {
        "USE_HF_DIRECT": os.environ.get("USE_HF_DIRECT", "NOT_SET"),
        "HF_DEVICE": os.environ.get("HF_DEVICE", "NOT_SET"), 
        "HF_MODEL_PATH": os.environ.get("HF_MODEL_PATH", "NOT_SET"),
        "TWIN_AGENTS": os.environ.get("TWIN_AGENTS", "NOT_SET"),
        "DATABASE_URL": os.environ.get("DATABASE_URL", "NOT_SET")[:50] + "..." if os.environ.get("DATABASE_URL") else "NOT_SET"
    }
    
    for key, value in env_checks.items():
        print(f"   {key}: {value}")
    
    return env_checks

def test_dependencies():
    """Test Python dependencies for HF-Direct"""
    print("\n🔍 DEPENDENCY DIAGNOSTIC") 
    print("=" * 40)
    
    results = {}
    
    # Test PyTorch
    try:
        import torch
        results["torch"] = {
            "available": True,
            "version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "cuda_device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0
        }
        if torch.cuda.is_available():
            results["torch"]["cuda_device_name"] = torch.cuda.get_device_name(0)
        print(f"   ✅ PyTorch: {torch.__version__}")
        print(f"   ✅ CUDA: {'Available' if torch.cuda.is_available() else 'Not Available'}")
        if torch.cuda.is_available():
            print(f"   ✅ GPU: {torch.cuda.get_device_name(0)}")
    except ImportError as e:
        results["torch"] = {"available": False, "error": str(e)}
        print(f"   ❌ PyTorch: {e}")
    
    # Test Transformers
    try:
        import transformers
        from transformers.models.qwen2_5_vl import Qwen2_5_VLForConditionalGeneration
        from transformers import AutoProcessor
        results["transformers"] = {
            "available": True,
            "version": transformers.__version__,
            "qwen_available": True
        }
        print(f"   ✅ Transformers: {transformers.__version__}")
        print(f"   ✅ Qwen2.5-VL: Available")
    except ImportError as e:
        results["transformers"] = {"available": False, "error": str(e)}
        print(f"   ❌ Transformers: {e}")
    
    # Test Gemini dependencies
    try:
        import requests
        import google.generativeai as genai
        results["gemini"] = {"available": True}
        print(f"   ✅ Gemini dependencies: Available")
    except ImportError as e:
        results["gemini"] = {"available": False, "error": str(e)}
        print(f"   ❌ Gemini dependencies: {e}")
    
    # Test database connectivity
    try:
        import psycopg2
        results["database"] = {"available": True}
        print(f"   ✅ PostgreSQL client: Available")
    except ImportError as e:
        results["database"] = {"available": False, "error": str(e)}
        print(f"   ❌ PostgreSQL client: {e}")
    
    return results

def test_database_connection():
    """Test database connection if available"""
    print("\n🔍 DATABASE CONNECTION TEST")
    print("=" * 40)
    
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("   ❌ DATABASE_URL not set")
        return {"available": False, "error": "DATABASE_URL not set"}
    
    try:
        import psycopg2
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT COUNT(*) FROM arsredovisning_documents;")
        doc_count = cursor.fetchone()[0]
        
        # Test connection details
        cursor.execute("SELECT version();")
        pg_version = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"   ✅ Connection: Successful")
        print(f"   ✅ PostgreSQL: {pg_version.split(' ')[1]}")
        print(f"   ✅ Documents: {doc_count}")
        
        return {
            "available": True,
            "doc_count": doc_count,
            "postgres_version": pg_version
        }
        
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return {"available": False, "error": str(e)}

def test_model_loading():
    """Test if we can actually load the Qwen model"""
    print("\n🔍 MODEL LOADING TEST")
    print("=" * 40)
    
    if os.environ.get("USE_HF_DIRECT", "false").lower() != "true":
        print("   ⚠️  USE_HF_DIRECT not enabled, skipping model test")
        return {"skipped": True}
    
    try:
        import torch
        from transformers.models.qwen2_5_vl import Qwen2_5_VLForConditionalGeneration
        from transformers import AutoProcessor
        
        if not torch.cuda.is_available():
            print("   ❌ CUDA not available, cannot test model loading")
            return {"available": False, "error": "CUDA not available"}
        
        model_path = os.environ.get("HF_MODEL_PATH", "Qwen/Qwen2.5-VL-7B-Instruct")
        device = os.environ.get("HF_DEVICE", "cuda:0")
        
        print(f"   🚀 Loading model: {model_path}")
        print(f"   🎯 Target device: {device}")
        
        # Test model loading (this may take time on first run)
        model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            device_map=device,
            trust_remote_code=True
        )
        processor = AutoProcessor.from_pretrained(model_path, trust_remote_code=True)
        
        print(f"   ✅ Model loaded successfully")
        print(f"   ✅ Model class: {model.__class__.__name__}")
        print(f"   ✅ Has generate method: {hasattr(model, 'generate')}")
        
        # Clean up to save memory
        del model
        del processor
        torch.cuda.empty_cache()
        
        return {"available": True, "model_path": model_path, "device": device}
        
    except Exception as e:
        print(f"   ❌ Model loading failed: {e}")
        return {"available": False, "error": str(e)}

def main():
    """Run comprehensive HF-Direct diagnostic"""
    print("🎯 HF-DIRECT COMPREHENSIVE DIAGNOSTIC")
    print("=" * 50)
    
    # Run all tests
    env_results = test_environment()
    dep_results = test_dependencies()
    db_results = test_database_connection()
    model_results = test_model_loading()
    
    # Compile overall status
    overall_status = {
        "environment": env_results,
        "dependencies": dep_results,
        "database": db_results,
        "model_loading": model_results,
        "hf_direct_ready": False,
        "blocking_issues": []
    }
    
    # Determine HF-Direct readiness
    if not dep_results.get("torch", {}).get("cuda_available", False):
        overall_status["blocking_issues"].append("CUDA not available")
    
    if not dep_results.get("transformers", {}).get("available", False):
        overall_status["blocking_issues"].append("Transformers not available")
    
    if not db_results.get("available", False):
        overall_status["blocking_issues"].append("Database connection failed")
    
    if env_results.get("USE_HF_DIRECT") != "true":
        overall_status["blocking_issues"].append("USE_HF_DIRECT not enabled")
    
    overall_status["hf_direct_ready"] = len(overall_status["blocking_issues"]) == 0
    
    # Final summary
    print("\n" + "=" * 50)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 50)
    
    if overall_status["hf_direct_ready"]:
        print("✅ HF-DIRECT READY: All requirements met")
        print("🚀 Proceed with 5-PDF POC execution")
    else:
        print("❌ HF-DIRECT NOT READY:")
        for issue in overall_status["blocking_issues"]:
            print(f"   - {issue}")
        print("🔧 Resolve blocking issues before proceeding")
    
    # Save diagnostic results
    os.makedirs("artifacts", exist_ok=True)
    with open("artifacts/hf_direct_diagnostic.json", "w") as f:
        json.dump(overall_status, f, indent=2, default=str)
    
    print(f"\n📋 Full diagnostic saved to: artifacts/hf_direct_diagnostic.json")
    
    return 0 if overall_status["hf_direct_ready"] else 1

if __name__ == "__main__":
    sys.exit(main())