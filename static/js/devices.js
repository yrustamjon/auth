/**
 * Device management functions
 * Fields: id, pc_id, location, is_active, revoked, last_seen, registered_at, device_public_key
 */



// ── Load ───────────────────────────────────────────────────────
async function loadDevices() {
    const tbody = document.querySelector('#devicesTable tbody');
    tbody.innerHTML = `
        <tr class="loading-row">
            <td colspan="9">
                <div class="loading-spinner">
                    <i class="fas fa-circle-notch fa-spin"></i> Loading devices...
                </div>
            </td>
        </tr>`;

    try {
        const res = await fetchWithAuth('/api/devices');
        if (!res.ok) throw new Error(`Failed to load devices: ${res.status}`);
        devicesCache = await res.json();
        filterDevices();
    } catch (err) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="empty-state error-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Xatolik: ${err.message}</p>
                </td>
            </tr>`;
    }
}

// ── Filter ─────────────────────────────────────────────────────
function filterDevices() {
    const q       = (document.getElementById('deviceSearch').value || '').toLowerCase().trim();
    const statVal = document.getElementById('statusFilter').value;
    const revVal  = document.getElementById('revokedFilter').value;

    const filtered = devicesCache.filter(d => {
        const matchQ = !q ||
            (d.pc_id    || '').toLowerCase().includes(q) ||
            (d.location || '').toLowerCase().includes(q);
        const matchS = !statVal ||
            (statVal === 'active'   &&  d.is_active) ||
            (statVal === 'inactive' && !d.is_active);
        const matchR = !revVal ||
            (revVal === 'revoked'   &&  d.revoked) ||
            (revVal === 'ok'        && !d.revoked);
        return matchQ && matchS && matchR;
    });

    displayDevices(filtered, q);

    const rc = document.getElementById('deviceResultCount');
    if (filtered.length === devicesCache.length) {
        rc.textContent = `${devicesCache.length} ta`;
        rc.style.color = '#6b7280';
    } else {
        rc.textContent = `${filtered.length} / ${devicesCache.length} ta natija`;
        rc.style.color = filtered.length === 0 ? '#dc2626' : '#6b7280';
    }
}

function highlight(text, q) {
    if (!q || !text) return String(text || '');
    const esc = q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    return String(text).replace(new RegExp(esc, 'gi'), m => `<mark>${m}</mark>`);
}

// ── Display ────────────────────────────────────────────────────
function displayDevices(devices, q = '') {
    const tbody = document.querySelector('#devicesTable tbody');
    tbody.innerHTML = '';

    if (!devices || devices.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="empty-state">
                    <i class="fas fa-desktop"></i>
                    <p>Qurilmalar topilmadi.</p>
                </td>
            </tr>`;
        return;
    }

    devices.forEach(device => {
        const row = document.createElement('tr');

        const registeredAt = device.registered_at
            ? new Date(device.registered_at).toLocaleDateString('uz-UZ', { day: '2-digit', month: 'short', year: 'numeric' })
            : '<span class="text-muted">—</span>';

        const lastSeen = device.last_seen
            ? new Date(device.last_seen).toLocaleString('uz-UZ', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
            : '<span class="text-muted">Hech qachon</span>';

        const did = device.id;
        const activeBtn = device.is_active
            ? `<button class="toggle-btn toggle-active" onclick="toggleDeviceField(${did}, 'is_active', false)" title="O'chirish">
                   <i class="fas fa-check-circle"></i> Active
               </button>`
            : `<button class="toggle-btn toggle-inactive" onclick="toggleDeviceField(${did}, 'is_active', true)" title="Yoqish">
                   <i class="fas fa-times-circle"></i> Inactive
               </button>`;

        const revokedBtn = device.revoked
            ? `<button class="toggle-btn toggle-revoked" onclick="toggleDeviceField(${did}, 'revoked', false)" title="Tiklash">
                   <i class="fas fa-ban"></i> Revoked
               </button>`
            : `<button class="toggle-btn toggle-ok" onclick="toggleDeviceField(${did}, 'revoked', true)" title="Bloklash">
                   <i class="fas fa-shield-alt"></i> OK
               </button>`;

        row.innerHTML = `
            <td class="col-id">${device.id}</td>
            <td class="col-pcid"><strong>${highlight(device.pc_id, q)}</strong></td>
            <td>
                <i class="fas fa-map-marker-alt location-icon"></i>
                ${highlight(device.location, q)}
            </td>
            <td>${activeBtn}</td>
            <td>${revokedBtn}</td>
            <td>${lastSeen}</td>
            <td>${registeredAt}</td>
            <td class="actions">
                <button class="btn-action btn-edit" onclick="editDevice(${did})">
                    <i class="fas fa-edit"></i> Edit
                </button>
                <button class="btn-action btn-delete" onclick="deleteDevice(${did})">
                    <i class="fas fa-trash"></i> Delete
                </button>
            </td>`;

        tbody.appendChild(row);
    });
}

// ── Toggle field (is_active yoki revoked) ─────────────────────
async function toggleDeviceField(deviceId, field, value) {
    try {
        const res = await fetchWithAuth(`/api/devices/${deviceId}/`, {
            method: 'PATCH',
            body: JSON.stringify({ [field]: value })
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || `Failed: ${res.status}`);
        }

        const cached = devicesCache.find(d => d.id === deviceId);
        if (cached) cached[field] = value;

        const label = field === 'is_active' ? 'Status' : 'Revoked holati';
        showToast(`${label} yangilandi!`, 'success');
        filterDevices();
    } catch (err) {
        showToast('Xatolik: ' + err.message, 'error');
    }
}

// ── Create ─────────────────────────────────────────────────────
async function createDevice(data) {
    const res = await fetchWithAuth('/api/devices', { method: 'POST', body: JSON.stringify(data) });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Failed: ${res.status}`);
    }
    showToast("Qurilma qo'shildi!", 'success');
    return await res.json();
}

// ── Update ─────────────────────────────────────────────────────
async function updateDevice(deviceId, data) {
    const res = await fetchWithAuth(`/api/devices/${deviceId}/`, { method: 'PUT', body: JSON.stringify(data) });
    if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Failed: ${res.status}`);
    }
    showToast('Qurilma yangilandi!', 'success');
    return await res.json();
}

// ── Delete ─────────────────────────────────────────────────────
async function deleteDevice(deviceId) {
    if (!confirm("Bu qurilmani o'chirmoqchimisiz? Bu amalni qaytarib bo'lmaydi.")) return;
    try {
        const res = await fetchWithAuth(`/api/devices/${deviceId}/`, { method: 'DELETE' });
        if (!res.ok) throw new Error(`Failed: ${res.status}`);
        showToast("Qurilma o'chirildi!", 'success');
        loadDevices();
    } catch (err) {
        showToast('Xatolik: ' + err.message, 'error');
    }
}

// ── Edit ───────────────────────────────────────────────────────
async function editDevice(deviceId) {
    try {
        let device = devicesCache.find(d => d.id === deviceId);
        if (!device) {
            const res = await fetchWithAuth(`/api/devices/${deviceId}/`);
            if (!res.ok) throw new Error('Qurilma topilmadi');
            device = await res.json();
        }

        document.getElementById('deviceModalTitle').textContent = 'Qurilmani tahrirlash';
        document.getElementById('deviceId').value              = device.id;
        document.getElementById('pc_id').value                 = device.pc_id;
        document.getElementById('location').value              = device.location;
        document.getElementById('license').value               = device.license || '';
        document.getElementById('is_active').checked           = device.is_active;
        document.getElementById('revoked').checked             = device.revoked;
        document.getElementById('device_public_key').value     = device.device_public_key || '';

        document.getElementById('deviceModal').style.display = 'flex';
    } catch (err) {
        showToast('Xatolik: ' + err.message, 'error');
    }
}

// ── Toast ──────────────────────────────────────────────────────
function showToast(message, type = 'success') {
    const existing = document.querySelector('.toast-notification');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;
    toast.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
        <span>${message}</span>`;
    document.body.appendChild(toast);

    setTimeout(() => toast.classList.add('toast-show'), 10);
    setTimeout(() => {
        toast.classList.remove('toast-show');
        setTimeout(() => toast.remove(), 400);
    }, 3000);
}

// ── Events (DOMContentLoaded) ──────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    loadDevices();

    // Search & filter
    document.getElementById('deviceSearch').addEventListener('input', filterDevices);
    document.getElementById('statusFilter').addEventListener('change', filterDevices);
    document.getElementById('revokedFilter').addEventListener('change', filterDevices);
    document.getElementById('clearFiltersBtn').addEventListener('click', () => {
        document.getElementById('deviceSearch').value  = '';
        document.getElementById('statusFilter').value  = '';
        document.getElementById('revokedFilter').value = '';
        filterDevices();
    });

    // Modal — Add
    document.getElementById('addDeviceBtn').addEventListener('click', () => {
        document.getElementById('deviceModalTitle').textContent = "Yangi qurilma qo'shish";
        document.getElementById('deviceForm').reset();
        document.getElementById('deviceId').value    = '';
        document.getElementById('is_active').checked = true;
        document.getElementById('revoked').checked   = false;
        document.getElementById('deviceModal').style.display = 'flex';
    });

    // Modal — Close
    const modal = document.getElementById('deviceModal');
    document.getElementById('closeDeviceModal').addEventListener('click', () => modal.style.display = 'none');
    document.getElementById('cancelDeviceBtn').addEventListener('click', () => modal.style.display = 'none');
    window.addEventListener('click', e => { if (e.target === modal) modal.style.display = 'none'; });

    // Form submit
    document.getElementById('deviceForm').addEventListener('submit', async e => {
        e.preventDefault();
        const deviceId = document.getElementById('deviceId').value;
        const data = {
            pc_id:             document.getElementById('pc_id').value.trim(),
            location:          document.getElementById('location').value.trim(),
            license:           document.getElementById('license').value.trim(),
            is_active:         document.getElementById('is_active').checked,
            revoked:           document.getElementById('revoked').checked,
            device_public_key: document.getElementById('device_public_key').value.trim() || null,
        };

        if (!data.pc_id || !data.location || !data.license) {
            showToast("PC ID, Location va License to'ldirilishi shart.", 'error');
            return;
        }

        try {
            if (deviceId) {
                await updateDevice(parseInt(deviceId), data);
            } else {
                await createDevice(data);
            }
            modal.style.display = 'none';
            loadDevices();
        } catch (err) {
            showToast('Xatolik: ' + err.message, 'error');
        }
    });

    // Logout (optional — agar index.html da bo'lsa)
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', () => {
            if (typeof adminLogout === 'function') adminLogout();
            window.location.href = '/login/';
        });
    }
});

window.editDevice = editDevice;
window.deleteDevice = deleteDevice;
window.toggleDeviceField = toggleDeviceField;