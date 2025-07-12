# Banking Web Application - Complete Documentation

## Overview
A comprehensive personal finance management web application built with modern technologies, enabling users to upload transaction data, automatically categorize expenses, create account-specific budgets, and generate detailed financial reports.

## Technology Stack
- **Frontend**: Astro with TypeScript and Tailwind CSS
- **Backend**: Flask with SQLAlchemy ORM and Flask-Login authentication
- **Database**: PostgreSQL (primary), SQLite (fallback for development)
- **APIs**: RESTful APIs with session-based authentication

## Key Features
- **Multi-Account Management**: Support for checking, savings, credit cards, and investment accounts
- **CSV Transaction Upload**: 4-step wizard with validation, mapping, preview, and import
- **Intelligent Categorization**: ML-powered automatic transaction categorization
- **Account-Specific Budgeting**: Budget creation with account filtering and real-time tracking
- **Financial Reports**: Cash flow statements, net worth calculations, spending analysis
- **User Authentication**: Complete profile management with avatar upload

## Quick Start

### Local Development (Recommended)
```bash
# Start both backend and frontend
./start_app.sh

# Backend only (port 5001)
cd backend && source venv/bin/activate && python run.py

# Frontend only (port 3000)
cd frontend && npm run dev

# Database migration
python backend/migrate_db.py
```

### Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL (optional - SQLite fallback available)

### Access Points
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5001
- **Database**: PostgreSQL on localhost:5432

## Architecture

### Backend Structure (`backend/app/`)
- **models/__init__.py**: All SQLAlchemy models (User, Account, Transaction, Category, Budget, etc.)
- **routes/**: Blueprint-based API endpoints
  - `auth.py`: Complete authentication system with profile management
  - `accounts.py`: Account CRUD operations
  - `transactions.py`: Transaction management with filtering
  - `csv_upload.py`: 4-step CSV import wizard with validation
  - `budgets.py`: Account-specific budget management with performance tracking
  - `reports.py`: Financial reports generation
  - `categories.py`: Transaction categories management
- **services/**: Business logic layer
  - `csv_validator.py`: File validation and intelligent column mapping
  - `csv_processor.py`: Transaction processing with duplicate detection
  - `categorizer.py`: ML-based transaction categorization
  - `report_generator.py`: Financial report generation

### Frontend Structure (`frontend/src/`)
- **pages/**: Astro page components
  - Authentication: `login.astro`, `register.astro`, `profile.astro`
  - Core Features: `accounts.astro`, `transactions.astro`, `budget-management.astro`
  - Data Import: `csv-upload.astro` (4-step wizard)
  - Analytics: `reports.astro`
- **components/Layout.astro**: Main layout with authentication-aware navigation
- **scripts/api.js**: Centralized API client with all backend endpoints

### Database Schema
Key relationships with many-to-many account associations:
- **User** → **Account** (1:many) → **Transaction** (1:many)
- **Category** → **Transaction** (1:many), supports hierarchical categories
- **Budget** ←→ **Account** (many:many via budget_accounts table)
- **Budget** → **BudgetItem** (1:many) → **Category** (many:1)
- **UploadHistory**: Tracks CSV import batches with comprehensive error handling

## Core Features Detail

### Authentication System
- Session-based authentication using Flask-Login
- Complete user profile management with avatar upload
- Password change with current password validation
- Protected routes with automatic redirection
- Avatar storage in `uploads/avatars/` with UUID naming

### Account-Specific Budget Management
Enhanced budget system allowing budgets to be associated with one or more accounts:
- **Budget Creation**: Select specific accounts for budget scope
- **Filtered Calculations**: All budget vs. actual calculations filter by selected accounts
- **Real-time Tracking**: Live budget performance with visual progress indicators
- **Alert System**: Configurable alerts at 50%, 80%, and 100%+ budget usage
- **Account Selection UI**: Intuitive checkbox interface for account association

### CSV Import Wizard
Multi-step process with session state management:
1. **File Upload**: Validation, encoding detection, sample data extraction
2. **Column Mapping**: Auto-detection with confidence scoring, manual override capability
3. **Preview**: Sample transaction display with mapping validation
4. **Import**: Batch processing with duplicate detection using MD5 hash keys

Supports multiple bank formats:
- Chase Bank, Bank of America, Wells Fargo
- Generic CSV format
- Smart column detection with pattern matching
- Date parsing with multiple format support
- Currency handling with symbol and parentheses parsing

### Financial Reporting
- **Cash Flow Statements**: Monthly, quarterly, and annual analysis
- **Net Worth Tracking**: Asset and liability calculations
- **Spending Analysis**: Category-wise breakdowns with trends
- **Budget Performance**: Variance analysis and goal tracking
- **Export Options**: PDF and CSV export capabilities

## API Reference

### Authentication Endpoints
```
POST /api/auth/register      # User registration
POST /api/auth/login         # User login
POST /api/auth/logout        # User logout
GET  /api/auth/me            # Current user info
PUT  /api/auth/profile       # Update profile
POST /api/auth/change-password    # Change password
POST /api/auth/upload-avatar      # Upload avatar
DELETE /api/auth/remove-avatar    # Remove avatar
```

### Core Application Endpoints
```
# Accounts
GET  /api/accounts           # List user accounts
POST /api/accounts           # Create account
PUT  /api/accounts/{id}      # Update account
DELETE /api/accounts/{id}    # Delete account

# Transactions
GET  /api/transactions       # List with filtering
POST /api/transactions/upload     # CSV upload
PUT  /api/transactions/{id}       # Update transaction
DELETE /api/transactions/{id}     # Delete transaction

# Account-Specific Budgets
GET  /api/budgets            # List budgets
POST /api/budgets            # Create budget (with account selection)
PUT  /api/budgets/{id}       # Update budget
DELETE /api/budgets/{id}     # Delete budget
GET  /api/budgets/{id}/performance   # Budget vs actual (filtered by accounts)
GET  /api/budgets/alerts     # Budget alert notifications

# Reports
GET  /api/reports/cashflow   # Cash flow statement
GET  /api/reports/networth   # Net worth calculation
GET  /api/reports/spending   # Spending analysis
```

## Environment Configuration

### Required Environment Variables
```bash
# Backend (.env)
DATABASE_URL=postgresql://localhost/banking_app
SECRET_KEY=your-secret-key-here-change-in-production
PORT=5001
MAX_CONTENT_LENGTH=16777216
```

### Database Options
- **PostgreSQL (Recommended)**: Full-featured with better performance
- **SQLite (Fallback)**: Automatic fallback for development (`banking_app.db`)

## Security Features
- **Password Hashing**: Werkzeug secure password hashing with salt
- **Session Management**: Flask-Login with secure session cookies
- **File Upload Security**: Type validation, size limits, secure filename handling
- **Input Validation**: Comprehensive server-side validation with SQLAlchemy ORM
- **CORS Configuration**: Properly configured for `localhost:3000` and `localhost:3001`

## Development Workflow

### Making Changes
- **Backend**: Flask auto-reloads in development mode
- **Frontend**: Astro provides hot module replacement
- **Database**: Use migration scripts or restart for schema changes

### Testing Commands
```bash
# Backend dependencies
cd backend && pip install -r requirements.txt

# Frontend dependencies
cd frontend && npm install

# Frontend build
cd frontend && npm run build

# Database setup
./setup_postgres.sh  # PostgreSQL setup if needed
```

## Key Implementation Details

### Port Configuration
- **Backend**: Port 5001 (changed from 5000 to avoid macOS AirPlay conflict)
- **Frontend**: Port 3000
- **PostgreSQL**: Port 5432

### Budget Account Association
The enhanced budget system uses a many-to-many relationship:
```sql
-- Association table for budget-account relationships
budget_accounts (
    budget_id VARCHAR(36) FOREIGN KEY,
    account_id VARCHAR(36) FOREIGN KEY,
    PRIMARY KEY (budget_id, account_id)
)
```

All budget calculations filter transactions by the selected accounts:
```python
# Example: Budget vs actual calculation with account filtering
budget_account_ids = [acc.id for acc in budget.accounts]
actual_amount = db.session.query(func.sum(Transaction.amount)).join(Account).filter(
    Account.user_id == current_user.id,
    Account.id.in_(budget_account_ids) if budget_account_ids else True,
    Transaction.category_id == item.category_id,
    Transaction.date >= budget.start_date,
    Transaction.date <= budget.end_date,
    Transaction.amount < 0
).scalar() or 0
```

### CSV Processing Architecture
- **File Validation**: Type, size, and encoding detection
- **Column Mapping**: Pattern-based auto-detection with confidence scoring
- **Duplicate Detection**: MD5 hash comparison of date+description+amount
- **Batch Processing**: Efficient database inserts with progress tracking
- **Error Handling**: Comprehensive error capture and user feedback

### Performance Optimizations
- **Database Indexing**: Key columns indexed for faster queries
- **Query Optimization**: Efficient joins and filtered queries
- **File Processing**: Batch processing for large CSV files
- **Session Management**: Optimized session handling for CSV upload wizard

## Troubleshooting

### Common Issues
1. **Port 5000 Conflict**: Use port 5001 for backend (macOS AirPlay conflict resolution)
2. **Database Connection**: Automatic PostgreSQL to SQLite fallback
3. **File Upload Errors**: Check permissions on `uploads/` directory
4. **Frontend Build Issues**: Ensure Node.js 18+ and run `npm install`

### Development Commands
```bash
# Check connectivity
python tests/test_connectivity.py

# Database migration
python backend/migrate_db.py

# Clean restart
pkill -f "python run.py" && pkill -f "npm run dev" && ./start_app.sh
```

## Recent Enhancements

### Budget System Upgrade
- **Account Association**: Budgets can now be limited to specific accounts
- **Enhanced UI**: Account selection interface with checkboxes
- **Filtered Calculations**: All budget metrics respect account selections
- **Migration Support**: Database migration for budget_accounts table

### Authentication Improvements
- **Avatar System**: Complete profile picture management
- **Password Security**: Enhanced password change workflow
- **Session Handling**: Improved session management and CORS configuration

### CSV Import Enhancements
- **Smart Detection**: Improved column mapping with pattern recognition
- **Error Handling**: Better error messages and recovery options
- **Progress Tracking**: Real-time import progress indicators

This application provides a solid foundation for personal finance management with room for additional features and scaling. The architecture supports both individual users and potential multi-tenant deployments.