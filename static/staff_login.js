function togglePassword() {
    const password = document.getElementById("password");
    const eyeIcon = document.getElementById("eyeIcon");

    if (password.type === "password") {
        password.type = "text";
        eyeIcon.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24">
                <path fill="#555"
                d="M2 5.27 3.28 4 20 20.72 18.73 22l-3.06-3.06A11.64 11.64 0 0 1 12 19c-5 0-9.27-3.11-11-7a11.78 11.78 0 0 1 4.11-5.13L2 5.27z"/>
            </svg>`;
    } else {
        password.type = "password";
        eyeIcon.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24">
                <path fill="#555"
                d="M12 5C7 5 2.73 8.11 1 12c1.73 3.89 6 7 11 7s9.27-3.11 11-7c-1.73-3.89-6-7-11-7zm0 11a4 4 0 1 1 0-8 4 4 0 0 1 0 8z"/>
            </svg>`;
    }
}
