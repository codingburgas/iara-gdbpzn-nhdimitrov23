document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu toggle
    const menuToggle = document.querySelector('.menu-toggle');
    const navLinks = document.querySelector('.navbar-links');

    if (menuToggle && navLinks) {
        menuToggle.addEventListener('click', function() {
            navLinks.classList.toggle('active');

            // Change icon
            const icon = menuToggle.querySelector('i');
            if (icon) {
                if (navLinks.classList.contains('active')) {
                    icon.className = 'fas fa-times';
                } else {
                    icon.className = 'fas fa-bars';
                }
            }
        });

        // Close mobile menu when clicking a link
        navLinks.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', function() {
                navLinks.classList.remove('active');
                const icon = menuToggle.querySelector('i');
                if (icon) {
                    icon.className = 'fas fa-bars';
                }
            });
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

    // Check if running as PWA
    if (window.matchMedia('(display-mode: standalone)').matches) {
        console.log('📱 Running as PWA');
        document.body.classList.add('pwa-mode');
    }

    // Add pull-to-refresh indicator
    let touchStartY = 0;
    let isPulling = false;

    document.addEventListener('touchstart', function(e) {
        if (window.scrollY === 0) {
            touchStartY = e.touches[0].pageY;
            isPulling = true;
        }
    });

    document.addEventListener('touchmove', function(e) {
        if (isPulling && window.scrollY === 0) {
            const pullDistance = e.touches[0].pageY - touchStartY;
            if (pullDistance > 30) {
                e.preventDefault();
                // Show pull to refresh indicator
                const indicator = document.querySelector('.pull-to-refresh');
                if (indicator) {
                    indicator.classList.add('active');
                    indicator.textContent = '🔄 Пуснете за обновяване...';
                }
            }
        }
    });

    document.addEventListener('touchend', function(e) {
        if (isPulling && window.scrollY === 0) {
            const pullDistance = e.changedTouches[0].pageY - touchStartY;
            if (pullDistance > 50) {
                location.reload();
            }
        }
        isPulling = false;
        const indicator = document.querySelector('.pull-to-refresh');
        if (indicator) {
            indicator.classList.remove('active');
        }
    });
});

// Socket.IO for real-time features
let socket = null;

function initSocket() {
    if (!socket) {
        try {
            socket = io({
                transports: ['websocket', 'polling'],
                reconnection: true,
                reconnectionAttempts: 5,
                reconnectionDelay: 1000
            });

            socket.on('connect', function() {
                console.log('✅ WebSocket connected');
                // Request push notification permission
                requestNotificationPermission();
            });

            socket.on('disconnect', function() {
                console.log('❌ WebSocket disconnected');
            });

            socket.on('connect_error', function(error) {
                console.log('⚠️ WebSocket connection error:', error);
            });

            socket.on('incident_created', function(data) {
                console.log('📢 New incident created:', data);
                showNotification('🚒 Ново произшествие: ' + data.incident_number);
            });

            socket.on('incident_updated', function(data) {
                console.log('📢 Incident updated:', data);
            });

            socket.on('message_received', function(data) {
                console.log('💬 New message:', data);
                showNotification('💬 Ново съобщение от ' + data.user_name);
            });

        } catch (e) {
            console.log('⚠️ Socket.IO not available:', e);
        }
    }
    return socket;
}

// Request notification permission
function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission().then(function(permission) {
            if (permission === 'granted') {
                console.log('✅ Notification permission granted');
            }
        });
    }
}

// Show notification
function showNotification(message) {
    // If PWA and notifications are supported
    if ('Notification' in window && Notification.permission === 'granted') {
        const notification = new Notification('ГДПБЗН', {
            body: message,
            icon: '/static/icons/icon-192x192.png',
            badge: '/static/icons/icon-72x72.png',
            vibrate: [200, 100, 200],
            requireInteraction: true
        });

        notification.onclick = function() {
            window.focus();
            notification.close();
        };
    }

    // Also show in flash messages
    const flashContainer = document.querySelector('.flash-messages');
    if (flashContainer) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-info';
        alert.textContent = message;
        flashContainer.appendChild(alert);

        setTimeout(function() {
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.5s ease';
            setTimeout(function() {
                alert.remove();
            }, 500);
        }, 5000);
    }
}

// Initialize SocketIO when page loads
if (typeof io !== 'undefined') {
    document.addEventListener('DOMContentLoaded', function() {
        initSocket();
    });
}