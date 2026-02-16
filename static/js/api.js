/**
 * API wrapper with session cookie support
 * Handles authentication and error handling
 */

// Base API URL (configure this based on your backend)

const API_BASE_URL = "http://127.0.0.1:8000";



/**
 * Wrapper for fetch with authentication
 * @param {string} url - API endpoint
 * @param {Object} options - Fetch options
 * @returns {Promise<Response>}
 */
async function fetchWithAuth(url, options = {}) {
    // Include credentials (cookies) for session authentication
    const fetchOptions = {
        ...options,
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
            ...options.headers
        }
    };
    
    const response = await fetch(`${API_BASE_URL}${url}`, fetchOptions);
    
    // Handle 401 Unauthorized - redirect to login
    if (response.status === 401) {
        // Clear any cached session data
        sessionStorage.removeItem('isAuthenticated');
        localStorage.removeItem('isAuthenticated');
        

        window.location.href = '/login/';

        throw new Error('Session expired. Please login again.');
    }
    
    return response;
}

/**
 * Check if user is authenticated
 * @returns {Promise<boolean>}
 */
async function checkAuthStatus() {
    try {
        // Try to fetch a protected endpoint
        const response = await fetchWithAuth('/api/users');
        return response.ok;
    } catch (error) {
        return false;
    }
}

/**
 * Format error message from API response
 * @param {Error|Response} error - Error object or Response
 * @returns {string}
 */
function formatErrorMessage(error) {
    if (error instanceof Response) {
        return `HTTP ${error.status}: ${error.statusText}`;
    }
    if (error.message) {
        return error.message;
    }
    return 'An unknown error occurred';
}




