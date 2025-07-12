from sqlalchemy import func, extract, case
from datetime import datetime, date, timedelta
from collections import defaultdict, OrderedDict
from ..models import db, Transaction, Account, Category

class ReportGenerator:
    def __init__(self):
        pass
    
    def generate_cashflow_report(self, user_id, start_date, end_date, period='monthly'):
        """Generate cash flow report showing income vs expenses over time"""
        
        # Base query for user's transactions
        base_query = db.session.query(Transaction).join(Account).filter(
            Account.user_id == user_id,
            Transaction.date >= start_date,
            Transaction.date <= end_date
        )
        
        if period == 'monthly':
            date_field = func.to_char(Transaction.date, 'YYYY-MM')
        elif period == 'quarterly':
            date_field = func.concat(
                extract('year', Transaction.date),
                '-Q',
                extract('quarter', Transaction.date)
            )
        else:  # annual
            date_field = extract('year', Transaction.date)
        
        # Query for income and expenses by period
        cashflow_data = base_query.with_entities(
            date_field.label('period'),
            func.sum(case((Transaction.amount > 0, Transaction.amount), else_=0)).label('income'),
            func.sum(case((Transaction.amount < 0, func.abs(Transaction.amount)), else_=0)).label('expenses')
        ).group_by(date_field).order_by(date_field).all()
        
        # Format the results
        periods = []
        for row in cashflow_data:
            net_flow = row.income - row.expenses
            periods.append({
                'period': str(row.period),
                'income': float(row.income or 0),
                'expenses': float(row.expenses or 0),
                'net_flow': float(net_flow),
                'savings_rate': (net_flow / row.income * 100) if row.income > 0 else 0
            })
        
        # Calculate totals and averages
        total_income = sum(p['income'] for p in periods)
        total_expenses = sum(p['expenses'] for p in periods)
        total_net_flow = total_income - total_expenses
        avg_monthly_income = total_income / len(periods) if periods else 0
        avg_monthly_expenses = total_expenses / len(periods) if periods else 0
        
        return {
            'report_type': 'cashflow',
            'period_type': period,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'periods': periods,
            'summary': {
                'total_income': total_income,
                'total_expenses': total_expenses,
                'total_net_flow': total_net_flow,
                'average_monthly_income': avg_monthly_income,
                'average_monthly_expenses': avg_monthly_expenses,
                'overall_savings_rate': (total_net_flow / total_income * 100) if total_income > 0 else 0
            }
        }
    
    def generate_networth_report(self, user_id, as_of_date):
        """Generate net worth report showing assets and liabilities"""
        
        # Get all accounts for the user
        accounts = Account.query.filter_by(user_id=user_id, is_active=True).all()
        
        assets = []
        liabilities = []
        total_assets = 0
        total_liabilities = 0
        
        for account in accounts:
            # Calculate account balance as of the specified date
            transactions_sum = db.session.query(func.sum(Transaction.amount)).filter(
                Transaction.account_id == account.id,
                Transaction.date <= as_of_date
            ).scalar() or 0
            
            current_balance = float(account.opening_balance) + float(transactions_sum)
            
            account_data = {
                'account_id': str(account.id),
                'account_name': account.name,
                'account_type': account.account_type,
                'institution': account.institution,
                'balance': current_balance
            }
            
            if account.account_type in ['checking', 'savings', 'investment']:
                assets.append(account_data)
                total_assets += current_balance
            elif account.account_type == 'credit_card':
                # Credit card balances are typically negative (what you owe)
                account_data['balance'] = abs(current_balance)
                liabilities.append(account_data)
                total_liabilities += abs(current_balance)
        
        net_worth = total_assets - total_liabilities
        
        return {
            'report_type': 'networth',
            'as_of_date': as_of_date.isoformat(),
            'assets': assets,
            'liabilities': liabilities,
            'summary': {
                'total_assets': total_assets,
                'total_liabilities': total_liabilities,
                'net_worth': net_worth,
                'debt_to_asset_ratio': (total_liabilities / total_assets * 100) if total_assets > 0 else 0
            }
        }
    
    def generate_spending_analysis(self, user_id, start_date, end_date, group_by='category'):
        """Generate spending analysis grouped by category, merchant, or time period"""
        
        base_query = db.session.query(Transaction).join(Account).filter(
            Account.user_id == user_id,
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.amount < 0  # Only expenses
        )
        
        if group_by == 'category':
            spending_data = base_query.outerjoin(Category).with_entities(
                Category.name.label('group_name'),
                func.sum(func.abs(Transaction.amount)).label('total_amount'),
                func.count(Transaction.id).label('transaction_count')
            ).group_by(Category.name).order_by(func.sum(func.abs(Transaction.amount)).desc()).all()
            
        elif group_by == 'merchant':
            spending_data = base_query.with_entities(
                Transaction.merchant.label('group_name'),
                func.sum(func.abs(Transaction.amount)).label('total_amount'),
                func.count(Transaction.id).label('transaction_count')
            ).group_by(Transaction.merchant).order_by(func.sum(func.abs(Transaction.amount)).desc()).limit(20).all()
            
        else:  # group by month
            spending_data = base_query.with_entities(
                func.to_char(Transaction.date, 'YYYY-MM').label('group_name'),
                func.sum(func.abs(Transaction.amount)).label('total_amount'),
                func.count(Transaction.id).label('transaction_count')
            ).group_by(func.to_char(Transaction.date, 'YYYY-MM')).order_by('group_name').all()
        
        # Calculate total spending for percentages
        total_spending = sum(float(row.total_amount or 0) for row in spending_data)
        
        # Format results
        breakdown = []
        for row in spending_data:
            amount = float(row.total_amount or 0)
            breakdown.append({
                'name': row.group_name or 'Unknown',
                'amount': amount,
                'transaction_count': row.transaction_count,
                'percentage': (amount / total_spending * 100) if total_spending > 0 else 0
            })
        
        return {
            'report_type': 'spending_analysis',
            'group_by': group_by,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'breakdown': breakdown,
            'summary': {
                'total_spending': total_spending,
                'average_transaction': total_spending / sum(row.transaction_count for row in spending_data) if spending_data else 0,
                'transaction_count': sum(row.transaction_count for row in spending_data)
            }
        }
    
    def generate_spending_trends(self, user_id, start_date, end_date, category_id=None):
        """Generate spending trends over time, optionally filtered by category"""
        
        base_query = db.session.query(Transaction).join(Account).filter(
            Account.user_id == user_id,
            Transaction.date >= start_date,
            Transaction.date <= end_date,
            Transaction.amount < 0
        )
        
        if category_id:
            base_query = base_query.filter(Transaction.category_id == category_id)
        
        # Group by month
        trends_data = base_query.with_entities(
            func.to_char(Transaction.date, 'YYYY-MM').label('month'),
            func.sum(func.abs(Transaction.amount)).label('total_amount'),
            func.count(Transaction.id).label('transaction_count'),
            func.avg(func.abs(Transaction.amount)).label('avg_transaction')
        ).group_by(func.to_char(Transaction.date, 'YYYY-MM')).order_by('month').all()
        
        # Format results
        trends = []
        for row in trends_data:
            trends.append({
                'month': row.month,
                'amount': float(row.total_amount or 0),
                'transaction_count': row.transaction_count,
                'average_transaction': float(row.avg_transaction or 0)
            })
        
        # Calculate month-over-month changes
        for i in range(1, len(trends)):
            prev_amount = trends[i-1]['amount']
            curr_amount = trends[i]['amount']
            
            if prev_amount > 0:
                trends[i]['month_over_month_change'] = ((curr_amount - prev_amount) / prev_amount) * 100
            else:
                trends[i]['month_over_month_change'] = 0
        
        if trends:
            trends[0]['month_over_month_change'] = 0  # First month has no previous comparison
        
        return {
            'report_type': 'spending_trends',
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'category_id': category_id,
            'trends': trends,
            'summary': {
                'total_months': len(trends),
                'average_monthly_spending': sum(t['amount'] for t in trends) / len(trends) if trends else 0,
                'highest_month': max(trends, key=lambda x: x['amount']) if trends else None,
                'lowest_month': min(trends, key=lambda x: x['amount']) if trends else None
            }
        }