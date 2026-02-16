async function fetchWithAuth(url, options = {}) {
    // Include credentials (cookies) for session authentication
    const fetchOptions = {
        ...options,
        credentials: 'include',
        headers: {
            'Content-Type': 'application/json',
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


async function loadAdminUser() {
    try {
        const response = await fetchWithAuth('/api/system/admins');
        
        if (!response.ok) {
            throw new Error(`Failed to load admin users: ${response.status}`);
        }
        
        const adminUsers = await response.json();
        adminUsersCache = adminUsers;
        
        return adminUsers;
    } catch (error) {
        console.error('Error loading admin users:', error);
        alert('Error loading admin users: ' + error.message);
    }
}