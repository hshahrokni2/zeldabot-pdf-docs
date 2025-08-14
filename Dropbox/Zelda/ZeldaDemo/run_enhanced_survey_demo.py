#!/usr/bin/env python3
"""
Launch script for the Enhanced BRF Sjöstaden 2 Survey System Demo

This script provides a simple way to launch the enhanced survey demonstration
with proper error handling and environment setup.
"""

import sys
import subprocess
import os
from pathlib import Path

def check_requirements():
    """Check if required packages are available."""
    required_packages = [
        'streamlit',
        'plotly', 
        'pandas',
        'numpy'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Missing required packages: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        
        for package in missing_packages:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
    
    return True

def check_data_files():
    """Check if required data files exist."""
    current_dir = Path(__file__).parent
    required_files = [
        'killer_eghs_dataset_with_booli_coords.json',
        'survey_system.py',
        'enhanced_survey_sjostaden2_demo.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not (current_dir / file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"Missing required files: {', '.join(missing_files)}")
        return False
    
    return True

def main():
    """Main launch function."""
    print("🏢 BRF Sjöstaden 2 Enhanced Survey System")
    print("=" * 50)
    
    # Check requirements
    print("Checking requirements...")
    if not check_requirements():
        print("❌ Requirements check failed!")
        return
    
    print("✅ Requirements satisfied")
    
    # Check data files
    print("Checking data files...")
    if not check_data_files():
        print("❌ Required data files missing!")
        return
    
    print("✅ Data files found")
    
    # Launch Streamlit app
    print("\n🚀 Launching Enhanced Survey System...")
    print("The application will open in your default web browser.")
    print("Press Ctrl+C to stop the application.")
    print("-" * 50)
    
    try:
        subprocess.run([
            'streamlit', 'run', 
            'enhanced_survey_sjostaden2_demo.py',
            '--server.headless', 'false',
            '--server.runOnSave', 'true',
            '--theme.base', 'light'
        ])
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error launching application: {e}")
    except FileNotFoundError:
        print("❌ Streamlit not found. Please install streamlit:")
        print("pip install streamlit")

if __name__ == "__main__":
    main()