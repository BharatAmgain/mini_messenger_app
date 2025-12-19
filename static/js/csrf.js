// Function to get CSRF token from cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Get CSRF token
const csrftoken = getCookie('csrftoken');

// Set up AJAX requests to include CSRF token
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!(/^(GET|HEAD|OPTIONS|TRACE)$/.test(settings.type)) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

// Alternative: Add CSRF token to all forms dynamically
document.addEventListener('DOMContentLoaded', function() {
    // Add CSRF token to all AJAX requests
    const originalFetch = window.fetch;
    window.fetch = function(url, options = {}) {
        // Only add CSRF for same-origin POST, PUT, PATCH, DELETE requests
        if (!options.credentials) options.credentials = 'same-origin';

        if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(options.method?.toUpperCase())) {
            const requestUrl = typeof url === 'string' ? url : url.url;
            const isSameOrigin = new URL(requestUrl, window.location.origin).origin === window.location.origin;

            if (isSameOrigin) {
                options.headers = {
                    ...options.headers,
                    'X-CSRFToken': csrftoken
                };
            }
        }
        return originalFetch(url, options);
    };
});

// Function to update online status with CSRF protection
function updateOnlineStatus(isOnline) {
    fetch('/chat/update-online-status/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({ is_online: isOnline }),
        credentials: 'same-origin'
    }).then(response => {
        if (!response.ok) {
            console.error('Failed to update online status');
        }
    }).catch(error => {
        console.error('Error updating online status:', error);
    });
}