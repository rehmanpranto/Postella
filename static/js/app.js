// API Configuration
const API_BASE_URL = `${window.location.origin}/api`;

// Auth Helper Functions
function getToken() {
    return localStorage.getItem('access_token');
}

function setToken(token) {
    localStorage.setItem('access_token', token);
}

function removeToken() {
    localStorage.removeItem('access_token');
}

function isAuthenticated() {
    const token = getToken();
    return !!token && token.split('.').length === 3;
}

function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = '/login.html';
        return false;
    }
    return true;
}

// API Call Helper
async function apiCall(endpoint, options = {}) {
    const token = getToken();
    const headers = {
        ...options.headers,
    };
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    
    if (!(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
    }
    
    const config = {
        ...options,
        headers
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
        const skipAuthRedirect = options.skipAuthRedirect === true || endpoint.startsWith('/auth/');
        
        if ((response.status === 401 || response.status === 422) && !skipAuthRedirect) {
            removeToken();
            window.location.href = '/login.html';
            throw new Error('Session expired. Please log in again.');
        }
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || data.message || 'Request failed');
        }
        
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// UI Helper Functions
function showError(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = message;
        element.style.display = 'block';
    }
}

function hideError(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = 'none';
    }
}

function showSuccess(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = message;
        element.style.display = 'block';
    }
}

function formatDate(dateString) {
    if (!dateString) return 'Not scheduled';
    const date = new Date(dateString);
    return date.toLocaleString();
}

function formatDateShort(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString();
}

function getStatusBadge(status) {
    const badges = {
        'draft': 'badge-draft',
        'scheduled': 'badge-scheduled',
        'posted': 'badge-posted',
        'failed': 'badge-failed'
    };
    return `<span class="badge ${badges[status]}">${status}</span>`;
}

function getPlatformBadge(platform) {
    return `<span class="platform-badge platform-${platform}">${platform}</span>`;
}

// Logout Handler
document.addEventListener('DOMContentLoaded', () => {
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            removeToken();
            window.location.href = '/login.html';
        });
    }
});
