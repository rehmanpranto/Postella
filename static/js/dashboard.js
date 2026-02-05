// Dashboard Page Scripts

if (!requireAuth()) {
    throw new Error('Authentication required');
}

// Load Dashboard Data
async function loadDashboard() {
    try {
        // Load posts
        const postsData = await apiCall('/posts?per_page=100');
        const posts = postsData.posts;
        
        // Calculate stats
        const stats = {
            total: posts.length,
            scheduled: posts.filter(p => p.status === 'scheduled').length,
            posted: posts.filter(p => p.status === 'posted').length,
            failed: posts.filter(p => p.status === 'failed').length
        };
        
        // Update stats cards
        document.getElementById('totalPosts').textContent = stats.total;
        document.getElementById('scheduledPosts').textContent = stats.scheduled;
        document.getElementById('postedPosts').textContent = stats.posted;
        document.getElementById('failedPosts').textContent = stats.failed;
        
        // Show recent posts
        displayRecentPosts(posts.slice(0, 5));
        
        // Show upcoming posts
        const now = new Date();
        const upcoming = posts
            .filter(p => p.scheduled_time && new Date(p.scheduled_time) > now)
            .sort((a, b) => new Date(a.scheduled_time) - new Date(b.scheduled_time))
            .slice(0, 5);
        
        displayUpcomingPosts(upcoming);
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

function displayRecentPosts(posts) {
    const container = document.getElementById('recentPosts');
    
    if (posts.length === 0) {
        container.innerHTML = '<p class="loading">No posts yet. <a href="/create-post.html">Create your first post!</a></p>';
        return;
    }
    
    container.innerHTML = posts.map(post => `
        <div class="post-item">
            <div class="post-info">
                <div class="post-title">${post.title}</div>
                <div class="post-meta">
                    ${getPlatformBadge(post.platform)}
                    ${getStatusBadge(post.status)}
                    <span>${formatDateShort(post.created_at)}</span>
                </div>
                <div class="post-content-preview">${truncate(post.content, 100)}</div>
            </div>
            <div class="post-actions">
                <button class="btn btn-secondary" onclick="editPost(${post.id})">Edit</button>
            </div>
        </div>
    `).join('');
}

function displayUpcomingPosts(posts) {
    const container = document.getElementById('upcomingPosts');
    
    if (posts.length === 0) {
        container.innerHTML = '<p class="loading">No upcoming posts scheduled.</p>';
        return;
    }
    
    container.innerHTML = posts.map(post => `
        <div class="post-item">
            <div class="post-info">
                <div class="post-title">${post.title}</div>
                <div class="post-meta">
                    ${getPlatformBadge(post.platform)}
                    ${getStatusBadge(post.status)}
                    <span>📅 ${formatDate(post.scheduled_time)}</span>
                </div>
            </div>
        </div>
    `).join('');
}

function truncate(text, length) {
    if (text.length <= length) return text;
    return text.substring(0, length) + '...';
}

function editPost(postId) {
    window.location.href = `/create-post.html?id=${postId}`;
}

// Load on page load
document.addEventListener('DOMContentLoaded', loadDashboard);
