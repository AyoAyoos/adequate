// Wait for the DOM to be fully loaded before running scripts
document.addEventListener('DOMContentLoaded', () => {

    // --- Page Fade-In Logic ---
    document.body.classList.add('is-loaded');

    // --- Page Fade-Out & Navigation Logic ---
    const allLinks = document.querySelectorAll('a');
    allLinks.forEach(link => {
        link.addEventListener('click', e => {
            const destination = link.getAttribute('href');
            if (destination && destination !== '#' && !destination.startsWith('javascript:')) {
                e.preventDefault();
                // We remove the 'is-loaded' class to trigger the fade-out
                document.body.classList.remove('is-loaded'); 
                setTimeout(() => { window.location.href = destination; }, 500);
            }
        });
    });

    // --- Back-Forward Cache Fix ---
    window.addEventListener('pageshow', event => {
        if (event.persisted) {
            document.body.classList.add('is-loaded');
        }
    });

    // --- Password Visibility Toggle ---
    const toggleBtn = document.querySelector('.toggle-password');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            const passwordInput = document.getElementById('password');
            const eyeIcon = document.getElementById('eye-icon');
            
            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                eyeIcon.className = 'fas fa-eye-slash';
            } else {
                passwordInput.type = 'password';
                eyeIcon.className = 'fas fa-eye';
            }
        });
    }

});

