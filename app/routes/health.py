from flask import Blueprint, jsonify
from app.extensions import db
from sqlalchemy import text

bp = Blueprint('health', __name__, url_prefix='/api')


@bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        db.session.execute(text('SELECT 1'))
        db_status = 'healthy'
    except Exception as e:
        db_status = f'unhealthy: {str(e)}'
    
    return jsonify({
        'status': 'healthy' if db_status == 'healthy' else 'degraded',
        'database': db_status
    }), 200 if db_status == 'healthy' else 503


@bp.route('/', methods=['GET'])
def index():
    """API index"""
    return jsonify({
        'name': 'AutoContent Calendar API',
        'version': '1.0.0',
        'endpoints': {
            'health': '/api/health',
            'auth': '/api/auth',
            'posts': '/api/posts',
            'calendar': '/api/calendar',
            'oauth': '/api/oauth',
            'admin': '/api/admin'
        }
    }), 200
