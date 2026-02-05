from app import create_app
from app.extensions import celery

app = create_app()
app.app_context().push()

# Ensure Celery tasks are registered
import app.tasks  # noqa: F401
