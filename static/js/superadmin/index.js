/**
 * System Admin Control Center
 * Multi-Tenant Security System
 * Super Admin Panel
 * Version: 2.0.0
 */

// ========================================
// GLOBAL STATE & CONFIGURATION
// ========================================
const AppState = {
    currentPage: 'dashboard',
    organizations: [],
    admins: [],
    loading: false,
    filters: {
        organizations: '',
        admins: ''
    }
};

// ========================================
// DUMMY DATA (API SIMULATION)
// ========================================
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
    ],
    
    adminLogins: [
        { username: 'john.doe', organization: 'TechCorp Solutions', loginTime: '2024-03-10 14:30:00', status: 'success' },
        { username: 'sarah.johnson', organization: 'HealthCare Plus', loginTime: '2024-03-10 11:20:00', status: 'success' },
        { username: 'jane.smith', organization: 'Global Security Inc', loginTime: '2024-03-09 09:15:00', status: 'locked' },
        { username: 'mike.wilson', organization: 'FinSecure Bank', loginTime: '2024-03-08 16:45:00', status: 'success' },
        { username: 'robert.brown', organization: 'EduTech Systems', loginTime: '2024-03-07 10:00:00', status: 'failed' }
    ],
    
    recentOrganizations: [
        { name: 'EduTech Systems', createdBy: 'john.doe', date: '2024-02-15' },
        { name: 'HealthCare Plus', createdBy: 'sarah.johnson', date: '2024-02-10' },
        { name: 'FinSecure Bank', createdBy: 'mike.wilson', date: '2024-02-01' }
    ]
};

// ========================================
// UTILITY FUNCTIONS
// ========================================

/**
 * Show loading spinner
 */
function showLoading() {
    AppState.loading = true;
    let spinner = document.querySelector('.spinner-overlay');
    if (!spinner) {
        spinner = document.createElement('div');
        spinner.className = 'spinner-overlay';
        spinner.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
        document.body.appendChild(spinner);
    }
    spinner.style.display = 'flex';
}

/**
 * Hide loading spinner
 */
function hideLoading() {
    AppState.loading = false;
    const spinner = document.querySelector('.spinner-overlay');
    if (spinner) {
        spinner.style.display = 'none';
    }
}

/**
 * Show toast notification
 */
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

/**
 * Show confirmation modal
 */
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

/**
 * Format date
 */
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('en-US', options);
}

// ========================================
// API SIMULATION FUNCTIONS
// ========================================

/**
 * Simulate API call
 */
async function simulateAPI(data, delay = 500) {
    showLoading();
    return new Promise((resolve) => {
        setTimeout(() => {
            hideLoading();
            resolve(data);
        }, delay);
    });
}

/**
 * Fetch organizations
 */
async function fetchOrganizations() {
    return await simulateAPI(DummyData.organizations);
}

/**
 * Fetch admins
 */
async function fetchAdmins() {
    return await simulateAPI(DummyData.admins);
}

// ========================================
// RENDERING FUNCTIONS
// ========================================

/**
 * Render dashboard page
 */
async function renderDashboard() {
    const content = document.getElementById('page-content');
    
    const organizations = await fetchOrganizations();
    const admins = await fetchAdmins();
    
    const stats = {
        totalOrgs: organizations.length,
        totalAdmins: admins.length,
        activeAdmins: admins.filter(a => !a.locked).length,
        lockedAdmins: admins.filter(a => a.locked).length
    };
    
    content.innerHTML = `
        <div class="fade-in">
            <h2 class="mb-4">Dashboard</h2>
            
            <!-- Stats Cards -->
            <div class="row g-4 mb-4">
                <div class="col-xl-3 col-md-6">
                    <div class="stat-card">
                        <div class="icon primary">
                            <i class="fas fa-building"></i>
                        </div>
                        <h3>${stats.totalOrgs}</h3>
                        <p>Total Organizations</p>
                    </div>
                </div>
                <div class="col-xl-3 col-md-6">
                    <div class="stat-card">
                        <div class="icon success">
                            <i class="fas fa-user-shield"></i>
                        </div>
                        <h3>${stats.totalAdmins}</h3>
                        <p>Total Admins</p>
                    </div>
                </div>
                <div class="col-xl-3 col-md-6">
                    <div class="stat-card">
                        <div class="icon info">
                            <i class="fas fa-user-check"></i>
                        </div>
                        <h3>${stats.activeAdmins}</h3>
                        <p>Active Admins</p>
                    </div>
                </div>
                <div class="col-xl-3 col-md-6">
                    <div class="stat-card">
                        <div class="icon warning">
                            <i class="fas fa-user-lock"></i>
                        </div>
                        <h3>${stats.lockedAdmins}</h3>
                        <p>Locked Admins</p>
                    </div>
                </div>
            </div>
            
            <!-- Tables -->
            <div class="row">
                <div class="col-lg-6">
                    <div class="table-container">
                        <h5><i class="fas fa-history me-2"></i>Latest Admin Logins</h5>
                        <div class="table-responsive">
                            <table class="table">
                                <thead>
                                    <tr>
                                        <th>Username</th>
                                        <th>Organization</th>
                                        <th>Login Time</th>
                                        <th>Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${DummyData.adminLogins.map(login => `
                                        <tr>
                                            <td><strong>${login.username}</strong></td>
                                            <td>${login.organization}</td>
                                            <td>${login.loginTime}</td>
                                            <td>
                                                <span class="badge bg-${login.status === 'success' ? 'success' : login.status === 'locked' ? 'danger' : 'warning'}">
                                                    ${login.status}
                                                </span>
                                            </td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
                
                <div class="col-lg-6">
                    <div class="table-container">
                        <h5><i class="fas fa-clock me-2"></i>Recently Created Organizations</h5>
                        <div class="table-responsive">
                            <table class="table">
                                <thead>
                                    <tr>
                                        <th>Organization</th>
                                        <th>Created By</th>
                                        <th>Date</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${DummyData.recentOrganizations.map(org => `
                                        <tr>
                                            <td><strong>${org.name}</strong></td>
                                            <td>${org.createdBy}</td>
                                            <td>${formatDate(org.date)}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Render organizations page
 */
async function renderOrganizations() {
    const content = document.getElementById('page-content');
    const organizations = await fetchOrganizations();
    
    content.innerHTML = `
        <div class="fade-in">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2>Organizations</h2>
                <button class="btn btn-primary" onclick="openCreateOrgModal()">
                    <i class="fas fa-plus me-2"></i>Create Organization
                </button>
            </div>
            
            <!-- Search Bar -->
            <div class="search-bar">
                <i class="fas fa-search"></i>
                <input type="text" class="form-control" placeholder="Search organizations..." id="orgSearch" onkeyup="filterOrganizations()">
            </div>
            
            <!-- Organizations Table -->
            <div class="table-container">
                <div class="table-responsive">
                    <table class="table" id="orgsTable">
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Slug</th>
                                <th>Status</th>
                                <th>Admin Count</th>
                                <th>Created Date</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${organizations.map(org => `
                                <tr data-org-id="${org.id}">
                                    <td><strong>${org.name}</strong></td>
                                    <td><code>${org.slug}</code></td>
                                    <td>
                                        <span class="badge bg-${org.active ? 'success' : 'danger'}">
                                            ${org.active ? 'Active' : 'Inactive'}
                                        </span>
                                    </td>
                                    <td><span class="badge bg-info">${org.adminCount}</span></td>
                                    <td>${formatDate(org.createdDate)}</td>
                                    <td>
                                        <button class="btn btn-sm btn-outline-primary btn-action" onclick="viewOrganization(${org.id})" title="View">
                                            <i class="fas fa-eye"></i>
                                        </button>
                                        <button class="btn btn-sm btn-outline-warning btn-action" onclick="editOrganization(${org.id})" title="Edit">
                                            <i class="fas fa-edit"></i>
                                        </button>
                                        <button class="btn btn-sm btn-outline-${org.active ? 'danger' : 'success'} btn-action" onclick="toggleOrgStatus(${org.id})" title="${org.active ? 'Disable' : 'Enable'}">
                                            <i class="fas fa-${org.active ? 'ban' : 'check'}"></i>
                                        </button>
                                        <button class="btn btn-sm btn-outline-danger btn-action" onclick="deleteOrganization(${org.id})" title="Delete">
                                            <i class="fas fa-trash"></i>
                                        </button>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
}

/**
 * Render admins page
 */
async function renderAdmins() {
    const content = document.getElementById('page-content');
    const admins = await fetchAdmins();
    
    content.innerHTML = `
        <div class="fade-in">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2>Admin Users</h2>
                <button class="btn btn-primary" onclick="openCreateAdminModal()">
                    <i class="fas fa-plus me-2"></i>Create Admin
                </button>
            </div>
            
            <!-- Search Bar -->
            <div class="search-bar">
                <i class="fas fa-search"></i>
                <input type="text" class="form-control" placeholder="Search admins..." id="adminSearch" onkeyup="filterAdmins()">
            </div>
            
            <!-- Admins Table -->
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
                            ${admins.map(admin => `
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
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
}

// ========================================
// FILTER FUNCTIONS
// ========================================

function filterOrganizations() {
    const searchTerm = document.getElementById('orgSearch').value.toLowerCase();
    const rows = document.querySelectorAll('#orgsTable tbody tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm) ? '' : 'none';
    });
}

function filterAdmins() {
    const searchTerm = document.getElementById('adminSearch').value.toLowerCase();
    const rows = document.querySelectorAll('#adminsTable tbody tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm) ? '' : 'none';
    });
}

// ========================================
// MODAL FUNCTIONS - ORGANIZATIONS
// ========================================

function openCreateOrgModal() {
    const modalId = 'createOrgModal';
    let modal = document.getElementById(modalId);
    
    if (!modal) {
        modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = modalId;
        modal.setAttribute('tabindex', '-1');
        
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Create New Organization</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="createOrgForm">
                            <div class="mb-3">
                                <label class="form-label">Organization Name</label>
                                <input type="text" class="form-control" id="orgName" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Slug</label>
                                <input type="text" class="form-control" id="orgSlug" required>
                            </div>
                            <div class="mb-3">
                                <div class="form-check form-switch">
                                    <input class="form-check-input" type="checkbox" id="orgActive" checked>
                                    <label class="form-check-label">Active</label>
                                </div>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" onclick="createOrganization()">Create</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
    }
    
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

function createOrganization() {
    const name = document.getElementById('orgName').value;
    const slug = document.getElementById('orgSlug').value;
    const active = document.getElementById('orgActive').checked;
    
    if (!name || !slug) {
        showToast('Please fill all fields', 'danger');
        return;
    }
    
    // Simulate API call
    setTimeout(() => {
        const newOrg = {
            id: DummyData.organizations.length + 1,
            name: name,
            slug: slug,
            active: active,
            adminCount: 0,
            createdDate: new Date().toISOString().split('T')[0]
        };
        
        DummyData.organizations.push(newOrg);
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('createOrgModal'));
        modal.hide();
        
        showToast('Organization created successfully');
        
        // Refresh page if on organizations
        if (AppState.currentPage === 'organizations') {
            renderOrganizations();
        }
    }, 500);
}

function editOrganization(id) {
    const org = DummyData.organizations.find(o => o.id === id);
    if (!org) return;
    
    const modalId = 'editOrgModal';
    let modal = document.getElementById(modalId);
    
    if (!modal) {
        modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.id = modalId;
        modal.setAttribute('tabindex', '-1');
        
        document.body.appendChild(modal);
    }
    
    modal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Edit Organization</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <form id="editOrgForm">
                        <input type="hidden" id="editOrgId" value="${org.id}">
                        <div class="mb-3">
                            <label class="form-label">Organization Name</label>
                            <input type="text" class="form-control" id="editOrgName" value="${org.name}" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Slug</label>
                            <input type="text" class="form-control" id="editOrgSlug" value="${org.slug}" required>
                        </div>
                        <div class="mb-3">
                            <div class="form-check form-switch">
                                <input class="form-check-input" type="checkbox" id="editOrgActive" ${org.active ? 'checked' : ''}>
                                <label class="form-check-label">Active</label>
                            </div>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="button" class="btn btn-primary" onclick="updateOrganization()">Save Changes</button>
                </div>
            </div>
        </div>
    `;
    
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

function updateOrganization() {
    const id = parseInt(document.getElementById('editOrgId').value);
    const name = document.getElementById('editOrgName').value;
    const slug = document.getElementById('editOrgSlug').value;
    const active = document.getElementById('editOrgActive').checked;
    
    const orgIndex = DummyData.organizations.findIndex(o => o.id === id);
    if (orgIndex === -1) return;
    
    DummyData.organizations[orgIndex] = {
        ...DummyData.organizations[orgIndex],
        name,
        slug,
        active
    };
    
    const modal = bootstrap.Modal.getInstance(document.getElementById('editOrgModal'));
    modal.hide();
    
    showToast('Organization updated successfully');
    
    if (AppState.currentPage === 'organizations') {
        renderOrganizations();
    }
}

function toggleOrgStatus(id) {
    const org = DummyData.organizations.find(o => o.id === id);
    if (!org) return;
    
    const action = org.active ? 'disable' : 'enable';
    
    showConfirmation(
        `${action === 'disable' ? 'Disable' : 'Enable'} Organization`,
        `Are you sure you want to ${action} ${org.name}?`,
        () => {
            org.active = !org.active;
            showToast(`Organization ${action}d successfully`);
            
            if (AppState.currentPage === 'organizations') {
                renderOrganizations();
            }
        }
    );
}

function deleteOrganization(id) {
    const org = DummyData.organizations.find(o => o.id === id);
    if (!org) return;
    
    showConfirmation(
        'Delete Organization',
        `Are you sure you want to delete ${org.name}? This action cannot be undone.`,
        () => {
            const index = DummyData.organizations.findIndex(o => o.id === id);
            DummyData.organizations.splice(index, 1);
            
            showToast('Organization deleted successfully');
            
            if (AppState.currentPage === 'organizations') {
                renderOrganizations();
            }
        }
    );
}

function viewOrganization(id) {
    const org = DummyData.organizations.find(o => o.id === id);
    if (!org) return;
    
    const orgAdmins = DummyData.admins.filter(a => a.orgId === id);
    
    const modalId = 'viewOrgModal';
    let modal = document.getElementById(modalId);
    
    if (!modal) {
        modal = document.createElement('div');
        modal.className = 'modal fade modal-xl';
        modal.id = modalId;
        modal.setAttribute('tabindex', '-1');
        
        document.body.appendChild(modal);
    }
    
    modal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Organization Details: ${org.name}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="row mb-4">
                        <div class="col-md-6">
                            <h6>Organization Information</h6>
                            <table class="table table-borderless">
                                <tr>
                                    <td><strong>Name:</strong></td>
                                    <td>${org.name}</td>
                                </tr>
                                <tr>
                                    <td><strong>Slug:</strong></td>
                                    <td><code>${org.slug}</code></td>
                                </tr>
                                <tr>
                                    <td><strong>Status:</strong></td>
                                    <td><span class="badge bg-${org.active ? 'success' : 'danger'}">${org.active ? 'Active' : 'Inactive'}</span></td>
                                </tr>
                                <tr>
                                    <td><strong>Created Date:</strong></td>
                                    <td>${formatDate(org.createdDate)}</td>
                                </tr>
                            </table>
                        </div>
                        <div class="col-md-6">
                            <div class="d-flex justify-content-between align-items-center">
                                <h6>Admins in this Organization</h6>
                                <button class="btn btn-sm btn-primary" onclick="createAdminForOrg(${org.id})">
                                    <i class="fas fa-plus"></i> Add Admin
                                </button>
                            </div>
                        </div>
                    </div>
                    
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>Username</th>
                                    <th>SuperAdmin</th>
                                    <th>Status</th>
                                    <th>Failed Attempts</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${orgAdmins.length > 0 ? orgAdmins.map(admin => `
                                    <tr>
                                        <td><strong>${admin.username}</strong></td>
                                        <td><span class="badge bg-${admin.superAdmin ? 'warning' : 'secondary'}">${admin.superAdmin ? 'Yes' : 'No'}</span></td>
                                        <td><span class="badge bg-${admin.locked ? 'danger' : 'success'}">${admin.locked ? 'Locked' : 'Active'}</span></td>
                                        <td><span class="badge bg-${admin.failedAttempts > 3 ? 'danger' : 'warning'}">${admin.failedAttempts}</span></td>
                                        <td>
                                            <button class="btn btn-sm btn-outline-danger" onclick="deleteAdmin(${admin.id})">
                                                <i class="fas fa-trash"></i>
                                            </button>
                                        </td>
                                    </tr>
                                `).join('') : '<tr><td colspan="5" class="text-center">No admins found</td></tr>'}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

// ========================================
// MODAL FUNCTIONS - ADMINS
// ========================================

function openCreateAdminModal(orgId = null) {
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
}

function createAdminForOrg(orgId) {
    openCreateAdminModal(orgId);
    
    // Close the view modal if open
    const viewModal = bootstrap.Modal.getInstance(document.getElementById('viewOrgModal'));
    if (viewModal) {
        viewModal.hide();
    }
}

function createAdmin() {
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
    
    // Update organization admin count
    org.adminCount++;
    
    const modal = bootstrap.Modal.getInstance(document.getElementById('createAdminModal'));
    modal.hide();
    
    showToast('Admin created successfully');
    
    if (AppState.currentPage === 'admins') {
        renderAdmins();
    }
}

function toggleAdminLock(id) {
    const admin = DummyData.admins.find(a => a.id === id);
    if (!admin) return;
    
    const action = admin.locked ? 'unlock' : 'lock';
    
    showConfirmation(
        `${action === 'lock' ? 'Lock' : 'Unlock'} Admin`,
        `Are you sure you want to ${action} ${admin.username}?`,
        () => {
            admin.locked = !admin.locked;
            showToast(`Admin ${action}ed successfully`);
            
            if (AppState.currentPage === 'admins') {
                renderAdmins();
            }
        }
    );
}

function resetAttempts(id) {
    const admin = DummyData.admins.find(a => a.id === id);
    if (!admin) return;
    
    showConfirmation(
        'Reset Failed Attempts',
        `Reset failed login attempts for ${admin.username}?`,
        () => {
            admin.failedAttempts = 0;
            showToast('Failed attempts reset successfully');
            
            if (AppState.currentPage === 'admins') {
                renderAdmins();
            }
        }
    );
}

function changeOrg(id) {
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
}

function updateAdminOrg() {
    const adminId = parseInt(document.getElementById('changeAdminId').value);
    const newOrgId = parseInt(document.getElementById('newOrgId').value);
    
    const admin = DummyData.admins.find(a => a.id === adminId);
    const oldOrg = DummyData.organizations.find(o => o.id === admin.orgId);
    const newOrg = DummyData.organizations.find(o => o.id === newOrgId);
    
    if (!admin || !newOrg) return;
    
    // Update counts
    oldOrg.adminCount--;
    newOrg.adminCount++;
    
    // Update admin
    admin.orgId = newOrgId;
    admin.organization = newOrg.name;
    
    const modal = bootstrap.Modal.getInstance(document.getElementById('changeOrgModal'));
    modal.hide();
    
    showToast(`Organization changed to ${newOrg.name}`);
    
    if (AppState.currentPage === 'admins') {
        renderAdmins();
    }
}

function forceLogout(id) {
    const admin = DummyData.admins.find(a => a.id === id);
    if (!admin) return;
    
    showConfirmation(
        'Force Logout',
        `Force logout ${admin.username} from all sessions?`,
        () => {
            showToast(`${admin.username} has been logged out`);
        }
    );
}

function deleteAdmin(id) {
    const admin = DummyData.admins.find(a => a.id === id);
    if (!admin) return;
    
    showConfirmation(
        'Delete Admin',
        `Are you sure you want to delete ${admin.username}? This action cannot be undone.`,
        () => {
            // Update organization count
            const org = DummyData.organizations.find(o => o.id === admin.orgId);
            if (org) {
                org.adminCount--;
            }
            
            // Remove admin
            const index = DummyData.admins.findIndex(a => a.id === id);
            DummyData.admins.splice(index, 1);
            
            showToast('Admin deleted successfully');
            
            if (AppState.currentPage === 'admins') {
                renderAdmins();
            }
        }
    );
}

// ========================================
// PAGE NAVIGATION
// ========================================

async function navigateTo(page) {
    AppState.currentPage = page;
    
    // Update active menu
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.dataset.page === page) {
            link.classList.add('active');
        }
    });
    
    // Render page
    switch(page) {
        case 'dashboard':
            await renderDashboard();
            break;
        case 'organizations':
            await renderOrganizations();
            break;
        case 'admins':
            await renderAdmins();
            break;
    }
}

// ========================================
// LOGOUT
// ========================================

async function System_Logout() {
    try {
        await fetch(`/api/system/logout`, {
            method: 'POST',
            credentials: 'include',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
            }
        });
    } catch (error) {
        console.error('Logout error:', error);
        return
    }

    sessionStorage.removeItem('isAuthenticated');
    localStorage.removeItem('isAuthenticated');
}




async function logout() {
    showConfirmation(
        'Logout',
        'Are you sure you want to logout?',
         async () => {
            try {   
                await System_Logout();
            } catch (error) {
                console.error('Logout failed:', error);
                showToast('Logout failed. Please try again.', 'danger');
            }
            showToast('Logged out successfully');
            window.location.href = '/system/login/';
        }
    );
}

// ========================================
// INITIALIZATION
// ========================================

document.addEventListener('DOMContentLoaded', () => {
    // Sidebar toggle
    document.getElementById('sidebarCollapse').addEventListener('click', () => {
        document.getElementById('sidebar').classList.toggle('active');
    });
    
    // Navigation
    document.querySelectorAll('.nav-link[data-page]').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = e.currentTarget.dataset.page;
            navigateTo(page);
        });
    });
    
    // Logout buttons
    document.getElementById('logoutBtn').addEventListener('click', async (e) => {
        e.preventDefault();
        await logout();
    });
    

    
    // Load dashboard by default
    navigateTo('dashboard');
});