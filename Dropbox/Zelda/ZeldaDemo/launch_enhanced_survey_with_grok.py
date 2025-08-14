#!/usr/bin/env python3
"""
Launch script for Enhanced BRF Survey System with Grok Supplier Database

This script launches the enhanced survey system with real Stockholm supplier data
from the Grok research database.

Features demonstrated:
- Real supplier data with contact details and pricing
- Pre-populated BRF Sjöstaden 2 demo data
- Enhanced supplier recommendations for low ratings
- Immediate value demonstration with supplier alternatives
"""

import subprocess
import sys
import os

def main():
    """Launch the enhanced survey system."""
    
    print("🚀 Launching Enhanced BRF Survey System with Grok Supplier Database...")
    print("=" * 70)
    print("Features:")
    print("✅ Real Stockholm supplier database (20 suppliers, 10 categories)")
    print("✅ Pre-populated BRF Sjöstaden 2 data with realistic ratings")
    print("✅ Enhanced supplier cards with contact details & pricing")
    print("✅ Immediate supplier recommendations for low ratings (≤3 stars)")
    print("✅ Sustainability features and specialties highlighted")
    print("=" * 70)
    
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Check if Grok database exists
    if not os.path.exists('grok_suppliers_database.json'):
        print("⚠️  Warning: Grok suppliers database not found!")
        print("   The system will use fallback supplier data.")
        print()
    
    # Launch Streamlit app
    try:
        cmd = [
            sys.executable, "-m", "streamlit", "run", 
            "enhanced_survey_sjostaden2_demo.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ]
        
        print("🌐 Starting web interface on http://localhost:8501")
        print("📱 The interface is mobile-responsive and works on all devices")
        print()
        print("🎯 Demo Flow:")
        print("1. Survey starts pre-filled with BRF Sjöstaden 2 data")
        print("2. Several suppliers have low ratings (2-3 stars)")
        print("3. Immediate alternatives shown with real contact details")
        print("4. Enhanced supplier cards with pricing and sustainability info")
        print("5. Full analysis unlocked after survey completion")
        print()
        print("Press Ctrl+C to stop the server")
        print("=" * 70)
        
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error launching Streamlit: {e}")
        print("Make sure Streamlit is installed: pip install streamlit")
    except FileNotFoundError:
        print("❌ Python or Streamlit not found in PATH")
        print("Please ensure Python and Streamlit are properly installed")

if __name__ == "__main__":
    main()