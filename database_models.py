# backend/app/models/__init__.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
import uuid

db = SQLAlchemy()

# backend/app/models/user.py
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    accounts = db.relationship('Account', backref='owner', lazy=True, cascade='all, delete-orphan')
    budgets = db.relationship('Budget', backref='user', lazy=True, cascade='all, delete-orphan')

# backend/app/models/account.py
class Account(db.Model):
    __tablename__ = 'accounts'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    account_type = db.Column(db.Enum('checking', 'savings', 'credit_card', 'investment', name='account_types'), nullable=False)
    institution = db.Column(db.String(255))
    account_number_masked = db.Column(db.String(20))  # Only show last 4 digits
    opening_balance = db.Column(db.Numeric(12, 2), default=0.00)
    current_balance = db.Column(db.Numeric(12, 2), default=0.00)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='account', lazy=True, cascade='all, delete-orphan')
    
    def calculate_balance(self):
        """Calculate current balance based on transactions"""
        total_transactions = db.session.query(db.func.sum(Transaction.amount)).filter_by(account_id=self.id).scalar() or 0
        return self.opening_balance + total_transactions

# backend/app/models/category.py
class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), nullable=False)
    parent_id = db.Column(UUID(as_uuid=True), db.ForeignKey('categories.id'), nullable=True)
    color = db.Column(db.String(7), default='#6B7280')  # Hex color code
    is_income = db.Column(db.Boolean, default=False)
    is_system = db.Column(db.Boolean, default=False)  # System vs user-created
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Self-referential relationship for subcategories
    subcategories = db.relationship('Category', backref=db.backref('parent', remote_side=[id]))
    transactions = db.relationship('Transaction', backref='category', lazy=True)

# backend/app/models/transaction.py
class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = db.Column(UUID(as_uuid=True), db.ForeignKey('accounts.id'), nullable=False)
    category_id = db.Column(UUID(as_uuid=True), db.ForeignKey('categories.id'), nullable=True)
    
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)  # Positive for income, negative for expenses
    merchant = db.Column(db.String(255))
    reference_number = db.Column(db.String(100))
    
    # Categorization
    category_confidence = db.Column(db.Float, default=0.0)  # ML confidence score
    is_manually_categorized = db.Column(db.Boolean, default=False)
    
    # Deduplication
    hash_key = db.Column(db.String(64), unique=True)  # For duplicate detection
    
    # Upload tracking
    upload_batch_id = db.Column(UUID(as_uuid=True), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.Index('idx_transaction_date', 'date'),
        db.Index('idx_transaction_account', 'account_id'),
        db.Index('idx_transaction_category', 'category_id'),
    )

# backend/app/models/budget.py
class Budget(db.Model):
    __tablename__ = 'budgets'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    period_type = db.Column(db.Enum('monthly', 'quarterly', 'annual', name='budget_periods'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    budget_items = db.relationship('BudgetItem', backref='budget', lazy=True, cascade='all, delete-orphan')

class BudgetItem(db.Model):
    __tablename__ = 'budget_items'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    budget_id = db.Column(UUID(as_uuid=True), db.ForeignKey('budgets.id'), nullable=False)
    category_id = db.Column(UUID(as_uuid=True), db.ForeignKey('categories.id'), nullable=False)
    budgeted_amount = db.Column(db.Numeric(12, 2), nullable=False)
    actual_amount = db.Column(db.Numeric(12, 2), default=0.00)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    category = db.relationship('Category', backref='budget_items')

# backend/app/models/upload_history.py
class UploadHistory(db.Model):
    __tablename__ = 'upload_history'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    account_id = db.Column(UUID(as_uuid=True), db.ForeignKey('accounts.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer)
    total_rows = db.Column(db.Integer)
    processed_rows = db.Column(db.Integer)
    duplicate_rows = db.Column(db.Integer)
    error_rows = db.Column(db.Integer)
    status = db.Column(db.Enum('processing', 'completed', 'failed', name='upload_statuses'), nullable=False)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

# backend/app/models/categorization_rule.py
class CategorizationRule(db.Model):
    __tablename__ = 'categorization_rules'
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(UUID(as_uuid=True), db.ForeignKey('categories.id'), nullable=False)
    
    rule_type = db.Column(db.Enum('merchant', 'description', 'amount', name='rule_types'), nullable=False)
    condition = db.Column(db.Enum('contains', 'equals', 'starts_with', 'ends_with', 'greater_than', 'less_than', name='rule_conditions'), nullable=False)
    value = db.Column(db.String(255), nullable=False)
    
    priority = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    category = db.relationship('Category', backref='rules')