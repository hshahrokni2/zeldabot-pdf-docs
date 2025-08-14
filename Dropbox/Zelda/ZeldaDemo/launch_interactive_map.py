#!/usr/bin/env python3
"""
Launch Script for Hammarby Sjöstad Interactive Map

This script handles dependency installation and launches the Streamlit application
for the interactive mapping interface.
"""

import subprocess
import sys
import os
from pathlib import Path

def check_and_install_dependencies():
    """Check for and install required dependencies."""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'streamlit',
        'folium',
        'plotly',
        'pandas',
        'numpy',
        'shapely'
    ]
    
    optional_packages = [
        'streamlit-folium',
        'geopandas'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} is installed")
        except ImportError:
            print(f"❌ {package} is missing")
            missing_packages.append(package)
    
    # Check optional packages
    for package in optional_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} is installed (optional)")
        except ImportError:
            print(f"⚠️  {package} is missing (optional but recommended)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 Installing missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install"
            ] + missing_packages)
            print("✅ All dependencies installed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            print("Please install manually using:")
            print(f"pip install {' '.join(missing_packages)}")
            return False
    
    return True

def check_data_files():
    """Check if required data files exist."""
    print("\n📁 Checking data files...")
    
    current_dir = Path(__file__).parent
    required_files = [
        'hammarby_map_visualization_data.json',
        'hammarby_interactive_map.py',
        'polygon_selection_handler.py'
    ]
    
    missing_files = []
    
    for file_name in required_files:
        file_path = current_dir / file_name
        if file_path.exists():
            print(f"✅ {file_name} found")
        else:
            print(f"❌ {file_name} missing")
            missing_files.append(file_name)
    
    if missing_files:
        print(f"\n⚠️  Missing required files: {', '.join(missing_files)}")
        print("Please ensure all project files are in the correct location.")
        return False
    
    return True

def launch_streamlit_app():
    """Launch the Streamlit application."""
    print("\n🚀 Launching Hammarby Sjöstad Interactive Map...")
    
    current_dir = Path(__file__).parent
    app_file = current_dir / 'hammarby_interactive_map.py'
    
    try:
        # Launch Streamlit with the interactive map
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(app_file),
            "--browser.serverAddress", "localhost",
            "--browser.serverPort", "8501",
            "--server.enableCORS", "false",
            "--server.enableXsrfProtection", "false"
        ])
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Failed to launch Streamlit app: {e}")
        print("\nTry launching manually with:")
        print(f"streamlit run {app_file}")

def create_desktop_shortcut():
    """Create a desktop shortcut for easy access (optional)."""
    try:
        import platform
        
        if platform.system() == "Darwin":  # macOS
            print("\n🖥️  To create a desktop shortcut on macOS:")
            print("1. Open Automator")
            print("2. Create new Application")
            print("3. Add 'Run Shell Script' action")
            print(f"4. Set content to: cd '{Path(__file__).parent}' && python3 launch_interactive_map.py")
            print("5. Save as 'Hammarby Map' to Desktop")
            
        elif platform.system() == "Windows":
            print("\n🖥️  To create a desktop shortcut on Windows:")
            print("1. Right-click on Desktop")
            print("2. New > Shortcut")
            print(f"3. Location: python '{Path(__file__)}' ")
            print("4. Name: Hammarby Sjöstad Interactive Map")
            
    except Exception:
        pass

def print_usage_instructions():
    """Print usage instructions for the application."""
    print("\n" + "="*60)
    print("🏗️  HAMMARBY SJÖSTAD INTERACTIVE MAP")
    print("="*60)
    print("\n📋 FEATURES:")
    print("• Interactive map with building markers")
    print("• Polygon drawing tools for area selection")
    print("• Energy performance color coding")
    print("• Building details in popups")
    print("• Performance analytics and charts")
    print("• Export functionality for selected buildings")
    
    print("\n🎯 HOW TO USE:")
    print("1. The map will open in your web browser")
    print("2. Use the drawing tools to select building areas")
    print("3. Click on buildings for detailed information")
    print("4. Use sidebar filters to refine your view")
    print("5. Export selected buildings for further analysis")
    
    print("\n🔧 TROUBLESHOOTING:")
    print("• If map doesn't load, refresh the browser")
    print("• For polygon tools, use the drawing controls on the left")
    print("• If performance is slow, try filtering to fewer buildings")
    
    print("\n🌐 ACCESS:")
    print("• Local URL: http://localhost:8501")
    print("• To stop: Press Ctrl+C in this terminal")
    print("\n" + "="*60)

def main():
    """Main function to launch the interactive map application."""
    print("🏗️ Hammarby Sjöstad Interactive Map Launcher")
    print("=" * 50)
    
    # Check and install dependencies
    if not check_and_install_dependencies():
        print("\n❌ Dependency installation failed. Exiting.")
        return
    
    # Check data files
    if not check_data_files():
        print("\n❌ Required data files missing. Exiting.")
        return
    
    # Print usage instructions
    print_usage_instructions()
    
    # Create desktop shortcut option
    create_desktop_shortcut()
    
    # Launch the application
    print("\n⏳ Starting application in 3 seconds...")
    import time
    time.sleep(3)
    
    launch_streamlit_app()

if __name__ == "__main__":
    main()