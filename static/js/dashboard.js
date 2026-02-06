// ── Dashboard Page Scripts ──
if (!requireAuth()) throw new Error('Auth required');

async function loadDashboard() {
    try {
        const postsData = await apiCall('/posts?per_page=100');
        const posts = postsData.posts;

        const stats = {
            total: postsData.total || posts.length,
            scheduled: posts.filter(p => p.status === 'scheduled').length,
            posted: posts.filter(p => p.status === 'posted').length,
            failed: posts.filter(p => p.status === 'failed').length
        };

        document.getElementById('totalPosts').textContent = stats.total;
        document.getElementById('scheduledPosts').textContent = stats.scheduled;
        document.getElementById('postedPosts').textContent = stats.posted;
        document.getElementById('failedPosts').textContent = stats.failed;

        displayRecentPosts(posts.slice(0, 5));

        const now = new Date();
        const upcoming = posts
            .filter(p => p.scheduled_time && new Date(p.scheduled_time) > now && p.status === 'scheduled')
            .sort((a, b) => new Date(a.scheduled_time) - new Date(b.scheduled_time))
            .slice(0, 5);
        displayUpcomingPosts(upcoming);
    } catch (error) {
        console.error('Dashboard error:', error);
    }
}

function displayRecentPosts(posts) {
    const container = document.getElementById('recentPosts');
    if (posts.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📝</div>
                <h3>No posts yet</h3>
                <p>Create your first post to get started.</p>
                <a href="/create-post.html" class="btn btn-primary">+ Create Post</a>
            </div>`;
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
            </div>
            <div class="post-actions">
                <button class="btn btn-secondary btn-sm" onclick="location.href='/create-post.html?id=${post.id}'">Edit</button>
            </div>
        </div>
    `).join('');
}

function displayUpcomingPosts(posts) {
    const container = document.getElementById('upcomingPosts');
    if (posts.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📅</div>
                <h3>Nothing scheduled</h3>
                <p>Schedule posts from the calendar or create page.</p>
            </div>`;
        return;
    }
    container.innerHTML = posts.map(post => `
        <div class="post-item">
            <div class="post-info">
                <div class="post-title">${post.title}</div>
                <div class="post-meta">
                    ${getPlatformBadge(post.platform)}
                    <span>📅 ${formatDate(post.scheduled_time)}</span>
                </div>
            </div>
        </div>
    `).join('');
}

document.addEventListener('DOMContentLoaded', loadDashboard);
