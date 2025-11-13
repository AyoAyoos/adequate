// Wait for the DOM to be fully loaded before running scripts
document.addEventListener('DOMContentLoaded', () => {

    // --- SMOOTH PAGE TRANSITION LOGIC ---
    const body = document.querySelector('body');
    const allLinks = document.querySelectorAll('a');

    allLinks.forEach(link => {
        link.addEventListener('click', e => {
            const destination = link.getAttribute('href');
            if (destination && destination !== '#' && !destination.startsWith('javascript:')) {
                e.preventDefault();
                body.classList.add('is-leaving');
                setTimeout(() => {
                    window.location.href = destination;
                }, 500);
            }
        });
    });

    window.addEventListener('pageshow', event => {
        if (event.persisted) {
            body.classList.remove('is-leaving');
        }
    });


    // --- INTERACTIVE GLASS PANEL TILT EFFECT ---
    const glassPanels = document.querySelectorAll('.glass-panel');

    glassPanels.forEach(panel => {
        panel.addEventListener('mousemove', e => {
            const rect = panel.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            const rotateX = (y - centerY) / 20;
            const rotateY = (centerX - x) / 20;
            panel.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
        });

        panel.addEventListener('mouseleave', () => {
            panel.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg)';
        });
    });


    // --- PASSWORD TOGGLE VISIBILITY LOGIC ---
    const toggleBtn = document.querySelector('.toggle-password');

    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            const passwordInput = document.getElementById('password');
            const eyeIcon = document.getElementById('eye-icon');
            
            if (passwordInput && eyeIcon) {
                if (passwordInput.type === 'password') {
                    passwordInput.type = 'text';
                    eyeIcon.className = 'fas fa-eye-slash';
                } else {
                    passwordInput.type = 'password';
                    eyeIcon.className = 'fas fa-eye';
                }
            }
        });
    }

});
