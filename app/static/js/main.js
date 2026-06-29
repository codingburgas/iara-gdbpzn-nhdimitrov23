// app/static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu toggle
    const menuToggle = document.querySelector('.menu-toggle');
    const navLinks = document.querySelector('.navbar-links');

    if (menuToggle && navLinks) {
        menuToggle.addEventListener('click', function() {
            navLinks.classList.toggle('active');
        });
    }

    // Auto-dismiss flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(function(msg) {
        setTimeout(function() {
            msg.style.opacity = '0';
            msg.style.transition = 'opacity 0.5s ease';
            setTimeout(function() {
                msg.remove();
            }, 500);
        }, 5000);
    });
});

// Socket.IO for real-time features
// This will be initialized when needed
let socket = null;

function initSocket() {
    if (!socket) {
        socket = io();
        socket.on('connect', function() {
            console.log('WebSocket connected');
        });
        socket.on('disconnect', function() {
            console.log('WebSocket disconnected');
        });
    }
    return socket;
}