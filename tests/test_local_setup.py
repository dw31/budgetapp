#!/usr/bin/env python3
"""
Test script for local setup verification
"""

import os
import sys
import subprocess
from pathlib import Path

def check_file_exists(file_path, description):
    """Check if a file exists and print result"""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path}")
        return False

def check_python_env():
    """Check Python environment setup"""
    print("\n🐍 Python Environment:")
    backend_dir = Path("backend")
    venv_dir = backend_dir / "venv"
    
    if venv_dir.exists():
        print(f"✅ Virtual environment exists: {venv_dir}")
        
        # Check if requirements are installed
        if os.name == 'nt':  # Windows
            pip_cmd = str(venv_dir / "Scripts" / "pip")
        else:  # Unix/Linux/macOS
            pip_cmd = str(venv_dir / "bin" / "pip")
        
        try:
            result = subprocess.run([pip_cmd, "list"], capture_output=True, text=True, check=True)
            installed_packages = result.stdout.lower()
            required_packages = ['flask', 'sqlalchemy', 'pandas', 'scikit-learn']
            
            for package in required_packages:
                if package in installed_packages:
                    print(f"✅ {package} installed")
                else:
                    print(f"❌ {package} not found")
                    
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Could not check installed packages")
            return False
    else:
        print(f"❌ Virtual environment not found: {venv_dir}")
        return False
    
    return True

def check_node_env():
    """Check Node.js environment setup"""
    print("\n🌐 Node.js Environment:")
    frontend_dir = Path("frontend")
    node_modules = frontend_dir / "node_modules"
    
    if node_modules.exists():
        print(f"✅ Node modules installed: {node_modules}")
        
        # Check package.json
        package_json = frontend_dir / "package.json"
        if package_json.exists():
            print(f"✅ Package.json exists: {package_json}")
        else:
            print(f"❌ Package.json missing: {package_json}")
            return False
    else:
        print(f"❌ Node modules not found: {node_modules}")
        return False
    
    return True

def check_configuration():
    """Check configuration files"""
    print("\n⚙️  Configuration:")
    
    config_files = [
        ("backend/.env", "Backend environment file"),
        ("backend/.env.example", "Backend environment example"),
        ("frontend/astro.config.mjs", "Astro configuration"),
        ("frontend/tailwind.config.mjs", "Tailwind configuration")
    ]
    
    all_exist = True
    for file_path, description in config_files:
        if not check_file_exists(file_path, description):
            all_exist = False
    
    return all_exist

def check_scripts():
    """Check start scripts"""
    print("\n📜 Start Scripts:")
    
    scripts = [
        ("local_setup.py", "Local setup script"),
        ("setup_database.py", "Database setup script"),
        ("start_app.sh", "Combined start script"),
        ("start_backend.sh", "Backend start script"),
        ("start_frontend.sh", "Frontend start script")
    ]
    
    all_exist = True
    for script_path, description in scripts:
        if check_file_exists(script_path, description):
            # Check if executable
            if os.access(script_path, os.X_OK):
                print(f"   ✅ {script_path} is executable")
            else:
                print(f"   ⚠️  {script_path} is not executable")
        else:
            all_exist = False
    
    return all_exist

def main():
    """Main test function"""
    print("🧪 Banking App - Local Setup Test")
    print("=" * 50)
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    errors = 0
    
    # Test different components
    if not check_configuration():
        errors += 1
    
    if not check_scripts():
        errors += 1
    
    if not check_python_env():
        errors += 1
    
    if not check_node_env():
        errors += 1
    
    # Summary
    print("\n" + "=" * 50)
    if errors == 0:
        print("🎉 Local setup verification passed!")
        print("\n📋 Ready to run:")
        print("   python3 setup_database.py  # Set up database")
        print("   ./start_app.sh            # Start the application")
        print("\n🌐 Application URLs:")
        print("   Frontend: http://localhost:3000")
        print("   Backend:  http://localhost:5000")
        return 0
    else:
        print(f"❌ Found {errors} issues with the setup")
        print("\n🔧 To fix issues:")
        print("   python3 local_setup.py    # Re-run setup")
        return 1

if __name__ == "__main__":
    sys.exit(main())