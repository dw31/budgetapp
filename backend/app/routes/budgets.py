from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime, date
from ..models import db, Budget, BudgetItem, Category, Transaction, Account
from ..services.recurring_detector import RecurringTransactionDetector

budgets_bp = Blueprint('budgets', __name__)

@budgets_bp.route('', methods=['GET'])
@login_required
def get_budgets():
    budgets = Budget.query.filter_by(user_id=current_user.id, is_active=True).all()
    
    result = []
    for budget in budgets:
        budget_data = {
            'id': str(budget.id),
            'name': budget.name,
            'period_type': budget.period_type,
            'start_date': budget.start_date.isoformat(),
            'end_date': budget.end_date.isoformat(),
            'is_active': budget.is_active,
            'account_ids': [str(acc.id) for acc in budget.accounts],
            'account_names': [acc.name for acc in budget.accounts],
            'items': []
        }
        
        for item in budget.budget_items:
            # Calculate actual spending for this category in budget period
            # Only include transactions from accounts associated with this budget
            budget_account_ids = [acc.id for acc in budget.accounts]
            
            actual_amount = db.session.query(func.sum(Transaction.amount)).join(Account).filter(
                Account.user_id == current_user.id,
                Account.id.in_(budget_account_ids) if budget_account_ids else True,
                Transaction.category_id == item.category_id,
                Transaction.date >= budget.start_date,
                Transaction.date <= budget.end_date,
                Transaction.amount < 0  # Only expenses
            ).scalar() or 0
            
            budget_data['items'].append({
                'id': str(item.id),
                'category_id': str(item.category_id),
                'category_name': item.category.name if item.category else 'Unknown',
                'budgeted_amount': float(item.budgeted_amount),
                'actual_amount': float(abs(actual_amount)),
                'remaining_amount': float(item.budgeted_amount - abs(actual_amount)),
                'percentage_used': min(100, (abs(actual_amount) / item.budgeted_amount * 100)) if item.budgeted_amount > 0 else 0
            })
        
        result.append(budget_data)
    
    return jsonify(result)

@budgets_bp.route('', methods=['POST'])
@login_required
def create_budget():
    data = request.get_json()
    
    required_fields = ['name', 'period_type', 'start_date', 'end_date', 'items', 'account_ids']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Validate account_ids
    account_ids = data.get('account_ids', [])
    if not account_ids:
        return jsonify({'error': 'At least one account must be selected'}), 400
    
    # Verify all accounts belong to the current user
    user_accounts = Account.query.filter(
        Account.id.in_(account_ids),
        Account.user_id == current_user.id
    ).all()
    
    if len(user_accounts) != len(account_ids):
        return jsonify({'error': 'One or more accounts not found or not accessible'}), 400
    
    try:
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400
    
    budget = Budget(
        user_id=current_user.id,
        name=data['name'],
        period_type=data['period_type'],
        start_date=start_date,
        end_date=end_date
    )
    
    db.session.add(budget)
    db.session.flush()  # Get the budget ID
    
    # Associate accounts with the budget
    for account in user_accounts:
        budget.accounts.append(account)
    
    # Add budget items
    for item_data in data['items']:
        budget_item = BudgetItem(
            budget_id=budget.id,
            category_id=item_data['category_id'],
            budgeted_amount=item_data['budgeted_amount']
        )
        db.session.add(budget_item)
    
    db.session.commit()
    
    return jsonify({
        'id': str(budget.id),
        'name': budget.name,
        'period_type': budget.period_type,
        'start_date': budget.start_date.isoformat(),
        'end_date': budget.end_date.isoformat()
    }), 201

@budgets_bp.route('/<budget_id>', methods=['PUT'])
@login_required
def update_budget(budget_id):
    budget = Budget.query.filter_by(id=budget_id, user_id=current_user.id).first()
    if not budget:
        return jsonify({'error': 'Budget not found'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        budget.name = data['name']
    
    if 'is_active' in data:
        budget.is_active = data['is_active']
    
    # Update account associations if provided
    if 'account_ids' in data:
        account_ids = data['account_ids']
        if account_ids:  # Only update if not empty
            # Verify all accounts belong to the current user
            user_accounts = Account.query.filter(
                Account.id.in_(account_ids),
                Account.user_id == current_user.id
            ).all()
            
            if len(user_accounts) != len(account_ids):
                return jsonify({'error': 'One or more accounts not found or not accessible'}), 400
            
            # Clear existing associations and add new ones
            budget.accounts.clear()
            for account in user_accounts:
                budget.accounts.append(account)
    
    if 'items' in data:
        # Remove existing items and add new ones
        BudgetItem.query.filter_by(budget_id=budget.id).delete()
        
        for item_data in data['items']:
            budget_item = BudgetItem(
                budget_id=budget.id,
                category_id=item_data['category_id'],
                budgeted_amount=item_data['budgeted_amount']
            )
            db.session.add(budget_item)
    
    db.session.commit()
    
    return jsonify({'message': 'Budget updated successfully'})

@budgets_bp.route('/<budget_id>/performance', methods=['GET'])
@login_required
def get_budget_performance(budget_id):
    budget = Budget.query.filter_by(id=budget_id, user_id=current_user.id).first()
    if not budget:
        return jsonify({'error': 'Budget not found'}), 404
    
    performance_data = {
        'budget_id': str(budget.id),
        'budget_name': budget.name,
        'period': f"{budget.start_date.isoformat()} to {budget.end_date.isoformat()}",
        'categories': [],
        'summary': {
            'total_budgeted': 0,
            'total_spent': 0,
            'total_remaining': 0,
            'overall_percentage': 0
        }
    }
    
    total_budgeted = 0
    total_spent = 0
    
    for item in budget.budget_items:
        # Calculate actual spending only from accounts associated with this budget
        budget_account_ids = [acc.id for acc in budget.accounts]
        
        actual_amount = db.session.query(func.sum(Transaction.amount)).join(Account).filter(
            Account.user_id == current_user.id,
            Account.id.in_(budget_account_ids) if budget_account_ids else True,
            Transaction.category_id == item.category_id,
            Transaction.date >= budget.start_date,
            Transaction.date <= budget.end_date,
            Transaction.amount < 0
        ).scalar() or 0
        
        actual_amount = abs(actual_amount)
        total_budgeted += float(item.budgeted_amount)
        total_spent += actual_amount
        
        performance_data['categories'].append({
            'category_name': item.category.name if item.category else 'Unknown',
            'budgeted': float(item.budgeted_amount),
            'spent': actual_amount,
            'remaining': float(item.budgeted_amount) - actual_amount,
            'percentage_used': min(100, (actual_amount / float(item.budgeted_amount) * 100)) if item.budgeted_amount > 0 else 0
        })
    
    performance_data['summary'] = {
        'total_budgeted': total_budgeted,
        'total_spent': total_spent,
        'total_remaining': total_budgeted - total_spent,
        'overall_percentage': min(100, (total_spent / total_budgeted * 100)) if total_budgeted > 0 else 0
    }
    
    return jsonify(performance_data)

@budgets_bp.route('/<budget_id>', methods=['DELETE'])
@login_required
def delete_budget(budget_id):
    budget = Budget.query.filter_by(id=budget_id, user_id=current_user.id).first()
    if not budget:
        return jsonify({'error': 'Budget not found'}), 404
    
    try:
        # Delete the budget (cascade will handle budget items)
        db.session.delete(budget)
        db.session.commit()
        return jsonify({'message': 'Budget deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to delete budget: {str(e)}'}), 500

@budgets_bp.route('/alerts', methods=['GET'])
@login_required
def get_budget_alerts():
    """Get budget alerts and warnings for the current user"""
    try:
        # Get all active budgets for the user
        budgets = Budget.query.filter_by(user_id=current_user.id, is_active=True).all()
        
        alerts = []
        warnings = []
        over_budget = []
        
        for budget in budgets:
            # Check if budget is current (includes today's date)
            from datetime import date
            today = date.today()
            if not (budget.start_date <= today <= budget.end_date):
                continue
                
            for item in budget.budget_items:
                # Calculate actual spending only from accounts associated with this budget
                budget_account_ids = [acc.id for acc in budget.accounts]
                
                actual_amount = db.session.query(func.sum(Transaction.amount)).join(Account).filter(
                    Account.user_id == current_user.id,
                    Account.id.in_(budget_account_ids) if budget_account_ids else True,
                    Transaction.category_id == item.category_id,
                    Transaction.date >= budget.start_date,
                    Transaction.date <= budget.end_date,
                    Transaction.amount < 0  # Only expenses
                ).scalar() or 0
                
                actual_amount = abs(actual_amount)
                budgeted_amount = float(item.budgeted_amount)
                percentage_used = (actual_amount / budgeted_amount * 100) if budgeted_amount > 0 else 0
                
                category_name = item.category.name if item.category else 'Unknown'
                
                if percentage_used >= 100:
                    over_budget.append({
                        'budget_name': budget.name,
                        'category_name': category_name,
                        'budgeted_amount': budgeted_amount,
                        'actual_amount': actual_amount,
                        'over_amount': actual_amount - budgeted_amount,
                        'percentage_used': percentage_used
                    })
                elif percentage_used >= 80:
                    warnings.append({
                        'budget_name': budget.name,
                        'category_name': category_name,
                        'budgeted_amount': budgeted_amount,
                        'actual_amount': actual_amount,
                        'remaining_amount': budgeted_amount - actual_amount,
                        'percentage_used': percentage_used
                    })
                elif percentage_used >= 50:
                    alerts.append({
                        'budget_name': budget.name,
                        'category_name': category_name,
                        'budgeted_amount': budgeted_amount,
                        'actual_amount': actual_amount,
                        'remaining_amount': budgeted_amount - actual_amount,
                        'percentage_used': percentage_used
                    })
        
        return jsonify({
            'success': True,
            'alerts': alerts,           # 50-79% used
            'warnings': warnings,       # 80-99% used  
            'over_budget': over_budget, # 100%+ used
            'total_issues': len(alerts) + len(warnings) + len(over_budget)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get budget alerts: {str(e)}',
            'alerts': [],
            'warnings': [],
            'over_budget': [],
            'total_issues': 0
        }), 500

@budgets_bp.route('/detect-recurring', methods=['POST'])
@login_required
def detect_recurring_transactions():
    """Detect and mark recurring transactions for the current user"""
    try:
        # Check if the database has the required fields
        from sqlalchemy import text
        try:
            # Test if the columns exist
            with db.engine.connect() as conn:
                result = conn.execute(text("SELECT is_recurring FROM transactions LIMIT 1"))
                db_ready = True
        except Exception:
            db_ready = False
        
        if not db_ready:
            return jsonify({
                'success': False,
                'error': 'Database migration required. Please restart the application to enable recurring transaction detection.',
                'migration_required': True
            }), 400
        
        detector = RecurringTransactionDetector()
        result = detector.detect_recurring_transactions(current_user.id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'Failed to detect recurring transactions: {str(e)}'}), 500

@budgets_bp.route('/recurring-patterns', methods=['GET'])
@login_required
def get_recurring_patterns():
    """Get summary of all recurring transaction patterns"""
    try:
        # Check if the database has the required fields
        from sqlalchemy import text
        try:
            # Test if the columns exist
            with db.engine.connect() as conn:
                result = conn.execute(text("SELECT is_recurring FROM transactions LIMIT 1"))
                db_ready = True
        except Exception:
            db_ready = False
        
        if not db_ready:
            return jsonify({
                'success': True,
                'patterns': [],
                'total_patterns': 0,
                'database_ready': False,
                'message': 'Database migration required. Please run migration first.'
            })
        
        detector = RecurringTransactionDetector()
        patterns = detector.get_recurring_patterns_summary(current_user.id)
        return jsonify({
            'success': True,
            'patterns': patterns,
            'total_patterns': len(patterns),
            'database_ready': True
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get recurring patterns: {str(e)}',
            'patterns': [],
            'total_patterns': 0
        }), 200  # Return 200 to avoid frontend errors

@budgets_bp.route('/monthly-analysis/<int:year>/<int:month>', methods=['GET'])
@login_required
def get_monthly_analysis(year, month):
    """Get recurring vs non-recurring expenses analysis for a specific month"""
    try:
        # Validate month
        if not (1 <= month <= 12):
            return jsonify({'error': 'Invalid month. Must be 1-12'}), 400
        
        detector = RecurringTransactionDetector()
        analysis = detector.get_monthly_recurring_vs_nonrecurring(current_user.id, year, month)
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
    except Exception as e:
        return jsonify({'error': f'Failed to get monthly analysis: {str(e)}'}), 500

@budgets_bp.route('/available-months', methods=['GET'])
@login_required
def get_available_months():
    """Get list of months that have transaction data"""
    try:
        # Get date range of user's transactions
        query = db.session.query(
            func.min(Transaction.date).label('min_date'),
            func.max(Transaction.date).label('max_date')
        ).join(Account).filter(Account.user_id == current_user.id)
        
        result = query.first()
        
        if not result.min_date or not result.max_date:
            return jsonify({
                'success': True,
                'months': []
            })
        
        # Generate list of months between min and max dates
        months = []
        current_date = result.min_date.replace(day=1)
        end_date = result.max_date.replace(day=1)
        
        while current_date <= end_date:
            months.append({
                'year': current_date.year,
                'month': current_date.month,
                'display': f"{current_date.strftime('%B')} {current_date.year}",
                'value': f"{current_date.year}-{current_date.month:02d}"
            })
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        # Reverse to show most recent first
        months.reverse()
        
        return jsonify({
            'success': True,
            'months': months
        })
    except Exception as e:
        return jsonify({'error': f'Failed to get available months: {str(e)}'}), 500