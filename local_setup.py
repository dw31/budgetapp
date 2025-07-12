#!/usr/bin/env python3
"""
Local development setup script for Banking App
This script will set up the entire application for local development
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description, cwd=None):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True,
            cwd=cwd
        )
        if result.stdout:
            output_lines = result.stdout.strip().split('\n')
            for line in output_lines[-3:]:  # Show last 3 lines
                if line.strip():
                    print(f"   📝 {line}")
        print(f"   ✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error: {e.stderr.strip() if e.stderr else str(e)}")
        return False

def check_prerequisites():
    """Check if required tools are installed"""
    print("🔍 Checking prerequisites...")
    
    prerequisites = {
        'python3': 'Python 3.9+',
        'node': 'Node.js 18+',
        'npm': 'npm package manager'
    }
    
    missing = []
    for cmd, desc in prerequisites.items():
        try:
            result = subprocess.run([cmd, '--version'], capture_output=True, text=True, check=True)
            print(f"   ✅ {desc}: {result.stdout.strip().split()[0] if result.stdout else 'Found'}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"   ❌ {desc}: Not found")
            missing.append(desc)
    
    if missing:
        print(f"\n❌ Missing prerequisites: {', '.join(missing)}")
        print("Please install the missing tools and try again.")
        return False
    
    return True

def setup_backend():
    """Set up the Flask backend"""
    print("\n🐍 Setting up Python backend...")
    
    backend_dir = Path("backend")
    
    # Create virtual environment
    venv_dir = backend_dir / "venv"
    if not venv_dir.exists():
        if not run_command("python3 -m venv venv", "Creating Python virtual environment", backend_dir):
            return False
    else:
        print("   ✅ Virtual environment already exists")
    
    # Determine activation script
    if os.name == 'nt':  # Windows
        activate_script = venv_dir / "Scripts" / "activate"
        pip_cmd = "venv\\Scripts\\pip"
        python_cmd = "venv\\Scripts\\python"
    else:  # Unix/Linux/macOS
        activate_script = venv_dir / "bin" / "activate"
        pip_cmd = "venv/bin/pip"
        python_cmd = "venv/bin/python"
    
    # Install dependencies
    if not run_command(f"{pip_cmd} install -r requirements.txt", "Installing Python dependencies", backend_dir):
        return False
    
    # Create uploads directory
    uploads_dir = backend_dir / "uploads"
    uploads_dir.mkdir(exist_ok=True)
    print("   ✅ Created uploads directory")
    
    return True

def setup_frontend():
    """Set up the Astro frontend"""
    print("\n🌐 Setting up Astro frontend...")
    
    frontend_dir = Path("frontend")
    
    # Install npm dependencies
    if not run_command("npm install", "Installing Node.js dependencies", frontend_dir):
        return False
    
    return True

def setup_environment():
    """Set up environment files"""
    print("\n⚙️  Setting up environment configuration...")
    
    # Backend environment
    backend_env = Path("backend/.env")
    backend_env_example = Path("backend/.env.example")
    
    if not backend_env.exists() and backend_env_example.exists():
        shutil.copy(backend_env_example, backend_env)
        print("   ✅ Created backend/.env from example")
    elif backend_env.exists():
        print("   ✅ Backend .env file already exists")
    
    return True

def create_start_scripts():
    """Create convenience start scripts"""
    print("\n📜 Creating start scripts...")
    
    # Backend start script
    backend_script_content = '''#!/bin/bash
# Start the Flask backend server
cd backend
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null
python run.py
'''
    
    # Frontend start script
    frontend_script_content = '''#!/bin/bash
# Start the Astro frontend server
cd frontend
npm run dev
'''
    
    # Combined start script
    combined_script_content = '''#!/bin/bash
# Start both backend and frontend servers
echo "🚀 Starting Banking App..."

# Function to kill background processes on exit
cleanup() {
    echo "🛑 Shutting down servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set up signal handling
trap cleanup SIGINT SIGTERM

# Start backend
echo "🐍 Starting backend server..."
cd backend
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null
python run.py &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to start
sleep 3

# Start frontend
echo "🌐 Starting frontend server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "✅ Servers started!"
echo "   - Backend:  http://localhost:5000"
echo "   - Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for background processes
wait $BACKEND_PID $FRONTEND_PID
'''
    
    # Write scripts
    scripts = [
        ("start_backend.sh", backend_script_content),
        ("start_frontend.sh", frontend_script_content),
        ("start_app.sh", combined_script_content)
    ]
    
    for script_name, content in scripts:
        script_path = Path(script_name)
        with open(script_path, 'w') as f:
            f.write(content)
        script_path.chmod(0o755)  # Make executable
        print(f"   ✅ Created {script_name}")
    
    return True

def main():
    """Main setup function"""
    print("🏦 Banking App - Local Development Setup")
    print("=" * 50)
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Check prerequisites
    if not check_prerequisites():
        return 1
    
    # Set up components
    if not setup_backend():
        print("\n❌ Backend setup failed")
        return 1
    
    if not setup_frontend():
        print("\n❌ Frontend setup failed")
        return 1
    
    if not setup_environment():
        print("\n❌ Environment setup failed")
        return 1
    
    if not create_start_scripts():
        print("\n❌ Script creation failed")
        return 1
    
    # Success message
    print("\n" + "=" * 50)
    print("🎉 Local development setup completed successfully!")
    print("\n📋 Next steps:")
    print("   1. Set up database: python setup_database.py")
    print("   2. Start the application: ./start_app.sh")
    print("   3. Or start components separately:")
    print("      - Backend only:  ./start_backend.sh")
    print("      - Frontend only: ./start_frontend.sh")
    print("\n🌐 Application URLs:")
    print("   - Frontend: http://localhost:3000")
    print("   - Backend API: http://localhost:5000")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())