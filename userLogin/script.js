document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const subtitle = document.getElementById('form-subtitle');
    
    const toRegister = document.getElementById('to-register');
    const toLogin = document.getElementById('to-login');

    // Switch to Register Form
    toRegister.addEventListener('click', (e) => {
        e.preventDefault();
        
        // Hide Login, Show Register
        loginForm.classList.remove('active');
        setTimeout(() => {
            loginForm.style.display = 'none';
            registerForm.style.display = 'flex';
            setTimeout(() => {
                registerForm.classList.add('active');
                subtitle.textContent = 'Create your sanctuary of calm.';
            }, 50);
        }, 300);
    });

    // Switch to Login Form
    toLogin.addEventListener('click', (e) => {
        e.preventDefault();
        
        // Hide Register, Show Login
        registerForm.classList.remove('active');
        setTimeout(() => {
            registerForm.style.display = 'none';
            loginForm.style.display = 'flex';
            setTimeout(() => {
                loginForm.classList.add('active');
                subtitle.textContent = 'Your journey to peace starts here.';
            }, 50);
        }, 300);
    });

    // Form Submission Handling (Demo)
    const handleFormSubmit = (e) => {
        e.preventDefault();
        const formId = e.target.id;
        const btn = e.target.querySelector('button');
        const originalText = btn.textContent;
        
        // Loading state
        btn.textContent = 'Please wait...';
        btn.disabled = true;
        btn.style.opacity = '0.7';

        // Simulate network request
        setTimeout(() => {
            alert(`${formId === 'login-form' ? 'Logged in' : 'Account created'} successfully! (Demo Mode)`);
            btn.textContent = originalText;
            btn.disabled = false;
            btn.style.opacity = '1';
        }, 1500);
    };

    loginForm.addEventListener('submit', handleFormSubmit);
    registerForm.addEventListener('submit', handleFormSubmit);

    // Add subtle hover effect on inputs
    const inputs = document.querySelectorAll('input');
    inputs.forEach(input => {
        input.addEventListener('focus', () => {
            input.parentElement.style.transform = 'translateY(-2px)';
            input.parentElement.style.transition = 'transform 0.3s ease';
        });
        input.addEventListener('blur', () => {
            input.parentElement.style.transform = 'translateY(0)';
        });
    });
});
