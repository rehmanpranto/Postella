from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[]
)

# Celery is optional — only initialise when Redis is available
celery = None
try:
    from celery import Celery
    celery = Celery()
except ImportError:
    pass


def init_extensions(app):
    """Initialize Flask extensions"""
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, origins=app.config.get('CORS_ORIGINS', '*'))

    # Rate limiter
    storage_uri = app.config.get('RATELIMIT_STORAGE_URL', 'memory://')
    app.config['RATELIMIT_STORAGE_URI'] = storage_uri
    default_limits = app.config.get('RATELIMIT_DEFAULT')
    if isinstance(default_limits, (list, tuple)):
        app.config['RATELIMIT_DEFAULT'] = ';'.join(str(limit) for limit in default_limits)
    limiter.init_app(app)
    
    # Initialize Celery only when broker URL is configured
    if celery and app.config.get('CELERY_BROKER_URL'):
        celery.conf.update(
            broker_url=app.config['CELERY_BROKER_URL'],
            result_backend=app.config['CELERY_RESULT_BACKEND'],
            task_serializer=app.config['CELERY_TASK_SERIALIZER'],
            result_serializer=app.config['CELERY_RESULT_SERIALIZER'],
            accept_content=app.config['CELERY_ACCEPT_CONTENT'],
            timezone=app.config['CELERY_TIMEZONE'],
            beat_schedule=app.config['CELERY_BEAT_SCHEDULE']
        )

        class ContextTask(celery.Task):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)

        celery.Task = ContextTask
    
    return None
