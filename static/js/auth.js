/**
 * Authentication functions for admin panel
 * Handles login, logout, and session management
 */

/**
 * Admin login function
 * @param {string} username - Admin username
 * @param {string} password - Admin password
 * @returns {Promise<Object>} - Login response
 */


function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.slice(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

async function adminLogin(username, password) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/admin/login`, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'), // 🔥 QO‘SHILDI
            },
            body: JSON.stringify({ username, password })
        });
        
        if (response.ok) {
            return {
                success: true,
                message: 'Login successful'
            };
        } else {
            return {
                success: false,
                message: 'Invalid credentials'
            };
        }
    } catch (error) {
        console.error('Login error:', error);
        return {
            success: false,
            message: 'Network error. Please try again.'
        };
    }
}

async function adminLogout() {
    try {
        await fetch(`${API_BASE_URL}/api/admin/logout`, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'), // 🔥 QO‘SHILDI
            }
        });
    } catch (error) {
        console.error('Logout error:', error);
    } finally {
        sessionStorage.removeItem('isAuthenticated');
        localStorage.removeItem('isAuthenticated');
        window.location.href = '/login/';
    }
}



/**
 * Validate session on page load
 * Redirects to login if not authenticated
 */
async function validateSession() {
    const currentPage = window.location.pathname.split('/').pop();
    
    // Don't validate on login page
    if (currentPage === '/login' || currentPage === '') {
        return;
    }
    
    try {
        const isAuthenticated = await checkAuthStatus();
        
        if (!isAuthenticated) {
            // Redirect to login page
            window.location.href = '/login';
            return false;
        }
        
        return true;
    } catch (error) {
        console.error('Session validation error:', error);
        window.location.href = '/login';
        return false;
    }
}


