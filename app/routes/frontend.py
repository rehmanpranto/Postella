"""Frontend routes for serving static pages"""

from flask import Blueprint, send_from_directory, current_app, send_file
import os

bp = Blueprint('frontend', __name__)

@bp.route('/')
def index():
    """Serve the landing page as the default"""
    static_dir = os.path.join(current_app.root_path, '..', 'static')
    return send_from_directory(static_dir, 'landing.html')

@bp.route('/static/<path:filename>')
def serve_static_files(filename):
    """Serve static CSS/JS files"""
    static_dir = os.path.join(current_app.root_path, '..', 'static')
    return send_from_directory(static_dir, filename)


@bp.route('/uploads/<path:filename>')
def serve_uploads(filename):
    """Serve uploaded media files"""
    upload_root = current_app.config['UPLOAD_FOLDER']
    if not os.path.isabs(upload_root):
        upload_root = os.path.abspath(os.path.join(current_app.root_path, '..', upload_root))
    return send_from_directory(upload_root, filename)

@bp.route('/<path:filename>')
def serve_pages(filename):
    """Serve HTML pages"""
    static_dir = os.path.join(current_app.root_path, '..', 'static')
    return send_from_directory(static_dir, filename)
