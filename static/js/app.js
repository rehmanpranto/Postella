// ── Theme System (follows system clock & preference) ──
(function initTheme() {
    const stored = localStorage.getItem('theme'); // 'light' | 'dark' | null (auto)
    function getSystemTheme() {
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    function apply(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        // Update toggle icon on any existing toggle buttons
        document.querySelectorAll('.theme-toggle').forEach(btn => {
            btn.textContent = theme === 'dark' ? '☀️' : '🌙';
            btn.title = theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode';
        });
    }
    // Apply immediately (before DOMContentLoaded to avoid flash)
    apply(stored || getSystemTheme());
    // Listen for system preference changes when in auto mode
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        if (!localStorage.getItem('theme')) apply(e.matches ? 'dark' : 'light');
    });
    // Expose global toggle function
    window.toggleTheme = function () {
        const current = document.documentElement.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        localStorage.setItem('theme', next);
        apply(next);
    };
    // Expose for resetting to auto (system follows)
    window.resetThemeToAuto = function () {
        localStorage.removeItem('theme');
        apply(getSystemTheme());
    };
})();

// ── API Configuration ──
const API_BASE_URL = `${window.location.origin}/api`;

// ── Auth Helpers ──
function getToken() { return localStorage.getItem('access_token'); }
function setToken(token) { localStorage.setItem('access_token', token); }
function removeToken() { localStorage.removeItem('access_token'); }
function isAuthenticated() {
    const token = getToken();
    return !!token && token.split('.').length === 3;
}
function requireAuth() {
    if (!isAuthenticated()) { window.location.href = '/login.html'; return false; }
    return true;
}

// ── API Call Helper ──
async function apiCall(endpoint, options = {}) {
    const token = getToken();
    const headers = { ...options.headers };
    if (token) headers['Authorization'] = `Bearer ${token}`;
    if (!(options.body instanceof FormData)) headers['Content-Type'] = 'application/json';

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, { ...options, headers });
        const skipAuth = options.skipAuthRedirect === true || endpoint.startsWith('/auth/');

        if ((response.status === 401 || response.status === 422) && !skipAuth) {
            removeToken();
            window.location.href = '/login.html';
            throw new Error('Session expired. Please log in again.');
        }

        const data = await response.json();
        if (!response.ok) throw new Error(data.error || data.message || 'Request failed');
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// ── Toast Notification System ──
function _getToastContainer() {
    let c = document.getElementById('toast-container');
    if (!c) {
        c = document.createElement('div');
        c.id = 'toast-container';
        c.className = 'toast-container';
        document.body.appendChild(c);
    }
    return c;
}
function toast(message, type = 'info', duration = 4000) {
    const container = _getToastContainer();
    const el = document.createElement('div');
    el.className = `toast toast-${type}`;
    el.innerHTML = `<span>${message}</span><button class="toast-close" onclick="this.parentElement.remove()">&times;</button>`;
    container.appendChild(el);
    setTimeout(() => { el.style.animation = 'slideOut 0.3s ease forwards'; setTimeout(() => el.remove(), 300); }, duration);
}

// ── UI Helpers ──
function showError(elementId, message) {
    const el = document.getElementById(elementId);
    if (el) { el.textContent = message; el.style.display = 'block'; }
}
function hideError(elementId) {
    const el = document.getElementById(elementId);
    if (el) el.style.display = 'none';
}
function showSuccess(elementId, message) {
    const el = document.getElementById(elementId);
    if (el) { el.textContent = message; el.style.display = 'block'; }
}
function setLoading(btn, loading) {
    if (!btn) return;
    if (loading) { btn.classList.add('loading'); btn.disabled = true; btn._origText = btn.textContent; }
    else { btn.classList.remove('loading'); btn.disabled = false; }
}

// ── Formatters ──
function formatDate(dateString) {
    if (!dateString) return 'Not scheduled';
    return new Date(dateString).toLocaleString(undefined, { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}
function formatDateShort(dateString) {
    if (!dateString) return '';
    return new Date(dateString).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
}
function getStatusBadge(status) {
    const classes = { draft: 'badge-draft', scheduled: 'badge-scheduled', posted: 'badge-posted', failed: 'badge-failed' };
    return `<span class="badge ${classes[status] || ''}">${status}</span>`;
}
function getPlatformBadge(platform) {
    const icons = { facebook: '📘', instagram: '📸', linkedin: '💼', twitter: '𝕏' };
    return `<span class="platform-badge platform-${platform}">${icons[platform] || ''} ${platform}</span>`;
}

// ── Mobile Menu Toggle ──
document.addEventListener('DOMContentLoaded', () => {
    // Apply theme toggle icon to any buttons rendered after DOMContentLoaded
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    document.querySelectorAll('.theme-toggle').forEach(btn => {
        btn.textContent = currentTheme === 'dark' ? '☀️' : '🌙';
        btn.title = currentTheme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode';
    });

    // Logout button
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            removeToken();
            toast('Logged out successfully', 'info');
            setTimeout(() => window.location.href = '/login.html', 500);
        });
    }

    // Mobile hamburger toggle
    const toggle = document.querySelector('.nav-toggle');
    const menu = document.querySelector('.nav-menu');
    if (toggle && menu) {
        toggle.addEventListener('click', () => menu.classList.toggle('open'));
        // Close menu when a link is clicked
        menu.querySelectorAll('.nav-link, .btn').forEach(link => {
            link.addEventListener('click', () => menu.classList.remove('open'));
        });
    }
});
