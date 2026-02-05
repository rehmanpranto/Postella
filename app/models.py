from datetime import datetime
from enum import Enum as PyEnum
from app.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash


class UserRole(PyEnum):
    """User role enumeration"""
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class PostStatus(PyEnum):
    """Post status enumeration"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    POSTED = "posted"
    FAILED = "failed"


class PlatformType(PyEnum):
    """Social media platform enumeration"""
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"


class User(db.Model):
    """User model"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.EDITOR, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    posts = db.relationship('Post', back_populates='user', cascade='all, delete-orphan')
    oauth_tokens = db.relationship('OAuthToken', back_populates='user', cascade='all, delete-orphan')
    audit_logs = db.relationship('AuditLog', back_populates='user', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role.value,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class Post(db.Model):
    """Content post model"""
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    platform = db.Column(db.Enum(PlatformType), nullable=False)
    status = db.Column(db.Enum(PostStatus), default=PostStatus.DRAFT, nullable=False, index=True)
    scheduled_time = db.Column(db.DateTime, nullable=True, index=True)
    timezone = db.Column(db.String(50), default='UTC', nullable=False)
    media_path = db.Column(db.String(500), nullable=True)
    media_type = db.Column(db.String(50), nullable=True)  # image, video
    published_at = db.Column(db.DateTime, nullable=True)
    platform_post_id = db.Column(db.String(255), nullable=True)  # ID from social platform
    error_message = db.Column(db.Text, nullable=True)
    retry_count = db.Column(db.Integer, default=0, nullable=False)
    max_retries = db.Column(db.Integer, default=3, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = db.relationship('User', back_populates='posts')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'content': self.content,
            'platform': self.platform.value,
            'status': self.status.value,
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'timezone': self.timezone,
            'media_path': self.media_path,
            'media_type': self.media_type,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'platform_post_id': self.platform_post_id,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class OAuthToken(db.Model):
    """OAuth token storage for social media platforms"""
    __tablename__ = 'oauth_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    platform = db.Column(db.Enum(PlatformType), nullable=False)
    access_token = db.Column(db.Text, nullable=False)  # Encrypted
    refresh_token = db.Column(db.Text, nullable=True)  # Encrypted
    token_type = db.Column(db.String(50), nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    scope = db.Column(db.Text, nullable=True)
    platform_user_id = db.Column(db.String(255), nullable=True)
    platform_username = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = db.relationship('User', back_populates='oauth_tokens')
    
    # Unique constraint: one token per user per platform
    __table_args__ = (
        db.UniqueConstraint('user_id', 'platform', name='unique_user_platform'),
    )
    
    def to_dict(self, include_tokens=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'platform': self.platform.value,
            'platform_user_id': self.platform_user_id,
            'platform_username': self.platform_username,
            'is_active': self.is_active,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_tokens:
            data.update({
                'access_token': self.access_token,
                'refresh_token': self.refresh_token,
                'token_type': self.token_type,
                'scope': self.scope
            })
        
        return data


class AuditLog(db.Model):
    """Audit log for tracking all publishing actions"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True, index=True)
    action = db.Column(db.String(100), nullable=False)  # create, update, delete, publish, etc.
    platform = db.Column(db.Enum(PlatformType), nullable=True)
    status = db.Column(db.String(50), nullable=False)  # success, failed
    details = db.Column(db.Text, nullable=True)  # JSON or text details
    ip_address = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = db.relationship('User', back_populates='audit_logs')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'post_id': self.post_id,
            'action': self.action,
            'platform': self.platform.value if self.platform else None,
            'status': self.status,
            'details': self.details,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'created_at': self.created_at.isoformat()
        }


class PlatformConfig(db.Model):
    """Platform-specific configuration and constraints"""
    __tablename__ = 'platform_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.Enum(PlatformType), unique=True, nullable=False)
    max_text_length = db.Column(db.Integer, nullable=False)
    supports_images = db.Column(db.Boolean, default=True, nullable=False)
    supports_videos = db.Column(db.Boolean, default=True, nullable=False)
    max_image_size_mb = db.Column(db.Integer, nullable=False)
    max_video_size_mb = db.Column(db.Integer, nullable=False)
    allowed_image_formats = db.Column(db.String(200), nullable=False)
    allowed_video_formats = db.Column(db.String(200), nullable=False)
    rate_limit_per_hour = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'platform': self.platform.value,
            'max_text_length': self.max_text_length,
            'supports_images': self.supports_images,
            'supports_videos': self.supports_videos,
            'max_image_size_mb': self.max_image_size_mb,
            'max_video_size_mb': self.max_video_size_mb,
            'allowed_image_formats': self.allowed_image_formats,
            'allowed_video_formats': self.allowed_video_formats,
            'rate_limit_per_hour': self.rate_limit_per_hour,
            'is_active': self.is_active
        }
