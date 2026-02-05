import os
from app import create_app
from app.extensions import celery

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', app.config.get('PORT', 5000)))
    app.run(debug=app.config.get('DEBUG', False), host='0.0.0.0', port=port)
