document.addEventListener('DOMContentLoaded', () => {
    const body = document.querySelector('body');
    body.classList.add('is-loaded'); // Add class when page content is ready

    // Find all links on the page
    const allLinks = document.querySelectorAll('a');

    allLinks.forEach(link => {
        link.addEventListener('click', e => {
            // Get the destination URL from the link's href attribute
            const destination = link.getAttribute('href');

            // Check if it's a valid link to another page (not an anchor # or javascript:)
            if (destination && destination !== '#' && !destination.startsWith('javascript:')) {
                e.preventDefault(); // Stop the browser's default navigation
                body.classList.add('is-leaving'); // Add fade-out class

                // Wait for the animation to finish, then navigate
                setTimeout(() => {
                    window.location.href = destination;
                }, 500); // This duration should match your CSS transition time
            }
        });
    });

    // --- THIS IS THE FIX ---
    // This code block solves the "invisible page on back button" issue.
    window.addEventListener('pageshow', event => {
        // The 'persisted' property is true if the page is from the back-forward cache.
        if (event.persisted) {
            // If it's from the cache, remove the class that makes it invisible.
            body.classList.remove('is-leaving');
        }
    });
});

