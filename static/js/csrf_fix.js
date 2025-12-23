// static/js/csrf_fix.js - COMPLETE FIXED VERSION
(function() {
    console.log('CSRF Fix: Initializing...');

    // Function to get CSRF token
    function getCSRFToken() {
        let csrfToken = null;

        // Try from cookies first
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith('csrftoken=')) {
                csrfToken = decodeURIComponent(cookie.substring('csrftoken='.length));
                break;
            } else if (cookie.startsWith('csrf_token=')) {
                csrfToken = decodeURIComponent(cookie.substring('csrf_token='.length));
                break;
            }
        }

        // Try from meta tag
        if (!csrfToken) {
            const metaToken = document.querySelector('meta[name="csrf-token"]');
            if (metaToken) {
                csrfToken = metaToken.getAttribute('content');
            }
        }

        console.log('CSRF Token found:', csrfToken ? 'Yes' : 'No');
        return csrfToken;
    }

    // Store globally
    window.csrftoken = getCSRFToken();

    // Setup AJAX requests to include CSRF token
    if (window.csrftoken) {
        // For fetch API
        const originalFetch = window.fetch;
        window.fetch = function(url, options = {}) {
            // Clone options to avoid mutating original
            const newOptions = { ...options };

            // Only add CSRF for same-origin POST/PUT/PATCH/DELETE requests
            const isSameOrigin = new URL(url, window.location.origin).origin === window.location.origin;
            const isMutatingMethod = ['POST', 'PUT', 'PATCH', 'DELETE'].includes(
                (newOptions.method || 'GET').toUpperCase()
            );

            if (isSameOrigin && isMutatingMethod) {
                if (!newOptions.headers) {
                    newOptions.headers = {};
                }
                newOptions.headers['X-CSRFToken'] = window.csrftoken;
                newOptions.credentials = 'same-origin';
            }

            return originalFetch(url, newOptions);
        };

        console.log('CSRF Fix: Applied to fetch API');
    }

    // Function to update online status - SIMPLIFIED VERSION
    function updateOnlineStatus(isOnline) {
        // Only run if user is authenticated
        if (!document.body.classList.contains('user-authenticated')) {
            return;
        }

        const csrfToken = window.csrftoken || getCSRFToken();
        if (!csrfToken) {
            console.warn('CSRF Fix: Token not found for online status update');
            return;
        }

        // Simple form data instead of JSON to avoid parsing errors
        const formData = new FormData();
        formData.append('online', isOnline.toString());
        formData.append('csrfmiddlewaretoken', csrfToken);

        fetch('/chat/update-online-status/', {
            method: 'POST',
            body: formData,
            credentials: 'same-origin'
        }).then(response => {
            if (!response.ok) {
                console.log('Online status update failed:', response.status);
            }
        }).catch(error => {
            console.log('Online status error (non-critical):', error);
        });
    }

    // Store function globally
    window.updateOnlineStatus = updateOnlineStatus;

    console.log('CSRF Fix: Initialization complete');
})();