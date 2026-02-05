from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import Post, PostStatus, PlatformType, PlatformConfig
from app.extensions import db
from app.utils.decorators import active_user_required, get_current_user_id
from datetime import datetime, timedelta
import pytz
import calendar as calendar_lib

bp = Blueprint('calendar', __name__, url_prefix='/api/calendar')


@bp.route('/posts', methods=['GET'])
@jwt_required()
@active_user_required
def get_calendar_posts():
    """Get posts for calendar view with date range filtering"""
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({'error': 'Invalid token'}), 401
    
    # Get date range from query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    view = request.args.get('view', 'month')  # day, week, month
    
    # Parse dates
    try:
        if start_date:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        else:
            # Default to start of current month
            now = datetime.now(pytz.UTC)
            start = datetime(now.year, now.month, 1, tzinfo=pytz.UTC)
        
        if end_date:
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        else:
            # Default based on view
            if view == 'day':
                end = start + timedelta(days=1)
            elif view == 'week':
                end = start + timedelta(weeks=1)
            else:  # month
                # End of month
                if start.month == 12:
                    end = datetime(start.year + 1, 1, 1, tzinfo=pytz.UTC)
                else:
                    end = datetime(start.year, start.month + 1, 1, tzinfo=pytz.UTC)
    except ValueError as e:
        return jsonify({'error': f'Invalid date format: {str(e)}'}), 400
    
    # Query posts in date range
    query = Post.query.filter(
        Post.user_id == user_id,
        Post.scheduled_time >= start,
        Post.scheduled_time < end
    ).order_by(Post.scheduled_time)
    
    posts = query.all()
    
    # Group posts by date
    posts_by_date = {}
    for post in posts:
        date_key = post.scheduled_time.date().isoformat()
        if date_key not in posts_by_date:
            posts_by_date[date_key] = []
        posts_by_date[date_key].append(post.to_dict())
    
    return jsonify({
        'start_date': start.isoformat(),
        'end_date': end.isoformat(),
        'view': view,
        'posts_by_date': posts_by_date,
        'total_posts': len(posts)
    }), 200


@bp.route('/stats', methods=['GET'])
@jwt_required()
@active_user_required
def get_calendar_stats():
    """Get statistics for calendar view"""
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({'error': 'Invalid token'}), 401
    
    # Get date range
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    try:
        if start_date:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        else:
            now = datetime.now(pytz.UTC)
            start = datetime(now.year, now.month, 1, tzinfo=pytz.UTC)
        
        if end_date:
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        else:
            if start.month == 12:
                end = datetime(start.year + 1, 1, 1, tzinfo=pytz.UTC)
            else:
                end = datetime(start.year, start.month + 1, 1, tzinfo=pytz.UTC)
    except ValueError as e:
        return jsonify({'error': f'Invalid date format: {str(e)}'}), 400
    
    # Base query
    base_query = Post.query.filter(
        Post.user_id == user_id,
        Post.scheduled_time >= start,
        Post.scheduled_time < end
    )
    
    # Count by status
    stats = {
        'total': base_query.count(),
        'by_status': {
            'draft': base_query.filter_by(status=PostStatus.DRAFT).count(),
            'scheduled': base_query.filter_by(status=PostStatus.SCHEDULED).count(),
            'posted': base_query.filter_by(status=PostStatus.POSTED).count(),
            'failed': base_query.filter_by(status=PostStatus.FAILED).count()
        },
        'by_platform': {}
    }
    
    # Count by platform
    from app.models import PlatformType
    for platform in PlatformType:
        count = base_query.filter_by(platform=platform).count()
        if count > 0:
            stats['by_platform'][platform.value] = count
    
    return jsonify(stats), 200


@bp.route('/move', methods=['POST'])
@jwt_required()
@active_user_required
def move_post():
    """Move a post to a different date/time (drag and drop support)"""
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({'error': 'Invalid token'}), 401
    data = request.get_json()
    
    if not data or 'post_id' not in data or 'new_scheduled_time' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    post_id = data['post_id']
    new_scheduled_time = data['new_scheduled_time']
    
    # Get post
    post = Post.query.filter_by(id=post_id, user_id=user_id).first()
    
    if not post:
        return jsonify({'error': 'Post not found'}), 404
    
    if post.status == PostStatus.POSTED:
        return jsonify({'error': 'Cannot move already posted content'}), 400
    
    # Parse new time
    try:
        scheduled_datetime = datetime.fromisoformat(new_scheduled_time.replace('Z', '+00:00'))
        
        # Convert to UTC if needed
        if post.timezone != 'UTC':
            tz = pytz.timezone(post.timezone)
            if scheduled_datetime.tzinfo is None:
                scheduled_datetime = tz.localize(scheduled_datetime)
            scheduled_datetime = scheduled_datetime.astimezone(pytz.UTC)
        
        post.scheduled_time = scheduled_datetime
        
        # Update status
        if scheduled_datetime > datetime.now(pytz.UTC):
            post.status = PostStatus.SCHEDULED
        else:
            post.status = PostStatus.DRAFT
        
        db.session.commit()
        
        from app.utils.audit import log_action
        log_action(user_id, 'move_post', 'success', post_id=post.id, platform=post.platform)
        
        return jsonify({
            'message': 'Post moved successfully',
            'post': post.to_dict()
        }), 200
    
    except (ValueError, pytz.exceptions.UnknownTimeZoneError) as e:
        return jsonify({'error': f'Invalid scheduled time: {str(e)}'}), 400


class _SafeFormatDict(dict):
    def __missing__(self, key):
        return '{' + key + '}'


def _render_template(template, local_date, platform=None):
    """Render a simple template with date placeholders."""
    data = _SafeFormatDict(
        date=local_date.strftime('%Y-%m-%d'),
        day=local_date.strftime('%A'),
        month=local_date.strftime('%B'),
        day_of_month=local_date.day,
        platform=platform or ''
    )
    return template.format_map(data)


def _parse_bool(value, default=False):
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, str):
        return value.strip().lower() in {'1', 'true', 'yes', 'on'}
    return bool(value)


@bp.route('/plan-month', methods=['POST'])
@jwt_required()
@active_user_required
def plan_month():
    """Bulk plan posts across a whole month"""
    user_id = get_current_user_id()
    if user_id is None:
        return jsonify({'error': 'Invalid token'}), 401

    data = request.get_json() or {}

    month_value = data.get('month')  # YYYY-MM
    platform = data.get('platform')
    content_template = data.get('content_template')
    title_template = data.get('title_template') or 'Planned post for {date}'
    time_value = data.get('time') or '09:00'
    timezone = data.get('timezone') or 'UTC'
    weekdays_only = _parse_bool(data.get('weekdays_only'))
    skip_existing = _parse_bool(data.get('skip_existing', True), default=True)

    if not month_value or not platform or not content_template:
        return jsonify({'error': 'Missing required fields'}), 400

    platform_enums = []
    if platform == 'all':
        active_platforms = PlatformConfig.query.filter_by(is_active=True).all()
        if active_platforms:
            platform_enums = [p.platform for p in active_platforms]
        else:
            platform_enums = list(PlatformType)
    else:
        try:
            platform_enums = [PlatformType(platform)]
        except ValueError:
            return jsonify({'error': 'Invalid platform'}), 400

    try:
        year_str, month_str = month_value.split('-')
        year = int(year_str)
        month = int(month_str)
        if month < 1 or month > 12:
            raise ValueError('Invalid month')
    except Exception:
        return jsonify({'error': 'Invalid month format. Use YYYY-MM.'}), 400

    try:
        hour_str, minute_str = time_value.split(':')
        hour = int(hour_str)
        minute = int(minute_str)
        if hour not in range(0, 24) or minute not in range(0, 60):
            raise ValueError('Invalid time')
    except Exception:
        return jsonify({'error': 'Invalid time format. Use HH:MM.'}), 400

    try:
        tz = pytz.timezone(timezone)
    except pytz.exceptions.UnknownTimeZoneError:
        return jsonify({'error': 'Invalid timezone'}), 400

    days_in_month = calendar_lib.monthrange(year, month)[1]
    now_utc = datetime.now(pytz.UTC)
    created = 0
    skipped = 0
    posts = []

    for day in range(1, days_in_month + 1):
        local_date = datetime(year, month, day, hour, minute)
        if weekdays_only and local_date.weekday() >= 5:
            continue

        localized = tz.localize(local_date)
        scheduled_utc = localized.astimezone(pytz.UTC)

        for platform_enum in platform_enums:
            if skip_existing:
                existing = Post.query.filter_by(
                    user_id=user_id,
                    platform=platform_enum,
                    scheduled_time=scheduled_utc
                ).first()
                if existing:
                    skipped += 1
                    continue

            post = Post(
                user_id=user_id,
                title=_render_template(title_template, localized, platform_enum.value),
                content=_render_template(content_template, localized, platform_enum.value),
                platform=platform_enum,
                status=PostStatus.SCHEDULED if scheduled_utc > now_utc else PostStatus.DRAFT,
                scheduled_time=scheduled_utc,
                timezone=timezone
            )
            posts.append(post)
            created += 1

    if posts:
        db.session.add_all(posts)
        db.session.commit()

        from app.utils.audit import log_action
        log_action(user_id, 'plan_month', 'success', details=f"Created {created}, skipped {skipped}")

    return jsonify({
        'message': 'Monthly plan created',
        'created': created,
        'skipped': skipped,
        'month': month_value
    }), 201
