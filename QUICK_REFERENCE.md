# Quick Reference Guide

## 🚀 Getting Started (5 minutes)

1. **Quick Setup:**
```bash
cd AutoContentCalendar
./quick_start.sh
```

2. **Start Application:**
```bash
./run_all.sh
```

3. **Access:** http://localhost:5000/login.html

4. **Login:**
- Email: admin@example.com
- Password: admin123

## 📝 Common Tasks

### Create a New Post
1. Go to Dashboard → Click "Create Post"
2. Fill in title, platform, content
3. Upload media (optional)
4. Set scheduled time
5. Click "Create Post"

### View Calendar
- Navigate to "Calendar" tab
- Switch between Day/Week/Month views
- Click on posts to view details

### Connect Social Media
1. Go to Settings
2. Click "Connect [Platform]"
3. Authorize in popup window
4. Return to app - connected!

### View Failed Posts (Admin)
1. Navigate to Posts
2. Filter by Status: "Failed"
3. Check error messages
4. Edit and reschedule

## 🔧 Configuration

### Environment Variables (.env)
```bash
# Required
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@localhost/dbname
REDIS_URL=redis://localhost:6379/0

# OAuth (get from platform developer portals)
FACEBOOK_CLIENT_ID=your-facebook-id
FACEBOOK_CLIENT_SECRET=your-facebook-secret
# ... repeat for other platforms
```

### Platform Character Limits
- **Facebook:** 63,206 characters
- **Instagram:** 2,200 characters
- **LinkedIn:** 3,000 characters
- **Twitter:** 280 characters

## 🐛 Troubleshooting

### Application won't start
```bash
# Check logs
cat logs/flask.log
cat logs/celery_worker.log

# Verify services running
psql -U postgres -l  # Check database
redis-cli ping        # Check Redis
```

### Posts not publishing
```bash
# Check Celery worker
tail -f logs/celery_worker.log

# Verify OAuth token
# Go to Settings → Check connected platforms

# Check post status
# Posts → Filter by "Failed" → Check error messages
```

### Database errors
```bash
# Reinitialize database
flask init-db

# Or manually
psql autocontent_calendar
\dt  # List tables
```

## 📊 Useful Commands

### Flask CLI
```bash
flask init-db              # Initialize database
flask create-admin         # Create admin user
```

### Database Management
```bash
# Backup
pg_dump autocontent_calendar > backup.sql

# Restore
psql autocontent_calendar < backup.sql

# Access database
psql autocontent_calendar
```

### Celery Commands
```bash
# Check active tasks
celery -A celery_worker.celery inspect active

# Check scheduled tasks
celery -A celery_worker.celery inspect scheduled

# Purge queue
celery -A celery_worker.celery purge
```

### Service Management
```bash
# Start all
./run_all.sh

# Stop all
./stop_all.sh

# View logs
tail -f logs/flask.log
tail -f logs/celery_worker.log
tail -f logs/celery_beat.log
```

## 🔐 Security Checklist

Before going to production:

- [ ] Change all default passwords
- [ ] Generate strong SECRET_KEY and JWT_SECRET_KEY
- [ ] Set DEBUG=False in production
- [ ] Enable HTTPS/SSL
- [ ] Configure firewall
- [ ] Set up database backups
- [ ] Review rate limits
- [ ] Update OAuth redirect URIs
- [ ] Enable audit logging
- [ ] Set up monitoring

## 📱 API Quick Reference

### Authentication
```bash
# Register
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pass123","full_name":"John"}'

# Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"pass123"}'
```

### Create Post
```bash
curl -X POST http://localhost:5000/api/posts \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "title=My Post" \
  -F "platform=facebook" \
  -F "content=Hello World" \
  -F "scheduled_time=2024-01-25T14:00:00" \
  -F "timezone=UTC"
```

### Get Posts
```bash
curl -X GET "http://localhost:5000/api/posts?status=scheduled" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🎯 Tips & Best Practices

### Content Scheduling
- Schedule posts during peak engagement times
- Spread posts throughout the day
- Test content on one platform first
- Use platform-specific character limits
- Always preview before scheduling

### Media Handling
- Use high-quality images (but compress them)
- Verify video formats per platform
- Keep file sizes reasonable
- Test media uploads before scheduling

### OAuth Management
- Reconnect tokens before expiry
- Test posts after connecting
- Keep backup of OAuth credentials
- Monitor token expiration dates

### Performance
- Schedule bulk posts during off-peak hours
- Monitor Celery queue length
- Keep Redis memory in check
- Regular database maintenance

## 📞 Support

- **Documentation:** README.md, API_DOCS.md, DEPLOYMENT.md
- **Logs:** Check `logs/` directory
- **Issues:** Review error messages in logs
- **Community:** [GitHub Issues](#)

## 🔄 Update Process

```bash
# Pull latest code
git pull

# Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# Run migrations (if any)
flask db upgrade

# Restart services
./stop_all.sh
./run_all.sh
```

## 💡 Pro Tips

1. **Use sample data for testing:**
   ```bash
   python generate_sample_data.py
   ```

2. **Monitor background tasks:**
   - Check Celery logs regularly
   - Set up alerts for failed posts

3. **Backup regularly:**
   - Daily database backups
   - Weekly full backups
   - Test restore process

4. **Security:**
   - Rotate secrets periodically
   - Review audit logs
   - Keep dependencies updated

5. **Performance:**
   - Index frequently queried columns
   - Use Redis caching
   - Monitor server resources

---

**Quick Links:**
- Dashboard: http://localhost:5000/index.html
- Calendar: http://localhost:5000/calendar.html
- Posts: http://localhost:5000/posts.html
- Settings: http://localhost:5000/settings.html

**Test Accounts:**
- Admin: admin@example.com / admin123
- Editor: editor@example.com / editor123
- Editor: sarah@example.com / sarah123
