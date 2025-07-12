#!/usr/bin/env python3
"""
Database migration script to update schema for new user fields
"""

from app import create_app
from app.models import db, User, Category
from sqlalchemy import text
import os

def migrate_database():
    print("🔧 Migrating database schema...")
    
    app = create_app()
    
    with app.app_context():
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        print(f"   Using database: {db_uri}")
        
        if db_uri.startswith('postgresql'):
            print("   Using PostgreSQL database")
            try:
                # For PostgreSQL, check if tables exist
                with db.engine.connect() as conn:
                    result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
                    tables = [row[0] for row in result]
                    
                    if 'users' in tables:
                        print("   Found existing users table")
                        # Check if columns exist
                        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'users'"))
                        columns = [row[0] for row in result]
                        
                        if 'avatar_url' not in columns:
                            print("   Adding avatar_url column...")
                            conn.execute(text("ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500)"))
                            conn.commit()
                        
                        if 'is_active' not in columns:
                            print("   Adding is_active column...")
                            conn.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT true"))
                            conn.commit()
                    
                    # Check for recurring transaction fields
                    if 'transactions' in tables:
                        result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'transactions'"))
                        tx_columns = [row[0] for row in result]
                        
                        if 'is_recurring' not in tx_columns:
                            print("   Adding is_recurring column...")
                            conn.execute(text("ALTER TABLE transactions ADD COLUMN is_recurring BOOLEAN DEFAULT false"))
                            conn.commit()
                        
                        if 'recurring_pattern_id' not in tx_columns:
                            print("   Adding recurring_pattern_id column...")
                            conn.execute(text("ALTER TABLE transactions ADD COLUMN recurring_pattern_id VARCHAR(64)"))
                            conn.commit()
                    
                    # Check if hash_key unique constraint exists and remove it
                    try:
                        constraint_query = text("""
                            SELECT constraint_name 
                            FROM information_schema.table_constraints 
                            WHERE table_name = 'transactions' 
                            AND constraint_type = 'UNIQUE' 
                            AND constraint_name LIKE '%hash_key%'
                        """)
                        result = conn.execute(constraint_query)
                        constraints = [row[0] for row in result]
                        
                        for constraint_name in constraints:
                            print(f"   Dropping unique constraint on hash_key: {constraint_name}")
                            conn.execute(text(f"ALTER TABLE transactions DROP CONSTRAINT {constraint_name}"))
                            conn.commit()
                    except Exception as e:
                        print(f"   Note: Could not check/remove hash_key constraints: {e}")
                    
                    print("   ✅ Database migration completed")
                
                if 'users' not in tables:
                    print("   Creating new PostgreSQL database schema...")
                    db.create_all()
                    print("   ✅ PostgreSQL database created")
                    
            except Exception as e:
                print(f"   ⚠️  PostgreSQL migration failed: {e}")
                print("   Creating fresh database schema...")
                db.drop_all()
                db.create_all()
                print("   ✅ Fresh PostgreSQL database created")
        
        elif db_uri.startswith('sqlite'):
            print("   Using SQLite database")
            db_path = db_uri.replace('sqlite:///', '')
            if os.path.exists(db_path):
                print(f"   Found existing database: {db_path}")
                
                # Try to add missing columns manually
                try:
                    # Check if columns exist
                    with db.engine.connect() as conn:
                        result = conn.execute("PRAGMA table_info(users)")
                        columns = [row[1] for row in result]
                    
                    if 'avatar_url' not in columns:
                        print("   Adding avatar_url column...")
                        with db.engine.connect() as conn:
                            conn.execute("ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500)")
                            conn.commit()
                    
                    if 'is_active' not in columns:
                        print("   Adding is_active column...")
                        with db.engine.connect() as conn:
                            conn.execute("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1")
                            conn.commit()
                    
                    # Check for recurring transaction fields
                    with db.engine.connect() as conn:
                        result = conn.execute("PRAGMA table_info(transactions)")
                        tx_columns = [row[1] for row in result]
                    
                    if 'is_recurring' not in tx_columns:
                        print("   Adding is_recurring column...")
                        with db.engine.connect() as conn:
                            conn.execute("ALTER TABLE transactions ADD COLUMN is_recurring INTEGER DEFAULT 0")
                            conn.commit()
                    
                    if 'recurring_pattern_id' not in tx_columns:
                        print("   Adding recurring_pattern_id column...")
                        with db.engine.connect() as conn:
                            conn.execute("ALTER TABLE transactions ADD COLUMN recurring_pattern_id TEXT")
                            conn.commit()
                    
                    print("   ✅ Database migration completed")
                    
                except Exception as e:
                    print(f"   ⚠️  Migration failed: {e}")
                    print("   Creating fresh database...")
                    os.remove(db_path)
                    db.create_all()
                    print("   ✅ Fresh database created")
            else:
                print("   Creating new SQLite database...")
                db.create_all()
                print("   ✅ New SQLite database created")
        
        else:
            print("   Creating new database...")
            db.create_all()
            print("   ✅ New database created")
        
        # Create default categories if they don't exist
        if Category.query.count() == 0:
            print("   Creating default categories...")
            default_categories = [
                {'name': 'Food & Dining', 'color': '#10B981', 'is_income': False},
                {'name': 'Transportation', 'color': '#3B82F6', 'is_income': False},
                {'name': 'Shopping', 'color': '#8B5CF6', 'is_income': False},
                {'name': 'Entertainment', 'color': '#F59E0B', 'is_income': False},
                {'name': 'Bills & Utilities', 'color': '#EF4444', 'is_income': False},
                {'name': 'Healthcare', 'color': '#EC4899', 'is_income': False},
                {'name': 'Salary', 'color': '#059669', 'is_income': True},
                {'name': 'Business Income', 'color': '#0D9488', 'is_income': True},
                {'name': 'Investments', 'color': '#7C3AED', 'is_income': True},
                {'name': 'Other Income', 'color': '#65A30D', 'is_income': True},
            ]
            
            for cat_data in default_categories:
                category = Category(
                    name=cat_data['name'],
                    color=cat_data['color'],
                    is_income=cat_data['is_income'],
                    is_system=True
                )
                db.session.add(category)
            
            db.session.commit()
            print(f"   ✅ Created {len(default_categories)} default categories")

if __name__ == '__main__':
    migrate_database()
    print("\n🎉 Database migration completed successfully!")
    print("You can now start the application with: ./start_app.sh")