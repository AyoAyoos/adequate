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

    // Fix for browser back-forward cache making page invisible
    window.addEventListener('pageshow', event => {
        if (event.persisted) {
            body.classList.remove('is-leaving');
        }
    });

    // --- INTERACTIVE GLASS PANEL TILT EFFECT ---
    const glassPanel = document.querySelector('.glass-panel');
    if (glassPanel) {
        glassPanel.addEventListener('mousemove', e => {
            const rect = glassPanel.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            const rotateX = (y - centerY) / 20;
            const rotateY = (centerX - x) / 20;
            glassPanel.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
        });

        glassPanel.addEventListener('mouseleave', () => {
            glassPanel.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg)';
        });
    }

    // --- FILTERING LOGIC ---
    const filterButtons = document.querySelectorAll('.filter-btn');
    const resultCards = document.querySelectorAll('.result-card');

    filterButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Manage active button style
            filterButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');

            const selectedLevel = button.getAttribute('data-level');

            // Show or hide cards based on selected level
            resultCards.forEach(card => {
                if (selectedLevel === 'all' || card.getAttribute('data-level') === selectedLevel) {
                    card.classList.remove('hidden');
                } else {
                    card.classList.add('hidden');
                }
            });
        });
    });

});
