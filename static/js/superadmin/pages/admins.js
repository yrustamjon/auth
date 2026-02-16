// ========================================
// ADMINS PAGE
// ========================================

// Global state
const AppState = {
    organizations: [],
    admins: []
};

// Dummy data
const DummyData = {
    organizations: [
        { id: 1, name: 'TechCorp Solutions', slug: 'techcorp', active: true, adminCount: 5, createdDate: '2024-01-15' },
        { id: 2, name: 'Global Security Inc', slug: 'globalsec', active: true, adminCount: 3, createdDate: '2024-01-20' },
        { id: 3, name: 'FinSecure Bank', slug: 'finsecure', active: false, adminCount: 2, createdDate: '2024-02-01' },
        { id: 4, name: 'HealthCare Plus', slug: 'healthcare', active: true, adminCount: 4, createdDate: '2024-02-10' },
        { id: 5, name: 'EduTech Systems', slug: 'edutech', active: true, adminCount: 6, createdDate: '2024-02-15' }
    ],
    
    admins: [
        { id: 1, username: 'john.doe', organization: 'TechCorp Solutions', orgId: 1, superAdmin: true, locked: false, failedAttempts: 0, lastLogin: '2024-03-10 14:30' },
        { id: 2, username: 'jane.smith', organization: 'Global Security Inc', orgId: 2, superAdmin: false, locked: true, failedAttempts: 5, lastLogin: '2024-03-09 09:15' },
        { id: 3, username: 'mike.wilson', organization: 'FinSecure Bank', orgId: 3, superAdmin: false, locked: false, failedAttempts: 2, lastLogin: '2024-03-08 16:45' },
        { id: 4, username: 'sarah.johnson', organization: 'HealthCare Plus', orgId: 4, superAdmin: true, locked: false, failedAttempts: 0, lastLogin: '2024-03-10 11:20' },
        { id: 5, username: 'robert.brown', organization: 'EduTech Systems', orgId: 5, superAdmin: false, locked: false, failedAttempts: 1, lastLogin: '2024-03-07 10:00' }
    ]
};

// Utility functions
function showLoading() {
    let spinner = document.querySelector('.spinner-overlay');
    if (!spinner) {
        spinner = document.createElement('div');
        spinner.className = 'spinner-overlay';
        spinner.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
        document.body.appendChild(spinner);
    }
    spinner.style.display = 'flex';
}

function hideLoading() {
    const spinner = document.querySelector('.spinner-overlay');
    if (spinner) {
        spinner.style.display = 'none';
    }
}

function showToast(message, type = 'success') {
    const toastContainer = document.querySelector('.toast-container');
    const toastId = 'toast-' + Date.now();
    
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.id = toastId;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="toast-header bg-${type} text-white">
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} me-2"></i>
            <strong class="me-auto">${type === 'success' ? 'Success' : 'Error'}</strong>
            <small>just now</small>
            <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
        </div>
        <div class="toast-body">
            ${message}
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast, { autohide: true, delay: 3000 });
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

// API functions
async function simulateAPI(data, delay = 500) {
    showLoading();
    return new Promise((resolve) => {
        setTimeout(() => {
            hideLoading();
            resolve(data);
        }, delay);
    });
}

async function fetchAdmins() {
    return await simulateAPI(DummyData.admins);
}

async function fetchOrganizations() {
    return await simulateAPI(DummyData.organizations);
}

// Confirmation modal
function showConfirmation(title, message, onConfirm) {
    const modalId = 'confirmModal-' + Date.now();
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.id = modalId;
    modal.setAttribute('tabindex', '-1');
    
    modal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">${title}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p>${message}</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-danger" id="confirmBtn">Confirm</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    document.getElementById('confirmBtn').addEventListener('click', () => {
        bsModal.hide();
        onConfirm();
        modal.addEventListener('hidden.bs.modal', () => {
            modal.remove();
        });
    });
    
    modal.addEventListener('hidden.bs.modal', () => {
        modal.remove();
    });
}

// Render admins
async function renderAdmins() {
    const container = document.getElementById('page-content');
    if (!container) return;
    
    const admins = await fetchAdmins();
    
    const adminsHTML = admins.map(admin => `
        <tr data-admin-id="${admin.id}">
            <td><strong>${admin.username}</strong></td>
            <td>${admin.organization}</td>
            <td>
                <span class="badge bg-${admin.superAdmin ? 'warning' : 'secondary'}">
                    ${admin.superAdmin ? 'Yes' : 'No'}
                </span>
            </td>
            <td>
                <span class="badge bg-${admin.locked ? 'danger' : 'success'}">
                    ${admin.locked ? 'Locked' : 'Active'}
                </span>
            </td>
            <td>
                <span class="badge bg-${admin.failedAttempts > 3 ? 'danger' : admin.failedAttempts > 0 ? 'warning' : 'success'}">
                    ${admin.failedAttempts}
                </span>
            </td>
            <td>
                <button class="btn btn-sm btn-outline-${admin.locked ? 'success' : 'danger'} btn-action" onclick="toggleAdminLock(${admin.id})" title="${admin.locked ? 'Unlock' : 'Lock'}">
                    <i class="fas fa-${admin.locked ? 'lock-open' : 'lock'}"></i>
                </button>
                <button class="btn btn-sm btn-outline-warning btn-action" onclick="resetAttempts(${admin.id})" title="Reset Attempts">
                    <i class="fas fa-rotate-left"></i>
                </button>
                <button class="btn btn-sm btn-outline-primary btn-action" onclick="changeOrg(${admin.id})" title="Change Organization">
                    <i class="fas fa-building"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger btn-action" onclick="forceLogout(${admin.id})" title="Force Logout">
                    <i class="fas fa-sign-out-alt"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger btn-action" onclick="deleteAdmin(${admin.id})" title="Delete">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
    
    container.innerHTML = `
        <div class="fade-in">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2>Admin Users</h2>
                <button class="btn btn-primary" onclick="openCreateAdminModal()">
                    <i class="fas fa-plus me-2"></i>Create Admin
                </button>
            </div>
            
            <div class="search-bar">
                <i class="fas fa-search"></i>
                <input type="text" class="form-control" placeholder="Search admins..." id="adminSearch" onkeyup="filterAdmins()">
            </div>
            
            <div class="table-container">
                <div class="table-responsive">
                    <table class="table" id="adminsTable">
                        <thead>
                            <tr>
                                <th>Username</th>
                                <th>Organization</th>
                                <th>SuperAdmin</th>
                                <th>Status</th>
                                <th>Failed Attempts</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${adminsHTML}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
}

// Filter admins
window.filterAdmins = function() {
    const searchTerm = document.getElementById('adminSearch')?.value.toLowerCase() || '';
    const rows = document.querySelectorAll('#adminsTable tbody tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm) ? '' : 'none';
    });
};

// Create admin modal
window.openCreateAdminModal = function(orgId = null) {
    const modalId = 'createAdminModal';
    let modal = document.getElementById(modalId);
    
    if (!modal) {
        modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = modalId;
        modal.setAttribute('tabindex', '-1');
        document.body.appendChild(modal);
    }
    
    const orgOptions = DummyData.organizations.map(org => 
        `<option value="${org.id}" ${orgId === org.id ? 'selected' : ''}>${org.name}</option>`
    ).join('');
    
    modal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Create New Admin</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <form id="createAdminForm">
                        <div class="mb-3">
                            <label class="form-label">Username</label>
                            <input type="text" class="form-control" id="adminUsername" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Organization</label>
                            <select class="form-select" id="adminOrg">
                                ${orgOptions}
                            </select>
                        </div>
                        <div class="mb-3">
                            <div class="form-check form-switch">
                                <input class="form-check-input" type="checkbox" id="adminSuperAdmin">
                                <label class="form-check-label">Super Admin</label>
                            </div>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-primary" onclick="createAdmin()">Create</button>
                </div>
            </div>
        </div>
    `;
    
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
};

// Create admin
window.createAdmin = function() {
    const username = document.getElementById('adminUsername').value;
    const orgId = parseInt(document.getElementById('adminOrg').value);
    const superAdmin = document.getElementById('adminSuperAdmin').checked;
    
    if (!username || !orgId) {
        showToast('Please fill all fields', 'danger');
        return;
    }
    
    const org = DummyData.organizations.find(o => o.id === orgId);
    
    const newAdmin = {
        id: DummyData.admins.length + 1,
        username: username,
        organization: org.name,
        orgId: orgId,
        superAdmin: superAdmin,
        locked: false,
        failedAttempts: 0,
        lastLogin: null
    };
    
    DummyData.admins.push(newAdmin);
    org.adminCount++;
    
    const modal = bootstrap.Modal.getInstance(document.getElementById('createAdminModal'));
    modal.hide();
    
    showToast('Admin created successfully');
    renderAdmins();
};

// Toggle admin lock
window.toggleAdminLock = function(id) {
    const admin = DummyData.admins.find(a => a.id === id);
    if (!admin) return;
    
    const action = admin.locked ? 'unlock' : 'lock';
    
    showConfirmation(
        `${action === 'lock' ? 'Lock' : 'Unlock'} Admin`,
        `Are you sure you want to ${action} ${admin.username}?`,
        () => {
            admin.locked = !admin.locked;
            showToast(`Admin ${action}ed successfully`);
            renderAdmins();
        }
    );
};

// Reset attempts
window.resetAttempts = function(id) {
    const admin = DummyData.admins.find(a => a.id === id);
    if (!admin) return;
    
    showConfirmation(
        'Reset Failed Attempts',
        `Reset failed login attempts for ${admin.username}?`,
        () => {
            admin.failedAttempts = 0;
            showToast('Failed attempts reset successfully');
            renderAdmins();
        }
    );
};

// Change organization
window.changeOrg = function(id) {
    const admin = DummyData.admins.find(a => a.id === id);
    if (!admin) return;
    
    const modalId = 'changeOrgModal';
    let modal = document.getElementById(modalId);
    
    if (!modal) {
        modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = modalId;
        modal.setAttribute('tabindex', '-1');
        document.body.appendChild(modal);
    }
    
    const orgOptions = DummyData.organizations.map(org => 
        `<option value="${org.id}" ${org.id === admin.orgId ? 'selected' : ''}>${org.name}</option>`
    ).join('');
    
    modal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Change Organization for ${admin.username}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <form id="changeOrgForm">
                        <input type="hidden" id="changeAdminId" value="${admin.id}">
                        <div class="mb-3">
                            <label class="form-label">Select New Organization</label>
                            <select class="form-select" id="newOrgId">
                                ${orgOptions}
                            </select>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-primary" onclick="updateAdminOrg()">Update</button>
                </div>
            </div>
        </div>
    `;
    
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
};

// Update admin organization
window.updateAdminOrg = function() {
    const adminId = parseInt(document.getElementById('changeAdminId').value);
    const newOrgId = parseInt(document.getElementById('newOrgId').value);
    
    const admin = DummyData.admins.find(a => a.id === adminId);
    const oldOrg = DummyData.organizations.find(o => o.id === admin.orgId);
    const newOrg = DummyData.organizations.find(o => o.id === newOrgId);
    
    if (!admin || !newOrg) return;
    
    oldOrg.adminCount--;
    newOrg.adminCount++;
    
    admin.orgId = newOrgId;
    admin.organization = newOrg.name;
    
    const modal = bootstrap.Modal.getInstance(document.getElementById('changeOrgModal'));
    modal.hide();
    
    showToast(`Organization changed to ${newOrg.name}`);
    renderAdmins();
};

// Force logout
window.forceLogout = function(id) {
    const admin = DummyData.admins.find(a => a.id === id);
    if (!admin) return;
    
    showConfirmation(
        'Force Logout',
        `Force logout ${admin.username} from all sessions?`,
        () => {
            showToast(`${admin.username} has been logged out`);
        }
    );
};

// Delete admin
window.deleteAdmin = function(id) {
    const admin = DummyData.admins.find(a => a.id === id);
    if (!admin) return;
    
    showConfirmation(
        'Delete Admin',
        `Are you sure you want to delete ${admin.username}? This action cannot be undone.`,
        () => {
            const org = DummyData.organizations.find(o => o.id === admin.orgId);
            if (org) {
                org.adminCount--;
            }
            
            const index = DummyData.admins.findIndex(a => a.id === id);
            DummyData.admins.splice(index, 1);
            
            showToast('Admin deleted successfully');
            renderAdmins();
        }
    );
};

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Sidebar toggle
    const sidebarCollapse = document.getElementById('sidebarCollapse');
    if (sidebarCollapse) {
        sidebarCollapse.addEventListener('click', () => {
            document.getElementById('sidebar').classList.toggle('active');
        });
    }
    
    // Logout button
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            await logout();
        });
    }
    
    // Render admins
    renderAdmins();
});

// Logout function
async function logout() {
    showConfirmation(
        'Logout',
        'Are you sure you want to logout?',
        async () => {
            showToast('Logged out successfully');
            window.location.href = '/system/login/';
        }
    );
}