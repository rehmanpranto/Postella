# Deployment Guide - AutoContent Calendar

## Table of Contents
1. [Local Development](#local-development)
2. [Production Deployment](#production-deployment)
3. [Docker Deployment](#docker-deployment)
4. [Cloud Deployment](#cloud-deployment)
5. [Security Checklist](#security-checklist)
6. [Monitoring](#monitoring)
7. [Backup Strategy](#backup-strategy)

---

## Local Development

### Prerequisites
- Python 3.9+
- PostgreSQL 12+
- Redis 6+
- Git

### Step-by-Step Setup

1. **Clone and Setup**
```bash
git clone <repository-url>
cd AutoContentCalendar
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. **Database Setup**
```bash
# Install PostgreSQL
# macOS
brew install postgresql@14
brew services start postgresql@14

# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql

# Create database
createdb autocontent_calendar
```

3. **Redis Setup**
```bash
# macOS
brew install redis
brew services start redis

# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis
```

4. **Environment Configuration**
```bash
cp .env.example .env
# Edit .env with your settings
nano .env
```

5. **Initialize Application**
```bash
# Initialize database
flask init-db

# Create admin user
flask create-admin
```

6. **Run Application**

Terminal 1 - Flask App:
```bash
python app.py
```

Terminal 2 - Celery Worker:
```bash
celery -A celery_worker.celery worker --loglevel=info
```

Terminal 3 - Celery Beat:
```bash
celery -A celery_worker.celery beat --loglevel=info
```

Access at: http://localhost:5000

---

## Production Deployment

### Ubuntu/Debian Server Setup

#### 1. Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3-pip python3-venv nginx postgresql redis-server supervisor

# Create application user
sudo useradd -m -s /bin/bash autocontent
sudo su - autocontent
```

#### 2. Application Setup

```bash
# Clone repository
git clone <repository-url> /home/autocontent/app
cd /home/autocontent/app

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

#### 3. PostgreSQL Configuration

```bash
# Switch to postgres user
sudo -u postgres psql

# In PostgreSQL prompt:
CREATE DATABASE autocontent_calendar;
CREATE USER autocontent WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE autocontent_calendar TO autocontent;
\q

# Configure PostgreSQL for remote connections if needed
sudo nano /etc/postgresql/14/main/postgresql.conf
# Uncomment and set: listen_addresses = 'localhost'

sudo nano /etc/postgresql/14/main/pg_hba.conf
# Add: local   autocontent_calendar   autocontent   md5

sudo systemctl restart postgresql
```

#### 4. Environment Configuration

```bash
# Create production .env
nano /home/autocontent/app/.env
```

```bash
# Production .env
FLASK_ENV=production
SECRET_KEY=<generate-strong-secret-key>
DEBUG=False

DATABASE_URL=postgresql://autocontent:secure_password_here@localhost/autocontent_calendar

REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

JWT_SECRET_KEY=<generate-strong-jwt-key>
ENCRYPTION_KEY=<generate-32-byte-key>

# Add your social media credentials
FACEBOOK_CLIENT_ID=...
FACEBOOK_CLIENT_SECRET=...
# ... etc
```

#### 5. Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/autocontent
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /home/autocontent/app/static;
        expires 30d;
    }

    location /uploads {
        alias /home/autocontent/app/uploads;
        expires 7d;
    }

    client_max_body_size 20M;
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/autocontent /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 6. SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
sudo systemctl reload nginx
```

#### 7. Supervisor Configuration

```bash
sudo nano /etc/supervisor/conf.d/autocontent.conf
```

```ini
[program:autocontent_web]
command=/home/autocontent/app/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
directory=/home/autocontent/app
user=autocontent
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/autocontent/web.err.log
stdout_logfile=/var/log/autocontent/web.out.log

[program:autocontent_celery_worker]
command=/home/autocontent/app/venv/bin/celery -A celery_worker.celery worker --loglevel=info
directory=/home/autocontent/app
user=autocontent
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/autocontent/celery_worker.err.log
stdout_logfile=/var/log/autocontent/celery_worker.out.log

[program:autocontent_celery_beat]
command=/home/autocontent/app/venv/bin/celery -A celery_worker.celery beat --loglevel=info
directory=/home/autocontent/app
user=autocontent
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/autocontent/celery_beat.err.log
stdout_logfile=/var/log/autocontent/celery_beat.out.log

[group:autocontent]
programs=autocontent_web,autocontent_celery_worker,autocontent_celery_beat
```

```bash
# Create log directory
sudo mkdir -p /var/log/autocontent
sudo chown autocontent:autocontent /var/log/autocontent

# Start services
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start autocontent:*
```

---

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application
COPY . .

# Create uploads directory
RUN mkdir -p uploads

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://autocontent:password@db:5432/autocontent_calendar
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - SECRET_KEY=${SECRET_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
    depends_on:
      - db
      - redis
    volumes:
      - ./uploads:/app/uploads
    restart: unless-stopped

  db:
    image: postgres:14
    environment:
      POSTGRES_DB: autocontent_calendar
      POSTGRES_USER: autocontent
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

  celery_worker:
    build: .
    command: celery -A celery_worker.celery worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://autocontent:password@db:5432/autocontent_calendar
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    restart: unless-stopped

  celery_beat:
    build: .
    command: celery -A celery_worker.celery beat --loglevel=info
    environment:
      - DATABASE_URL=postgresql://autocontent:password@db:5432/autocontent_calendar
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    restart: unless-stopped

volumes:
  postgres_data:
```

### Deploy with Docker

```bash
# Build and start
docker-compose up -d

# Initialize database
docker-compose exec web flask init-db

# Create admin user
docker-compose exec web flask create-admin

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## Cloud Deployment

### Heroku

```bash
# Install Heroku CLI
brew install heroku/brew/heroku  # macOS
# or visit heroku.com

# Login
heroku login

# Create app
heroku create autocontent-calendar

# Add addons
heroku addons:create heroku-postgresql:hobby-dev
heroku addons:create heroku-redis:hobby-dev

# Set config vars
heroku config:set SECRET_KEY=your-secret-key
heroku config:set JWT_SECRET_KEY=your-jwt-key
heroku config:set ENCRYPTION_KEY=your-encryption-key
# Set all other environment variables

# Deploy
git push heroku main

# Initialize database
heroku run flask init-db
heroku run flask create-admin

# Scale workers
heroku ps:scale web=1 worker=1 beat=1
```

### AWS (EC2 + RDS + ElastiCache)

1. **Launch EC2 instance** (Ubuntu 22.04)
2. **Create RDS PostgreSQL instance**
3. **Create ElastiCache Redis cluster**
4. Follow Ubuntu server setup above
5. Configure security groups
6. Set up Application Load Balancer
7. Configure Auto Scaling

### DigitalOcean App Platform

1. Connect GitHub repository
2. Configure environment variables
3. Add PostgreSQL and Redis databases
4. Deploy

---

## Security Checklist

### Before Production

- [ ] Change all default passwords
- [ ] Use strong SECRET_KEY and JWT_SECRET_KEY
- [ ] Enable HTTPS/SSL
- [ ] Configure firewall (UFW or cloud security groups)
- [ ] Set up database backups
- [ ] Enable database encryption at rest
- [ ] Restrict database access to application only
- [ ] Use environment variables for all secrets
- [ ] Set DEBUG=False
- [ ] Configure CORS properly
- [ ] Set up rate limiting
- [ ] Enable audit logging
- [ ] Regular security updates
- [ ] Use strong encryption keys
- [ ] Implement 2FA for admin accounts
- [ ] Set up monitoring and alerts
- [ ] Configure log rotation
- [ ] Backup OAuth tokens securely

### Firewall Configuration

```bash
# UFW example
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 443/tcp # HTTPS
sudo ufw enable
```

---

## Monitoring

### Application Monitoring

```bash
# Install monitoring tools
pip install sentry-sdk flask-monitoring-dashboard

# Add to app/__init__.py
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FlaskIntegration()],
    traces_sample_rate=1.0
)
```

### Log Monitoring

```bash
# Logrotate configuration
sudo nano /etc/logrotate.d/autocontent
```

```
/var/log/autocontent/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 autocontent autocontent
    sharedscripts
    postrotate
        supervisorctl restart autocontent:*
    endscript
}
```

### System Monitoring

- Use Prometheus + Grafana
- Monitor: CPU, Memory, Disk, Network
- Set up alerts for high resource usage
- Monitor Celery queue length
- Track API response times

---

## Backup Strategy

### Database Backups

```bash
# Daily backup script
#!/bin/bash
BACKUP_DIR="/backups/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)
FILENAME="autocontent_${DATE}.sql"

mkdir -p $BACKUP_DIR
pg_dump -U autocontent autocontent_calendar > $BACKUP_DIR/$FILENAME
gzip $BACKUP_DIR/$FILENAME

# Keep only last 30 days
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
```

```bash
# Add to crontab
0 2 * * * /path/to/backup-script.sh
```

### Media Backups

```bash
# Backup uploads directory
rsync -avz /home/autocontent/app/uploads/ /backups/uploads/
```

### Restore Procedure

```bash
# Database restore
gunzip < backup.sql.gz | psql -U autocontent autocontent_calendar

# Media restore
rsync -avz /backups/uploads/ /home/autocontent/app/uploads/
```

---

## Performance Optimization

### Database

- Add indexes on frequently queried columns
- Use connection pooling
- Regular VACUUM and ANALYZE
- Monitor slow queries

### Caching

- Implement Redis caching for API responses
- Cache user sessions
- Cache platform configurations

### Application

- Use Gunicorn with multiple workers
- Enable gzip compression in Nginx
- Optimize database queries
- Use CDN for static files

---

## Troubleshooting

### Common Issues

**Service won't start:**
```bash
sudo supervisorctl status
sudo tail -f /var/log/autocontent/web.err.log
```

**Database connection error:**
```bash
sudo systemctl status postgresql
psql -U autocontent -d autocontent_calendar
```

**Celery not processing tasks:**
```bash
sudo supervisorctl restart autocontent:autocontent_celery_worker
celery -A celery_worker.celery inspect active
```

**High memory usage:**
```bash
htop
# Reduce Gunicorn workers or Celery concurrency
```

---

## Maintenance

### Regular Tasks

- Weekly: Review logs for errors
- Weekly: Check disk space
- Monthly: Update dependencies
- Monthly: Review and rotate logs
- Quarterly: Security audit
- Quarterly: Database optimization

### Updates

```bash
# Pull latest code
cd /home/autocontent/app
git pull

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Run migrations if any
flask db upgrade

# Restart services
sudo supervisorctl restart autocontent:*
```

---

## Support

For deployment issues:
- Check logs: `/var/log/autocontent/`
- Review Nginx logs: `/var/log/nginx/`
- Check system resources: `htop`, `df -h`
- Contact: support@example.com
