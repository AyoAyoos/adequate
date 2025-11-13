// static/js/registration.js

document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('.registration-form');
    const password = document.getElementById('password');
    const confirmPassword = document.getElementById('confirm_password');

    form.addEventListener('submit', function(event) {
        // Simple client-side password match validation
        if (password.value !== confirmPassword.value) {
            alert("Passwords do not match!"); // Or display a more elegant error message
            event.preventDefault(); // Stop form submission
            return false;
        }

        // Add more client-side validations here (e.g., email format, minimum password length if not handled by pattern attribute)
    });
});