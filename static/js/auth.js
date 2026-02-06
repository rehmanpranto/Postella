// ── Auth Page Scripts ──

// Login Form
const loginForm = document.getElementById('loginForm');
if (loginForm) {
    // If already logged in, redirect
    if (isAuthenticated()) window.location.href = '/index.html';

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideError('errorMessage');
        const btn = loginForm.querySelector('button[type="submit"]');
        setLoading(btn, true);

        try {
            const data = await apiCall('/auth/login', {
                method: 'POST',
                body: JSON.stringify({
                    email: document.getElementById('email').value,
                    password: document.getElementById('password').value
                })
            });
            setToken(data.access_token);
            toast('Welcome back!', 'success');
            setTimeout(() => window.location.href = '/index.html', 500);
        } catch (error) {
            showError('errorMessage', error.message);
            setLoading(btn, false);
        }
    });
}

// Register Form
const registerForm = document.getElementById('registerForm');
if (registerForm) {
    if (isAuthenticated()) window.location.href = '/index.html';

    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideError('errorMessage');
        hideError('successMessage');
        const btn = registerForm.querySelector('button[type="submit"]');

        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirmPassword');
        if (confirmPassword && confirmPassword.value !== password) {
            showError('errorMessage', 'Passwords do not match');
            return;
        }

        setLoading(btn, true);

        try {
            await apiCall('/auth/register', {
                method: 'POST',
                body: JSON.stringify({
                    full_name: document.getElementById('fullName').value,
                    email: document.getElementById('email').value,
                    password: password
                })
            });
            showSuccess('successMessage', 'Account created! Redirecting to login...');
            toast('Registration successful!', 'success');
            setTimeout(() => window.location.href = '/login.html', 1500);
        } catch (error) {
            showError('errorMessage', error.message);
            setLoading(btn, false);
        }
    });
}
