from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from ..models import db, Transaction, Account, Category
from ..services.csv_processor import CSVProcessor
from ..services.categorizer import TransactionCategorizer

transactions_bp = Blueprint('transactions', __name__)

@transactions_bp.route('', methods=['GET'])
@login_required
def get_transactions():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    account_id = request.args.get('account_id')
    category_id = request.args.get('category_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    search = request.args.get('search')
    
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
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                Transaction.description.ilike(search_term),
                Transaction.merchant.ilike(search_term)
            )
        )
    
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
            'category_name': t.category.name if t.category else None,
            'category_color': t.category.color if t.category else None,
            'is_manually_categorized': t.is_manually_categorized,
            'category_confidence': t.category_confidence or 0.0,
            'is_recurring': getattr(t, 'is_recurring', False),
            'recurring_pattern_id': getattr(t, 'recurring_pattern_id', None),
            'account_id': str(t.account_id),
            'account_name': t.account.name if t.account else None
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
    
    # Add categorization information to the result
    if result.get('success'):
        result['message'] = f"Successfully imported {result['processed']} transactions as uncategorized. Visit the Categories page to run auto-categorization."
        result['categorization_note'] = "All transactions were imported without categories. Use auto-categorization to assign categories automatically."
    
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
        transaction.category_confidence = 1.0  # Manual categorization has 100% confidence
    
    if 'description' in data:
        transaction.description = data['description']
    
    if 'amount' in data:
        transaction.amount = data['amount']
    
    if 'merchant' in data:
        transaction.merchant = data['merchant']
    
    db.session.commit()
    
    return jsonify({
        'id': str(transaction.id),
        'date': transaction.date.isoformat(),
        'description': transaction.description,
        'amount': float(transaction.amount),
        'merchant': transaction.merchant,
        'category_id': str(transaction.category_id) if transaction.category_id else None,
        'category_name': transaction.category.name if transaction.category else None,
        'category_color': transaction.category.color if transaction.category else None,
        'is_manually_categorized': transaction.is_manually_categorized,
        'category_confidence': transaction.category_confidence or 0.0,
        'is_recurring': getattr(transaction, 'is_recurring', False),
        'recurring_pattern_id': getattr(transaction, 'recurring_pattern_id', None)
    })

@transactions_bp.route('/<transaction_id>', methods=['DELETE'])
@login_required
def delete_transaction(transaction_id):
    # Get transaction and verify ownership
    transaction = Transaction.query.join(Account).filter(
        Transaction.id == transaction_id,
        Account.user_id == current_user.id
    ).first()
    
    if not transaction:
        return jsonify({'error': 'Transaction not found'}), 404
    
    db.session.delete(transaction)
    db.session.commit()
    
    return jsonify({'message': 'Transaction deleted successfully'}), 200