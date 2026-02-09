/**
 * Role management functions
 * Handles CRUD operations for roles and user-role assignments
 */

let rolesCache = [];
let userRolesCache = [];
let usersCache = [];

/**
 * Load all roles and display in table
 */
async function loadRoles() {
    try {
        const response = await fetchWithAuth('/api/roles');
        
        if (!response.ok) {
            throw new Error(`Failed to load roles: ${response.status}`);
        }
        
        const roles = await response.json();
        rolesCache = roles;
        
        displayRoles(roles);
    } catch (error) {
        console.error('Error loading roles:', error);
        alert('Error loading roles: ' + error.message);
    }
}

/**
 * Display roles in the table
 * @param {Array} roles - Array of role objects
 */
function displayRoles(roles) {
    const tbody = document.querySelector('#rolesTable tbody');
    tbody.innerHTML = '';
    
    roles.forEach(role => {
        const row = document.createElement('tr');
        
        row.innerHTML = `
            <td>${role.id}</td>
            <td>${role.name}</td>
            <td>${new Date(role.created_at || Date.now()).toLocaleDateString()}</td>
            <td class="actions">
                <button class="btn-danger btn-sm" onclick="deleteRole(${role.id})">
                    <i class="fas fa-trash"></i> Delete
                </button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

/**
 * Load all users for role assignment dropdown
 */
async function loadUsersForAssignment() {
    try {
        const response = await fetchWithAuth('/api/users');
        
        if (response.ok) {
            usersCache = await response.json();
            
            const select = document.getElementById('assignUser');
            select.innerHTML = '<option value="">Select user...</option>';
            
            usersCache.forEach(user => {
                const option = document.createElement('option');
                option.value = user.id;
                option.textContent = `${user.fio} (${user.lavozim})`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading users for assignment:', error);
    }
}

/**
 * Load all roles for role assignment dropdown
 */
async function loadRolesForAssignment() {
    try {
        const response = await fetchWithAuth('/api/roles');
        
        if (response.ok) {
            const roles = await response.json();
            
            const select = document.getElementById('assignRole');
            select.innerHTML = '<option value="">Select role...</option>';
            
            roles.forEach(role => {
                const option = document.createElement('option');
                option.value = role.id;
                option.textContent = role.name;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading roles for assignment:', error);
    }
}

/**
 * Load user-role assignments
 */
async function loadUserRoles() {
    try {
        // Note: This endpoint might need to be implemented
        // For now, we'll create a mock or fetch from /api/user-roles if available
        const response = await fetchWithAuth('/api/user-roles');
        
        if (response.ok) {
            userRolesCache = await response.json();
            displayUserRoles(userRolesCache);
        }
    } catch (error) {
        console.error('Error loading user roles:', error);
        // If endpoint doesn't exist, we'll show an empty table
        displayUserRoles([]);
    }
}

/**
 * Display user-role assignments in table
 * @param {Array} assignments - Array of user-role assignment objects
 */
function displayUserRoles(assignments) {
    const tbody = document.querySelector('#userRolesTable tbody');
    tbody.innerHTML = '';
    
    if (assignments.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td colspan="5" style="text-align: center; padding: 2rem;">
                No role assignments found. Click "Add Role" button to assign roles to users.
            </td>
        `;
        tbody.appendChild(row);
        return;
    }
    
    assignments.forEach(assignment => {
        const row = document.createElement('tr');
        
        // Find user and role names
        const user = usersCache.find(u => u.id === assignment.user_id);
        const role = rolesCache.find(r => r.id === assignment.role_id);
        
        row.innerHTML = `
            <td>${assignment.id}</td>
            <td>${user ? user.fio : 'Unknown User'}</td>
            <td>${role ? role.name : 'Unknown Role'}</td>
            <td>${new Date(assignment.assigned_at || Date.now()).toLocaleString()}</td>
            <td class="actions">
                <button class="btn-danger btn-sm" onclick="removeRoleAssignment(${assignment.id})">
                    <i class="fas fa-times"></i> Remove
                </button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

/**
 * Create a new role
 * @param {Object} roleData - Role data {name}
 */
async function createRole(roleData) {
    try {
        const response = await fetchWithAuth('/api/roles', {
            method: 'POST',
            body: JSON.stringify(roleData)
        });
        
        if (!response.ok) {
            throw new Error(`Failed to create role: ${response.status}`);
        }
        
        alert('Role created successfully!');
        return await response.json();
    } catch (error) {
        console.error('Error creating role:', error);
        throw error;
    }
}

/**
 * Delete a role
 * @param {number} roleId - Role ID to delete
 */
async function deleteRole(roleId) {
    if (!confirm('Are you sure you want to delete this role? This may affect user permissions.')) {
        return;
    }
    
    try {
        const response = await fetchWithAuth(`/api/roles/${roleId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error(`Failed to delete role: ${response.status}`);
        }
        
        alert('Role deleted successfully!');
        loadRoles();
        loadUserRoles();
    } catch (error) {
        console.error('Error deleting role:', error);
        alert('Error deleting role: ' + error.message);
    }
}

/**
 * Assign role to user
 * @param {Object} assignmentData - {user_id, role_id}
 */
async function assignRoleToUser(assignmentData) {
    try {
        const response = await fetchWithAuth('/api/user-roles', {
            method: 'POST',
            body: JSON.stringify(assignmentData)
        });
        
        if (!response.ok) {
            throw new Error(`Failed to assign role: ${response.status}`);
        }
        
        alert('Role assigned successfully!');
        return await response.json();
    } catch (error) {
        console.error('Error assigning role:', error);
        throw error;
    }
}

/**
 * Remove role assignment
 * @param {number} assignmentId - Assignment ID to remove
 */
async function removeRoleAssignment(assignmentId) {
    if (!confirm('Are you sure you want to remove this role assignment?')) {
        return;
    }
    
    try {
        const response = await fetchWithAuth(`/api/user-roles/${assignmentId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error(`Failed to remove role assignment: ${response.status}`);
        }
        
        alert('Role assignment removed successfully!');
        loadUserRoles();
    } catch (error) {
        console.error('Error removing role assignment:', error);
        alert('Error removing role assignment: ' + error.message);
    }
}