# Banking Web Application - Project Structure

## Directory Structure
```
banking-app/
├── frontend/                 # Astro frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── AccountCard.astro
│   │   │   ├── TransactionTable.astro
│   │   │   ├── BudgetChart.astro
│   │   │   ├── FileUpload.astro
│   │   │   └── Layout.astro
│   │   ├── pages/
│   │   │   ├── index.astro
│   │   │   ├── accounts.astro
│   │   │   ├── transactions.astro
│   │   │   ├── budget.astro
│   │   │   └── reports.astro
│   │   ├── scripts/
│   │   │   └── api.js
│   │   └── styles/
│   │       └── global.css
│   ├── public/
│   ├── package.json
│   └── astro.config.mjs
├── backend/                  # Flask backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── account.py
│   │   │   ├── transaction.py
│   │   │   ├── category.py
│   │   │   └── budget.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── accounts.py
│   │   │   ├── transactions.py
│   │   │   ├── budgets.py
│   │   │   └── reports.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── csv_processor.py
│   │   │   ├── categorizer.py
│   │   │   └── report_generator.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── helpers.py
│   ├── migrations/
│   ├── requirements.txt
│   └── run.py
├── database/
│   ├── init.sql
│   └── seed_data.sql
├── docker-compose.yml
└── README.md
```

## Setup Instructions

### 1. Create Project Structure
```bash
mkdir banking-app
cd banking-app
mkdir -p frontend/{src/{components,pages,scripts,styles},public}
mkdir -p backend/{app/{models,routes,services,utils},migrations}
mkdir database
```

### 2. Frontend Setup (Astro)
```bash
cd frontend
npm create astro@latest . --template minimal --typescript
npm install @astrojs/tailwind tailwindcss @astrojs/node chart.js dropzone
```

### 3. Backend Setup (Flask)
```bash
cd ../backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install flask flask-sqlalchemy flask-login flask-cors pandas scikit-learn alembic psycopg2-binary python-dotenv
pip freeze > requirements.txt
```

### 4. Database Setup (PostgreSQL)
```bash
# Using Docker
docker run --name banking-postgres -e POSTGRES_PASSWORD=yourpassword -e POSTGRES_DB=banking_app -p 5432:5432 -d postgres:13

# Or install PostgreSQL locally and create database
createdb banking_app
```

### 5. Environment Configuration
Create `.env` file in backend directory:
```
DATABASE_URL=postgresql://username:password@localhost:5432/banking_app
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
```