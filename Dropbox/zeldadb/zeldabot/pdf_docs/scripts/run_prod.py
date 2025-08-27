#!/usr/bin/env python3
"""
Production Pipeline Runner - Single entry point
Calls src.pipeline.prod:run_from_db() with proper environment setup
"""
import os
import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def main():
    parser = argparse.ArgumentParser(description="Run production extraction pipeline")
    parser.add_argument("--run-id", required=True, help="Run ID for tracking")
    parser.add_argument("--limit", type=int, default=1, help="Number of documents to process")
    args = parser.parse_args()
    
    # Environment validation
    required_env = [
        "DATABASE_URL",
        "OBS_STRICT", 
        "QWEN_TRANSPORT",
        "OLLAMA_URL",
        "QWEN_MODEL_TAG"
    ]
    
    missing = [var for var in required_env if not os.environ.get(var)]
    if missing:
        print(f"❌ Missing environment variables: {missing}")
        sys.exit(1)
    
    # Import and run
    try:
        from pipeline.prod import run_from_db
        result = run_from_db(args.run_id, args.limit)
        sys.exit(result)
    except ImportError as e:
        print(f"❌ Failed to import production pipeline: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()