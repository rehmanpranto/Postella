from datetime import datetime
from app.models import AuditLog
from app.extensions import db
from flask import request


def log_action(user_id, action, status='success', post_id=None, platform=None, details=None):
    """Create audit log entry"""
    log = AuditLog(
        user_id=user_id,
        post_id=post_id,
        action=action,
        platform=platform,
        status=status,
        details=details,
        ip_address=request.remote_addr if request else None,
        user_agent=request.headers.get('User-Agent') if request else None
    )
    db.session.add(log)
    db.session.commit()
    return log
