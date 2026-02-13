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
        const response = await fetch(`/api/admin/login`, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'), // 🔥 QO‘SHILDI
            },
            body: JSON.stringify({ username, password })
        });
        const data = await response.json();
        
        if (response.ok) {
            return {
                success: true,
                message: 'Login successful'
            };
        } else {
            console.log('Login failed:', data);
            return {
                success: false,
                message: data.detail || 'Invalid credentials'
            };
        }
    } catch (error) {
        console.error('Login error:', error, response );
        return {
            success: false,
            message: 'Network error. Please try again.'
        };
    }
}

async function adminLogout() {
    try {
        
        await fetch(`/api/admin/logout`, {
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

    // Login sahifada tekshirmaymiz
    if (window.location.pathname.startsWith('/login')) {
        return true;
    }

    try {
        const isAuthenticated = await checkAuthStatus();

        if (!isAuthenticated) {
            window.location.replace('/login');
            return false;
        }

        return true;

    } catch (error) {
        console.error('Session validation error:', error);
        window.location.replace('/login');
        return false;
    }
}



