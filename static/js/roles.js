/**
 * roles.js
 * Global cache — faqat shu yerda e'lon qilinadi
 */

// Global state — boshqa fayllarda qayta e'lon qilinmaydi
var rolesCache = [];
var usersCache = [];

// ─── Load ─────────────────────────────────────────────────────────

async function loadRoles() {
    try {
        const response = await fetchWithAuth('/api/roles');
        if (!response.ok) throw new Error(`${response.status}`);

        const data = await response.json();
        rolesCache = Array.isArray(data) ? data : (data.roles ?? []);

        // Faqat #rolesTable mavjud sahifada ko'rsatamiz
        if (document.querySelector('#rolesTable tbody')) {
            displayRoles(rolesCache);
        }

    } catch (error) {
        console.error('Error loading roles:', error);
        showToast('Rollarni yuklashda xato: ' + error.message, 'error');
    }
}

// ─── Display ──────────────────────────────────────────────────────

function displayRoles(roles) {
    const tbody = document.querySelector('#rolesTable tbody');
    if (!tbody) return;

    tbody.innerHTML = '';

    if (roles.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="empty-msg">Rollar topilmadi.</td></tr>`;
        return;
    }

    roles.forEach(role => {
        const row = document.createElement('tr');
        if (!role.is_active) row.classList.add('inactive-row');

        const idCell = document.createElement('td');
        idCell.textContent = role.id;

        const nameCell = document.createElement('td');
        nameCell.textContent = role.name;

        const statusCell = document.createElement('td');
        const badge = document.createElement('span');
        badge.className = role.is_active ? 'badge badge-active' : 'badge badge-inactive';
        badge.textContent = role.is_active ? 'Active' : 'Inactive';
        statusCell.appendChild(badge);

        const dateCell = document.createElement('td');
        dateCell.textContent = role.created_at
            ? new Date(role.created_at).toLocaleDateString()
            : 'N/A';

        const actionsCell = document.createElement('td');
        actionsCell.className = 'actions';

        const editBtn = document.createElement('button');
        editBtn.className = 'btn-warning btn-sm';
        editBtn.innerHTML = '<i class="fas fa-edit"></i>';
        editBtn.title = 'Tahrirlash';
        editBtn.addEventListener('click', () => openEditModal(role));

        const toggleBtn = document.createElement('button');
        toggleBtn.className = role.is_active ? 'btn-secondary btn-sm' : 'btn-success btn-sm';
        toggleBtn.innerHTML = role.is_active ? '<i class="fas fa-ban"></i>' : '<i class="fas fa-check"></i>';
        toggleBtn.title = role.is_active ? 'Deactivate' : 'Activate';
        toggleBtn.addEventListener('click', () => toggleRoleStatus(role));

        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'btn-danger btn-sm';
        deleteBtn.innerHTML = '<i class="fas fa-trash"></i>';
        deleteBtn.title = "O'chirish";
        deleteBtn.addEventListener('click', () => deleteRole(role.id));

        actionsCell.append(editBtn, toggleBtn, deleteBtn);
        row.append(idCell, nameCell, statusCell, dateCell, actionsCell);
        tbody.appendChild(row);
    });
}

// ─── Create ───────────────────────────────────────────────────────

async function createRole(roleData) {
    try {
        const response = await fetchWithAuth('/api/roles', {
            method: 'POST',
            body: JSON.stringify(roleData)
        });
        if (!response.ok) throw new Error(`${response.status}`);

        showToast('Rol yaratildi!', 'success');
        await loadRoles();
        return await response.json();
    } catch (error) {
        console.error('Error creating role:', error);
        throw error;
    }
}

// ─── Update ───────────────────────────────────────────────────────

async function updateRole(roleId, roleData) {
    try {
        const response = await fetchWithAuth(`/api/roles/${roleId}`, {
            method: 'PATCH',
            body: JSON.stringify(roleData)
        });
        if (!response.ok) throw new Error(`${response.status}`);

        showToast('Rol yangilandi!', 'success');
        await loadRoles();
    } catch (error) {
        console.error('Error updating role:', error);
        throw error;
    }
}

// ─── Toggle ───────────────────────────────────────────────────────

async function toggleRoleStatus(role) {
    if (!confirm(`Rolni ${role.is_active ? "o'chirishni" : 'aktivlashtirishni'} tasdiqlaysizmi?`)) return;

    try {
        const response = await fetchWithAuth(`/api/roles/${role.id}`, {
            method: 'PATCH',
            body: JSON.stringify({ is_active: !role.is_active })
        });
        if (!response.ok) throw new Error(`${response.status}`);

        showToast(`Rol ${role.is_active ? 'deaktivlandi' : 'aktivlandi'}!`, 'success');
        await loadRoles();
    } catch (error) {
        showToast("Holatni o'zgartirishda xato: " + error.message, 'error');
    }
}

// ─── Delete ───────────────────────────────────────────────────────

async function deleteRole(roleId) {
    if (!confirm("Bu rolni o'chirishni tasdiqlaysizmi?")) return;

    try {
        const response = await fetchWithAuth(`/api/roles/${roleId}`, {
            method: 'DELETE'
        });
        if (!response.ok) throw new Error(`${response.status}`);

        showToast("Rol o'chirildi!", 'success');
        await loadRoles();
        if (typeof loadUsers === 'function') await loadUsers();
    } catch (error) {
        showToast("O'chirishda xato: " + error.message, 'error');
    }
}

// ─── Edit Modal ───────────────────────────────────────────────────

function openEditModal(role) {
    const modal = document.getElementById('editRoleModal');
    if (!modal) return;
    document.getElementById('editRoleId').value = role.id;
    document.getElementById('editRoleName').value = role.name;
    modal.style.display = 'flex';
}

// ─── Toast ────────────────────────────────────────────────────────

function showToast(message, type = 'success') {
    const existing = document.getElementById('toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.id = 'toast';
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => toast.classList.add('show'), 10);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}