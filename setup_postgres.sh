#!/bin/bash

# PostgreSQL Setup Script for Banking App
echo "🐘 Setting up PostgreSQL for Banking App..."

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL is not installed. Please install PostgreSQL first."
    echo "On macOS: brew install postgresql"
    echo "On Ubuntu: sudo apt-get install postgresql postgresql-contrib"
    exit 1
fi

# Check if PostgreSQL is running
if ! pg_isready -h localhost -p 5432; then
    echo "❌ PostgreSQL is not running. Please start PostgreSQL first."
    echo "On macOS: brew services start postgresql"
    echo "On Ubuntu: sudo systemctl start postgresql"
    exit 1
fi

echo "✅ PostgreSQL is running"

# Create database if it doesn't exist
echo "📊 Creating banking_app database..."
psql -h localhost -U $USER -c "CREATE DATABASE banking_app;" 2>/dev/null || echo "Database already exists"

# Test database connection
if psql -h localhost -U $USER -d banking_app -c "SELECT 1;" &> /dev/null; then
    echo "✅ Database connection successful"
else
    echo "❌ Failed to connect to database"
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
cd backend
source venv/bin/activate || {
    echo "❌ Virtual environment not found. Please run: python -m venv venv"
    exit 1
}

pip install -r requirements.txt

# Run database migration
echo "🔧 Running database migration..."
python migrate_db.py

echo "🎉 PostgreSQL setup complete!"
echo "Database URI: postgresql://localhost/banking_app"
echo "You can now start the application with: ./start_app.sh"