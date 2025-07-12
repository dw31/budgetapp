from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func, extract
from datetime import datetime, date, timedelta
from collections import defaultdict
from ..models import db, Transaction, Account, Category
from ..services.report_generator import ReportGenerator

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/cashflow', methods=['GET'])
@login_required
def get_cashflow_report():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    period = request.args.get('period', 'monthly')  # monthly, quarterly, annual
    
    if not start_date or not end_date:
        # Default to last 12 months
        end_date = date.today()
        start_date = end_date - timedelta(days=365)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    generator = ReportGenerator()
    report = generator.generate_cashflow_report(current_user.id, start_date, end_date, period)
    
    return jsonify(report)

@reports_bp.route('/networth', methods=['GET'])
@login_required
def get_networth_report():
    as_of_date = request.args.get('as_of_date')
    
    if not as_of_date:
        as_of_date = date.today()
    else:
        as_of_date = datetime.strptime(as_of_date, '%Y-%m-%d').date()
    
    generator = ReportGenerator()
    report = generator.generate_networth_report(current_user.id, as_of_date)
    
    return jsonify(report)

@reports_bp.route('/spending', methods=['GET'])
@login_required
def get_spending_analysis():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    group_by = request.args.get('group_by', 'category')  # category, merchant, month
    
    if not start_date or not end_date:
        # Default to last 3 months
        end_date = date.today()
        start_date = end_date - timedelta(days=90)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    generator = ReportGenerator()
    report = generator.generate_spending_analysis(current_user.id, start_date, end_date, group_by)
    
    return jsonify(report)

@reports_bp.route('/trends', methods=['GET'])
@login_required
def get_spending_trends():
    months = int(request.args.get('months', 12))
    category_id = request.args.get('category_id')
    
    end_date = date.today()
    start_date = end_date - timedelta(days=months * 30)
    
    generator = ReportGenerator()
    report = generator.generate_spending_trends(current_user.id, start_date, end_date, category_id)
    
    return jsonify(report)