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
                // We now remove the 'is-loaded' class to trigger the fade-out
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

    // --- Dashboard-specific JS (e.g., file input) ---
    const fileInput = document.getElementById('fileUpload');
    const fileNameSpan = document.getElementById('file-name');
    if (fileInput && fileNameSpan) {
        fileInput.addEventListener('change', () => {
            fileNameSpan.textContent = fileInput.files.length > 0 ? fileInput.files[0].name : 'No file chosen';
        });
    }

    // The "Interactive Glass Panel Tilt Effect" block has been completely removed.
    // The panels will no longer move with the cursor.

});

