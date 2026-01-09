const togglePassword = document.getElementById('togglePassword');
const password = document.getElementById('password');

togglePassword.addEventListener('click', () => {
    const type = password.getAttribute('type') === 'password' ? 'text' : 'password';
    password.setAttribute('type', type);

    // Change icon based on state
    togglePassword.src = type === 'password' 
        ? '/static/eye-closed.png' 
        : '/static/eye-open.png';
});
