#!/usr/bin/env python3
"""
Quick start script for Banking App
This script provides a guided setup experience
"""

import os
import sys
import subprocess
from pathlib import Path

def print_banner():
    """Print welcome banner"""
    print("""
🏦 ========================================== 🏦
   Welcome to Banking App Setup
🏦 ========================================== 🏦

This script will help you get the Banking App
running on your local machine in just a few steps!
""")

def check_prerequisites():
    """Check and guide user through prerequisites"""
    print("🔍 Checking prerequisites...")
    
    prerequisites = [
        ('python3', 'Python 3.9+', 'https://www.python.org/downloads/'),
        ('node', 'Node.js 18+', 'https://nodejs.org/'),
        ('npm', 'npm (comes with Node.js)', 'https://nodejs.org/')
    ]
    
    missing = []
    for cmd, desc, url in prerequisites:
        try:
            result = subprocess.run([cmd, '--version'], capture_output=True, text=True, check=True)
            version = result.stdout.strip().split()[0] if result.stdout else 'Found'
            print(f"   ✅ {desc}: {version}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"   ❌ {desc}: Not found")
            print(f"      📥 Install from: {url}")
            missing.append(desc)
    
    if missing:
        print(f"\n⚠️  Please install missing prerequisites: {', '.join(missing)}")
        print("   Then run this script again.")
        return False
    
    print("   🎉 All prerequisites found!")
    return True

def ask_database_preference():
    """Ask user about database preference"""
    print("\n💾 Database Setup:")
    print("   1. PostgreSQL (recommended for production)")
    print("   2. SQLite (simple, no setup required)")
    
    while True:
        try:
            choice = input("\nSelect database option (1 or 2): ").strip()
            if choice == '1':
                return 'postgresql'
            elif choice == '2':
                return 'sqlite'
            else:
                print("Please enter 1 or 2")
        except KeyboardInterrupt:
            print("\n\n👋 Setup cancelled by user")
            sys.exit(0)

def run_setup_script():
    """Run the main setup script"""
    print("\n🔧 Running automated setup...")
    try:
        result = subprocess.run([sys.executable, 'local_setup.py'], check=True)
        print("   ✅ Setup completed successfully!")
        return True
    except subprocess.CalledProcessError:
        print("   ❌ Setup failed. Please check the output above.")
        return False

def setup_database(db_type):
    """Set up database based on user choice"""
    if db_type == 'sqlite':
        print("\n💾 Setting up SQLite database...")
        # Update .env file for SQLite
        env_file = Path("backend/.env")
        if env_file.exists():
            content = env_file.read_text()
            content = content.replace(
                'DATABASE_URL=postgresql://postgres:password@localhost:5432/banking_app',
                'DATABASE_URL=sqlite:///banking_app.db'
            )
            env_file.write_text(content)
            print("   ✅ Configured for SQLite")
        return True
    else:
        print("\n💾 Setting up PostgreSQL database...")
        try:
            result = subprocess.run([sys.executable, 'setup_database.py'], check=True)
            print("   ✅ Database setup completed!")
            return True
        except subprocess.CalledProcessError:
            print("   ⚠️  PostgreSQL setup failed, falling back to SQLite...")
            return setup_database('sqlite')

def show_completion_message():
    """Show completion message and next steps"""
    print("""
🎉 ========================================== 🎉
   Setup Complete!
🎉 ========================================== 🎉

Your Banking App is ready to run!

🚀 To start the application:
   ./start_app.sh

📱 Application URLs:
   Frontend: http://localhost:3000
   Backend:  http://localhost:5000

📋 What you can do:
   1. Register a new user account
   2. Create bank accounts
   3. Upload CSV transaction files
   4. Set up budgets
   5. View financial reports

📖 For more details, see:
   - LOCAL_SETUP.md (detailed setup guide)
   - README.md (general documentation)

🔧 Individual components:
   ./start_backend.sh   (backend only)
   ./start_frontend.sh  (frontend only)

Enjoy your Banking App! 💰
""")

def main():
    """Main setup flow"""
    try:
        print_banner()
        
        # Check prerequisites
        if not check_prerequisites():
            return 1
        
        # Ask about database
        db_type = ask_database_preference()
        
        # Run setup
        if not run_setup_script():
            return 1
        
        # Setup database
        if not setup_database(db_type):
            return 1
        
        # Show completion
        show_completion_message()
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled by user")
        return 0
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Please check the error and try again.")
        return 1

if __name__ == "__main__":
    sys.exit(main())