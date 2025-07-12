# Banking App - Local Development Setup

This guide will help you set up the Banking App for local development without Docker.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.9+** - [Download here](https://www.python.org/downloads/)
- **Node.js 18+** - [Download here](https://nodejs.org/)
- **PostgreSQL** (optional, SQLite is used as fallback) - [Download here](https://www.postgresql.org/download/)

### Quick Prerequisites Check

```bash
python3 --version
node --version
npm --version
```

## Automated Setup (Recommended)

### 1. Run the Setup Script

```bash
# Make sure you're in the project root directory
python3 local_setup.py
```

This script will:
- Check prerequisites
- Set up Python virtual environment
- Install Python dependencies
- Install Node.js dependencies
- Create environment files
- Generate start scripts

### 2. Set Up Database

```bash
python3 setup_database.py
```

This script will:
- Check for PostgreSQL installation
- Create and initialize the database
- Fall back to SQLite if PostgreSQL is not available

### 3. Start the Application

```bash
# Start both backend and frontend
./start_app.sh

# Or start them separately:
./start_backend.sh   # Backend only
./start_frontend.sh  # Frontend only
```

## Manual Setup

If you prefer to set up manually or the automated script doesn't work:

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create uploads directory
mkdir -p uploads

# Copy environment file
cp .env.example .env
```

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
```

### 3. Database Setup

#### Option A: PostgreSQL (Recommended)

```bash
# Install PostgreSQL (if not already installed)
# macOS: brew install postgresql
# Ubuntu: sudo apt-get install postgresql postgresql-contrib
# Windows: Download installer from postgresql.org

# Start PostgreSQL service
# macOS: brew services start postgresql
# Ubuntu: sudo service postgresql start
# Windows: Usually starts automatically

# Create database
createdb banking_app

# Initialize database
psql -d banking_app -f database/init.sql
psql -d banking_app -f database/seed_data.sql
```

#### Option B: SQLite (Fallback)

If PostgreSQL is not available, the app will automatically use SQLite:

```bash
# Update backend/.env file
# Change DATABASE_URL to:
DATABASE_URL=sqlite:///banking_app.db
```

### 4. Start the Application

#### Start Backend

```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python run.py
```

The backend will be available at: http://localhost:5000

#### Start Frontend

```bash
cd frontend
npm run dev
```

The frontend will be available at: http://localhost:3000

## Environment Configuration

The backend uses environment variables defined in `backend/.env`:

```bash
# Database (choose one)
DATABASE_URL=postgresql://postgres:password@localhost:5432/banking_app
# DATABASE_URL=sqlite:///banking_app.db

SECRET_KEY=your-secret-key-here
FLASK_ENV=development
FLASK_DEBUG=1
UPLOAD_FOLDER=./uploads
MAX_CONTENT_LENGTH=16777216
```

## Troubleshooting

### Common Issues

1. **PostgreSQL Connection Error**
   ```
   psql: error: connection to server on socket "/tmp/.s.PGSQL.5432" failed
   ```
   **Solution**: Start PostgreSQL service or switch to SQLite

2. **Python Module Not Found**
   ```
   ModuleNotFoundError: No module named 'flask'
   ```
   **Solution**: Ensure virtual environment is activated and dependencies are installed

3. **Node Modules Error**
   ```
   Error: Cannot find module 'astro'
   ```
   **Solution**: Run `npm install` in the frontend directory

4. **Port Already in Use**
   ```
   OSError: [Errno 48] Address already in use
   ```
   **Solution**: Kill existing processes or change ports in configuration

### Database Issues

If you encounter database issues:

1. **Reset SQLite Database**
   ```bash
   cd backend
   rm banking_app.db  # Remove existing database
   python run.py      # Will create new database
   ```

2. **Reset PostgreSQL Database**
   ```bash
   dropdb banking_app
   createdb banking_app
   psql -d banking_app -f database/init.sql
   psql -d banking_app -f database/seed_data.sql
   ```

### Port Configuration

To change default ports, update:

- **Backend**: Modify `PORT` in `backend/run.py` (default: 5000)
- **Frontend**: Modify `server.port` in `frontend/astro.config.mjs` (default: 3000)

## Development Workflow

### Making Changes

1. **Backend Changes**: 
   - Flask auto-reloads in development mode
   - No restart needed for most changes

2. **Frontend Changes**:
   - Astro has hot module replacement
   - Changes reflect immediately in browser

### Adding Dependencies

#### Backend (Python)
```bash
cd backend
source venv/bin/activate
pip install new-package
pip freeze > requirements.txt
```

#### Frontend (Node.js)
```bash
cd frontend
npm install new-package
```

### Database Migrations

When you modify the database schema:

1. Update `database/init.sql`
2. For existing databases, create migration scripts
3. Or reset the database (development only)

## Testing

### Backend Tests
```bash
cd backend
source venv/bin/activate
python -m pytest tests/  # If tests exist
```

### Frontend Tests
```bash
cd frontend
npm test  # If tests are configured
```

## Production Deployment

For production deployment:

1. Set `FLASK_ENV=production` in `.env`
2. Use a production WSGI server (Gunicorn, uWSGI)
3. Use PostgreSQL instead of SQLite
4. Build frontend: `npm run build`
5. Serve frontend with a web server (nginx, Apache)

## Getting Help

If you encounter issues:

1. Check the logs in terminal output
2. Verify all prerequisites are installed
3. Try the automated setup script
4. Check the troubleshooting section above
5. Create an issue in the project repository

## Application URLs

Once running:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **API Documentation**: http://localhost:5000/api (if implemented)

## Next Steps

After setup is complete:

1. Register a new user account
2. Create your first bank account
3. Upload a CSV file with transactions
4. Explore budgeting and reporting features

Enjoy using your Banking App! 🏦