// Post Form Scripts

if (!requireAuth()) {
    throw new Error('Authentication required');
}

let platformConfigs = {};
let editMode = false;
let currentPostId = null;

const COUNTRY_TIMEZONES = [
    { code: 'BD', name: 'Bangladesh', timezones: ['Asia/Dhaka'] },
    { code: 'IN', name: 'India', timezones: ['Asia/Kolkata'] },
    { code: 'PK', name: 'Pakistan', timezones: ['Asia/Karachi'] },
    { code: 'AE', name: 'United Arab Emirates', timezones: ['Asia/Dubai'] },
    { code: 'SG', name: 'Singapore', timezones: ['Asia/Singapore'] },
    { code: 'GB', name: 'United Kingdom', timezones: ['Europe/London'] },
    { code: 'FR', name: 'France', timezones: ['Europe/Paris'] },
    { code: 'DE', name: 'Germany', timezones: ['Europe/Berlin'] },
    { code: 'US', name: 'United States', timezones: ['America/New_York', 'America/Chicago', 'America/Denver', 'America/Los_Angeles'] },
    { code: 'CA', name: 'Canada', timezones: ['America/Toronto', 'America/Winnipeg', 'America/Edmonton', 'America/Vancouver'] },
    { code: 'AU', name: 'Australia', timezones: ['Australia/Sydney', 'Australia/Adelaide', 'Australia/Perth'] },
    { code: 'JP', name: 'Japan', timezones: ['Asia/Tokyo'] }
];

// Load platform configs
async function loadPlatformConfigs() {
    try {
        const data = await apiCall('/posts/platforms');
        platformConfigs = data.platforms.reduce((acc, p) => {
            acc[p.platform] = p;
            return acc;
        }, {});
    } catch (error) {
        console.error('Error loading platforms:', error);
    }
}

// Check if editing existing post
async function checkEditMode() {
    const urlParams = new URLSearchParams(window.location.search);
    const postId = urlParams.get('id');
    
    if (postId) {
        editMode = true;
        currentPostId = postId;
        document.getElementById('pageTitle').textContent = 'Edit Post';
        document.getElementById('submitBtn').textContent = 'Update Post';
        
        try {
            const post = await apiCall(`/posts/${postId}`);
            populateForm(post);
        } catch (error) {
            console.error('Error loading post:', error);
            toast('Failed to load post', 'error');
        }
    }
}

function populateForm(post) {
    document.getElementById('postId').value = post.id;
    document.getElementById('title').value = post.title;

    // Check the matching platform checkbox
    const cb = document.querySelector(`input[name="platforms"][value="${post.platform}"]`);
    if (cb) cb.checked = true;

    document.getElementById('content').value = post.content;
    const timezoneSelect = document.getElementById('timezone');
    const countrySelect = document.getElementById('country');
    const matchedCountry = COUNTRY_TIMEZONES.find((c) => c.timezones.includes(post.timezone));

    if (matchedCountry) {
        countrySelect.value = matchedCountry.code;
        populateTimezoneOptions(matchedCountry.timezones, post.timezone);
    } else {
        countrySelect.value = 'BD';
        populateTimezoneOptions(['Asia/Dhaka'], post.timezone || 'Asia/Dhaka');
    }
    
    if (post.scheduled_time) {
        const date = new Date(post.scheduled_time);
        const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
        const dateStr = localDate.toISOString().split('T')[0];
        const timeStr = localDate.toTimeString().slice(0, 5);
        
        document.getElementById('scheduledDate').value = dateStr;
        document.getElementById('scheduledTime').value = timeStr;
    }
    
    updateCharCount();
    updatePlatformInfo();
}

// Platform selection handler
const platformCheckboxes = document.querySelectorAll('input[name="platforms"]');
const platformAllCheckbox = document.getElementById('platformAll');

// "All Platforms" toggle
platformAllCheckbox.addEventListener('change', () => {
    platformCheckboxes.forEach(cb => { cb.checked = platformAllCheckbox.checked; });
    updatePlatformInfo();
});

// Individual checkbox → keep "All" in sync
platformCheckboxes.forEach(cb => {
    cb.addEventListener('change', () => {
        platformAllCheckbox.checked = [...platformCheckboxes].every(c => c.checked);
        updatePlatformInfo();
    });
});

function getSelectedPlatforms() {
    return [...platformCheckboxes].filter(cb => cb.checked).map(cb => cb.value);
}

function updatePlatformInfo() {
    const selected = getSelectedPlatforms();
    const infoDiv = document.getElementById('platformInfo');

    if (selected.length === 0) {
        infoDiv.innerHTML = '';
        document.getElementById('maxChars').textContent = 'unlimited';
        return;
    }

    // When multiple platforms are selected, show the strictest limits
    let minTextLength = Infinity;
    const lines = selected.map(name => {
        const config = platformConfigs[name];
        if (!config) return null;
        if (config.max_text_length < minTextLength) minTextLength = config.max_text_length;
        return `<strong>${name.charAt(0).toUpperCase() + name.slice(1)}:</strong> ${config.max_text_length} chars`;
    }).filter(Boolean);

    document.getElementById('maxChars').textContent = minTextLength === Infinity ? 'unlimited' : minTextLength;

    if (selected.length === 1) {
        const config = platformConfigs[selected[0]];
        if (config) {
            infoDiv.innerHTML = `
                <strong>Platform Limits:</strong><br>
                Max text: ${config.max_text_length} characters<br>
                Images: ${config.supports_images ? '✓' : '✗'} (max ${config.max_image_size_mb}MB)<br>
                Videos: ${config.supports_videos ? '✓' : '✗'} (max ${config.max_video_size_mb}MB)
            `;
        }
    } else {
        infoDiv.innerHTML = `
            <strong>Posting to ${selected.length} platforms</strong> — character limit set to the strictest (${minTextLength}).<br>
            ${lines.join(' · ')}
        `;
    }
}

// Character counter
document.getElementById('content').addEventListener('input', updateCharCount);

function updateCharCount() {
    const content = document.getElementById('content').value;
    const charCount = document.getElementById('charCount');
    const maxChars = document.getElementById('maxChars').textContent;
    
    charCount.textContent = content.length;
    
    if (maxChars !== 'unlimited' && content.length > parseInt(maxChars)) {
        charCount.style.color = 'var(--error-color)';
    } else {
        charCount.style.color = 'inherit';
    }
}

// Media preview
document.getElementById('media').addEventListener('change', (e) => {
    const file = e.target.files[0];
    const preview = document.getElementById('mediaPreview');
    
    if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            if (file.type.startsWith('image/')) {
                preview.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
            } else if (file.type.startsWith('video/')) {
                preview.innerHTML = `<video src="${e.target.result}" controls></video>`;
            }
        };
        reader.readAsDataURL(file);
    } else {
        preview.innerHTML = '';
    }
});

// Form submission
document.getElementById('postForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const submitBtn = document.getElementById('submitBtn');
    const selectedPlatforms = getSelectedPlatforms();

    if (!editMode && selectedPlatforms.length === 0) {
        toast('Please select at least one platform', 'error');
        return;
    }

    setLoading(submitBtn, true);
    
    const formData = new FormData();
    formData.append('title', document.getElementById('title').value);
    formData.append('content', document.getElementById('content').value);
    formData.append('timezone', document.getElementById('timezone').value);
    
    const scheduledDate = document.getElementById('scheduledDate').value;
    const scheduledTime = document.getElementById('scheduledTime').value;
    
    if (scheduledDate && scheduledTime) {
        const datetime = `${scheduledDate}T${scheduledTime}:00`;
        formData.append('scheduled_time', datetime);
    }
    
    const mediaFile = document.getElementById('media').files[0];
    if (mediaFile) {
        formData.append('media', mediaFile);
    }
    
    try {
        const token = getToken();
        let endpoint, method;

        if (editMode) {
            // Edit mode: single platform update (keep existing behaviour)
            formData.append('platform', selectedPlatforms[0] || document.querySelector('input[name="platforms"]:checked')?.value);
            endpoint = `/posts/${currentPostId}`;
            method = 'PUT';
        } else if (selectedPlatforms.length === 1) {
            // Single platform: use original endpoint
            formData.append('platform', selectedPlatforms[0]);
            endpoint = '/posts';
            method = 'POST';
        } else {
            // Multiple platforms: use the multi endpoint
            formData.append('platforms', selectedPlatforms.join(','));
            endpoint = '/posts/multi';
            method = 'POST';
        }

        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: method,
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || error.message || 'Failed to save post');
        }
        
        const data = await response.json();
        const count = data.posts ? data.posts.length : 1;
        const msg = editMode
            ? 'Post updated successfully!'
            : count > 1
                ? `Post created for ${count} platforms! 🎉`
                : 'Post created successfully!';
        toast(msg, 'success');
        
        setTimeout(() => {
            window.location.href = '/posts.html';
        }, 1500);
        
    } catch (error) {
        toast(error.message, 'error');
    } finally {
        setLoading(submitBtn, false);
    }
});

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    setupCountryTimezone();
    await loadPlatformConfigs();
    await checkEditMode();
});

function setupCountryTimezone() {
    const countrySelect = document.getElementById('country');
    const timezoneSelect = document.getElementById('timezone');

    COUNTRY_TIMEZONES.forEach((country) => {
        const option = document.createElement('option');
        option.value = country.code;
        option.textContent = country.name;
        countrySelect.appendChild(option);
    });

    countrySelect.addEventListener('change', () => {
        const selected = COUNTRY_TIMEZONES.find((c) => c.code === countrySelect.value);
        populateTimezoneOptions(selected ? selected.timezones : ['UTC']);
    });

    const browserTz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const browserCountry = COUNTRY_TIMEZONES.find((c) => c.timezones.includes(browserTz));

    if (browserCountry) {
        countrySelect.value = browserCountry.code;
        populateTimezoneOptions(browserCountry.timezones, browserTz);
    } else {
        countrySelect.value = 'BD';
        populateTimezoneOptions(['Asia/Dhaka'], 'Asia/Dhaka');
    }
}

function populateTimezoneOptions(timezones, selectedValue = null) {
    const timezoneSelect = document.getElementById('timezone');
    timezoneSelect.innerHTML = '';

    timezones.forEach((tz) => {
        const option = document.createElement('option');
        option.value = tz;
        option.textContent = tz.replace('_', ' ');
        timezoneSelect.appendChild(option);
    });

    if (selectedValue && timezones.includes(selectedValue)) {
        timezoneSelect.value = selectedValue;
    }
}
