#!/usr/bin/env python3
"""
Simple migration script to add recurring transaction fields
"""

import os
import sys

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def run_migration():
    try:
        # Import and run the migration
        from migrate_db import migrate_database
        migrate_database()
        print("✅ Migration completed successfully!")
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    if run_migration():
        print("🎉 Database is ready with recurring transaction support!")
    else:
        print("⚠️ Migration had issues. Please check the error messages above.")