from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from flask_login import LoginManager
from .models import db, User
import os
from dotenv import load_dotenv

def create_app():
    app = Flask(__name__)
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    
    # Database configuration - PostgreSQL as default, SQLite as fallback
    postgres_url = os.environ.get('DATABASE_URL', 'postgresql://localhost/banking_app')
    
    # Handle potential SQLite fallback for local development
    if postgres_url.startswith('sqlite'):
        app.config['SQLALCHEMY_DATABASE_URI'] = postgres_url
    else:
        # Try PostgreSQL first
        try:
            app.config['SQLALCHEMY_DATABASE_URI'] = postgres_url
        except Exception:
            # Fallback to SQLite for local development
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///banking_app.db'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB max file size
    
    # Session configuration for CORS
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    
    # Ensure upload directory exists
    upload_folder = os.environ.get('UPLOAD_FOLDER', './uploads')
    os.makedirs(upload_folder, exist_ok=True)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app, 
         origins=['http://localhost:3000', 'http://localhost:3001'],  # Astro dev server
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    
    # Login Manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = None  # Disable automatic redirects for API
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)
    
    @login_manager.unauthorized_handler
    def unauthorized():
        return jsonify({'error': 'Authentication required'}), 401
    
    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.accounts import accounts_bp
    from .routes.transactions import transactions_bp
    from .routes.budgets import budgets_bp
    from .routes.reports import reports_bp
    from .routes.categories import categories_bp
    from .routes.csv_upload import csv_upload_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(accounts_bp, url_prefix='/api/accounts')
    app.register_blueprint(transactions_bp, url_prefix='/api/transactions')
    app.register_blueprint(budgets_bp, url_prefix='/api/budgets')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(categories_bp, url_prefix='/api/categories')
    app.register_blueprint(csv_upload_bp, url_prefix='/api/csv')
    
    # Avatar serving route
    @app.route('/api/avatars/<filename>')
    def serve_avatar(filename):
        return send_from_directory(os.path.join(os.getcwd(), 'uploads', 'avatars'), filename)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app