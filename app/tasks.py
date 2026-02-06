"""Background tasks — requires Celery + Redis. App works without them."""

from app.extensions import celery, db
from app.models import Post, PostStatus, OAuthToken, PlatformType
from app.utils.encryption import EncryptionService
from datetime import datetime, timedelta
import pytz


# Guard: if Celery is not available, define no-op placeholders
if celery is None:
    class _FakeTask:
        """Placeholder when Celery is not installed."""
        def delay(self, *a, **kw):
            pass
        def __call__(self, *a, **kw):
            pass

    check_and_publish_posts = _FakeTask()
    publish_post = _FakeTask()
    cleanup_old_posts = _FakeTask()
    check_token_expiry = _FakeTask()

else:
    from flask import current_app

    @celery.task(name='app.tasks.check_and_publish_posts')
    def check_and_publish_posts():
        """Check for scheduled posts and publish them. Runs every minute via Celery Beat."""
        now = datetime.now(pytz.UTC)

        posts_to_publish = Post.query.filter(
            Post.status == PostStatus.SCHEDULED,
            Post.scheduled_time <= now,
            Post.retry_count < Post.max_retries
        ).all()

        current_app.logger.info(f"Found {len(posts_to_publish)} posts to publish")

        for post in posts_to_publish:
            publish_post.delay(post.id)

        return {'checked_at': now.isoformat(), 'posts_queued': len(posts_to_publish)}

    @celery.task(name='app.tasks.publish_post', bind=True, max_retries=3)
    def publish_post(self, post_id):
        """Publish a single post to its platform."""
        from app.services.social_media import publish_to_platform

        post = Post.query.get(post_id)
        if not post:
            current_app.logger.error(f"Post {post_id} not found")
            return {'status': 'error', 'message': 'Post not found'}

        oauth_token = OAuthToken.query.filter_by(
            user_id=post.user_id, platform=post.platform, is_active=True
        ).first()

        if not oauth_token:
            post.status = PostStatus.FAILED
            post.error_message = "No active OAuth token found for this platform"
            db.session.commit()
            current_app.logger.error(f"No OAuth token for post {post_id}")
            return {'status': 'error', 'message': 'No OAuth token'}

        access_token = EncryptionService.decrypt(oauth_token.access_token)

        if oauth_token.expires_at and oauth_token.expires_at < datetime.utcnow():
            from app.services.social_media import refresh_oauth_token
            new_token = refresh_oauth_token(oauth_token)
            if new_token:
                access_token = new_token
            else:
                post.status = PostStatus.FAILED
                post.error_message = "OAuth token expired and refresh failed"
                db.session.commit()
                return {'status': 'error', 'message': 'Token expired'}

        try:
            result = publish_to_platform(post, access_token)
            if result['success']:
                post.status = PostStatus.POSTED
                post.published_at = datetime.utcnow()
                post.platform_post_id = result.get('post_id')
                post.error_message = None
                current_app.logger.info(f"Successfully published post {post_id}")
            else:
                raise Exception(result.get('error', 'Unknown error'))
        except Exception as e:
            post.retry_count += 1
            error_message = str(e)
            current_app.logger.error(f"Failed to publish post {post_id}: {error_message}")
            if post.retry_count >= post.max_retries:
                post.status = PostStatus.FAILED
                post.error_message = f"Failed after {post.retry_count} attempts: {error_message}"
            else:
                retry_delay = 60 * (2 ** post.retry_count)
                self.retry(countdown=retry_delay, exc=e)
            db.session.commit()
            return {'status': 'retry' if post.retry_count < post.max_retries else 'failed'}

        db.session.commit()

        from app.utils.audit import log_action
        log_action(
            post.user_id, 'publish_post',
            'success' if post.status == PostStatus.POSTED else 'failed',
            post_id=post.id, platform=post.platform
        )
        return {'status': 'success', 'post_id': post_id, 'platform_post_id': post.platform_post_id}

    @celery.task(name='app.tasks.cleanup_old_posts')
    def cleanup_old_posts():
        """Clean up old posted/failed posts (optional maintenance task)."""
        cutoff_date = datetime.utcnow() - timedelta(days=90)
        deleted = Post.query.filter(
            Post.status.in_([PostStatus.POSTED, PostStatus.FAILED]),
            Post.created_at < cutoff_date
        ).delete()
        db.session.commit()
        current_app.logger.info(f"Cleaned up {deleted} old posts")
        return {'deleted_count': deleted, 'cutoff_date': cutoff_date.isoformat()}

    @celery.task(name='app.tasks.check_token_expiry')
    def check_token_expiry():
        """Check for expiring OAuth tokens and send notifications."""
        warning_date = datetime.utcnow() + timedelta(days=7)
        expiring_tokens = OAuthToken.query.filter(
            OAuthToken.is_active == True,
            OAuthToken.expires_at <= warning_date,
            OAuthToken.expires_at > datetime.utcnow()
        ).all()
        current_app.logger.info(f"Found {len(expiring_tokens)} expiring tokens")
        for token in expiring_tokens:
            current_app.logger.warning(
                f"Token for user {token.user_id} on {token.platform.value} "
                f"expires at {token.expires_at}"
            )
        return {'expiring_tokens': len(expiring_tokens)}
