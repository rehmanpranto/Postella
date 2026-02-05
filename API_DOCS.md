# API Documentation

## Base URL
```
http://localhost:5000/api
```

## Authentication

All authenticated endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

---

## Endpoints

### Health Check

#### GET /health
Check API health status

**Response:**
```json
{
  "status": "healthy",
  "database": "healthy"
}
```

---

## Authentication Endpoints

### POST /auth/register
Register a new user

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Doe"
}
```

**Response:** `201 Created`
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "editor",
    "is_active": true,
    "created_at": "2024-01-21T10:00:00",
    "updated_at": "2024-01-21T10:00:00"
  }
}
```

**Rate Limit:** 5 per hour

---

### POST /auth/login
Login and receive JWT token

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "editor"
  }
}
```

**Rate Limit:** 10 per minute

---

### GET /auth/me
Get current user information

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "editor",
  "is_active": true,
  "created_at": "2024-01-21T10:00:00",
  "updated_at": "2024-01-21T10:00:00"
}
```

---

### POST /auth/change-password
Change user password

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "old_password": "currentpassword",
  "new_password": "newsecurepassword"
}
```

**Response:** `200 OK`
```json
{
  "message": "Password changed successfully"
}
```

**Rate Limit:** 3 per hour

---

## Posts Endpoints

### GET /posts
Get all posts for current user

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `status` (optional): draft, scheduled, posted, failed
- `platform` (optional): facebook, instagram, linkedin, twitter
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 20)

**Response:** `200 OK`
```json
{
  "posts": [
    {
      "id": 1,
      "user_id": 1,
      "title": "My First Post",
      "content": "Hello World!",
      "platform": "facebook",
      "status": "scheduled",
      "scheduled_time": "2024-01-25T14:00:00",
      "timezone": "America/New_York",
      "media_path": "posts/image_20240121.jpg",
      "media_type": "image",
      "published_at": null,
      "platform_post_id": null,
      "error_message": null,
      "retry_count": 0,
      "max_retries": 3,
      "created_at": "2024-01-21T10:00:00",
      "updated_at": "2024-01-21T10:00:00"
    }
  ],
  "total": 50,
  "page": 1,
  "per_page": 20,
  "pages": 3
}
```

---

### GET /posts/{id}
Get a specific post

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "id": 1,
  "title": "My First Post",
  "content": "Hello World!",
  "platform": "facebook",
  "status": "scheduled",
  "scheduled_time": "2024-01-25T14:00:00",
  ...
}
```

---

### POST /posts
Create a new post

**Headers:** 
- `Authorization: Bearer <token>`
- `Content-Type: multipart/form-data`

**Form Data:**
- `title` (required): Post title
- `platform` (required): facebook, instagram, linkedin, twitter
- `content` (required): Post content
- `scheduled_time` (optional): ISO datetime string
- `timezone` (optional): Timezone (default: UTC)
- `media` (optional): Image or video file

**Response:** `201 Created`
```json
{
  "message": "Post created successfully",
  "post": { ... }
}
```

**Rate Limit:** 50 per hour

---

### PUT /posts/{id}
Update a post

**Headers:** 
- `Authorization: Bearer <token>`
- `Content-Type: multipart/form-data`

**Form Data:** Same as POST /posts

**Response:** `200 OK`
```json
{
  "message": "Post updated successfully",
  "post": { ... }
}
```

---

### DELETE /posts/{id}
Delete a post

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "message": "Post deleted successfully"
}
```

---

### POST /posts/{id}/duplicate
Duplicate a post

**Headers:** `Authorization: Bearer <token>`

**Response:** `201 Created`
```json
{
  "message": "Post duplicated successfully",
  "post": { ... }
}
```

---

### GET /posts/platforms
Get platform configurations

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "platforms": [
    {
      "id": 1,
      "platform": "facebook",
      "max_text_length": 63206,
      "supports_images": true,
      "supports_videos": true,
      "max_image_size_mb": 4,
      "max_video_size_mb": 1024,
      "allowed_image_formats": "jpg,jpeg,png,gif",
      "allowed_video_formats": "mp4,mov",
      "rate_limit_per_hour": 200,
      "is_active": true
    }
  ]
}
```

---

## Calendar Endpoints

### GET /calendar/posts
Get posts for calendar view

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `start_date` (optional): ISO datetime
- `end_date` (optional): ISO datetime
- `view` (optional): day, week, month (default: month)

**Response:** `200 OK`
```json
{
  "start_date": "2024-01-01T00:00:00",
  "end_date": "2024-02-01T00:00:00",
  "view": "month",
  "posts_by_date": {
    "2024-01-15": [
      { "id": 1, "title": "Post 1", ... }
    ],
    "2024-01-20": [
      { "id": 2, "title": "Post 2", ... }
    ]
  },
  "total_posts": 15
}
```

---

### GET /calendar/stats
Get calendar statistics

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `start_date` (optional): ISO datetime
- `end_date` (optional): ISO datetime

**Response:** `200 OK`
```json
{
  "total": 50,
  "by_status": {
    "draft": 10,
    "scheduled": 25,
    "posted": 13,
    "failed": 2
  },
  "by_platform": {
    "facebook": 20,
    "twitter": 15,
    "linkedin": 10,
    "instagram": 5
  }
}
```

---

### POST /calendar/move
Move post to different date/time

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "post_id": 1,
  "new_scheduled_time": "2024-01-25T15:00:00"
}
```

**Response:** `200 OK`
```json
{
  "message": "Post moved successfully",
  "post": { ... }
}
```

---

## OAuth Endpoints

### GET /oauth/{platform}/connect
Initiate OAuth connection

**Headers:** `Authorization: Bearer <token>`

**Parameters:**
- `platform`: facebook, instagram, linkedin, twitter

**Response:** `200 OK`
```json
{
  "authorization_url": "https://platform.com/oauth/authorize?client_id=..."
}
```

---

### GET /oauth/{platform}/callback
OAuth callback (handled automatically)

**Query Parameters:**
- `code`: Authorization code
- `state`: State parameter

**Response:** Redirect to frontend with success/error

---

### GET /oauth/tokens
Get connected OAuth tokens

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "tokens": [
    {
      "id": 1,
      "user_id": 1,
      "platform": "facebook",
      "platform_user_id": "123456789",
      "platform_username": "johndoe",
      "is_active": true,
      "expires_at": "2024-06-01T00:00:00",
      "created_at": "2024-01-21T10:00:00",
      "updated_at": "2024-01-21T10:00:00"
    }
  ]
}
```

---

### DELETE /oauth/tokens/{id}
Disconnect platform

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "message": "Platform disconnected successfully"
}
```

---

## Admin Endpoints

All admin endpoints require admin role.

### GET /admin/users
Get all users

**Headers:** `Authorization: Bearer <admin-token>`

**Query Parameters:**
- `page` (optional): Page number
- `per_page` (optional): Items per page

**Response:** `200 OK`
```json
{
  "users": [ ... ],
  "total": 100,
  "page": 1,
  "per_page": 20,
  "pages": 5
}
```

---

### PUT /admin/users/{id}
Update user

**Headers:** `Authorization: Bearer <admin-token>`

**Request Body:**
```json
{
  "role": "admin",
  "is_active": true,
  "full_name": "Updated Name"
}
```

**Response:** `200 OK`

---

### GET /admin/posts
Get all posts from all users

**Headers:** `Authorization: Bearer <admin-token>`

**Query Parameters:**
- `status` (optional): Filter by status
- `page`, `per_page`: Pagination

**Response:** `200 OK`

---

### GET /admin/analytics
Get platform analytics

**Headers:** `Authorization: Bearer <admin-token>`

**Query Parameters:**
- `days` (optional): Number of days (default: 30)

**Response:** `200 OK`
```json
{
  "users": {
    "total": 150,
    "active": 120
  },
  "posts": {
    "total": 5000,
    "recent": 500,
    "upcoming": 200,
    "failed": 25,
    "by_status": { ... },
    "by_platform": { ... },
    "success_rate": 95.5
  },
  "period_days": 30
}
```

---

### GET /admin/failed-posts
Get failed post diagnostics

**Headers:** `Authorization: Bearer <admin-token>`

**Response:** `200 OK`
```json
{
  "failed_posts": [
    {
      "id": 1,
      "title": "Failed Post",
      "error_message": "OAuth token expired",
      "user_email": "user@example.com",
      ...
    }
  ],
  "total": 10
}
```

---

### GET /admin/audit-logs
Get audit logs

**Headers:** `Authorization: Bearer <admin-token>`

**Query Parameters:**
- `action` (optional): Filter by action
- `user_id` (optional): Filter by user
- `page`, `per_page`: Pagination

**Response:** `200 OK`

---

### POST /admin/posts/{id}/retry
Retry failed post

**Headers:** `Authorization: Bearer <admin-token>`

**Response:** `200 OK`
```json
{
  "message": "Post queued for retry",
  "post": { ... }
}
```

---

## Error Responses

All endpoints may return these error responses:

### 400 Bad Request
```json
{
  "error": "Bad request",
  "message": "Missing required fields"
}
```

### 401 Unauthorized
```json
{
  "error": "Unauthorized",
  "message": "Invalid credentials"
}
```

### 403 Forbidden
```json
{
  "error": "Forbidden",
  "message": "Admin access required"
}
```

### 404 Not Found
```json
{
  "error": "Not found",
  "message": "Post not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "message": "An unexpected error occurred"
}
```

---

## Rate Limits

Default rate limits (configurable in .env):
- Default: 200 per day, 50 per hour
- Registration: 5 per hour
- Login: 10 per minute
- Password change: 3 per hour
- Create post: 50 per hour

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 50
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640000000
```
