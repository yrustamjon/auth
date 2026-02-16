// ========================================
// ORGANIZATIONS PAGE
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

function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('en-US', options);
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

// Render organizations
async function renderOrganizations() {
    const container = document.getElementById('page-content');
    if (!container) return;
    
    const organizations = await fetchOrganizations();
    
    const organizationsHTML = organizations.map(org => `
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
    `).join('');
    
    container.innerHTML = `
        <div class="fade-in">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2>Organizations</h2>
                <button class="btn btn-primary" onclick="openCreateOrgModal()">
                    <i class="fas fa-plus me-2"></i>Create Organization
                </button>
            </div>
            
            <div class="search-bar">
                <i class="fas fa-search"></i>
                <input type="text" class="form-control" placeholder="Search organizations..." id="orgSearch" onkeyup="filterOrganizations()">
            </div>
            
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
                            ${organizationsHTML}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;
}

// Filter organizations
window.filterOrganizations = function() {
    const searchTerm = document.getElementById('orgSearch')?.value.toLowerCase() || '';
    const rows = document.querySelectorAll('#orgsTable tbody tr');
    
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(searchTerm) ? '' : 'none';
    });
};

// Create organization modal
window.openCreateOrgModal = function() {
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
};

// Create organization
window.createOrganization = function() {
    const name = document.getElementById('orgName').value;
    const slug = document.getElementById('orgSlug').value;
    const active = document.getElementById('orgActive').checked;
    
    if (!name || !slug) {
        showToast('Please fill all fields', 'danger');
        return;
    }
    
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
        
        const modal = bootstrap.Modal.getInstance(document.getElementById('createOrgModal'));
        modal.hide();
        
        showToast('Organization created successfully');
        renderOrganizations();
    }, 500);
};

// Edit organization
window.editOrganization = function(id) {
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
};

// Update organization
window.updateOrganization = function() {
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
    renderOrganizations();
};

// Toggle organization status
window.toggleOrgStatus = function(id) {
    const org = DummyData.organizations.find(o => o.id === id);
    if (!org) return;
    
    const action = org.active ? 'disable' : 'enable';
    
    showConfirmation(
        `${action === 'disable' ? 'Disable' : 'Enable'} Organization`,
        `Are you sure you want to ${action} ${org.name}?`,
        () => {
            org.active = !org.active;
            showToast(`Organization ${action}d successfully`);
            renderOrganizations();
        }
    );
};

// Delete organization
window.deleteOrganization = function(id) {
    const org = DummyData.organizations.find(o => o.id === id);
    if (!org) return;
    
    showConfirmation(
        'Delete Organization',
        `Are you sure you want to delete ${org.name}? This action cannot be undone.`,
        () => {
            const index = DummyData.organizations.findIndex(o => o.id === id);
            DummyData.organizations.splice(index, 1);
            showToast('Organization deleted successfully');
            renderOrganizations();
        }
    );
};

// View organization
window.viewOrganization = function(id) {
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
    
    const adminsHTML = orgAdmins.length > 0 ? orgAdmins.map(admin => `
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
    `).join('') : '<tr><td colspan="5" class="text-center">No admins found</td></tr>';
    
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
                                <button class="btn btn-sm btn-primary" onclick="openCreateAdminModal(${org.id})">
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
                                ${adminsHTML}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
};
window.openCreateAdminModal = function(orgId = null) {
    const modalId = 'createAdminModal';
    let modal = document.getElementById(modalId);
    const org = DummyData.organizations.find(o => o.id === orgId);
    
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
                            <select class="form-select" disabled>
                                <option value="${org.id}">${org.name}</option>
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
                    <button type="button" class="btn btn-primary" onclick="createAdmin(${orgId})">Create</button>
                </div>
            </div>
        </div>
    `;
    
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
};

window.createAdmin = function(orgId) {
    const username = document.getElementById('adminUsername').value;
    
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
    
    // Render organizations
    renderOrganizations();
});

// Logout function (qisqartirilgan)
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