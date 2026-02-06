import os
from app import create_app

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = app.config.get('DEBUG', False)
    print(f"\n  ✦ Postella running at http://localhost:{port}\n")
    app.run(debug=debug, host='0.0.0.0', port=port)
