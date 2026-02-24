/**
 * users.js
 * rolesCache va usersCache — roles.js dan keladi (var bilan e'lon qilingan)
 * Bu faylda qayta e'lon qilinmaydi
 */

// ─── Load & Display ───────────────────────────────────────────────

async function loadUsers() {
    try {
        const response = await fetchWithAuth('/api/users');
        if (!response.ok) throw new Error(`${response.status}`);

        const data = await response.json();
        usersCache = Array.isArray(data) ? data : (data.users ?? []);
        displayUsers(usersCache);
    } catch (error) {
        console.error('Error loading users:', error);
        showToast('Foydalanuvchilarni yuklashda xato: ' + error.message, 'error');
    }
}

function displayUsers(users) {
    const tbody = document.querySelector('#usersTable tbody');
    if (!tbody) return;

    tbody.innerHTML = '';

    if (users.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="empty-msg">Foydalanuvchilar topilmadi.</td></tr>`;
        return;
    }

    users.forEach(user => {
        const row = document.createElement('tr');
        if (!user.status) row.classList.add('inactive-row');

        const role = rolesCache.find(r => r.id === (user.role ?? user.role_id));

        const idCell = document.createElement('td');
        idCell.textContent = user.id;

        const fioCell = document.createElement('td');
        fioCell.textContent = user.fio;

        const lavozimCell = document.createElement('td');
        lavozimCell.textContent = user.lavozim;

        const usernameCell = document.createElement('td');
        usernameCell.textContent = user.username;

        const roleCell = document.createElement('td');
        roleCell.textContent = role ? role.name : '—';

        const statusCell = document.createElement('td');
        const badge = document.createElement('span');
        badge.className = user.status ? 'badge badge-active' : 'badge badge-inactive';
        badge.textContent = user.status ? 'Active' : 'Inactive';
        statusCell.appendChild(badge);

        const actionsCell = document.createElement('td');
        actionsCell.className = 'actions';

        const editBtn = document.createElement('button');
        editBtn.className = 'btn-warning btn-sm';
        editBtn.innerHTML = '<i class="fas fa-edit"></i>';
        editBtn.title = 'Tahrirlash';
        editBtn.addEventListener('click', () => openUserModal(user));

        const toggleBtn = document.createElement('button');
        toggleBtn.className = user.status ? 'btn-secondary btn-sm' : 'btn-success btn-sm';
        toggleBtn.innerHTML = user.status ? '<i class="fas fa-ban"></i>' : '<i class="fas fa-check"></i>';
        toggleBtn.title = user.status ? 'Deactivate' : 'Activate';
        toggleBtn.addEventListener('click', () => toggleUserStatus(user));

        const deleteBtn = document.createElement('button');
        deleteBtn.className = 'btn-danger btn-sm';
        deleteBtn.innerHTML = '<i class="fas fa-trash"></i>';
        deleteBtn.title = "O'chirish";
        deleteBtn.addEventListener('click', () => deleteUser(user.id));

        actionsCell.append(editBtn, toggleBtn, deleteBtn);
        row.append(idCell, fioCell, lavozimCell, usernameCell, roleCell, statusCell, actionsCell);
        tbody.appendChild(row);
    });
}

// ─── Modal ────────────────────────────────────────────────────────

function openUserModal(user = null) {
    const isEdit = !!user;

    document.getElementById('modalTitle').textContent = isEdit ? 'Foydalanuvchini Tahrirlash' : 'Yangi Foydalanuvchi';
    document.getElementById('userId').value   = isEdit ? user.id : '';
    document.getElementById('fio').value      = isEdit ? user.fio : '';
    document.getElementById('lavozim').value  = isEdit ? user.lavozim : '';
    document.getElementById('username').value = isEdit ? user.username : '';
    document.getElementById('status').checked = isEdit ? user.status : true;
    populateRoleSelect(isEdit ? (user.role ?? user.role_id) : null);

    document.getElementById('userModal').style.display = 'flex';
}

function populateRoleSelect(selectedRoleId = null) {
    const select = document.getElementById('roleSelect');
    select.innerHTML = '<option value="">— Rol tanlang —</option>';

    rolesCache
        .filter(r => r.is_active !== false)
        .forEach(role => {
            const option = document.createElement('option');
            option.value = role.id;
            option.textContent = role.name;
            if (role.id === selectedRoleId) option.selected = true;
            select.appendChild(option);
        });
}

// ─── CRUD ─────────────────────────────────────────────────────────

async function createUser(userData) {
    try {
        const response = await fetchWithAuth('/api/users', {
            method: 'POST',
            body: JSON.stringify(userData)
        });
        if (!response.ok) throw new Error(`${response.status}`);

        showToast('Foydalanuvchi yaratildi!', 'success');
        await loadUsers();
        return await response.json();
    } catch (error) {
        console.error('Error creating user:', error);
        throw error;
    }
}

async function updateUser(userId, userData) {
    try {
        const response = await fetchWithAuth(`/api/users/${userId}`, {
            method: 'PATCH',
            body: JSON.stringify(userData)
        });
        if (!response.ok) throw new Error(`${response.status}`);

        showToast('Foydalanuvchi yangilandi!', 'success');
        await loadUsers();
        return await response.json();
    } catch (error) {
        console.error('Error updating user:', error);
        throw error;
    }
}

async function toggleUserStatus(user) {
    if (!confirm(`Foydalanuvchini ${user.status ? "o'chirishni" : 'aktivlashtirishni'} tasdiqlaysizmi?`)) return;

    try {
        const response = await fetchWithAuth(`/api/users/${user.id}`, {
            method: 'PATCH',
            body: JSON.stringify({ status: !user.status })
        });
        if (!response.ok) throw new Error(`${response.status}`);

        showToast(`Foydalanuvchi ${user.status ? 'deaktivlandi' : 'aktivlandi'}!`, 'success');
        await loadUsers();
    } catch (error) {
        showToast("Holatni o'zgartirishda xato: " + error.message, 'error');
    }
}

async function deleteUser(userId) {
    if (!confirm("Foydalanuvchini o'chirishni tasdiqlaysizmi?")) return;

    try {
        const response = await fetchWithAuth(`/api/users/${userId}`, {
            method: 'DELETE'
        });
        if (!response.ok) throw new Error(`${response.status}`);

        showToast("Foydalanuvchi o'chirildi!", 'success');
        await loadUsers();
    } catch (error) {
        showToast("O'chirishda xato: " + error.message, 'error');
    }
}