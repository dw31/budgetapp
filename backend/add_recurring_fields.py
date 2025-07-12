#!/usr/bin/env python3
"""
Migration script to add recurring transaction fields to the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db
from sqlalchemy import text

def migrate_database():
    app = create_app()
    
    with app.app_context():
        try:
            # Check if columns already exist
            result = db.engine.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'transactions' 
                AND column_name IN ('is_recurring', 'recurring_pattern_id')
            """))
            
            existing_columns = [row[0] for row in result]
            
            if 'is_recurring' not in existing_columns:
                print("Adding is_recurring column...")
                db.engine.execute(text("ALTER TABLE transactions ADD COLUMN is_recurring BOOLEAN DEFAULT FALSE"))
                
            if 'recurring_pattern_id' not in existing_columns:
                print("Adding recurring_pattern_id column...")
                db.engine.execute(text("ALTER TABLE transactions ADD COLUMN recurring_pattern_id VARCHAR(64)"))
                
            print("✅ Migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            if "SQLite" in str(type(db.engine)):
                # For SQLite, we need different syntax
                try:
                    print("Detected SQLite, using SQLite-compatible syntax...")
                    db.engine.execute(text("ALTER TABLE transactions ADD COLUMN is_recurring INTEGER DEFAULT 0"))
                    db.engine.execute(text("ALTER TABLE transactions ADD COLUMN recurring_pattern_id TEXT"))
                    print("✅ SQLite migration completed successfully!")
                except Exception as sqlite_error:
                    print(f"❌ SQLite migration also failed: {sqlite_error}")
                    print("You may need to recreate the database or add columns manually.")

if __name__ == "__main__":
    migrate_database()