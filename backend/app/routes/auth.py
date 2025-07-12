from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import uuid
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
                'last_name': user.last_name,
                'avatar_url': user.avatar_url,
                'created_at': user.created_at.isoformat()
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
            'last_name': current_user.last_name,
            'avatar_url': current_user.avatar_url,
            'created_at': current_user.created_at.isoformat()
        }
    }), 200

@auth_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    try:
        data = request.get_json()
        
        # Update allowed fields
        if 'first_name' in data:
            current_user.first_name = data['first_name']
        if 'last_name' in data:
            current_user.last_name = data['last_name']
        if 'email' in data:
            # Check if email is already taken by another user
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user and existing_user.id != current_user.id:
                return jsonify({'error': 'Email already in use'}), 409
            current_user.email = data['email']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': {
                'id': str(current_user.id),
                'email': current_user.email,
                'first_name': current_user.first_name,
                'last_name': current_user.last_name,
                'avatar_url': current_user.avatar_url
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update profile'}), 500

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    try:
        data = request.get_json()
        
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({'error': 'Current password and new password required'}), 400
        
        # Verify current password
        if not check_password_hash(current_user.password_hash, data['current_password']):
            return jsonify({'error': 'Current password is incorrect'}), 400
        
        # Validate new password
        if len(data['new_password']) < 6:
            return jsonify({'error': 'New password must be at least 6 characters'}), 400
        
        # Update password
        current_user.password_hash = generate_password_hash(data['new_password'])
        db.session.commit()
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to change password'}), 500

@auth_bp.route('/upload-avatar', methods=['POST'])
@login_required
def upload_avatar():
    try:
        if 'avatar' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['avatar']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        if not file.filename.lower().endswith(tuple(allowed_extensions)):
            return jsonify({'error': 'Invalid file type. Please use PNG, JPG, JPEG, GIF, or WebP'}), 400
        
        # Validate file size (max 5MB)
        if len(file.read()) > 5 * 1024 * 1024:
            return jsonify({'error': 'File too large. Maximum size is 5MB'}), 400
        
        file.seek(0)  # Reset file pointer after reading
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        name, ext = os.path.splitext(filename)
        unique_filename = f"{current_user.id}_{uuid.uuid4().hex[:8]}{ext}"
        
        # Create avatars directory if it doesn't exist
        avatars_dir = os.path.join('uploads', 'avatars')
        os.makedirs(avatars_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(avatars_dir, unique_filename)
        file.save(file_path)
        
        # Delete old avatar if it exists
        if current_user.avatar_url:
            old_path = current_user.avatar_url.replace('/api/avatars/', 'uploads/avatars/')
            if os.path.exists(old_path):
                os.remove(old_path)
        
        # Update user avatar URL
        current_user.avatar_url = f'/api/avatars/{unique_filename}'
        db.session.commit()
        
        return jsonify({
            'message': 'Avatar uploaded successfully',
            'avatar_url': current_user.avatar_url
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to upload avatar'}), 500

@auth_bp.route('/remove-avatar', methods=['DELETE'])
@login_required
def remove_avatar():
    try:
        if current_user.avatar_url:
            # Delete file
            file_path = current_user.avatar_url.replace('/api/avatars/', 'uploads/avatars/')
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Remove from database
            current_user.avatar_url = None
            db.session.commit()
        
        return jsonify({'message': 'Avatar removed successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to remove avatar'}), 500