// Wait for the DOM to be fully loaded before running scripts
document.addEventListener('DOMContentLoaded', () => {
    document.body.classList.add('is-loaded');

    // --- SMOOTH PAGE TRANSITION LOGIC ---
    // This was the missing part. It handles the fade-out effect.
    const body = document.querySelector('body');
    const allLinks = document.querySelectorAll('a');

    allLinks.forEach(link => {
        link.addEventListener('click', e => {
            const destination = link.getAttribute('href');
            // Prevent animation for anchor links and javascript calls
            if (destination && destination !== '#' && !destination.startsWith('javascript:')) {
                e.preventDefault();
                body.classList.add('is-leaving');
                setTimeout(() => {
                    window.location.href = destination;
                }, 500); // Match this to your CSS transition duration
            }
        });
    });

    // Fix for browser back-forward cache making page invisible
    window.addEventListener('pageshow', event => {
        if (event.persisted) {
            body.classList.remove('is-leaving');
        }
    });


    // --- INTERACTIVE GLASS PANEL TILT EFFECT ---
    // This is your original code, which works perfectly.
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

});
