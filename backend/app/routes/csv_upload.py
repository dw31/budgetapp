from flask import Blueprint, request, jsonify, session
from flask_login import login_required, current_user
import os
import uuid
from werkzeug.utils import secure_filename
from ..services.csv_validator import CSVValidator
from ..services.csv_processor import CSVProcessor
from ..models import db, Account

csv_upload_bp = Blueprint('csv_upload', __name__)

# Configure upload settings
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '../../uploads')
ALLOWED_EXTENSIONS = {'csv'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@csv_upload_bp.route('/upload', methods=['POST'])
@login_required
def upload_csv():
    """Initial CSV file upload and validation"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only CSV files are allowed'}), 400
    
    try:
        # Create uploads directory if it doesn't exist
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, f"{file_id}_{filename}")
        
        # Save file
        file.save(file_path)
        
        # Validate file
        validator = CSVValidator()
        validation_result = validator.validate_file(file_path)
        
        if not validation_result.is_valid:
            # Clean up file if validation failed
            os.remove(file_path)
            return jsonify({
                'error': 'File validation failed',
                'details': validation_result.errors
            }), 400
        
        # Store file info in session for later use
        session['csv_upload'] = {
            'file_id': file_id,
            'file_path': file_path,
            'filename': filename,
            'validation_result': {
                'file_info': validation_result.file_info,
                'columns': validation_result.columns,
                'sample_data': validation_result.sample_data,
                'suggested_mappings': validation_result.suggested_mappings,
                'warnings': validation_result.warnings
            }
        }
        
        # Debug logging
        print(f"Stored in session: {session.get('csv_upload', {}).keys()}")
        session.modified = True
        
        return jsonify({
            'success': True,
            'file_id': file_id,
            'file_info': validation_result.file_info,
            'columns': validation_result.columns,
            'sample_data': validation_result.sample_data,
            'suggested_mappings': validation_result.suggested_mappings,
            'warnings': validation_result.warnings
        })
        
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@csv_upload_bp.route('/validate-mapping', methods=['POST'])
@login_required
def validate_mapping():
    """Validate user-defined column mappings"""
    print(f"Session keys: {list(session.keys())}")
    print(f"Session csv_upload exists: {'csv_upload' in session}")
    
    if 'csv_upload' not in session:
        return jsonify({'error': 'No file uploaded'}), 400
    
    try:
        data = request.get_json()
        mappings = data.get('mappings', {})
        
        # Debug logging
        print(f"Received mappings: {mappings}")
        
        file_path = session['csv_upload']['file_path']
        
        validator = CSVValidator()
        validation_result = validator.validate_column_mapping(file_path, mappings)
        
        # Debug logging
        print(f"Validation errors: {validation_result.errors}")
        print(f"Validation warnings: {validation_result.warnings}")
        
        if not validation_result.is_valid:
            return jsonify({
                'success': False,
                'errors': validation_result.errors,
                'warnings': validation_result.warnings
            }), 400
        
        # Update session with validated mappings
        session['csv_upload']['validated_mappings'] = mappings
        session.modified = True
        
        return jsonify({
            'success': True,
            'mappings': mappings,
            'warnings': validation_result.warnings
        })
        
    except Exception as e:
        print(f"Validation exception: {str(e)}")
        return jsonify({'error': f'Validation failed: {str(e)}'}), 500

@csv_upload_bp.route('/preview', methods=['POST'])
@login_required
def preview_import():
    """Preview CSV import with user mappings"""
    if 'csv_upload' not in session:
        return jsonify({'error': 'No file uploaded'}), 400
    
    try:
        data = request.get_json()
        mappings = data.get('mappings', {})
        account_id = data.get('account_id')
        
        if not account_id:
            return jsonify({'error': 'Account ID is required'}), 400
        
        # Verify account belongs to current user
        account = Account.query.filter_by(id=account_id, user_id=current_user.id).first()
        if not account:
            return jsonify({'error': 'Account not found'}), 404
        
        file_path = session['csv_upload']['file_path']
        
        # Validate mappings first
        validator = CSVValidator()
        validation_result = validator.validate_column_mapping(file_path, mappings)
        
        if not validation_result.is_valid:
            return jsonify({
                'success': False,
                'errors': validation_result.errors
            }), 400
        
        # Generate preview data
        processor = CSVProcessor()
        preview_data = processor.generate_preview(file_path, mappings, account_id)
        
        # Store preview info for confirmation
        session['csv_upload']['preview_mappings'] = mappings
        session['csv_upload']['preview_account_id'] = account_id
        session.modified = True  # Ensure Flask knows session has changed
        
        # Debug logging
        print(f"Stored preview_mappings: {mappings}")
        print(f"Stored preview_account_id: {account_id}")
        print(f"Session csv_upload keys after preview: {list(session['csv_upload'].keys())}")
        
        return jsonify({
            'success': True,
            'preview': preview_data,
            'account': {
                'id': account.id,
                'name': account.name,
                'type': account.account_type
            },
            'mappings': mappings
        })
        
    except Exception as e:
        return jsonify({'error': f'Preview failed: {str(e)}'}), 500

@csv_upload_bp.route('/confirm', methods=['POST'])
@login_required
def confirm_import():
    """Confirm and execute CSV import"""
    if 'csv_upload' not in session:
        return jsonify({'error': 'No file uploaded'}), 400
    
    try:
        upload_info = session['csv_upload']
        
        # Debug logging
        print(f"Upload info keys: {list(upload_info.keys())}")
        print(f"Has preview_mappings: {'preview_mappings' in upload_info}")
        print(f"Has preview_account_id: {'preview_account_id' in upload_info}")
        
        if 'preview_mappings' not in upload_info:
            return jsonify({'error': 'No preview generated'}), 400
        
        file_path = upload_info['file_path']
        mappings = upload_info['preview_mappings']
        account_id = upload_info['preview_account_id']
        
        # Process the CSV file
        processor = CSVProcessor()
        result = processor.process_csv_with_mappings(
            file_path, 
            mappings, 
            account_id, 
            current_user.id
        )
        
        # Clean up
        if os.path.exists(file_path):
            os.remove(file_path)
        session.pop('csv_upload', None)
        
        # Add additional information about categorization
        if result.get('success'):
            result['message'] = f"Successfully imported {result['processed']} transactions as uncategorized. Visit the Categories page to run auto-categorization."
            result['categorization_note'] = "All transactions were imported without categories. Use auto-categorization to assign categories automatically."
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': f'Import failed: {str(e)}'}), 500

@csv_upload_bp.route('/cancel', methods=['POST'])
@login_required
def cancel_upload():
    """Cancel CSV upload and clean up"""
    if 'csv_upload' in session:
        upload_info = session['csv_upload']
        file_path = upload_info.get('file_path')
        
        # Clean up file
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        
        # Clean up session
        session.pop('csv_upload', None)
    
    return jsonify({'success': True})

@csv_upload_bp.route('/accounts', methods=['GET'])
@login_required
def get_user_accounts():
    """Get user's accounts for CSV import"""
    accounts = Account.query.filter_by(user_id=current_user.id, is_active=True).all()
    
    return jsonify({
        'accounts': [{
            'id': account.id,
            'name': account.name,
            'type': account.account_type,
            'balance': float(account.current_balance)
        } for account in accounts]
    })