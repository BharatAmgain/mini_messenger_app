// CSRF Token Fix for Django
(function() {
    // Set global csrftoken variable
    window.csrftoken = null;

    // Function to get CSRF token from cookies
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.startsWith(name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Get CSRF token
    window.csrftoken = getCookie('csrftoken');

    // Ensure AJAX requests include CSRF token
    if (window.csrftoken) {
        // Store for jQuery if available
        if (typeof jQuery !== 'undefined') {
            $.ajaxSetup({
                headers: {
                    'X-CSRFToken': window.csrftoken
                }
            });
        }

        // Setup fetch to include CSRF token
        const originalFetch = window.fetch;
        window.fetch = function(url, options = {}) {
            const newOptions = { ...options };

            if (!newOptions.headers) {
                newOptions.headers = {};
            }

            // Add CSRF token for same-origin requests
            if (url.startsWith('/') || url.startsWith(window.location.origin)) {
                newOptions.headers['X-CSRFToken'] = window.csrftoken;
            }

            // Ensure credentials are included
            newOptions.credentials = 'same-origin';

            return originalFetch(url, newOptions);
        };

        // Setup XMLHttpRequest to include CSRF token
        const originalXHROpen = XMLHttpRequest.prototype.open;
        XMLHttpRequest.prototype.open = function(method, url) {
            originalXHROpen.apply(this, arguments);

            // Add CSRF token for same-origin requests
            if (url.startsWith('/') || url.startsWith(window.location.origin)) {
                this.addEventListener('readystatechange', function() {
                    if (this.readyState === 1 && window.csrftoken) {
                        this.setRequestHeader('X-CSRFToken', window.csrftoken);
                    }
                });
            }
        };
    }

    console.log('CSRF token fix loaded');
})();