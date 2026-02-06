"""Application package initialization"""

from flask import Flask
from config import config
from app.extensions import init_extensions, db
import os


def create_app(config_name=None):
    """Application factory pattern"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__, static_folder=None)
    app.config.from_object(config[config_name])
    
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Initialize extensions
    init_extensions(app)
    
    # Register blueprints
    from app.routes import auth, posts, calendar, oauth, admin, health, frontend
    from app.routes.contact import contact_bp
    
    app.register_blueprint(auth.bp)
    app.register_blueprint(posts.bp)
    app.register_blueprint(calendar.bp)
    app.register_blueprint(oauth.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(health.bp)
    app.register_blueprint(contact_bp)
    app.register_blueprint(frontend.bp)  # Register last to catch remaining routes
    
    # Error handlers
    register_error_handlers(app)
    
    # CLI commands
    register_commands(app)

    # Auto-create tables on first request (dev convenience)
    with app.app_context():
        db.create_all()
        _seed_platform_configs(app)
    
    return app


def _seed_platform_configs(app):
    """Seed default platform configs if table is empty."""
    from app.models import PlatformConfig, PlatformType
    try:
        if PlatformConfig.query.first() is None:
            platforms = [
                {
                    'platform': PlatformType.FACEBOOK,
                    'max_text_length': 63206,
                    'supports_images': True,
                    'supports_videos': True,
                    'max_image_size_mb': 4,
                    'max_video_size_mb': 1024,
                    'allowed_image_formats': 'jpg,jpeg,png,gif',
                    'allowed_video_formats': 'mp4,mov',
                    'rate_limit_per_hour': 200
                },
                {
                    'platform': PlatformType.INSTAGRAM,
                    'max_text_length': 2200,
                    'supports_images': True,
                    'supports_videos': True,
                    'max_image_size_mb': 8,
                    'max_video_size_mb': 100,
                    'allowed_image_formats': 'jpg,jpeg,png',
                    'allowed_video_formats': 'mp4,mov',
                    'rate_limit_per_hour': 25
                },
                {
                    'platform': PlatformType.LINKEDIN,
                    'max_text_length': 3000,
                    'supports_images': True,
                    'supports_videos': True,
                    'max_image_size_mb': 5,
                    'max_video_size_mb': 200,
                    'allowed_image_formats': 'jpg,jpeg,png,gif',
                    'allowed_video_formats': 'mp4,mov,avi',
                    'rate_limit_per_hour': 100
                },
                {
                    'platform': PlatformType.TWITTER,
                    'max_text_length': 280,
                    'supports_images': True,
                    'supports_videos': True,
                    'max_image_size_mb': 5,
                    'max_video_size_mb': 512,
                    'allowed_image_formats': 'jpg,jpeg,png,gif',
                    'allowed_video_formats': 'mp4,mov',
                    'rate_limit_per_hour': 300
                }
            ]
            for p in platforms:
                db.session.add(PlatformConfig(**p))
            db.session.commit()
    except Exception:
        db.session.rollback()


def register_error_handlers(app):
    """Register error handlers"""
    from flask import jsonify
    
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'error': 'Bad request', 'message': str(e)}), 400
    
    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({'error': 'Unauthorized', 'message': str(e)}), 401
    
    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({'error': 'Forbidden', 'message': str(e)}), 403
    
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Not found', 'message': str(e)}), 404
    
    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500


def register_commands(app):
    """Register CLI commands"""
    import click
    from app.models import User, UserRole, PlatformConfig, PlatformType
    
    @app.cli.command()
    def init_db():
        """Initialize the database"""
        db.create_all()
        click.echo('Database initialized.')
        
        # Create default platform configs
        platforms = [
            {
                'platform': PlatformType.FACEBOOK,
                'max_text_length': 63206,
                'supports_images': True,
                'supports_videos': True,
                'max_image_size_mb': 4,
                'max_video_size_mb': 1024,
                'allowed_image_formats': 'jpg,jpeg,png,gif',
                'allowed_video_formats': 'mp4,mov',
                'rate_limit_per_hour': 200
            },
            {
                'platform': PlatformType.INSTAGRAM,
                'max_text_length': 2200,
                'supports_images': True,
                'supports_videos': True,
                'max_image_size_mb': 8,
                'max_video_size_mb': 100,
                'allowed_image_formats': 'jpg,jpeg,png',
                'allowed_video_formats': 'mp4,mov',
                'rate_limit_per_hour': 25
            },
            {
                'platform': PlatformType.LINKEDIN,
                'max_text_length': 3000,
                'supports_images': True,
                'supports_videos': True,
                'max_image_size_mb': 5,
                'max_video_size_mb': 200,
                'allowed_image_formats': 'jpg,jpeg,png,gif',
                'allowed_video_formats': 'mp4,mov,avi',
                'rate_limit_per_hour': 100
            },
            {
                'platform': PlatformType.TWITTER,
                'max_text_length': 280,
                'supports_images': True,
                'supports_videos': True,
                'max_image_size_mb': 5,
                'max_video_size_mb': 512,
                'allowed_image_formats': 'jpg,jpeg,png,gif',
                'allowed_video_formats': 'mp4,mov',
                'rate_limit_per_hour': 300
            }
        ]
        
        for platform_data in platforms:
            platform = PlatformConfig.query.filter_by(
                platform=platform_data['platform']
            ).first()
            
            if not platform:
                platform = PlatformConfig(**platform_data)
                db.session.add(platform)
        
        db.session.commit()
        click.echo('Platform configurations created.')
    
    @app.cli.command()
    @click.option('--email', prompt=True)
    @click.option('--password', prompt=True, hide_input=True)
    @click.option('--name', prompt=True)
    def create_admin(email, password, name):
        """Create an admin user"""
        user = User.query.filter_by(email=email).first()
        if user:
            click.echo('User already exists.')
            return
        
        user = User(
            email=email,
            full_name=name,
            role=UserRole.ADMIN,
            is_active=True
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f'Admin user created: {email}')
