from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models import User, UserRole


def get_current_user_id():
    """Return the current user id as int or None if invalid."""
    user_id = get_jwt_identity()
    try:
        return int(user_id)
    except (TypeError, ValueError):
        return None


def admin_required(fn):
    """Decorator to require admin role"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_current_user_id()
        if user_id is None:
            return jsonify({'error': 'Invalid token'}), 401
        user = User.query.get(user_id)
        
        if not user or user.role != UserRole.ADMIN:
            return jsonify({'error': 'Admin access required'}), 403
        
        return fn(*args, **kwargs)
    
    return wrapper


def editor_required(fn):
    """Decorator to require editor or admin role"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_current_user_id()
        if user_id is None:
            return jsonify({'error': 'Invalid token'}), 401
        user = User.query.get(user_id)
        
        if not user or user.role not in [UserRole.ADMIN, UserRole.EDITOR]:
            return jsonify({'error': 'Editor access required'}), 403
        
        return fn(*args, **kwargs)
    
    return wrapper


def active_user_required(fn):
    """Decorator to require active user account"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user_id = get_current_user_id()
        if user_id is None:
            return jsonify({'error': 'Invalid token'}), 401
        user = User.query.get(user_id)
        
        if not user or not user.is_active:
            return jsonify({'error': 'Account is not active'}), 403
        
        return fn(*args, **kwargs)
    
    return wrapper
