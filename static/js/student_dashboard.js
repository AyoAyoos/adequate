// Wait for the DOM to be fully loaded before running scripts
document.addEventListener('DOMContentLoaded', () => {

    // --- Page Fade-In Logic ---
    document.body.classList.add('is-loaded');

    // --- Page Fade-Out & Navigation Logic ---
    const allLinks = document.querySelectorAll('a');
    allLinks.forEach(link => {
        link.addEventListener('click', e => {
            const destination = link.getAttribute('href');
            // Prevent animation for anchor links, javascript calls, etc.
            if (destination && destination !== '#' && !destination.startsWith('javascript:')) {
                e.preventDefault();
                // We now remove the 'is-loaded' class to trigger the fade-out
                document.body.classList.remove('is-loaded'); 
                // Wait for the fade-out animation to finish before navigating
                setTimeout(() => { window.location.href = destination; }, 500);
            }
        });
    });

    // --- Back-Forward Cache Fix ---
    // This ensures the page is visible if the user navigates with the back button.
    window.addEventListener('pageshow', event => {
        if (event.persisted) {
            document.body.classList.add('is-loaded');
        }
    });

});
