// Calendar Page Scripts

if (!requireAuth()) {
    throw new Error('Authentication required');
}

let currentDate = new Date();
let currentView = 'month';
let platformConfigs = {};

// Load Calendar
async function loadCalendar() {
    try {
        const { start, end } = getDateRange();
        const data = await apiCall(`/calendar/posts?start_date=${start}&end_date=${end}&view=${currentView}`);
        
        displayCalendar(data);
    } catch (error) {
        console.error('Error loading calendar:', error);
    }
}

async function loadPlatforms() {
    try {
        const data = await apiCall('/posts/platforms');
        platformConfigs = data.platforms.reduce((acc, p) => {
            acc[p.platform] = p;
            return acc;
        }, {});

        const select = document.getElementById('planPlatform');
        if (select) {
            select.innerHTML = '';
            const platforms = Object.keys(platformConfigs);
            const fallbackPlatforms = ['facebook', 'instagram', 'linkedin', 'twitter'];
            const options = platforms.length > 0 ? platforms : fallbackPlatforms;

            const allOption = document.createElement('option');
            allOption.value = 'all';
            allOption.textContent = 'All Platforms';
            select.appendChild(allOption);

            options.forEach((platform) => {
                const option = document.createElement('option');
                option.value = platform;
                option.textContent = platform.charAt(0).toUpperCase() + platform.slice(1);
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading platforms:', error);
    }
}

function getDateRange() {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    
    if (currentView === 'month') {
        const start = new Date(year, month, 1);
        const end = new Date(year, month + 1, 0);
        return {
            start: start.toISOString(),
            end: end.toISOString()
        };
    } else if (currentView === 'week') {
        const start = new Date(currentDate);
        start.setDate(currentDate.getDate() - currentDate.getDay());
        const end = new Date(start);
        end.setDate(start.getDate() + 7);
        return {
            start: start.toISOString(),
            end: end.toISOString()
        };
    } else {
        const start = new Date(currentDate);
        start.setHours(0, 0, 0, 0);
        const end = new Date(currentDate);
        end.setHours(23, 59, 59, 999);
        return {
            start: start.toISOString(),
            end: end.toISOString()
        };
    }
}

function displayCalendar(data) {
    updateMonthDisplay();
    
    const grid = document.getElementById('calendarGrid');
    
    if (currentView === 'month') {
        displayMonthView(data, grid);
    } else if (currentView === 'week') {
        displayWeekView(data, grid);
    } else {
        displayDayView(data, grid);
    }
}

function displayMonthView(data, grid) {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startingDayOfWeek = firstDay.getDay();
    const daysInMonth = lastDay.getDate();
    
    let html = '<div class="calendar-header">';
    const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    dayNames.forEach(day => {
        html += `<div class="calendar-day-name">${day}</div>`;
    });
    html += '</div><div class="calendar-days">';
    
    // Previous month days
    const prevMonthDays = new Date(year, month, 0).getDate();
    for (let i = startingDayOfWeek - 1; i >= 0; i--) {
        html += `<div class="calendar-day other-month"><div class="day-number">${prevMonthDays - i}</div></div>`;
    }
    
    // Current month days
    const today = new Date();
    for (let day = 1; day <= daysInMonth; day++) {
        const date = new Date(year, month, day);
        const dateKey = date.toISOString().split('T')[0];
        const isToday = date.toDateString() === today.toDateString();
        const posts = data.posts_by_date[dateKey] || [];
        
        html += `
            <div class="calendar-day ${isToday ? 'today' : ''}">
                <div class="day-number">${day}</div>
                <div class="day-posts">
                    ${posts.map(post => `
                        <div class="day-post platform-${post.platform}" onclick="showPostDetail(${post.id})">
                            ${post.title}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    // Next month days
    const remainingDays = 42 - (startingDayOfWeek + daysInMonth);
    for (let day = 1; day <= remainingDays; day++) {
        html += `<div class="calendar-day other-month"><div class="day-number">${day}</div></div>`;
    }
    
    html += '</div>';
    grid.innerHTML = html;
}

function displayWeekView(data, grid) {
    const start = new Date(data.start_date);
    const today = new Date();

    let html = '<div class="calendar-header">';
    const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    dayNames.forEach(day => {
        html += `<div class="calendar-day-name">${day}</div>`;
    });
    html += '</div><div class="calendar-days">';

    for (let i = 0; i < 7; i++) {
        const date = new Date(start);
        date.setDate(start.getDate() + i);
        const dateKey = date.toISOString().split('T')[0];
        const isToday = date.toDateString() === today.toDateString();
        const posts = data.posts_by_date[dateKey] || [];

        html += `
            <div class="calendar-day ${isToday ? 'today' : ''}">
                <div class="day-number">${date.getDate()}</div>
                <div class="day-posts">
                    ${posts.map(post => `
                        <div class="day-post platform-${post.platform}" onclick="showPostDetail(${post.id})">
                            ${post.title}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    html += '</div>';
    grid.innerHTML = html;
}

function displayDayView(data, grid) {
    const start = new Date(data.start_date);
    const dateKey = start.toISOString().split('T')[0];
    const posts = (data.posts_by_date[dateKey] || []).slice();

    posts.sort((a, b) => {
        if (!a.scheduled_time || !b.scheduled_time) return 0;
        return new Date(a.scheduled_time) - new Date(b.scheduled_time);
    });

    if (posts.length === 0) {
        grid.innerHTML = '<div class="loading">No posts scheduled for this day.</div>';
        return;
    }

    const items = posts.map(post => {
        const timeLabel = post.scheduled_time ? new Date(post.scheduled_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Anytime';
        return `
            <div class="day-view-item" onclick="showPostDetail(${post.id})">
                <div class="day-view-time">${timeLabel}</div>
                <div class="day-view-content">
                    <div class="day-view-title">${post.title}</div>
                    <div class="day-view-meta">
                        ${getPlatformBadge(post.platform)}
                        ${getStatusBadge(post.status)}
                    </div>
                </div>
            </div>
        `;
    }).join('');

    grid.innerHTML = `<div class="day-view-list">${items}</div>`;
}

function updateMonthDisplay() {
    const monthNames = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ];
    
    const monthDisplay = document.getElementById('currentMonth');
    if (currentView === 'day') {
        monthDisplay.textContent = currentDate.toLocaleDateString(undefined, {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
        return;
    }

    if (currentView === 'week') {
        const start = new Date(currentDate);
        start.setDate(currentDate.getDate() - currentDate.getDay());
        const end = new Date(start);
        end.setDate(start.getDate() + 6);
        const startLabel = `${monthNames[start.getMonth()]} ${start.getDate()}`;
        const endLabel = `${monthNames[end.getMonth()]} ${end.getDate()}, ${end.getFullYear()}`;
        monthDisplay.textContent = `${startLabel} - ${endLabel}`;
        return;
    }

    monthDisplay.textContent = `${monthNames[currentDate.getMonth()]} ${currentDate.getFullYear()}`;
}

function openPlanMonthModal() {
    const modal = document.getElementById('planMonthModal');
    if (!modal) return;

    const monthInput = document.getElementById('planMonth');
    const tzInput = document.getElementById('planTimezone');

    if (monthInput) {
        const monthValue = `${currentDate.getFullYear()}-${String(currentDate.getMonth() + 1).padStart(2, '0')}`;
        monthInput.value = monthValue;
    }

    if (tzInput) {
        tzInput.value = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
    }

    hidePlanMonthMessages();
    modal.style.display = 'flex';
}

function closePlanMonthModal() {
    const modal = document.getElementById('planMonthModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function showPlanMonthError(message) {
    const el = document.getElementById('planMonthError');
    if (el) {
        el.textContent = message;
        el.style.display = 'block';
    }
}

function showPlanMonthSuccess(message) {
    const el = document.getElementById('planMonthSuccess');
    if (el) {
        el.textContent = message;
        el.style.display = 'block';
    }
}

function hidePlanMonthMessages() {
    const errorEl = document.getElementById('planMonthError');
    const successEl = document.getElementById('planMonthSuccess');
    if (errorEl) errorEl.style.display = 'none';
    if (successEl) successEl.style.display = 'none';
}

async function showPostDetail(postId) {
    try {
        const post = await apiCall(`/posts/${postId}`);
        
        const modal = document.getElementById('postModal');
        const detail = document.getElementById('postDetail');
        
        detail.innerHTML = `
            <h2>${post.title}</h2>
            <div class="post-meta" style="margin: 1rem 0;">
                ${getPlatformBadge(post.platform)}
                ${getStatusBadge(post.status)}
            </div>
            <p><strong>Scheduled:</strong> ${formatDate(post.scheduled_time)}</p>
            <p><strong>Content:</strong></p>
            <p>${post.content}</p>
            ${post.media_path ? `<img src="/uploads/${post.media_path}" style="max-width: 100%; margin-top: 1rem;">` : ''}
            <div class="form-actions" style="margin-top: 2rem;">
                <button class="btn btn-secondary" onclick="editPost(${post.id})">Edit</button>
                <button class="btn btn-danger" onclick="deletePost(${post.id})">Delete</button>
            </div>
        `;
        
        modal.style.display = 'flex';
    } catch (error) {
        console.error('Error loading post:', error);
    }
}

function editPost(postId) {
    window.location.href = `/create-post.html?id=${postId}`;
}

async function deletePost(postId) {
    if (!confirm('Are you sure you want to delete this post?')) return;
    
    try {
        await apiCall(`/posts/${postId}`, { method: 'DELETE' });
        document.getElementById('postModal').style.display = 'none';
        loadCalendar();
    } catch (error) {
        console.error('Error deleting post:', error);
        alert('Failed to delete post: ' + error.message);
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    loadCalendar();
    loadPlatforms();
    
    document.getElementById('prevMonth').addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() - 1);
        loadCalendar();
    });
    
    document.getElementById('nextMonth').addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() + 1);
        loadCalendar();
    });
    
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentView = btn.dataset.view;
            loadCalendar();
        });
    });

    const planMonthBtn = document.getElementById('planMonthBtn');
    if (planMonthBtn) {
        planMonthBtn.addEventListener('click', openPlanMonthModal);
    }

    const planMonthClose = document.getElementById('planMonthClose');
    if (planMonthClose) {
        planMonthClose.addEventListener('click', closePlanMonthModal);
    }

    const planMonthForm = document.getElementById('planMonthForm');
    if (planMonthForm) {
        planMonthForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            hidePlanMonthMessages();

            const payload = {
                month: document.getElementById('planMonth').value,
                platform: document.getElementById('planPlatform').value,
                time: document.getElementById('planTime').value,
                timezone: document.getElementById('planTimezone').value,
                title_template: document.getElementById('planTitleTemplate').value,
                content_template: document.getElementById('planContentTemplate').value,
                weekdays_only: document.getElementById('planWeekdaysOnly').checked,
                skip_existing: document.getElementById('planSkipExisting').checked
            };

            try {
                const result = await apiCall('/calendar/plan-month', {
                    method: 'POST',
                    body: JSON.stringify(payload)
                });

                showPlanMonthSuccess(`Created ${result.created} posts. Skipped ${result.skipped}.`);
                await loadCalendar();
            } catch (error) {
                showPlanMonthError(error.message || 'Failed to plan month');
            }
        });
    }
    
    // Close modal
    document.querySelector('.close').addEventListener('click', () => {
        document.getElementById('postModal').style.display = 'none';
    });
    
    window.addEventListener('click', (e) => {
        const modal = document.getElementById('postModal');
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });

    window.addEventListener('click', (e) => {
        const modal = document.getElementById('planMonthModal');
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
});
