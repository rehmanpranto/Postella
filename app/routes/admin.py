from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User, Post, AuditLog, PostStatus, UserRole, PlatformType
from app.extensions import db
from app.utils.decorators import admin_required, get_current_user_id
from app.utils.audit import log_action
from datetime import datetime, timedelta
from sqlalchemy import func

bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required
def get_users():
    """Get all users (admin only)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'users': [user.to_dict() for user in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200


@bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_user(user_id):
    """Update user (admin only)"""
    admin_id = get_current_user_id()
    if admin_id is None:
        return jsonify({'error': 'Invalid token'}), 401
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    # Update allowed fields
    if 'role' in data:
        try:
            user.role = UserRole(data['role'])
        except ValueError:
            return jsonify({'error': 'Invalid role'}), 400
    
    if 'is_active' in data:
        user.is_active = bool(data['is_active'])
    
    if 'full_name' in data:
        user.full_name = data['full_name']
    
    db.session.commit()
    
    log_action(admin_id, 'update_user', 'success', details=f"Updated user {user_id}")
    
    return jsonify({
        'message': 'User updated successfully',
        'user': user.to_dict()
    }), 200


@bp.route('/posts', methods=['GET'])
@jwt_required()
@admin_required
def get_all_posts():
    """Get all posts from all users (admin only)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    status = request.args.get('status')
    
    query = Post.query
    
    if status:
        try:
            query = query.filter_by(status=PostStatus(status))
        except ValueError:
            return jsonify({'error': 'Invalid status'}), 400
    
    pagination = query.order_by(Post.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    posts_data = []
    for post in pagination.items:
        post_dict = post.to_dict()
        post_dict['user_email'] = post.user.email
        posts_data.append(post_dict)
    
    return jsonify({
        'posts': posts_data,
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200


@bp.route('/analytics', methods=['GET'])
@jwt_required()
@admin_required
def get_analytics():
    """Get platform usage analytics (admin only)"""
    days = request.args.get('days', 30, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Total users
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    
    # Total posts
    total_posts = Post.query.count()
    
    # Posts by status
    posts_by_status = {}
    for status in PostStatus:
        count = Post.query.filter_by(status=status).count()
        posts_by_status[status.value] = count
    
    # Posts by platform
    posts_by_platform = {}
    for platform in PlatformType:
        count = Post.query.filter_by(platform=platform).count()
        posts_by_platform[platform.value] = count
    
    # Recent posts (last N days)
    recent_posts = Post.query.filter(Post.created_at >= start_date).count()
    
    # Posts scheduled in next 7 days
    upcoming_posts = Post.query.filter(
        Post.status == PostStatus.SCHEDULED,
        Post.scheduled_time >= datetime.utcnow(),
        Post.scheduled_time <= datetime.utcnow() + timedelta(days=7)
    ).count()
    
    # Failed posts
    failed_posts = Post.query.filter_by(status=PostStatus.FAILED).count()
    
    # Success rate
    posted_count = Post.query.filter_by(status=PostStatus.POSTED).count()
    attempted_posts = posted_count + failed_posts
    success_rate = (posted_count / attempted_posts * 100) if attempted_posts > 0 else 0
    
    return jsonify({
        'users': {
            'total': total_users,
            'active': active_users
        },
        'posts': {
            'total': total_posts,
            'recent': recent_posts,
            'upcoming': upcoming_posts,
            'failed': failed_posts,
            'by_status': posts_by_status,
            'by_platform': posts_by_platform,
            'success_rate': round(success_rate, 2)
        },
        'period_days': days
    }), 200


@bp.route('/failed-posts', methods=['GET'])
@jwt_required()
@admin_required
def get_failed_posts():
    """Get failed post diagnostics (admin only)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = Post.query.filter_by(status=PostStatus.FAILED).order_by(
        Post.updated_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    failed_posts_data = []
    for post in pagination.items:
        post_dict = post.to_dict()
        post_dict['user_email'] = post.user.email
        failed_posts_data.append(post_dict)
    
    return jsonify({
        'failed_posts': failed_posts_data,
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200


@bp.route('/audit-logs', methods=['GET'])
@jwt_required()
@admin_required
def get_audit_logs():
    """Get audit logs (admin only)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    action = request.args.get('action')
    user_id = request.args.get('user_id', type=int)
    
    query = AuditLog.query
    
    if action:
        query = query.filter_by(action=action)
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    pagination = query.order_by(AuditLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'logs': [log.to_dict() for log in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200


@bp.route('/posts/<int:post_id>/retry', methods=['POST'])
@jwt_required()
@admin_required
def retry_failed_post(post_id):
    """Retry a failed post (admin only)"""
    admin_id = get_current_user_id()
    if admin_id is None:
        return jsonify({'error': 'Invalid token'}), 401
    post = Post.query.get(post_id)
    
    if not post:
        return jsonify({'error': 'Post not found'}), 404
    
    if post.status != PostStatus.FAILED:
        return jsonify({'error': 'Post is not in failed status'}), 400
    
    # Reset post for retry
    post.status = PostStatus.SCHEDULED
    post.retry_count = 0
    post.error_message = None
    
    db.session.commit()
    
    log_action(admin_id, 'retry_post', 'success', post_id=post.id, platform=post.platform)
    
    return jsonify({
        'message': 'Post queued for retry',
        'post': post.to_dict()
    }), 200
