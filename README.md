# AutoContent Calendar

A full-stack web application for planning, scheduling, and automatically publishing content to multiple social media platforms.

![AutoContent Calendar](https://img.shields.io/badge/version-1.0.0-blue.svg)
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
git clone https://github.com/yourusername/AutoContentCalendar.git
cd AutoContentCalendar
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
createdb autocontent_calendar

# Or using psql
psql -U postgres
CREATE DATABASE autocontent_calendar;
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

### Environment Variables

Edit the `.env` file with your configuration:

```bash
# Flask
SECRET_KEY=your-secret-key-here
FLASK_ENV=development

# Database
DATABASE_URL=postgresql://username:password@localhost:5432/autocontent_calendar

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_EXPIRES=3600

# Encryption
ENCRYPTION_KEY=your-32-byte-encryption-key

# Social Media OAuth (Get from respective developer portals)
FACEBOOK_CLIENT_ID=your-facebook-app-id
FACEBOOK_CLIENT_SECRET=your-facebook-app-secret
FACEBOOK_REDIRECT_URI=http://localhost:5000/api/oauth/facebook/callback

INSTAGRAM_CLIENT_ID=your-instagram-app-id
INSTAGRAM_CLIENT_SECRET=your-instagram-app-secret

LINKEDIN_CLIENT_ID=your-linkedin-client-id
LINKEDIN_CLIENT_SECRET=your-linkedin-client-secret

TWITTER_CLIENT_ID=your-twitter-client-id
TWITTER_CLIENT_SECRET=your-twitter-client-secret
```

### Social Media OAuth Setup

#### Facebook
1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Create a new app
3. Add Facebook Login product
4. Set redirect URI: `http://localhost:5000/api/oauth/facebook/callback`
5. Copy App ID and App Secret to `.env`

#### Instagram
1. Use Facebook Graph API (Instagram is owned by Facebook)
2. Configure in Facebook App settings
3. Add Instagram Basic Display product

#### LinkedIn
1. Go to [LinkedIn Developers](https://www.linkedin.com/developers/)
2. Create a new app
3. Add Sign In with LinkedIn product
4. Set redirect URI: `http://localhost:5000/api/oauth/linkedin/callback`

#### Twitter/X
1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Create a new project and app
3. Enable OAuth 2.0
4. Set redirect URI: `http://localhost:5000/api/oauth/twitter/callback`

## Usage

### Creating Your First Post

1. **Login** at `http://localhost:5000/login.html`
2. Navigate to **Dashboard** or click **"Create Post"**
3. Fill in the form:
   - Title (for your reference)
   - Platform (Facebook, Instagram, LinkedIn, Twitter)
   - Content (respects platform character limits)
   - Media (optional image or video)
   - Scheduled date & time
   - Timezone
4. Click **"Create Post"**

### Managing Posts

- **View All Posts:** Navigate to "Posts" page
- **Filter Posts:** By status (draft, scheduled, posted, failed) or platform
- **Edit Post:** Click "Edit" on any post
- **Duplicate Post:** Quickly create a copy with "Duplicate" button
- **Delete Post:** Remove posts you no longer need

### Calendar View

- **Switch Views:** Day, Week, or Month
- **Navigate:** Use arrow buttons to move between time periods
- **Drag & Drop:** Move posts to different dates (coming soon)
- **Click Posts:** View details in modal

### Connecting Social Media

1. Go to **Settings** page
2. Click **"Connect [Platform]"**
3. Authorize the app on the platform's OAuth page
4. Return to app - connection confirmed

## API Documentation

### Authentication

#### Register
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "John Doe"
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {...}
}
```

### Posts

#### Create Post
```http
POST /api/posts
Authorization: Bearer <token>
Content-Type: multipart/form-data

title: My First Post
platform: facebook
content: Hello World!
scheduled_time: 2024-01-25T14:00:00
timezone: America/New_York
media: <file>
```

#### Get Posts
```http
GET /api/posts?status=scheduled&platform=facebook&page=1&per_page=20
Authorization: Bearer <token>
```

#### Update Post
```http
PUT /api/posts/{id}
Authorization: Bearer <token>
Content-Type: multipart/form-data

title: Updated Title
content: Updated content
```

#### Delete Post
```http
DELETE /api/posts/{id}
Authorization: Bearer <token>
```

### Calendar

#### Get Calendar Posts
```http
GET /api/calendar/posts?start_date=2024-01-01&end_date=2024-01-31&view=month
Authorization: Bearer <token>
```

#### Get Calendar Stats
```http
GET /api/calendar/stats?start_date=2024-01-01&end_date=2024-01-31
Authorization: Bearer <token>
```

### OAuth

#### Connect Platform
```http
GET /api/oauth/{platform}/connect
Authorization: Bearer <token>

Returns: { "authorization_url": "https://..." }
```

#### Get Connected Tokens
```http
GET /api/oauth/tokens
Authorization: Bearer <token>
```

### Admin (Admin Role Required)

#### Get All Users
```http
GET /api/admin/users?page=1&per_page=20
Authorization: Bearer <admin-token>
```

#### Get Analytics
```http
GET /api/admin/analytics?days=30
Authorization: Bearer <admin-token>
```

#### Get Failed Posts
```http
GET /api/admin/failed-posts
Authorization: Bearer <admin-token>
```

## Database Schema

### Users Table
- `id` - Primary key
- `email` - Unique email address
- `password_hash` - Bcrypt hashed password
- `full_name` - User's full name
- `role` - admin, editor, viewer
- `is_active` - Account status
- `created_at`, `updated_at` - Timestamps

### Posts Table
- `id` - Primary key
- `user_id` - Foreign key to users
- `title` - Post title
- `content` - Post content
- `platform` - facebook, instagram, linkedin, twitter
- `status` - draft, scheduled, posted, failed
- `scheduled_time` - When to publish (UTC)
- `timezone` - User's timezone
- `media_path` - Path to uploaded media
- `published_at` - Actual publish time
- `platform_post_id` - ID from social platform
- `error_message` - Error details if failed
- `retry_count` - Number of retry attempts

### OAuth Tokens Table
- `id` - Primary key
- `user_id` - Foreign key to users
- `platform` - Social media platform
- `access_token` - Encrypted access token
- `refresh_token` - Encrypted refresh token
- `expires_at` - Token expiration
- `platform_user_id` - User ID on platform

### Audit Logs Table
- `id` - Primary key
- `user_id` - Foreign key to users
- `post_id` - Foreign key to posts (optional)
- `action` - Action performed
- `status` - success or failed
- `details` - JSON details
- `ip_address` - User's IP
- `created_at` - Timestamp

## Security Features

### Implemented
- ✅ **JWT Authentication** - Secure token-based auth
- ✅ **Password Hashing** - Bcrypt for password storage
- ✅ **OAuth Token Encryption** - All tokens encrypted at rest
- ✅ **Rate Limiting** - Prevent abuse and DoS attacks
- ✅ **CORS Protection** - Configured allowed origins
- ✅ **Input Validation** - All inputs validated
- ✅ **SQL Injection Prevention** - SQLAlchemy ORM
- ✅ **Audit Logging** - Track all critical actions

### Recommendations for Production
- [ ] Enable HTTPS/SSL
- [ ] Use environment-specific secrets
- [ ] Implement CSRF tokens for forms
- [ ] Add 2FA for admin accounts
- [ ] Regular security audits
- [ ] Database backups
- [ ] Monitor rate limits and logs

## Deployment

### Docker Deployment (Recommended)

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/autocontent
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: autocontent
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
  
  redis:
    image: redis:7
  
  celery_worker:
    build: .
    command: celery -A celery_worker.celery worker --loglevel=info
    depends_on:
      - redis
      - db
  
  celery_beat:
    build: .
    command: celery -A celery_worker.celery beat --loglevel=info
    depends_on:
      - redis
      - db
```

### Heroku Deployment

1. Create Heroku app
```bash
heroku create autocontent-calendar
```

2. Add PostgreSQL and Redis
```bash
heroku addons:create heroku-postgresql:hobby-dev
heroku addons:create heroku-redis:hobby-dev
```

3. Set environment variables
```bash
heroku config:set SECRET_KEY=your-secret-key
heroku config:set JWT_SECRET_KEY=your-jwt-key
# ... set all other environment variables
```

4. Deploy
```bash
git push heroku main
```

5. Initialize database
```bash
heroku run flask init-db
heroku run flask create-admin
```

### VPS Deployment

1. Install dependencies on server
2. Set up Nginx as reverse proxy
3. Use systemd for process management
4. Configure SSL with Let's Encrypt
5. Set up automated backups

## Testing

Run tests (to be implemented):
```bash
pytest tests/
```

## Troubleshooting

### Common Issues

**Database connection error**
- Ensure PostgreSQL is running
- Check DATABASE_URL in .env
- Verify database exists

**Celery not running**
- Check Redis is running
- Verify REDIS_URL in .env
- Check celery logs for errors

**OAuth callback fails**
- Verify redirect URIs match exactly
- Check client ID and secret
- Ensure app is in development/live mode

**Posts not publishing**
- Check Celery worker logs
- Verify OAuth token is valid
- Check platform API status

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: [Link to repo]
- Email: support@example.com
- Documentation: [Link to docs]

## Roadmap

### Planned Features
- [ ] Real-time notifications (WebSockets)
- [ ] Post analytics and insights
- [ ] Bulk post upload (CSV)
- [ ] Content templates
- [ ] Team collaboration features
- [ ] More platforms (TikTok, Pinterest, YouTube)
- [ ] Mobile app
- [ ] AI-powered content suggestions

## Acknowledgments

- Flask framework and community
- SQLAlchemy ORM
- Celery distributed task queue
- All contributors and testers

---

**Built with ❤️ for content creators and social media managers**
