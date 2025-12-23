// static/js/csrf_fix.js - FIXED VERSION
(function() {
    console.log('CSRF fix loaded...');

    // Function to get cookie by name
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Does this cookie string begin with the name we want?
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
    console.log('CSRF Token found:', csrftoken ? 'Yes' : 'No');

    // Store globally for access
    window.csrftoken = csrftoken;

    // Setup AJAX requests
    if (csrftoken) {
        // For jQuery
        if (typeof jQuery !== 'undefined') {
            $.ajaxSetup({
                beforeSend: function(xhr, settings) {
                    if (!this.crossDomain) {
                        xhr.setRequestHeader("X-CSRFToken", csrftoken);
                    }
                }
            });
        }

        // For fetch API
        const originalFetch = window.fetch;
        window.fetch = function(...args) {
            const [url, options = {}] = args;

            // Only add CSRF token for same-origin requests
            const isSameOrigin = new URL(url, window.location.origin).origin === window.location.origin;

            if (isSameOrigin && ['POST', 'PUT', 'PATCH', 'DELETE'].includes((options.method || 'GET').toUpperCase())) {
                options.headers = {
                    ...options.headers,
                    'X-CSRFToken': csrftoken
                };
                options.credentials = 'same-origin';
            }

            return originalFetch(url, options);
        };

        console.log('CSRF protection enabled for AJAX requests');
    } else {
        console.warn('CSRF token not found in cookies');
    }
})();