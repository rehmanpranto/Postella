from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models import User, UserRole
from app.extensions import db, limiter
from app.utils.audit import log_action
from email_validator import validate_email, EmailNotValidError
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import os

bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@bp.route('/register', methods=['POST'])
@limiter.limit("5 per hour")
def register():
    """Register a new user"""
    data = request.get_json()
    
    # Validate input
    if not data or not all(k in data for k in ['email', 'password', 'full_name']):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Validate email
    try:
        valid = validate_email(data['email'])
        email = valid.email
    except EmailNotValidError as e:
        return jsonify({'error': str(e)}), 400
    
    # Check if user already exists
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    # Validate password strength
    if len(data['password']) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    
    # Create user
    user = User(
        email=email,
        full_name=data['full_name'],
        role=UserRole.EDITOR,  # Default role
        is_active=True
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    # Log action
    log_action(user.id, 'register', 'success')
    
    return jsonify({
        'message': 'User registered successfully',
        'user': user.to_dict()
    }), 201


@bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    """Login user and return JWT token"""
    data = request.get_json()
    
    if not data or not all(k in data for k in ['email', 'password']):
        return jsonify({'error': 'Missing email or password'}), 400
    
    # Find user
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not user.check_password(data['password']):
        log_action(None, 'login', 'failed', details=f"Failed login attempt for {data['email']}")
        return jsonify({'error': 'Invalid email or password'}), 401
    
    if not user.is_active:
        return jsonify({'error': 'Account is not active'}), 403
    
    # Create access token
    access_token = create_access_token(identity=str(user.id))
    
    # Log successful login
    log_action(user.id, 'login', 'success')
    
    return jsonify({
        'access_token': access_token,
        'user': user.to_dict()
    }), 200


@bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current user information"""
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid token'}), 401
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(user.to_dict()), 200


@bp.route('/change-password', methods=['POST'])
@jwt_required()
@limiter.limit("3 per hour")
def change_password():
    """Change user password"""
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid token'}), 401
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    if not data or not all(k in data for k in ['old_password', 'new_password']):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Verify old password
    if not user.check_password(data['old_password']):
        log_action(user_id, 'change_password', 'failed')
        return jsonify({'error': 'Invalid old password'}), 401
    
    # Validate new password
    if len(data['new_password']) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400
    
    # Update password
    user.set_password(data['new_password'])
    db.session.commit()
    
    log_action(user_id, 'change_password', 'success')
    
    return jsonify({'message': 'Password changed successfully'}), 200


def _get_reset_serializer():
    """Get a timed serializer for password-reset tokens."""
    secret = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    return URLSafeTimedSerializer(secret, salt='password-reset')


@bp.route('/forgot-password', methods=['POST'])
@limiter.limit("5 per hour")
def forgot_password():
    """Generate a password-reset token for the given email.

    Since Postella may not have an email provider configured, the token is
    returned directly in the JSON response so the frontend can show it to
    the user (or, in production, you would email it instead).
    """
    data = request.get_json()

    if not data or 'email' not in data:
        return jsonify({'error': 'Email is required'}), 400

    try:
        valid = validate_email(data['email'])
        email = valid.email
    except EmailNotValidError as e:
        return jsonify({'error': str(e)}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        # Don't reveal whether the email exists
        return jsonify({
            'message': 'If an account with that email exists, a reset token has been generated.',
            'reset_token': None
        }), 200

    serializer = _get_reset_serializer()
    token = serializer.dumps(user.email)

    log_action(user.id, 'forgot_password', 'success')

    return jsonify({
        'message': 'If an account with that email exists, a reset token has been generated.',
        'reset_token': token
    }), 200


@bp.route('/reset-password', methods=['POST'])
@limiter.limit("5 per hour")
def reset_password():
    """Reset the password using a valid reset token."""
    data = request.get_json()

    if not data or not all(k in data for k in ['token', 'new_password']):
        return jsonify({'error': 'Token and new password are required'}), 400

    # Validate new password
    if len(data['new_password']) < 8:
        return jsonify({'error': 'Password must be at least 8 characters'}), 400

    serializer = _get_reset_serializer()
    try:
        email = serializer.loads(data['token'], max_age=3600)  # 1-hour expiry
    except SignatureExpired:
        return jsonify({'error': 'Reset token has expired. Please request a new one.'}), 400
    except BadSignature:
        return jsonify({'error': 'Invalid reset token.'}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': 'User not found.'}), 404

    user.set_password(data['new_password'])
    db.session.commit()

    log_action(user.id, 'reset_password', 'success')

    return jsonify({'message': 'Password has been reset successfully. You can now log in.'}), 200
