# Postella

A full-stack web application for planning, scheduling, and automatically publishing content to multiple social media platforms.

![Postella](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0.0-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## Features

### Core Functionality
- ✅ **User Authentication** - Email/password login with JWT tokens
- ✅ **Role-Based Access Control** - Admin, Editor, and Viewer roles
- ✅ **Content Calendar** - Day/week/month views with drag-and-drop
- ✅ **Post Management** - Create, edit, duplicate, and delete scheduled posts
- ✅ **Multi-Platform Support** - Facebook, Instagram, LinkedIn, Twitter/X
- ✅ **Media Upload** - Support for images and videos
- ✅ **Timezone-Aware Scheduling** - Schedule posts in any timezone
- ✅ **Automatic Publishing** - Background jobs publish content automatically
- ✅ **Retry Logic** - Automatic retries for failed posts
- ✅ **Audit Logging** - Track all actions with timestamps

### Technical Features
- ✅ **RESTful API** - Well-structured API with proper validation
- ✅ **OAuth Integration** - Secure social media authentication
- ✅ **Encrypted Token Storage** - All OAuth tokens are encrypted
- ✅ **Rate Limiting** - Protect against abuse
- ✅ **Platform-Specific Rules** - Character limits and media constraints
- ✅ **Background Task Queue** - Celery + Redis for async processing
- ✅ **Admin Dashboard** - Analytics, failed post diagnostics, user management

## Tech Stack

### Backend
- **Framework:** Flask 3.0
- **Database:** PostgreSQL with SQLAlchemy ORM
- **Task Queue:** Celery + Redis
- **Authentication:** Flask-JWT-Extended
- **Security:** Cryptography, bcrypt, rate limiting
- **API:** RESTful with JSON responses

### Frontend
- **HTML5/CSS3** - Responsive design
- **Vanilla JavaScript** - No framework dependencies
- **Modern UI** - Clean, professional interface

## Installation

### Prerequisites
- Python 3.9 or higher
- PostgreSQL 12 or higher
- Redis 6 or higher
- Node.js (optional, for frontend tooling)

### Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/Postella.git
cd Postella
```

2. **Create virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up PostgreSQL database**
```bash
# Create database
createdb postella

# Or using psql
psql -U postgres
CREATE DATABASE postella;
\q
```

5. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your configuration
```

6. **Initialize database**
```bash
flask init-db
```

7. **Create admin user**
```bash
flask create-admin
# Follow the prompts to enter email, password, and name
```

8. **Start Redis (in a separate terminal)**
```bash
redis-server
```

9. **Start Celery workers (in a separate terminal)**
```bash
celery -A celery_worker.celery worker --loglevel=info
```

10. **Start Celery beat scheduler (in a separate terminal)**
```bash
celery -A celery_worker.celery beat --loglevel=info
```

11. **Run the application**
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## Configuration

Copy .env.example to .env and fill in your values.

## Docs

- API reference: [API_DOCS.md](API_DOCS.md)
- Deployment: [DEPLOYMENT.md](DEPLOYMENT.md)
- Quick reference: [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

## License

MIT License - see LICENSE file for details
