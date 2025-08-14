#!/usr/bin/env python3
"""
Launcher script for the Integrated Survey & Map Application

This script launches the BRF peer survey system with all necessary
configurations and error handling.

Usage:
    python run_survey_app.py

Or with Streamlit directly:
    streamlit run integrated_survey_map_app.py
"""

import sys
import os
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if all required dependencies are installed."""
    required_packages = [
        'streamlit',
        'folium', 
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
    
    return missing_packages

def install_missing_packages(packages):
    """Install missing packages using pip."""
    if not packages:
        return
    
    print(f"Installing missing packages: {', '.join(packages)}")
    
    for package in packages:
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", package
            ])
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {package}: {e}")
            return False
    
    return True

def main():
    """Main launcher function."""
    
    print("🏢 BRF Peer Survey & Map Analysis System")
    print("=" * 50)
    
    # Check current directory
    current_dir = Path(__file__).parent
    app_file = current_dir / "integrated_survey_map_app.py"
    
    if not app_file.exists():
        print("❌ Error: integrated_survey_map_app.py not found in current directory")
        sys.exit(1)
    
    # Check data files
    data_file = current_dir / "hammarby_map_visualization_data.json"
    if not data_file.exists():
        print("⚠️  Warning: hammarby_map_visualization_data.json not found")
        print("   The application may not work correctly without building data")
    
    # Check dependencies
    print("🔍 Checking dependencies...")
    missing = check_dependencies()
    
    if missing:
        print(f"📦 Missing packages detected: {', '.join(missing)}")
        
        install_choice = input("Would you like to install them automatically? (y/n): ")
        if install_choice.lower().strip() == 'y':
            if not install_missing_packages(missing):
                print("❌ Failed to install some packages. Please install manually:")
                print(f"   pip install {' '.join(missing)}")
                sys.exit(1)
        else:
            print("Please install missing packages manually:")
            print(f"   pip install {' '.join(missing)}")
            sys.exit(1)
    
    print("✅ All dependencies satisfied")
    
    # Optional packages check
    optional_packages = ['streamlit-folium']
    missing_optional = []
    
    for package in optional_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_optional.append(package)
    
    if missing_optional:
        print(f"ℹ️  Optional packages not installed: {', '.join(missing_optional)}")
        print("   Install for enhanced map interactivity:")
        print(f"   pip install {' '.join(missing_optional)}")
    
    # Launch the application
    print("🚀 Starting application...")
    print("   Open http://localhost:8501 in your browser")
    print("   Press Ctrl+C to stop the application")
    print("")
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(app_file),
            "--server.address", "localhost",
            "--server.port", "8501",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except FileNotFoundError:
        print("❌ Streamlit not found. Please install it first:")
        print("   pip install streamlit")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()