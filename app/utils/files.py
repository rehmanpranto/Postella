import os
from werkzeug.utils import secure_filename
from flask import current_app
from datetime import datetime


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def save_uploaded_file(file, subfolder='posts'):
    """Save uploaded file and return path"""
    if not file or not allowed_file(file.filename):
        return None
    
    # Create timestamped filename
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filename = secure_filename(file.filename)
    name, ext = os.path.splitext(filename)
    unique_filename = f"{name}_{timestamp}{ext}"
    
    # Create subfolder path
    upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
    os.makedirs(upload_path, exist_ok=True)
    
    # Save file
    file_path = os.path.join(upload_path, unique_filename)
    file.save(file_path)
    
    # Return relative path
    return os.path.join(subfolder, unique_filename)


def get_media_type(filename):
    """Determine media type from filename"""
    if not filename:
        return None
    
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    image_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    video_extensions = {'mp4', 'mov', 'avi'}
    
    if ext in image_extensions:
        return 'image'
    elif ext in video_extensions:
        return 'video'
    
    return None
