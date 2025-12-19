// static/js/csrf_fix.js - Global CSRF fix for all AJAX requests

// Get CSRF token from various sources
function getCSRFToken() {
    // Try cookies first
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith('csrftoken=')) {
                cookieValue = decodeURIComponent(cookie.substring('csrftoken='.length));
                break;
            }
        }
    }

    // Try meta tag
    if (!cookieValue) {
        const metaToken = document.querySelector('meta[name="csrf-token"]');
        if (metaToken) {
            cookieValue = metaToken.getAttribute('content');
        }
    }

    // Try hidden input
    if (!cookieValue) {
        const inputToken = document.querySelector('input[name="csrfmiddlewaretoken"]');
        if (inputToken) {
            cookieValue = inputToken.value;
        }
    }

    return cookieValue;
}

// Override fetch to automatically include CSRF token
(function() {
    const originalFetch = window.fetch;
    window.fetch = function(url, options = {}) {
        const csrfToken = getCSRFToken();
        const method = options.method ? options.method.toUpperCase() : 'GET';

        if (csrfToken && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
            // Ensure headers exist
            options.headers = options.headers || {};

            // Add CSRF token
            options.headers['X-CSRFToken'] = csrfToken;

            // Set credentials
            options.credentials = 'same-origin';

            // If body is FormData, also append token
            if (options.body instanceof FormData) {
                options.body.append('csrfmiddlewaretoken', csrfToken);
            }
        }

        return originalFetch.call(this, url, options);
    };
})();

// Override XMLHttpRequest to include CSRF token
(function() {
    const originalOpen = XMLHttpRequest.prototype.open;
    const originalSend = XMLHttpRequest.prototype.send;

    XMLHttpRequest.prototype.open = function(method, url, async, user, password) {
        this._method = method.toUpperCase();
        return originalOpen.apply(this, arguments);
    };

    XMLHttpRequest.prototype.send = function(body) {
        const csrfToken = getCSRFToken();
        if (csrfToken && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(this._method)) {
            this.setRequestHeader('X-CSRFToken', csrfToken);

            // Also add to FormData if applicable
            if (body instanceof FormData) {
                body.append('csrfmiddlewaretoken', csrfToken);
            }
        }
        return originalSend.apply(this, arguments);
    };
})();