from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date
from decimal import Decimal
import uuid

db = SQLAlchemy()

# Association table for Budget-Account many-to-many relationship
budget_accounts = db.Table('budget_accounts',
    db.Column('budget_id', db.String(36), db.ForeignKey('budgets.id'), primary_key=True),
    db.Column('account_id', db.String(36), db.ForeignKey('accounts.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    avatar_url = db.Column(db.String(500))  # URL to avatar image
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    accounts = db.relationship('Account', backref='user', lazy=True, cascade='all, delete-orphan')
    budgets = db.relationship('Budget', backref='user', lazy=True, cascade='all, delete-orphan')
    upload_history = db.relationship('UploadHistory', backref='user', lazy=True, cascade='all, delete-orphan')
    categorization_rules = db.relationship('CategorizationRule', backref='user', lazy=True, cascade='all, delete-orphan')

class Account(db.Model):
    __tablename__ = 'accounts'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    account_type = db.Column(db.Enum('checking', 'savings', 'credit_card', 'investment', name='account_types'), nullable=False)
    institution = db.Column(db.String(255))
    account_number_masked = db.Column(db.String(20))
    opening_balance = db.Column(db.Numeric(12, 2), default=0.00)
    current_balance = db.Column(db.Numeric(12, 2), default=0.00)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='account', lazy=True, cascade='all, delete-orphan')
    upload_history = db.relationship('UploadHistory', backref='account', lazy=True, cascade='all, delete-orphan')

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    parent_id = db.Column(db.String(36), db.ForeignKey('categories.id'))
    color = db.Column(db.String(7), default='#6B7280')
    is_income = db.Column(db.Boolean, default=False)
    is_system = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='category', lazy=True)
    budget_items = db.relationship('BudgetItem', backref='category', lazy=True)
    categorization_rules = db.relationship('CategorizationRule', backref='category', lazy=True)
    
    # Self-referential relationship for parent categories
    children = db.relationship('Category', backref=db.backref('parent', remote_side=[id]))

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id = db.Column(db.String(36), db.ForeignKey('accounts.id'), nullable=False)
    category_id = db.Column(db.String(36), db.ForeignKey('categories.id'))
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text, nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    merchant = db.Column(db.String(255))
    reference_number = db.Column(db.String(100))
    category_confidence = db.Column(db.Float, default=0.0)
    is_manually_categorized = db.Column(db.Boolean, default=False)
    is_recurring = db.Column(db.Boolean, default=False)
    recurring_pattern_id = db.Column(db.String(64))  # Groups related recurring transactions
    hash_key = db.Column(db.String(64))
    upload_batch_id = db.Column(db.String(36))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Composite index for efficient duplicate detection
    __table_args__ = (
        db.Index('idx_duplicate_check', 'account_id', 'date', 'description', 'amount'),
    )

class Budget(db.Model):
    __tablename__ = 'budgets'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    period_type = db.Column(db.Enum('monthly', 'quarterly', 'annual', name='budget_periods'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    budget_items = db.relationship('BudgetItem', backref='budget', lazy=True, cascade='all, delete-orphan')
    accounts = db.relationship('Account', secondary=budget_accounts, lazy='subquery',
                              backref=db.backref('budgets', lazy=True))

class BudgetItem(db.Model):
    __tablename__ = 'budget_items'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    budget_id = db.Column(db.String(36), db.ForeignKey('budgets.id'), nullable=False)
    category_id = db.Column(db.String(36), db.ForeignKey('categories.id'), nullable=False)
    budgeted_amount = db.Column(db.Numeric(12, 2), nullable=False)
    actual_amount = db.Column(db.Numeric(12, 2), default=0.00)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class UploadHistory(db.Model):
    __tablename__ = 'upload_history'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    account_id = db.Column(db.String(36), db.ForeignKey('accounts.id'), nullable=False)
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

class CategorizationRule(db.Model):
    __tablename__ = 'categorization_rules'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.String(36), db.ForeignKey('categories.id'), nullable=False)
    rule_type = db.Column(db.Enum('merchant', 'description', 'amount', name='rule_types'), nullable=False)
    condition = db.Column(db.Enum('contains', 'equals', 'starts_with', 'ends_with', 'greater_than', 'less_than', name='rule_conditions'), nullable=False)
    value = db.Column(db.String(255), nullable=False)
    priority = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)