#!/usr/bin/env python3
"""
Local database setup script for the Banking App
This script will create and initialize the database with default data
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(f"   ✅ {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error: {e.stderr.strip() if e.stderr else str(e)}")
        return False

def check_postgresql():
    """Check if PostgreSQL is installed and running"""
    print("🔍 Checking PostgreSQL installation...")
    
    # Check if psql is available
    try:
        result = subprocess.run(['psql', '--version'], capture_output=True, text=True, check=True)
        print(f"   ✅ Found: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("   ❌ PostgreSQL not found or not in PATH")
        print("   💡 Please install PostgreSQL:")
        print("      - macOS: brew install postgresql")
        print("      - Ubuntu: sudo apt-get install postgresql postgresql-contrib")
        print("      - Windows: Download from https://www.postgresql.org/download/")
        return False

def setup_database():
    """Set up the database"""
    print("\n📊 Setting up database...")
    
    # Database configuration
    db_name = "banking_app"
    db_user = "dw31"
    
    # Check if database exists, create if not
    check_db_cmd = f'psql -U {db_user} -lqt | cut -d \\| -f 1 | grep -qw {db_name}'
    
    try:
        subprocess.run(check_db_cmd, shell=True, check=True)
        print(f"   ✅ Database '{db_name}' already exists")
    except subprocess.CalledProcessError:
        print(f"   📝 Creating database '{db_name}'...")
        create_db_cmd = f'createdb -U {db_user} {db_name}'
        if not run_command(create_db_cmd, f"Creating database {db_name}"):
            return False
    
    # Run initialization script
    init_script = Path("database/init.sql")
    if init_script.exists():
        init_cmd = f'psql -U {db_user} -d {db_name} -f {init_script}'
        if not run_command(init_cmd, "Running database initialization script"):
            return False
    else:
        print(f"   ⚠️  Warning: {init_script} not found")
    
    # Run seed data script
    seed_script = Path("database/seed_data.sql")
    if seed_script.exists():
        seed_cmd = f'psql -U {db_user} -d {db_name} -f {seed_script}'
        if not run_command(seed_cmd, "Running database seed script"):
            return False
    else:
        print(f"   ⚠️  Warning: {seed_script} not found")
    
    return True

def setup_sqlite_fallback():
    """Set up SQLite as a fallback option"""
    print("\n💾 Setting up SQLite fallback...")
    print("   📝 SQLite will be used as the database (no setup required)")
    print("   📝 Database file will be created automatically when the app starts")
    
    # Update .env to use SQLite
    env_file = Path("backend/.env")
    if env_file.exists():
        with open(env_file, 'r') as f:
            content = f.read()
        
        # Replace PostgreSQL URL with SQLite
        content = content.replace(
            'DATABASE_URL=postgresql://postgres:password@localhost:5432/banking_app',
            'DATABASE_URL=sqlite:///banking_app.db'
        )
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        print("   ✅ Updated .env file to use SQLite")
    
    return True

def main():
    """Main setup function"""
    print("🏦 Banking App - Local Database Setup")
    print("=" * 50)
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    # Check PostgreSQL availability
    if check_postgresql():
        # Try PostgreSQL setup
        if setup_database():
            print("\n🎉 PostgreSQL database setup completed successfully!")
            return 0
        else:
            print("\n⚠️  PostgreSQL setup failed, falling back to SQLite...")
            if setup_sqlite_fallback():
                print("\n🎉 SQLite fallback setup completed!")
                return 0
            else:
                print("\n❌ Database setup failed")
                return 1
    else:
        # Use SQLite fallback
        print("\n💾 PostgreSQL not available, using SQLite...")
        if setup_sqlite_fallback():
            print("\n🎉 SQLite setup completed!")
            return 0
        else:
            print("\n❌ Database setup failed")
            return 1

if __name__ == "__main__":
    sys.exit(main())