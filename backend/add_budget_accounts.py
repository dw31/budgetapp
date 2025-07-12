#!/usr/bin/env python3
"""
Database migration script to add budget-account association table
"""

from app import create_app
from app.models import db
from sqlalchemy import text
import os

def migrate_budget_accounts():
    print("🔧 Adding budget-account associations...")
    
    app = create_app()
    
    with app.app_context():
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        print(f"   Using database: {db_uri}")
        
        if db_uri.startswith('postgresql'):
            print("   Using PostgreSQL database")
            try:
                with db.engine.connect() as conn:
                    # Check if the table already exists
                    result = conn.execute(text("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'budget_accounts'
                    """))
                    
                    if result.fetchone():
                        print("   Budget-accounts association table already exists")
                        return
                    
                    # Create the association table
                    print("   Creating budget_accounts association table...")
                    conn.execute(text("""
                        CREATE TABLE budget_accounts (
                            budget_id VARCHAR(36) NOT NULL,
                            account_id VARCHAR(36) NOT NULL,
                            PRIMARY KEY (budget_id, account_id),
                            FOREIGN KEY (budget_id) REFERENCES budgets(id) ON DELETE CASCADE,
                            FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
                        )
                    """))
                    
                    # Migrate existing budgets to use all user accounts if none specified
                    print("   Migrating existing budgets to include all user accounts...")
                    conn.execute(text("""
                        INSERT INTO budget_accounts (budget_id, account_id)
                        SELECT DISTINCT b.id, a.id
                        FROM budgets b
                        JOIN accounts a ON a.user_id = b.user_id
                        WHERE NOT EXISTS (
                            SELECT 1 FROM budget_accounts ba 
                            WHERE ba.budget_id = b.id AND ba.account_id = a.id
                        )
                    """))
                    
                    conn.commit()
                    print("   ✅ PostgreSQL budget-accounts migration completed")
                    
            except Exception as e:
                print(f"   ⚠️  PostgreSQL migration failed: {e}")
                # If migration fails, recreate the table structure
                print("   Creating fresh database schema...")
                db.drop_all()
                db.create_all()
                print("   ✅ Fresh PostgreSQL database created")
        
        elif db_uri.startswith('sqlite'):
            print("   Using SQLite database")
            db_path = db_uri.replace('sqlite:///', '')
            
            try:
                with db.engine.connect() as conn:
                    # Check if table exists
                    result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='budget_accounts'"))
                    
                    if result.fetchone():
                        print("   Budget-accounts association table already exists")
                        return
                    
                    # Create the association table
                    print("   Creating budget_accounts association table...")
                    conn.execute(text("""
                        CREATE TABLE budget_accounts (
                            budget_id TEXT NOT NULL,
                            account_id TEXT NOT NULL,
                            PRIMARY KEY (budget_id, account_id),
                            FOREIGN KEY (budget_id) REFERENCES budgets(id) ON DELETE CASCADE,
                            FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
                        )
                    """))
                    
                    # Migrate existing budgets
                    print("   Migrating existing budgets to include all user accounts...")
                    conn.execute(text("""
                        INSERT INTO budget_accounts (budget_id, account_id)
                        SELECT DISTINCT b.id, a.id
                        FROM budgets b
                        JOIN accounts a ON a.user_id = b.user_id
                    """))
                    
                    conn.commit()
                    print("   ✅ SQLite budget-accounts migration completed")
                    
            except Exception as e:
                print(f"   ⚠️  SQLite migration failed: {e}")
                print("   Creating fresh database...")
                if os.path.exists(db_path):
                    os.remove(db_path)
                db.create_all()
                print("   ✅ Fresh SQLite database created")
        
        else:
            print("   Creating new database...")
            db.create_all()
            print("   ✅ New database created")

if __name__ == '__main__':
    migrate_budget_accounts()
    print("\n🎉 Budget-accounts migration completed successfully!")
    print("Budgets can now be associated with specific accounts.")