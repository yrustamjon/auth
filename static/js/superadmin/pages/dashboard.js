// ========================================
// DASHBOARD PAGE
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

async function fetchAdmins() {
    return await simulateAPI(DummyData.admins);
}

// Logout functions
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
        return;
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

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

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

// Render dashboard
async function renderDashboard() {
    const container = document.getElementById('page-content');
    if (!container) return;
    
    const organizations = await fetchOrganizations();
    const admins = await fetchAdmins();
    
    const stats = {
        totalOrgs: organizations.length,
        totalAdmins: admins.length,
        activeAdmins: admins.filter(a => !a.locked).length,
        lockedAdmins: admins.filter(a => a.locked).length
    };
    
    const adminLoginsHTML = DummyData.adminLogins.map(login => `
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
    `).join('');
    
    const recentOrgsHTML = DummyData.recentOrganizations.map(org => `
        <tr>
            <td><strong>${org.name}</strong></td>
            <td>${org.createdBy}</td>
            <td>${formatDate(org.date)}</td>
        </tr>
    `).join('');
    
    container.innerHTML = `
        <div class="fade-in">
            <h2 class="mb-4">Dashboard</h2>
            
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
                                    ${adminLoginsHTML}
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
                                    ${recentOrgsHTML}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

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
    
    // Render dashboard
    renderDashboard();
});