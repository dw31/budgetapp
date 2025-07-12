# Banking Web Application

A comprehensive personal finance management web application that enables users to upload transaction data, automatically categorize expenses, create account-specific budgets, and generate financial reports. Built with modern technologies and featuring advanced ML-powered categorization.

This application does NOT connect to banks or financial institutions. All data must come from CSV files that you upload.


## ✅ Implemented Features

### Core Features (100% Complete)

#### 🔐 User Authentication & Profile Management
- ✅ User registration, login, and logout
- ✅ Secure session-based authentication with Flask-Login
- ✅ Complete profile management (update info, change password)
- ✅ Avatar upload and management
- ✅ Password hashing and security

#### 🏦 Account Management
- ✅ Multiple bank accounts per user
- ✅ Account types: Checking, Savings, Credit Cards, Investment
- ✅ Full CRUD operations (create, read, update, delete)
- ✅ Account metadata: name, institution, masked account numbers
- ✅ Opening and current balance tracking
- ✅ Account status management (active/inactive)

#### 📊 Advanced CSV Upload & Processing
- ✅ **4-step CSV upload wizard** with validation and preview
- ✅ Support for multiple bank formats (Chase, Bank of America, Wells Fargo, Generic)
- ✅ **Intelligent column mapping** with auto-detection and confidence scoring
- ✅ Preview functionality before import
- ✅ **Duplicate detection** using hash-based deduplication
- ✅ Session-based upload state management
- ✅ Import history tracking with comprehensive error handling

#### 💳 Transaction Management
- ✅ Transaction listing with pagination and advanced filtering
- ✅ Filter by account, category, date range, merchant, and search terms
- ✅ Transaction CRUD operations (create, read, update, delete)
- ✅ **Bulk operations** including bulk categorization
- ✅ Transaction metadata (merchant, reference numbers, confidence scores)

#### 🤖 Sophisticated ML-Powered Categorization
- ✅ **Machine Learning categorization** using scikit-learn
- ✅ Multiple categorization methods (ML, rules, merchant patterns, amounts)
- ✅ Pre-defined hierarchical category system
- ✅ **Custom categorization rules** (merchant, description, amount-based)
- ✅ Manual category override with confidence tracking
- ✅ Auto-categorization for uncategorized transactions
- ✅ **Bulk re-categorization tools**
- ✅ Categorization statistics and performance testing

#### 💰 Budget Management & Tracking
- ✅ **Account-specific budgeting** - create budgets for specific accounts
- ✅ Budget creation with multiple periods (monthly, quarterly, annual)
- ✅ Category-based budget allocation and tracking
- ✅ **Real-time budget vs actual tracking** with visual indicators
- ✅ Budget performance analysis and variance reporting
- ✅ **Budget alerts** at configurable thresholds (50%, 80%, 100%+)
- ✅ Recurring transaction detection and pattern analysis

### Partially Complete Features

#### 📈 Financial Reporting (Backend Complete, Frontend in Progress)
- ✅ **Backend APIs complete**: Cash flow statements, net worth calculations
- ✅ Spending analysis and trend reports
- ✅ Category-wise expense reports with date ranges
- ⚠️ **Frontend UI**: Basic structure exists, full charts and visualizations in progress

## 🚧 TODO: Features to Implement

### High Priority Missing Features

#### ✏️ Manual Transaction Entry
- ❌ **TODO**: Transaction creation form UI
- ❌ **TODO**: Manual transaction entry API endpoints
- ❌ **TODO**: Transaction validation for manual entries

#### 📤 Export Capabilities
- ❌ **TODO**: PDF report export
- ❌ **TODO**: CSV/Excel export for transactions and reports
- ❌ **TODO**: Downloadable financial statements

#### 📊 Enhanced Reporting Frontend
- ❌ **TODO**: Interactive charts and visualizations (Chart.js integration)
- ❌ **TODO**: Customizable report dashboards
- ❌ **TODO**: Comparative analysis views (month-over-month, year-over-year)

### Medium Priority Enhancements

#### 💰 Advanced Budget Features
- ❌ **TODO**: Budget templates and presets
- ❌ **TODO**: Goal-based budgeting (savings targets, debt payoff)
- ❌ **TODO**: Budget copy/clone functionality
- ❌ **TODO**: Historical budget performance tracking

#### 📈 Advanced Analytics
- ❌ **TODO**: Account balance history tracking and visualization
- ❌ **TODO**: Spending trend predictions
- ❌ **TODO**: Financial health scoring
- ❌ **TODO**: Automated insights and recommendations

#### 🔔 Notifications & Alerts
- ❌ **TODO**: Email/SMS budget alerts
- ❌ **TODO**: Unusual spending notifications
- ❌ **TODO**: Monthly financial summaries
- ❌ **TODO**: Goal achievement notifications

## Tech Stack

- **Frontend**: Astro with TypeScript and Tailwind CSS
- **Backend**: Python Flask with SQLAlchemy ORM
- **Database**: PostgreSQL (primary), SQLite (fallback)
- **ML/AI**: scikit-learn for transaction categorization
- **Authentication**: Flask-Login with session management

## Quick Start

### Option 1: Local Development (Recommended)

#### Prerequisites
- Python 3.9+
- Node.js 18+
- PostgreSQL (optional, SQLite fallback available)

#### Automated Setup
```bash
# Start both backend and frontend
./start_app.sh

# Or start individually
cd backend && source venv/bin/activate && python run.py  # Backend (port 5001)
cd frontend && npm run dev  # Frontend (port 3000)
```

#### Access the application
- Frontend: http://localhost:3000
- Backend API: http://localhost:5001

📖 **Detailed setup guide**: [LOCAL_SETUP.md](LOCAL_SETUP.md) | **Complete documentation**: [APPLICATION.md](APPLICATION.md)

### Option 2: Docker (Alternative)

#### Prerequisites
- Docker and Docker Compose

#### Setup and Run
```bash
# Clone the repository
git clone <your-repo>
cd banking-app

# Create uploads directory
mkdir -p uploads backend/uploads

# Start the application
docker-compose up --build
```

## Key API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Current user info
- `PUT /api/auth/profile` - Update profile
- `POST /api/auth/upload-avatar` - Upload avatar

### Accounts
- `GET /api/accounts` - List user accounts
- `POST /api/accounts` - Create new account
- `PUT /api/accounts/{id}` - Update account
- `DELETE /api/accounts/{id}` - Delete account

### Transactions & CSV Upload
- `GET /api/transactions` - List transactions (with advanced filtering)
- `POST /api/transactions/upload` - 4-step CSV upload wizard
- `PUT /api/transactions/{id}` - Update transaction
- `DELETE /api/transactions/{id}` - Delete transaction

### Budgets
- `GET /api/budgets` - List budgets
- `POST /api/budgets` - Create budget (with account selection)
- `PUT /api/budgets/{id}` - Update budget
- `DELETE /api/budgets/{id}` - Delete budget
- `GET /api/budgets/{id}/performance` - Budget vs actual analysis
- `GET /api/budgets/alerts` - Budget alert notifications

### Categories & Categorization
- `GET /api/categories` - List categories
- `POST /api/categories/rules` - Create categorization rule
- `POST /api/transactions/categorize` - Bulk categorization

### Reports (Backend Complete)
- `GET /api/reports/cashflow` - Cash flow statement
- `GET /api/reports/networth` - Net worth calculation
- `GET /api/reports/spending` - Spending analysis

## CSV Upload Formats Supported

### Generic Format
```csv
date,description,amount
2025-01-15,Grocery Store,-85.50
2025-01-14,Salary Deposit,3500.00
```

### Chase Bank Format
```csv
Transaction Date,Description,Amount
01/15/2025,GROCERY STORE,-85.50
01/14/2025,PAYROLL DEPOSIT,3500.00
```

### Bank of America & Wells Fargo
Automatic format detection handles various bank-specific CSV structures.

## Architecture Highlights

- **Account-Specific Budgets**: Budgets can be associated with one or more accounts
- **Advanced ML Categorization**: Multiple algorithms with confidence scoring
- **4-Step CSV Wizard**: Validation → Mapping → Preview → Import
- **Session-Based Upload**: Maintains state across upload steps
- **Duplicate Detection**: Hash-based transaction deduplication
- **Real-time Budget Tracking**: Live budget vs actual calculations
- **Comprehensive API**: RESTful endpoints with proper error handling

## Security Features

- Session-based authentication with secure cookies
- Password hashing with Werkzeug
- Input validation and SQL injection prevention
- File upload security with type and size validation
- CORS configuration for development

## Development & Testing

```bash
# Backend setup
cd backend && pip install -r requirements.txt
python run.py

# Frontend setup
cd frontend && npm install
npm run dev

# Run tests
python tests/test_connectivity.py
python tests/test_auth_system.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit a pull request

Focus areas for contributions:
- Manual transaction entry UI/API
- Export functionality (PDF, Excel)
- Enhanced reporting frontend
- Advanced budgeting features

## License

MIT License