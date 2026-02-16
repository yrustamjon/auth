

/**
 * Load all users and display in table
 */
async function loadUsers() {
    try {
        const response = await fetchWithAuth('/api/users');
        
        if (!response.ok) {
            throw new Error(`Failed to load users: ${response.status}`);
        }
        const data = await response.json(); 
        usersCache = data.users;  
        displayUsers(data.users);  
    } catch (error) {
        alert('Error loading users: ' + error.message);
    }
}

/**
 * Display users in the table
 * @param {Array} users - Array of user objects
 */
function displayUsers(users) {
    const tbody = document.querySelector('#usersTable tbody');
    tbody.innerHTML = '';
    if (users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center">No users found.</td></tr>';
        return;
    }
    
    users.forEach(user => {
        const row = document.createElement('tr');
        
        // Get user roles
        const userRoles = getUserRoles(user.id);
        
        row.innerHTML = `
            <td>${user.id}</td>
            <td>${user.fio}</td>
            <td>${user.lavozim}</td>
            <td>
                <span class="${user.status ? 'status-active' : 'status-inactive'}">
                    ${user.status ? 'Active' : 'Inactive'}
                </span>
            </td>
            <td>${userRoles.join(', ') || 'No roles'}</td>
            <td class="actions">
                <button class="btn-primary btn-sm" onclick="editUser(${user.id})">
                    <i class="fas fa-edit"></i> Edit
                </button>
                <button class="btn-danger btn-sm" onclick="deleteUser(${user.id})">
                    <i class="fas fa-trash"></i> Delete
                </button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

/**
 * Get roles assigned to a user
 * @param {number} userId - User ID
 * @returns {Array} - Array of role names
 */
function getUserRoles(userId) {
    // This would ideally come from the API
    // For now, we'll implement it when we have user-roles data
    return [];
}

/**
 * Create a new user
 * @param {Object} userData - User data {fio, lavozim, status}
 */
async function createUser(userData) {
    try {
        console.log('Creating user with data:', userData);
        const response = await fetchWithAuth('/api/users', {
            method: 'POST',
            body: JSON.stringify(userData)
        });
        
        if (!response.ok) {
            throw new Error(`Failed to create user: ${response.status}`);
        }
        
        alert('User created successfully!');
        return await response.json();
    } catch (error) {
        console.error('Error creating user:', error);
        throw error;
    }
}

/**
 * Update an existing user
 * @param {number} userId - User ID
 * @param {Object} userData - Updated user data
 */
async function updateUser(userId, userData) {
    try {
        const response = await fetchWithAuth(`/api/users/${userId}`, {
            method: 'PUT',
            body: JSON.stringify(userData)
        });
        
        if (!response.ok) {
            throw new Error(`Failed to update user: ${response.status}`);
        }
        
        alert('User updated successfully!');
        return await response.json();
    } catch (error) {
        console.error('Error updating user:', error);
        throw error;
    }
}

/**
 * Delete a user
 * @param {number} userId - User ID to delete
 */
async function deleteUser(userId) {
    if (!confirm('Are you sure you want to delete this user?')) {
        return;
    }
    
    try {
        const response = await fetchWithAuth(`/api/users/${userId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error(`Failed to delete user: ${response.status}`);
        }
        
        alert('User deleted successfully!');
        loadUsers();
    } catch (error) {
        console.error('Error deleting user:', error);
        alert('Error deleting user: ' + error.message);
    }
}

/**
 * Edit user - populate modal with user data
 * @param {number} userId - User ID to edit
 */
async function editUser(userId) {
    try {
        const user = usersCache.find(u => u.id === userId);
        
        if (!user) {
            // Fetch user if not in cache
            const response = await fetchWithAuth(`/api/users/${userId}`);
            if (!response.ok) {
                throw new Error('User not found');
            }
            user = await response.json();
        }
        
        // Populate modal
        document.getElementById('modalTitle').textContent = 'Edit User';
        document.getElementById('userId').value = user.id;
        document.getElementById('fio').value = user.fio;
        document.getElementById('lavozim').value = user.lavozim;
        document.getElementById('status').checked = user.status;
        
        // Show modal
        document.getElementById('userModal').style.display = 'flex';
    } catch (error) {
        console.error('Error loading user for edit:', error);
        alert('Error loading user data: ' + error.message);
    }
}