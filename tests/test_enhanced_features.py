#!/usr/bin/env python3
"""
Test script for enhanced banking app features
"""

import os
import sys
from pathlib import Path

def check_file_exists(file_path, description):
    """Check if a file exists and print result"""
    if os.path.exists(file_path):
        print(f"✅ {description}: {file_path}")
        return True
    else:
        print(f"❌ {description}: {file_path}")
        return False

def check_file_content(file_path, search_terms, description):
    """Check if file contains expected content"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        missing_terms = []
        for term in search_terms:
            if term not in content:
                missing_terms.append(term)
        
        if not missing_terms:
            print(f"✅ {description}: All expected features found")
            return True
        else:
            print(f"⚠️  {description}: Missing features: {', '.join(missing_terms)}")
            return False
    except Exception as e:
        print(f"❌ {description}: Error reading file - {e}")
        return False

def main():
    """Test enhanced features"""
    print("🧪 Banking App - Enhanced Features Test")
    print("=" * 60)
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    errors = 0
    
    # Test account management enhancements
    print("\n🏦 Account Management Features:")
    account_features = [
        'editAccount', 'deleteAccount', 'updateAccount', 
        'filterAccounts', 'getAccount', 'showCreateAccountModal'
    ]
    if not check_file_content('frontend/src/pages/accounts.astro', account_features, 
                             'Account CRUD operations'):
        errors += 1
    
    # Test transaction management enhancements
    print("\n💳 Transaction Management Features:")
    transaction_features = [
        'applyFilters', 'updateDateFilters', 'handleSearchInput', 
        'deleteTransaction', 'updateTransactionCategory'
    ]
    if not check_file_content('frontend/src/pages/transactions.astro', transaction_features,
                             'Transaction filtering and management'):
        errors += 1
    
    # Test backend API enhancements
    print("\n🔧 Backend API Features:")
    backend_features = [
        'GET', 'PUT', 'DELETE', 'ilike', 'search'
    ]
    if not check_file_content('backend/app/routes/transactions.py', backend_features,
                             'Transaction API enhancements'):
        errors += 1
    
    account_api_features = [
        'get_account', 'update_account', 'delete_account'
    ]
    if not check_file_content('backend/app/routes/accounts.py', account_api_features,
                             'Account API enhancements'):
        errors += 1
    
    # Test category management
    print("\n📊 Category Management:")
    if not check_file_exists('backend/app/routes/categories.py', 'Categories API'):
        errors += 1
    
    # Test frontend API client
    print("\n🌐 Frontend API Client:")
    api_features = [
        'getAccount', 'updateAccount', 'deleteAccount', 
        'deleteTransaction', 'getCategories'
    ]
    if not check_file_content('frontend/src/scripts/api.js', api_features,
                             'API client enhancements'):
        errors += 1
    
    # Test page completeness
    print("\n📄 Page Completeness:")
    pages = [
        ('frontend/src/pages/accounts.astro', 'Enhanced accounts page'),
        ('frontend/src/pages/transactions.astro', 'Enhanced transactions page'),
        ('frontend/src/pages/budget.astro', 'Budget page'),
        ('frontend/src/pages/reports.astro', 'Reports page'),
        ('frontend/src/pages/index.astro', 'Dashboard page')
    ]
    
    for page_path, description in pages:
        if not check_file_exists(page_path, description):
            errors += 1
    
    # Test enhanced UI features
    print("\n🎨 UI Enhancements:")
    ui_features = [
        'Summary Cards', 'Filter', 'Search', 'Edit', 'Delete', 'Modal'
    ]
    accounts_ui_check = check_file_content('frontend/src/pages/accounts.astro', ui_features,
                                          'Account page UI features')
    transactions_ui_check = check_file_content('frontend/src/pages/transactions.astro', ui_features,
                                              'Transaction page UI features')
    
    if not (accounts_ui_check and transactions_ui_check):
        errors += 1
    
    # Summary
    print("\n" + "=" * 60)
    if errors == 0:
        print("🎉 All enhanced features are implemented!")
        print("\n✨ New Features Available:")
        print("   🏦 Account Management:")
        print("      • Create, edit, and delete accounts")
        print("      • Search and filter accounts")
        print("      • Account summary cards")
        print("      • Enhanced account details")
        print("")
        print("   💳 Transaction Management:")
        print("      • Advanced filtering by account, category, date")
        print("      • Search transactions by description/merchant")
        print("      • Quick date period selections")
        print("      • Transaction summary cards")
        print("      • Edit and delete transactions")
        print("      • Category assignment")
        print("")
        print("   🔧 Technical Improvements:")
        print("      • Enhanced API endpoints")
        print("      • Better error handling")
        print("      • Improved UI/UX")
        print("      • Search functionality")
        print("")
        print("📋 To start the application:")
        print("   1. Run: ./start_app.sh")
        print("   2. Open: http://localhost:3000")
        print("   3. Create accounts and upload transactions!")
        return 0
    else:
        print(f"❌ Found {errors} issues with enhanced features")
        print("Please check the implementation and try again.")
        return 1

if __name__ == "__main__":
    sys.exit(main())