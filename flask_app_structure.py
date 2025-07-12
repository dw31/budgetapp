# backend/app/__init__.py
from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager
from .models import db, User
import os

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://localhost/banking_app')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Initialize extensions
    db.init_app(app)
    CORS(app, origins=['http://localhost:3000'])  # Astro dev server
    
    # Login Manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)
    
    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.accounts import accounts_bp
    from .routes.transactions import transactions_bp
    from .routes.budgets import budgets_bp
    from .routes.reports import reports_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(accounts_bp, url_prefix='/api/accounts')
    app.register_blueprint(transactions_bp, url_prefix='/api/transactions')
    app.register_blueprint(budgets_bp, url_prefix='/api/budgets')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app

# backend/app/routes/auth.py
from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from ..models import db, User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['email', 'password', 'first_name', 'last_name']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if user already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'User already exists'}), 409
    
    # Create new user
    user = User(
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
        first_name=data['first_name'],
        last_name=data['last_name']
    )
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'message': 'User created successfully'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if user and check_password_hash(user.password_hash, data['password']):
        login_user(user)
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': str(user.id),
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        }), 200
    
    return jsonify({'error': 'Invalid credentials'}), 401

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'}), 200

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    return jsonify({
        'user': {
            'id': str(current_user.id),
            'email': current_user.email,
            'first_name': current_user.first_name,
            'last_name': current_user.last_name
        }
    }), 200

# backend/app/routes/accounts.py
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from ..models import db, Account

accounts_bp = Blueprint('accounts', __name__)

@accounts_bp.route('', methods=['GET'])
@login_required
def get_accounts():
    accounts = Account.query.filter_by(user_id=current_user.id, is_active=True).all()
    return jsonify([{
        'id': str(account.id),
        'name': account.name,
        'account_type': account.account_type,
        'institution': account.institution,
        'account_number_masked': account.account_number_masked,
        'current_balance': float(account.current_balance),
        'created_at': account.created_at.isoformat()
    } for account in accounts])

@accounts_bp.route('', methods=['POST'])
@login_required
def create_account():
    data = request.get_json()
    
    required_fields = ['name', 'account_type']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    account = Account(
        user_id=current_user.id,
        name=data['name'],
        account_type=data['account_type'],
        institution=data.get('institution'),
        account_number_masked=data.get('account_number_masked'),
        opening_balance=data.get('opening_balance', 0.00)
    )
    
    db.session.add(account)
    db.session.commit()
    
    return jsonify({
        'id': str(account.id),
        'name': account.name,
        'account_type': account.account_type,
        'institution': account.institution,
        'account_number_masked': account.account_number_masked,
        'current_balance': float(account.current_balance)
    }), 201

@accounts_bp.route('/<account_id>', methods=['PUT'])
@login_required
def update_account(account_id):
    account = Account.query.filter_by(id=account_id, user_id=current_user.id).first()
    if not account:
        return jsonify({'error': 'Account not found'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        account.name = data['name']
    if 'institution' in data:
        account.institution = data['institution']
    if 'account_number_masked' in data:
        account.account_number_masked = data['account_number_masked']
    
    db.session.commit()
    
    return jsonify({
        'id': str(account.id),
        'name': account.name,
        'account_type': account.account_type,
        'institution': account.institution,
        'account_number_masked': account.account_number_masked,
        'current_balance': float(account.current_balance)
    })

@accounts_bp.route('/<account_id>', methods=['DELETE'])
@login_required
def delete_account(account_id):
    account = Account.query.filter_by(id=account_id, user_id=current_user.id).first()
    if not account:
        return jsonify({'error': 'Account not found'}), 404
    
    account.is_active = False
    db.session.commit()
    
    return jsonify({'message': 'Account deleted successfully'}), 200

# backend/app/services/csv_processor.py
import pandas as pd
import hashlib
from datetime import datetime
from ..models import db, Transaction, UploadHistory
import uuid

class CSVProcessor:
    def __init__(self):
        self.supported_formats = {
            'chase': {
                'date_col': 'Transaction Date',
                'description_col': 'Description',
                'amount_col': 'Amount',
                'date_format': '%m/%d/%Y'
            },
            'bank_of_america': {
                'date_col': 'Date',
                'description_col': 'Description',
                'amount_col': 'Amount',
                'date_format': '%m/%d/%Y'
            },
            'wells_fargo': {
                'date_col': 'Date',
                'description_col': 'Description',
                'amount_col': 'Amount',
                'date_format': '%m/%d/%Y'
            },
            'generic': {
                'date_col': 'date',
                'description_col': 'description',
                'amount_col': 'amount',
                'date_format': '%Y-%m-%d'
            }
        }
    
    def process_csv(self, file_path, account_id, user_id, file_format='generic'):
        """Process CSV file and import transactions"""
        upload_history = UploadHistory(
            user_id=user_id,
            account_id=account_id,
            filename=file_path,
            status='processing'
        )
        db.session.add(upload_history)
        db.session.commit()
        
        try:
            # Read CSV file
            df = pd.read_csv(file_path)
            upload_history.total_rows = len(df)
            
            # Get format configuration
            format_config = self.supported_formats.get(file_format, self.supported_formats['generic'])
            
            # Process transactions
            processed_count = 0
            duplicate_count = 0
            error_count = 0
            batch_id = uuid.uuid4()
            
            for index, row in df.iterrows():
                try:
                    transaction_data = self._extract_transaction_data(row, format_config)
                    transaction_data['account_id'] = account_id
                    transaction_data['upload_batch_id'] = batch_id
                    
                    # Check for duplicates
                    hash_key = self._generate_hash(transaction_data)
                    if Transaction.query.filter_by(hash_key=hash_key).first():
                        duplicate_count += 1
                        continue
                    
                    transaction_data['hash_key'] = hash_key
                    transaction = Transaction(**transaction_data)
                    db.session.add(transaction)
                    processed_count += 1
                    
                except Exception as e:
                    error_count += 1
                    print(f"Error processing row {index}: {e}")
            
            db.session.commit()
            
            # Update upload history
            upload_history.processed_rows = processed_count
            upload_history.duplicate_rows = duplicate_count
            upload_history.error_rows = error_count
            upload_history.status = 'completed'
            upload_history.completed_at = datetime.utcnow()
            db.session.commit()
            
            return {
                'success': True,
                'processed': processed_count,
                'duplicates': duplicate_count,
                'errors': error_count
            }
            
        except Exception as e:
            upload_history.status = 'failed'
            upload_history.error_message = str(e)
            db.session.commit()
            return {'success': False, 'error': str(e)}
    
    def _extract_transaction_data(self, row, format_config):
        """Extract transaction data from CSV row"""
        date_str = str(row[format_config['date_col']])
        date_obj = datetime.strptime(date_str, format_config['date_format']).date()
        
        amount = float(row[format_config['amount_col']])
        description = str(row[format_config['description_col']])
        
        return {
            'date': date_obj,
            'description': description,
            'amount': amount,
            'merchant': self._extract_merchant(description)
        }
    
    def _extract_merchant(self, description):
        """Extract merchant name from transaction description"""
        # Simple merchant extraction logic
        words = description.split()
        return words[0] if words else description
    
    def _generate_hash(self, transaction_data):
        """Generate hash for duplicate detection"""
        hash_string = f"{transaction_data['date']}{transaction_data['description']}{transaction_data['amount']}"
        return hashlib.md5(hash_string.encode()).hexdigest()

# backend/app/services/categorizer.py
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import pickle
import os
from ..models import Transaction, Category, CategorizationRule

class TransactionCategorizer:
    def __init__(self):
        self.model = None
        self.model_path = 'categorization_model.pkl'
        self._load_or_create_model()
    
    def _load_or_create_model(self):
        """Load existing model or create new one"""
        if os.path.exists(self.model_path):
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
        else:
            self.model = Pipeline([
                ('tfidf', TfidfVectorizer(max_features=1000, stop_words='english')),
                ('classifier', MultinomialNB())
            ])
    
    def categorize_transaction(self, transaction):
        """Categorize a single transaction"""
        # First, try rule-based categorization
        category_id = self._apply_rules(transaction)
        if category_id:
            return category_id, 1.0  # 100% confidence for rule-based
        
        # Fallback to ML model
        if self.model and hasattr(self.model, 'predict_proba'):
            features = f"{transaction.description} {transaction.merchant or ''}"
            try:
                prediction = self.model.predict([features])[0]
                probability = self.model.predict_proba([features])[0].max()
                return prediction, probability
            except:
                pass
        
        # Default category (uncategorized)
        return self._get_default_category(), 0.0
    
    def _apply_rules(self, transaction):
        """Apply user-defined categorization rules"""
        rules = CategorizationRule.query.filter_by(is_active=True).order_by(CategorizationRule.priority).all()
        
        for rule in rules:
            if self._rule_matches(transaction, rule):
                return rule.category_id
        
        return None
    
    def _rule_matches(self, transaction, rule):
        """Check if transaction matches a rule"""
        if rule.rule_type == 'merchant':
            value = transaction.merchant or ''
        elif rule.rule_type == 'description':
            value = transaction.description
        elif rule.rule_type == 'amount':
            value = str(transaction.amount)
        else:
            return False
        
        if rule.condition == 'contains':
            return rule.value.lower() in value.lower()
        elif rule.condition == 'equals':
            return rule.value.lower() == value.lower()
        elif rule.condition == 'starts_with':
            return value.lower().startswith(rule.value.lower())
        elif rule.condition == 'ends_with':
            return value.lower().endswith(rule.value.lower())
        elif rule.condition == 'greater_than':
            return float(value) > float(rule.value)
        elif rule.condition == 'less_than':
            return float(value) < float(rule.value)
        
        return False
    
    def _get_default_category(self):
        """Get default uncategorized category"""
        category = Category.query.filter_by(name='Uncategorized', is_system=True).first()
        return category.id if category else None
    
    def train_model(self, transactions):
        """Train the ML model with categorized transactions"""
        if not transactions:
            return
        
        features = []
        labels = []
        
        for transaction in transactions:
            if transaction.category_id:
                feature_text = f"{transaction.description} {transaction.merchant or ''}"
                features.append(feature_text)
                labels.append(transaction.category_id)
        
        if features and labels:
            self.model.fit(features, labels)
            self._save_model()
    
    def _save_model(self):
        """Save the trained model"""
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)

# backend/app/routes/transactions.py
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from ..models import db, Transaction, Account
from ..services.csv_processor import CSVProcessor
from ..services.categorizer import TransactionCategorizer

transactions_bp = Blueprint('transactions', __name__)

@transactions_bp.route('', methods=['GET'])
@login_required
def get_transactions():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    account_id = request.args.get('account_id')
    category_id = request.args.get('category_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Build query
    query = Transaction.query.join(Account).filter(Account.user_id == current_user.id)
    
    if account_id:
        query = query.filter(Transaction.account_id == account_id)
    if category_id:
        query = query.filter(Transaction.category_id == category_id)
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    
    query = query.order_by(Transaction.date.desc())
    
    # Paginate
    transactions = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'transactions': [{
            'id': str(t.id),
            'date': t.date.isoformat(),
            'description': t.description,
            'amount': float(t.amount),
            'merchant': t.merchant,
            'category_id': str(t.category_id) if t.category_id else None,
            'account_id': str(t.account_id)
        } for t in transactions.items],
        'pagination': {
            'page': transactions.page,
            'pages': transactions.pages,
            'per_page': transactions.per_page,
            'total': transactions.total
        }
    })

@transactions_bp.route('/upload', methods=['POST'])
@login_required
def upload_transactions():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    account_id = request.form.get('account_id')
    file_format = request.form.get('format', 'generic')
    
    if not file.filename:
        return jsonify({'error': 'No file selected'}), 400
    
    if not account_id:
        return jsonify({'error': 'Account ID required'}), 400
    
    # Verify account ownership
    account = Account.query.filter_by(id=account_id, user_id=current_user.id).first()
    if not account:
        return jsonify({'error': 'Account not found'}), 404
    
    # Save uploaded file
    filename = secure_filename(file.filename)
    upload_path = os.path.join('uploads', filename)
    os.makedirs('uploads', exist_ok=True)
    file.save(upload_path)
    
    # Process CSV
    processor = CSVProcessor()
    result = processor.process_csv(upload_path, account_id, current_user.id, file_format)
    
    # Clean up uploaded file
    os.remove(upload_path)
    
    if result['success']:
        # Auto-categorize new transactions
        categorizer = TransactionCategorizer()
        new_transactions = Transaction.query.filter_by(upload_batch_id=result.get('batch_id')).all()
        
        for transaction in new_transactions:
            category_id, confidence = categorizer.categorize_transaction(transaction)
            if category_id:
                transaction.category_id = category_id
                transaction.category_confidence = confidence
        
        db.session.commit()
    
    return jsonify(result)

@transactions_bp.route('/<transaction_id>', methods=['PUT'])
@login_required
def update_transaction(transaction_id):
    # Get transaction and verify ownership
    transaction = Transaction.query.join(Account).filter(
        Transaction.id == transaction_id,
        Account.user_id == current_user.id
    ).first()
    
    if not transaction:
        return jsonify({'error': 'Transaction not found'}), 404
    
    data = request.get_json()
    
    if 'category_id' in data:
        transaction.category_id = data['category_id']
        transaction.is_manually_categorized = True
    
    if 'description' in data:
        transaction.description = data['description']
    
    if 'amount' in data:
        transaction.amount = data['amount']
    
    db.session.commit()
    
    return jsonify({
        'id': str(transaction.id),
        'date': transaction.date.isoformat(),
        'description': transaction.description,
        'amount': float(transaction.amount),
        'category_id': str(transaction.category_id) if transaction.category_id else None
    })

# backend/run.py
from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
            '