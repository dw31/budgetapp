#!/usr/bin/env python3
"""
Simple setup test script to verify all components are properly created
"""

import os
import sys

def check_file_exists(file_path, description):
    """Check if a file exists and print result"""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path}")
        return False

def check_directory_exists(dir_path, description):
    """Check if a directory exists and print result"""
    if os.path.isdir(dir_path):
        print(f"✅ {description}: {dir_path}")
        return True
    else:
        print(f"❌ {description}: {dir_path}")
        return False

def main():
    """Run setup verification tests"""
    print("🔍 Banking App Setup Verification")
    print("=" * 50)
    
    errors = 0
    
    # Check main directories
    print("\n📁 Directory Structure:")
    directories = [
        ("frontend/src/components", "Frontend components directory"),
        ("frontend/src/pages", "Frontend pages directory"),
        ("frontend/src/scripts", "Frontend scripts directory"),
        ("backend/app/models", "Backend models directory"),
        ("backend/app/routes", "Backend routes directory"),
        ("backend/app/services", "Backend services directory"),
        ("backend/app/utils", "Backend utils directory"),
        ("database", "Database directory"),
        ("uploads", "Uploads directory")
    ]
    
    for dir_path, description in directories:
        if not check_directory_exists(dir_path, description):
            errors += 1
    
    # Check backend files
    print("\n🐍 Backend Files:")
    backend_files = [
        ("backend/app/__init__.py", "Flask app factory"),
        ("backend/app/models/__init__.py", "Database models"),
        ("backend/app/routes/auth.py", "Authentication routes"),
        ("backend/app/routes/accounts.py", "Account routes"),
        ("backend/app/routes/transactions.py", "Transaction routes"),
        ("backend/app/routes/budgets.py", "Budget routes"),
        ("backend/app/routes/reports.py", "Report routes"),
        ("backend/app/services/csv_processor.py", "CSV processor service"),
        ("backend/app/services/categorizer.py", "Transaction categorizer"),
        ("backend/app/services/report_generator.py", "Report generator"),
        ("backend/run.py", "Flask application entry point"),
        ("backend/requirements.txt", "Python dependencies"),
        ("backend/Dockerfile", "Backend Docker configuration")
    ]
    
    for file_path, description in backend_files:
        if not check_file_exists(file_path, description):
            errors += 1
    
    # Check frontend files
    print("\n🌐 Frontend Files:")
    frontend_files = [
        ("frontend/src/components/Layout.astro", "Main layout component"),
        ("frontend/src/components/AccountCard.astro", "Account card component"),
        ("frontend/src/components/FileUpload.astro", "File upload component"),
        ("frontend/src/components/TransactionTable.astro", "Transaction table component"),
        ("frontend/src/components/BudgetChart.astro", "Budget chart component"),
        ("frontend/src/pages/index.astro", "Dashboard page"),
        ("frontend/src/pages/accounts.astro", "Accounts page"),
        ("frontend/src/scripts/api.js", "API client script"),
        ("frontend/package.json", "Frontend dependencies"),
        ("frontend/astro.config.mjs", "Astro configuration"),
        ("frontend/tailwind.config.mjs", "Tailwind configuration"),
        ("frontend/Dockerfile", "Frontend Docker configuration")
    ]
    
    for file_path, description in frontend_files:
        if not check_file_exists(file_path, description):
            errors += 1
    
    # Check database files
    print("\n🗄️ Database Files:")
    database_files = [
        ("database/init.sql", "Database initialization script"),
        ("database/seed_data.sql", "Database seed data")
    ]
    
    for file_path, description in database_files:
        if not check_file_exists(file_path, description):
            errors += 1
    
    # Check configuration files
    print("\n⚙️ Configuration Files:")
    config_files = [
        ("docker-compose.yml", "Docker Compose configuration"),
        ("backend/.env", "Backend environment variables"),
        ("README.md", "Project documentation")
    ]
    
    for file_path, description in config_files:
        if not check_file_exists(file_path, description):
            errors += 1
    
    # Summary
    print("\n" + "=" * 50)
    if errors == 0:
        print("🎉 All files and directories are present!")
        print("📋 Next steps:")
        print("   1. Run: docker-compose up --build")
        print("   2. Access frontend: http://localhost:3000")
        print("   3. Access backend API: http://localhost:5000")
        print("   4. Database: localhost:5432")
        return 0
    else:
        print(f"❌ Found {errors} missing files/directories")
        print("Please check the setup and ensure all files are created properly.")
        return 1

if __name__ == "__main__":
    sys.exit(main())