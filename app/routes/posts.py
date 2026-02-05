from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Post, PostStatus, PlatformType, PlatformConfig
from app.extensions import db, limiter
from app.utils.decorators import editor_required, active_user_required, get_current_user_id
from app.utils.files import save_uploaded_file, get_media_type
from app.utils.audit import log_action
from datetime import datetime
import pytz

bp = Blueprint('posts', __name__, url_prefix='/api/posts')


@bp.route('', methods=['GET'])
@jwt_required()
@active_user_required
def get_posts():
    """Get all posts for current user"""
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({'error': 'Invalid token'}), 401
    
    # Query parameters for filtering
    status = request.args.get('status')
    platform = request.args.get('platform')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Build query
    query = Post.query.filter_by(user_id=user_id)
    
    if status:
        try:
            query = query.filter_by(status=PostStatus(status))
        except ValueError:
            return jsonify({'error': 'Invalid status'}), 400
    
    if platform:
        try:
            query = query.filter_by(platform=PlatformType(platform))
        except ValueError:
            return jsonify({'error': 'Invalid platform'}), 400
    
    # Order by scheduled time
    query = query.order_by(Post.scheduled_time.desc().nullslast(), Post.created_at.desc())
    
    # Paginate
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'posts': [post.to_dict() for post in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200


@bp.route('/<int:post_id>', methods=['GET'])
@jwt_required()
@active_user_required
def get_post(post_id):
    """Get a specific post"""
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({'error': 'Invalid token'}), 401
    post = Post.query.filter_by(id=post_id, user_id=user_id).first()
    
    if not post:
        return jsonify({'error': 'Post not found'}), 404
    
    return jsonify(post.to_dict()), 200


@bp.route('', methods=['POST'])
@jwt_required()
@editor_required
@limiter.limit("50 per hour")
def create_post():
    """Create a new post"""
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({'error': 'Invalid token'}), 401
    
    # Get form data
    title = request.form.get('title')
    content = request.form.get('content')
    platform = request.form.get('platform')
    scheduled_time = request.form.get('scheduled_time')
    timezone = request.form.get('timezone', 'UTC')
    
    # Validate required fields
    if not all([title, content, platform]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Validate platform
    try:
        platform_enum = PlatformType(platform)
    except ValueError:
        return jsonify({'error': 'Invalid platform'}), 400
    
    # Validate against platform config
    platform_config = PlatformConfig.query.filter_by(platform=platform_enum).first()
    if platform_config:
        if len(content) > platform_config.max_text_length:
            return jsonify({
                'error': f'Content exceeds maximum length for {platform} ({platform_config.max_text_length} characters)'
            }), 400
    
    # Handle file upload
    media_path = None
    media_type = None
    if 'media' in request.files:
        file = request.files['media']
        if file.filename:
            media_path = save_uploaded_file(file)
            if not media_path:
                return jsonify({'error': 'Invalid file type'}), 400
            media_type = get_media_type(media_path)
    
    # Parse scheduled time
    scheduled_datetime = None
    status = PostStatus.DRAFT
    
    if scheduled_time:
        try:
            # Parse datetime
            scheduled_datetime = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
            
            # Convert to UTC
            if timezone != 'UTC':
                tz = pytz.timezone(timezone)
                if scheduled_datetime.tzinfo is None:
                    scheduled_datetime = tz.localize(scheduled_datetime)
                scheduled_datetime = scheduled_datetime.astimezone(pytz.UTC)
            
            # Set status to scheduled if time is in future
            if scheduled_datetime > datetime.now(pytz.UTC):
                status = PostStatus.SCHEDULED
        except (ValueError, pytz.exceptions.UnknownTimeZoneError) as e:
            return jsonify({'error': f'Invalid scheduled time or timezone: {str(e)}'}), 400
    
    # Create post
    post = Post(
        user_id=user_id,
        title=title,
        content=content,
        platform=platform_enum,
        status=status,
        scheduled_time=scheduled_datetime,
        timezone=timezone,
        media_path=media_path,
        media_type=media_type
    )
    
    db.session.add(post)
    db.session.commit()
    
    log_action(user_id, 'create_post', 'success', post_id=post.id, platform=platform_enum)
    
    return jsonify({
        'message': 'Post created successfully',
        'post': post.to_dict()
    }), 201


@bp.route('/<int:post_id>', methods=['PUT'])
@jwt_required()
@editor_required
def update_post(post_id):
    """Update a post"""
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({'error': 'Invalid token'}), 401
    post = Post.query.filter_by(id=post_id, user_id=user_id).first()
    
    if not post:
        return jsonify({'error': 'Post not found'}), 404
    
    # Cannot edit already posted items
    if post.status == PostStatus.POSTED:
        return jsonify({'error': 'Cannot edit already posted content'}), 400
    
    # Get form data
    title = request.form.get('title', post.title)
    content = request.form.get('content', post.content)
    platform = request.form.get('platform', post.platform.value)
    scheduled_time = request.form.get('scheduled_time')
    timezone = request.form.get('timezone', post.timezone)
    
    # Validate platform
    try:
        platform_enum = PlatformType(platform)
    except ValueError:
        return jsonify({'error': 'Invalid platform'}), 400
    
    # Handle file upload
    if 'media' in request.files:
        file = request.files['media']
        if file.filename:
            media_path = save_uploaded_file(file)
            if not media_path:
                return jsonify({'error': 'Invalid file type'}), 400
            post.media_path = media_path
            post.media_type = get_media_type(media_path)
    
    # Update fields
    post.title = title
    post.content = content
    post.platform = platform_enum
    post.timezone = timezone
    
    # Update scheduled time
    if scheduled_time:
        try:
            scheduled_datetime = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
            
            if timezone != 'UTC':
                tz = pytz.timezone(timezone)
                if scheduled_datetime.tzinfo is None:
                    scheduled_datetime = tz.localize(scheduled_datetime)
                scheduled_datetime = scheduled_datetime.astimezone(pytz.UTC)
            
            post.scheduled_time = scheduled_datetime
            
            # Update status
            if scheduled_datetime > datetime.now(pytz.UTC):
                post.status = PostStatus.SCHEDULED
            else:
                post.status = PostStatus.DRAFT
        except (ValueError, pytz.exceptions.UnknownTimeZoneError) as e:
            return jsonify({'error': f'Invalid scheduled time or timezone: {str(e)}'}), 400
    
    db.session.commit()
    
    log_action(user_id, 'update_post', 'success', post_id=post.id, platform=platform_enum)
    
    return jsonify({
        'message': 'Post updated successfully',
        'post': post.to_dict()
    }), 200


@bp.route('/<int:post_id>', methods=['DELETE'])
@jwt_required()
@editor_required
def delete_post(post_id):
    """Delete a post"""
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({'error': 'Invalid token'}), 401
    post = Post.query.filter_by(id=post_id, user_id=user_id).first()
    
    if not post:
        return jsonify({'error': 'Post not found'}), 404
    
    log_action(user_id, 'delete_post', 'success', post_id=post.id, platform=post.platform)
    
    db.session.delete(post)
    db.session.commit()
    
    return jsonify({'message': 'Post deleted successfully'}), 200


@bp.route('/<int:post_id>/duplicate', methods=['POST'])
@jwt_required()
@editor_required
def duplicate_post(post_id):
    """Duplicate a post"""
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({'error': 'Invalid token'}), 401
    original_post = Post.query.filter_by(id=post_id, user_id=user_id).first()
    
    if not original_post:
        return jsonify({'error': 'Post not found'}), 404
    
    # Create duplicate
    duplicate = Post(
        user_id=user_id,
        title=f"{original_post.title} (Copy)",
        content=original_post.content,
        platform=original_post.platform,
        status=PostStatus.DRAFT,
        scheduled_time=None,
        timezone=original_post.timezone,
        media_path=original_post.media_path,
        media_type=original_post.media_type
    )
    
    db.session.add(duplicate)
    db.session.commit()
    
    log_action(user_id, 'duplicate_post', 'success', post_id=duplicate.id, platform=duplicate.platform)
    
    return jsonify({
        'message': 'Post duplicated successfully',
        'post': duplicate.to_dict()
    }), 201


@bp.route('/platforms', methods=['GET'])
@jwt_required()
def get_platforms():
    """Get all platform configurations"""
    platforms = PlatformConfig.query.filter_by(is_active=True).all()
    return jsonify({
        'platforms': [platform.to_dict() for platform in platforms]
    }), 200
