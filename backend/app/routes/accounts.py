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
    try:
        data = request.get_json()
        
        required_fields = ['name', 'account_type']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Validate account_type
        valid_types = ['checking', 'savings', 'credit_card', 'investment']
        if data['account_type'] not in valid_types:
            return jsonify({'error': 'Invalid account type'}), 400
        
        opening_balance = data.get('opening_balance', 0.00)
        
        account = Account(
            user_id=current_user.id,
            name=data['name'],
            account_type=data['account_type'],
            institution=data.get('institution'),
            account_number_masked=data.get('account_number_masked'),
            opening_balance=opening_balance,
            current_balance=opening_balance  # Set current_balance to opening_balance
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
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating account: {str(e)}")
        return jsonify({'error': 'Failed to create account'}), 500

@accounts_bp.route('/<account_id>', methods=['GET'])
@login_required
def get_account(account_id):
    account = Account.query.filter_by(id=account_id, user_id=current_user.id).first()
    if not account:
        return jsonify({'error': 'Account not found'}), 404
    
    return jsonify({
        'id': str(account.id),
        'name': account.name,
        'account_type': account.account_type,
        'institution': account.institution,
        'account_number_masked': account.account_number_masked,
        'opening_balance': float(account.opening_balance),
        'current_balance': float(account.current_balance),
        'created_at': account.created_at.isoformat(),
        'is_active': account.is_active
    })

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
    if 'account_type' in data:
        account.account_type = data['account_type']
    
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