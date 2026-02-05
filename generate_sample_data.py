"""
Sample data generation script for AutoContent Calendar
Run this to populate the database with test data
"""

from app import create_app
from app.models import User, Post, PostStatus, PlatformType, PlatformConfig, UserRole
from app.extensions import db
from datetime import datetime, timedelta
import random

app = create_app()


def generate_sample_data():
    """Generate sample data for testing"""
    
    with app.app_context():
        print("🔧 Generating sample data...")
        
        # Clear existing data (be careful in production!)
        print("⚠️  Clearing existing posts...")
        Post.query.delete()
        
        # Create sample users if they don't exist
        print("👥 Creating sample users...")
        
        # Admin user
        admin = User.query.filter_by(email='admin@example.com').first()
        if not admin:
            admin = User(
                email='admin@example.com',
                full_name='Admin User',
                role=UserRole.ADMIN,
                is_active=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
        
        # Editor user
        editor = User.query.filter_by(email='editor@example.com').first()
        if not editor:
            editor = User(
                email='editor@example.com',
                full_name='John Editor',
                role=UserRole.EDITOR,
                is_active=True
            )
            editor.set_password('editor123')
            db.session.add(editor)
        
        # Another editor
        editor2 = User.query.filter_by(email='sarah@example.com').first()
        if not editor2:
            editor2 = User(
                email='sarah@example.com',
                full_name='Sarah Johnson',
                role=UserRole.EDITOR,
                is_active=True
            )
            editor2.set_password('sarah123')
            db.session.add(editor2)
        
        db.session.commit()
        
        users = [editor, editor2]
        
        # Sample post titles and content
        post_templates = [
            {
                'title': 'New Product Launch Announcement',
                'content': 'Excited to announce our latest product! Check out the amazing features and benefits. #ProductLaunch #Innovation'
            },
            {
                'title': 'Weekly Industry Tips',
                'content': 'Here are 5 tips to boost your productivity this week: 1) Plan ahead 2) Stay focused 3) Take breaks 4) Learn daily 5) Network actively'
            },
            {
                'title': 'Customer Success Story',
                'content': 'Amazing results from our client! They achieved 300% growth using our platform. Read their full story on our blog.'
            },
            {
                'title': 'Behind the Scenes',
                'content': 'Take a peek behind the curtain! Here\'s what a typical day looks like at our office. #CompanyCulture #TeamWork'
            },
            {
                'title': 'Industry News Update',
                'content': 'Breaking news in our industry! Here\'s what you need to know about the latest trends and developments.'
            },
            {
                'title': 'Team Spotlight',
                'content': 'Meet our amazing team member of the month! Learn about their journey and contributions to our success.'
            },
            {
                'title': 'Event Announcement',
                'content': 'Join us for our upcoming webinar! Register now to learn about best practices and industry insights. Limited spots available!'
            },
            {
                'title': 'Special Offer',
                'content': 'Limited time offer! Get 20% off on all our premium plans. Use code SAVE20 at checkout. Offer ends soon!'
            },
            {
                'title': 'Tutorial Tuesday',
                'content': 'Step-by-step guide to mastering our platform. Follow along and become a pro in just 10 minutes! #Tutorial'
            },
            {
                'title': 'Motivational Monday',
                'content': 'Start your week strong! Remember: Success is not final, failure is not fatal. Keep pushing forward! 💪'
            }
        ]
        
        platforms = [PlatformType.FACEBOOK, PlatformType.INSTAGRAM, PlatformType.LINKEDIN, PlatformType.TWITTER]
        statuses = [PostStatus.DRAFT, PostStatus.SCHEDULED, PostStatus.POSTED, PostStatus.FAILED]
        
        print("📝 Creating sample posts...")
        
        # Generate posts for the past week and next 2 weeks
        start_date = datetime.utcnow() - timedelta(days=7)
        
        posts_created = 0
        
        for day_offset in range(-7, 14):  # 7 days ago to 14 days ahead
            date = start_date + timedelta(days=day_offset)
            
            # Create 1-3 posts per day
            num_posts = random.randint(1, 3)
            
            for _ in range(num_posts):
                template = random.choice(post_templates)
                user = random.choice(users)
                platform = random.choice(platforms)
                
                # Set time
                hour = random.randint(9, 17)  # Business hours
                minute = random.choice([0, 15, 30, 45])
                scheduled_time = date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                # Determine status based on time
                now = datetime.utcnow()
                if scheduled_time < now - timedelta(days=1):
                    # Past posts - mostly posted, some failed
                    status = random.choices(
                        [PostStatus.POSTED, PostStatus.FAILED],
                        weights=[0.95, 0.05]
                    )[0]
                elif scheduled_time < now:
                    # Recent posts - should be posted
                    status = PostStatus.POSTED
                elif scheduled_time < now + timedelta(hours=1):
                    # Very soon - scheduled
                    status = PostStatus.SCHEDULED
                else:
                    # Future posts - draft or scheduled
                    status = random.choices(
                        [PostStatus.DRAFT, PostStatus.SCHEDULED],
                        weights=[0.3, 0.7]
                    )[0]
                
                # Create post
                post = Post(
                    user_id=user.id,
                    title=template['title'],
                    content=template['content'],
                    platform=platform,
                    status=status,
                    scheduled_time=scheduled_time,
                    timezone='UTC'
                )
                
                # Set published_at for posted posts
                if status == PostStatus.POSTED:
                    post.published_at = scheduled_time
                    post.platform_post_id = f"{platform.value}_{random.randint(100000, 999999)}"
                
                # Add error message for failed posts
                if status == PostStatus.FAILED:
                    error_messages = [
                        "OAuth token expired",
                        "Platform API rate limit exceeded",
                        "Invalid media format",
                        "Network timeout"
                    ]
                    post.error_message = random.choice(error_messages)
                    post.retry_count = random.randint(1, 3)
                
                db.session.add(post)
                posts_created += 1
        
        db.session.commit()
        
        print(f"✅ Created {posts_created} sample posts")
        
        # Generate some statistics
        print("\n📊 Sample Data Statistics:")
        print(f"   Total Users: {User.query.count()}")
        print(f"   Total Posts: {Post.query.count()}")
        print(f"   - Draft: {Post.query.filter_by(status=PostStatus.DRAFT).count()}")
        print(f"   - Scheduled: {Post.query.filter_by(status=PostStatus.SCHEDULED).count()}")
        print(f"   - Posted: {Post.query.filter_by(status=PostStatus.POSTED).count()}")
        print(f"   - Failed: {Post.query.filter_by(status=PostStatus.FAILED).count()}")
        
        print("\n🎉 Sample data generation complete!")
        print("\n📝 Test Account Credentials:")
        print("   Admin: admin@example.com / admin123")
        print("   Editor: editor@example.com / editor123")
        print("   Editor: sarah@example.com / sarah123")


if __name__ == '__main__':
    generate_sample_data()
