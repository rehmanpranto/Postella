"""Gunicorn configuration for Render deployment."""
import os

# Bind to the PORT env var that Render provides
bind = f"0.0.0.0:{os.getenv('PORT', '10000')}"
workers = int(os.getenv('WEB_CONCURRENCY', '4'))
timeout = 120
accesslog = "-"
errorlog = "-"
loglevel = "info"
