// Auth Page Scripts

// Login Form
const loginForm = document.getElementById('loginForm');
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideError('errorMessage');
        
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        
        try {
            const data = await apiCall('/auth/login', {
                method: 'POST',
                body: JSON.stringify({ email, password })
            });
            
            setToken(data.access_token);
            window.location.href = '/index.html';
        } catch (error) {
            showError('errorMessage', error.message);
        }
    });
}

// Register Form
const registerForm = document.getElementById('registerForm');
if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideError('errorMessage');
        
        const full_name = document.getElementById('fullName').value;
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        
        try {
            await apiCall('/auth/register', {
                method: 'POST',
                body: JSON.stringify({ full_name, email, password })
            });
            
            showSuccess('successMessage', 'Registration successful! Redirecting to login...');
            setTimeout(() => {
                window.location.href = '/login.html';
            }, 2000);
        } catch (error) {
            showError('errorMessage', error.message);
        }
    });
}
