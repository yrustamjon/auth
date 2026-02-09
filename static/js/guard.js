/**
 * Page protection guard (Django compatible)
 */

// Protected Django paths
const PROTECTED_PATHS = [
    '/dashboard/',
    '/users/',
    '/roles/',
    '/devices/',
    '/logs/'
];



/**
 * Check auth via DRF
 */
/**
 * Page guard
 */
async function checkSession() {
    const path = window.location.pathname;

    // Login page
   
    // Protected pages
    if (PROTECTED_PATHS.includes(path)) {
        const isValid = await validateSession();
        if (!isValid) {
            window.location.href = `${LOGIN_PATH}?next=${path}`;
        }
    }
}

/**
 * Intercept fetch → auto logout on 401
 */
(function () {
    const originalFetch = window.fetch;

    window.fetch = function (...args) {
        return originalFetch.apply(this, args).then(response => {
            if (response.status === 401) {
                window.location.href = LOGIN_PATH;
            }
            return response;
        });
    };
})();

// Init guard
document.addEventListener('DOMContentLoaded', checkSession);


