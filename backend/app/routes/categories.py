from flask import Blueprint, request, jsonify, session
from flask_login import login_required, current_user
from ..models import db, Category, Transaction, Account, CategorizationRule
from ..services.categorizer import TransactionCategorizer
from sqlalchemy import func, and_

categories_bp = Blueprint('categories', __name__)

@categories_bp.route('', methods=['GET'])
@login_required
def get_categories():
    """Get all categories (system + user's custom categories)"""
    try:
        # Get system categories (available to all users) - ordered alphabetically
        system_categories = Category.query.filter_by(is_system=True).order_by(Category.name.asc()).all()
        
        # Get user's custom categories (non-system categories) - ordered alphabetically
        user_categories = Category.query.filter_by(is_system=False).order_by(Category.name.asc()).all()
        
        all_categories = system_categories + user_categories
        
        # Get category usage statistics
        user_accounts = Account.query.filter_by(user_id=current_user.id).all()
        account_ids = [acc.id for acc in user_accounts]
        
        category_stats = {}
        if account_ids:
            stats_query = db.session.query(
                Transaction.category_id,
                func.count(Transaction.id).label('transaction_count'),
                func.sum(Transaction.amount).label('total_amount')
            ).filter(
                Transaction.account_id.in_(account_ids),
                Transaction.category_id.isnot(None)
            ).group_by(Transaction.category_id).all()
            
            for stat in stats_query:
                category_stats[stat.category_id] = {
                    'transaction_count': stat.transaction_count,
                    'total_amount': float(stat.total_amount) if stat.total_amount else 0
                }
        
        categories_data = []
        for category in all_categories:
            stats = category_stats.get(category.id, {'transaction_count': 0, 'total_amount': 0})
            categories_data.append({
                'id': str(category.id),
                'name': category.name,
                'parent_id': str(category.parent_id) if category.parent_id else None,
                'color': category.color,
                'is_income': category.is_income,
                'is_system': category.is_system,
                'transaction_count': stats['transaction_count'],
                'total_amount': stats['total_amount']
            })
        
        return jsonify(categories_data)
        
    except Exception as e:
        return jsonify({'error': f'Failed to get categories: {str(e)}'}), 500

@categories_bp.route('', methods=['POST'])
@login_required
def create_category():
    """Create a new custom category"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or not data.get('name'):
            return jsonify({'error': 'Category name is required'}), 400
        
        # Check if category already exists
        existing_category = Category.query.filter_by(name=data['name']).first()
        if existing_category:
            return jsonify({'error': 'Category with this name already exists'}), 400
        
        # Create new category
        category = Category(
            name=data['name'],
            parent_id=data.get('parent_id'),
            color=data.get('color', '#6B7280'),
            is_income=data.get('is_income', False),
            is_system=False  # User-created categories are not system categories
        )
        
        db.session.add(category)
        db.session.commit()
        
        return jsonify({
            'id': str(category.id),
            'name': category.name,
            'parent_id': str(category.parent_id) if category.parent_id else None,
            'color': category.color,
            'is_income': category.is_income,
            'is_system': category.is_system
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create category: {str(e)}'}), 500

@categories_bp.route('/<category_id>', methods=['PUT'])
@login_required
def update_category(category_id):
    """Update an existing category"""
    try:
        category = Category.query.get_or_404(category_id)
        
        # Don't allow updating system categories
        if category.is_system:
            return jsonify({'error': 'Cannot modify system categories'}), 403
        
        data = request.get_json()
        
        # Update fields
        if 'name' in data:
            # Check if new name already exists
            existing = Category.query.filter(
                Category.name == data['name'],
                Category.id != category_id
            ).first()
            if existing:
                return jsonify({'error': 'Category with this name already exists'}), 400
            category.name = data['name']
        
        if 'parent_id' in data:
            category.parent_id = data['parent_id']
        if 'color' in data:
            category.color = data['color']
        if 'is_income' in data:
            category.is_income = data['is_income']
        
        db.session.commit()
        
        return jsonify({
            'id': str(category.id),
            'name': category.name,
            'parent_id': str(category.parent_id) if category.parent_id else None,
            'color': category.color,
            'is_income': category.is_income,
            'is_system': category.is_system
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update category: {str(e)}'}), 500

@categories_bp.route('/<category_id>', methods=['DELETE'])
@login_required
def delete_category(category_id):
    """Delete a category"""
    try:
        category = Category.query.get_or_404(category_id)
        
        # Don't allow deleting system categories
        if category.is_system:
            return jsonify({'error': 'Cannot delete system categories'}), 403
        
        # Check if category is being used by transactions
        user_accounts = Account.query.filter_by(user_id=current_user.id).all()
        account_ids = [acc.id for acc in user_accounts]
        
        transaction_count = Transaction.query.filter(
            Transaction.account_id.in_(account_ids),
            Transaction.category_id == category_id
        ).count()
        
        if transaction_count > 0:
            return jsonify({
                'error': f'Cannot delete category. It is used by {transaction_count} transactions.',
                'suggestion': 'Please recategorize these transactions first.'
            }), 400
        
        # Delete the category
        db.session.delete(category)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete category: {str(e)}'}), 500

@categories_bp.route('/hierarchy', methods=['GET'])
@login_required
def get_category_hierarchy():
    """Get categories organized in hierarchical structure"""
    try:
        categories = Category.query.order_by(Category.name.asc()).all()
        
        # Build hierarchy
        category_dict = {cat.id: {
            'id': str(cat.id),
            'name': cat.name,
            'parent_id': str(cat.parent_id) if cat.parent_id else None,
            'color': cat.color,
            'is_income': cat.is_income,
            'is_system': cat.is_system,
            'children': []
        } for cat in categories}
        
        hierarchy = []
        for cat in categories:
            if cat.parent_id and cat.parent_id in category_dict:
                category_dict[cat.parent_id]['children'].append(category_dict[cat.id])
            else:
                hierarchy.append(category_dict[cat.id])
        
        return jsonify(hierarchy)
        
    except Exception as e:
        return jsonify({'error': f'Failed to get category hierarchy: {str(e)}'}), 500

@categories_bp.route('/rules', methods=['GET'])
@login_required
def get_categorization_rules():
    """Get user's categorization rules"""
    try:
        rules = CategorizationRule.query.filter_by(user_id=current_user.id).all()
        
        rules_data = []
        for rule in rules:
            rules_data.append({
                'id': str(rule.id),
                'category_id': str(rule.category_id),
                'category_name': rule.category.name if rule.category else None,
                'rule_type': rule.rule_type,
                'condition': rule.condition,
                'value': rule.value,
                'priority': rule.priority,
                'is_active': rule.is_active
            })
        
        return jsonify(rules_data)
        
    except Exception as e:
        return jsonify({'error': f'Failed to get categorization rules: {str(e)}'}), 500

@categories_bp.route('/rules', methods=['POST'])
@login_required
def create_categorization_rule():
    """Create a new categorization rule"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['category_id', 'rule_type', 'condition', 'value']
        for field in required_fields:
            if not data or not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate category exists
        category = Category.query.get(data['category_id'])
        if not category:
            return jsonify({'error': 'Category not found'}), 404
        
        # Create new rule
        rule = CategorizationRule(
            user_id=current_user.id,
            category_id=data['category_id'],
            rule_type=data['rule_type'],
            condition=data['condition'],
            value=data['value'],
            priority=data.get('priority', 1),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(rule)
        db.session.commit()
        
        return jsonify({
            'id': str(rule.id),
            'category_id': str(rule.category_id),
            'category_name': rule.category.name,
            'rule_type': rule.rule_type,
            'condition': rule.condition,
            'value': rule.value,
            'priority': rule.priority,
            'is_active': rule.is_active
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create rule: {str(e)}'}), 500

@categories_bp.route('/rules/<rule_id>', methods=['PUT'])
@login_required
def update_categorization_rule(rule_id):
    """Update a categorization rule"""
    try:
        rule = CategorizationRule.query.filter_by(
            id=rule_id,
            user_id=current_user.id
        ).first_or_404()
        
        data = request.get_json()
        
        # Update fields
        if 'category_id' in data:
            category = Category.query.get(data['category_id'])
            if not category:
                return jsonify({'error': 'Category not found'}), 404
            rule.category_id = data['category_id']
        
        if 'rule_type' in data:
            rule.rule_type = data['rule_type']
        if 'condition' in data:
            rule.condition = data['condition']
        if 'value' in data:
            rule.value = data['value']
        if 'priority' in data:
            rule.priority = data['priority']
        if 'is_active' in data:
            rule.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify({
            'id': str(rule.id),
            'category_id': str(rule.category_id),
            'category_name': rule.category.name,
            'rule_type': rule.rule_type,
            'condition': rule.condition,
            'value': rule.value,
            'priority': rule.priority,
            'is_active': rule.is_active
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update rule: {str(e)}'}), 500

@categories_bp.route('/rules/<rule_id>', methods=['DELETE'])
@login_required
def delete_categorization_rule(rule_id):
    """Delete a categorization rule"""
    try:
        rule = CategorizationRule.query.filter_by(
            id=rule_id,
            user_id=current_user.id
        ).first_or_404()
        
        db.session.delete(rule)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete rule: {str(e)}'}), 500

@categories_bp.route('/bulk-categorize', methods=['POST'])
@login_required
def bulk_categorize():
    """Bulk categorize transactions"""
    try:
        data = request.get_json()
        transaction_ids = data.get('transaction_ids', [])
        category_id = data.get('category_id')
        
        if not transaction_ids or not category_id:
            return jsonify({'error': 'transaction_ids and category_id are required'}), 400
        
        # Validate category exists
        category = Category.query.get(category_id)
        if not category:
            return jsonify({'error': 'Category not found'}), 404
        
        # Get user's transactions
        user_accounts = Account.query.filter_by(user_id=current_user.id).all()
        account_ids = [acc.id for acc in user_accounts]
        
        transactions = Transaction.query.filter(
            Transaction.id.in_(transaction_ids),
            Transaction.account_id.in_(account_ids)
        ).all()
        
        if not transactions:
            return jsonify({'error': 'No valid transactions found'}), 404
        
        # Update transactions
        updated_count = 0
        for transaction in transactions:
            transaction.category_id = category_id
            transaction.is_manually_categorized = True
            transaction.category_confidence = 1.0
            updated_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'updated_count': updated_count
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to bulk categorize: {str(e)}'}), 500

@categories_bp.route('/auto-categorize', methods=['POST'])
@login_required
def auto_categorize():
    """Auto-categorize uncategorized transactions"""
    try:
        print("=== Auto-Categorization Request ===")
        
        data = request.get_json() or {}
        force_retrain = data.get('force_retrain', False)
        
        # Get user's uncategorized transactions
        user_accounts = Account.query.filter_by(user_id=current_user.id).all()
        account_ids = [acc.id for acc in user_accounts]
        
        print(f"User has {len(user_accounts)} accounts")
        
        uncategorized_transactions = Transaction.query.filter(
            Transaction.account_id.in_(account_ids),
            Transaction.category_id.is_(None)
        ).all()
        
        print(f"Found {len(uncategorized_transactions)} uncategorized transactions")
        
        if not uncategorized_transactions:
            return jsonify({
                'success': True,
                'message': 'No uncategorized transactions found',
                'categorized_count': 0
            })
        
        # Initialize categorizer
        categorizer = TransactionCategorizer()
        
        # Train model if needed
        if force_retrain:
            print("Force retraining model...")
            categorizer.train_model(user_id=current_user.id)
        
        # Categorize transactions
        print("Starting bulk categorization...")
        result = categorizer.bulk_categorize(uncategorized_transactions, current_user.id)
        
        print(f"Bulk categorization result: {result}")
        
        return jsonify({
            'success': result['success'],
            'categorized_count': len(result.get('results', [])),
            'total_uncategorized': len(uncategorized_transactions),
            'results': result.get('results', []),
            'error': result.get('error')
        })
        
    except Exception as e:
        print(f"Auto-categorization error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to auto-categorize: {str(e)}'}), 500

@categories_bp.route('/train-model', methods=['POST'])
@login_required
def train_categorization_model():
    """Train the categorization model with user's data"""
    try:
        categorizer = TransactionCategorizer()
        success = categorizer.train_model(user_id=current_user.id)
        
        if success:
            stats = categorizer.get_categorization_stats(current_user.id)
            return jsonify({
                'success': True,
                'message': 'Model trained successfully',
                'stats': stats
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Insufficient data for training. Need at least 10 categorized transactions.'
            })
        
    except Exception as e:
        return jsonify({'error': f'Failed to train model: {str(e)}'}), 500

@categories_bp.route('/stats', methods=['GET'])
@login_required
def get_categorization_stats():
    """Get categorization statistics"""
    try:
        categorizer = TransactionCategorizer()
        stats = categorizer.get_categorization_stats(current_user.id)
        
        return jsonify(stats)
        
    except Exception as e:
        return jsonify({'error': f'Failed to get stats: {str(e)}'}), 500

@categories_bp.route('/test-categorization', methods=['POST'])
@login_required
def test_categorization():
    """Test categorization on a sample transaction"""
    try:
        print("=== Test Categorization Request ===")
        
        # Get a sample transaction to test
        user_accounts = Account.query.filter_by(user_id=current_user.id).all()
        account_ids = [acc.id for acc in user_accounts]
        
        print(f"User accounts: {len(user_accounts)}")
        print(f"Account IDs: {account_ids}")
        
        sample_transaction = Transaction.query.filter(
            Transaction.account_id.in_(account_ids),
            Transaction.category_id.is_(None)
        ).first()
        
        if not sample_transaction:
            print("No uncategorized transactions found, creating a test transaction")
            # Create a test transaction for demonstration
            if user_accounts:
                test_transaction = type('TestTransaction', (), {
                    'id': 'test',
                    'description': 'McDONALD\'S #12345',
                    'merchant': 'McDonald\'s',
                    'amount': -15.50,
                    'account_id': user_accounts[0].id
                })()
                
                # Test categorization
                categorizer = TransactionCategorizer()
                category_id, confidence, method = categorizer.categorize_transaction(test_transaction)
                
                # Get category name
                category_name = None
                if category_id:
                    category = Category.query.get(category_id)
                    category_name = category.name if category else 'Unknown'
                
                result = {
                    'success': True,
                    'transaction': {
                        'id': 'test',
                        'description': 'McDONALD\'S #12345',
                        'merchant': 'McDonald\'s',
                        'amount': -15.50
                    },
                    'categorization': {
                        'category_id': str(category_id) if category_id else None,
                        'category_name': category_name,
                        'confidence': float(confidence),
                        'method': method
                    },
                    'note': 'This is a test transaction since no uncategorized transactions were found'
                }
                
                print(f"Test result: {result}")
                return jsonify(result)
            else:
                return jsonify({
                    'success': False,
                    'error': 'No user accounts found',
                    'suggestion': 'Create an account first'
                }), 200
        
        print(f"Testing transaction: {sample_transaction.description}")
        
        # Test categorization
        categorizer = TransactionCategorizer()
        category_id, confidence, method = categorizer.categorize_transaction(sample_transaction)
        
        print(f"Categorization result: category_id={category_id}, confidence={confidence}, method={method}")
        
        # Get category name
        category_name = None
        if category_id:
            category = Category.query.get(category_id)
            category_name = category.name if category else 'Unknown'
        
        result = {
            'success': True,
            'transaction': {
                'id': str(sample_transaction.id),
                'description': sample_transaction.description or '',
                'merchant': sample_transaction.merchant or '',
                'amount': float(sample_transaction.amount)
            },
            'categorization': {
                'category_id': str(category_id) if category_id else None,
                'category_name': category_name,
                'confidence': float(confidence),
                'method': method
            }
        }
        
        print(f"Returning result: {result}")
        return jsonify(result)
        
    except Exception as e:
        print(f"Test categorization error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Failed to test categorization: {str(e)}'
        }), 500