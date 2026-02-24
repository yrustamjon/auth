/**
 * Device management functions
 * Handles CRUD operations for devices
 * Fields: id, pc_id, location, is_active, revoked, last_seen, registered_at, device_public_key
 */

let devicesCache = [];

async function loadDevices() {
    const tbody = document.querySelector('#devicesTable tbody');
    tbody.innerHTML = `
        <tr class="loading-row">
            <td colspan="8">
                <div class="loading-spinner">
                    <i class="fas fa-circle-notch fa-spin"></i> Loading devices...
                </div>
            </td>
        </tr>
    `;

    try {
        const response = await fetchWithAuth('/api/devices');
        if (!response.ok) throw new Error(`Failed to load devices: ${response.status}`);
        const devices = await response.json();
        devicesCache = devices;
        displayDevices(devices);
    } catch (error) {
        console.error('Error loading devices:', error);
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="empty-state error-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Error loading devices: ${error.message}</p>
                </td>
            </tr>
        `;
    }
}

function displayDevices(devices) {
    const tbody = document.querySelector('#devicesTable tbody');
    tbody.innerHTML = '';

    if (!devices || devices.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="empty-state">
                    <i class="fas fa-desktop"></i>
                    <p>No devices found. Add your first device!</p>
                </td>
            </tr>
        `;
        return;
    }

    devices.forEach(device => {
        const row = document.createElement('tr');

        const registeredAt = device.registered_at
            ? new Date(device.registered_at).toLocaleDateString('en-GB', { day:'2-digit', month:'short', year:'numeric' })
            : '<span class="text-muted">N/A</span>';

        const lastSeen = device.last_seen
            ? new Date(device.last_seen).toLocaleString('en-GB', { day:'2-digit', month:'short', year:'numeric', hour:'2-digit', minute:'2-digit' })
            : '<span class="text-muted">Never</span>';

        // is_active badge (display only)
        const isActiveLabel = device.is_active
            ? `<span class="badge badge-active"><i class="fas fa-check-circle"></i> Active</span>`
            : `<span class="badge badge-inactive"><i class="fas fa-times-circle"></i> Inactive</span>`;

        // revoked badge (display only)
        const revokedLabel = device.revoked
            ? `<span class="badge badge-revoked"><i class="fas fa-ban"></i> Revoked</span>`
            : `<span class="badge badge-ok"><i class="fas fa-shield-alt"></i> OK</span>`;

        row.innerHTML = `
            <td class="col-id">${device.id}</td>
            <td class="col-pcid"><strong>${device.pc_id}</strong></td>
            <td class="col-location">
                <i class="fas fa-map-marker-alt location-icon"></i>
                ${device.location}
            </td>
            <td class="col-status">${isActiveLabel}</td>
            <td class="col-revoked">${revokedLabel}</td>
            <td class="col-registered">${registeredAt}</td>
            <td class="col-lastseen">${lastSeen}</td>
            <td class="col-actions actions">
                <button class="btn-action btn-edit" onclick="editDevice(${device.id})" title="Edit Device">
                    <i class="fas fa-edit"></i> Edit
                </button>
                <button class="btn-action btn-delete" onclick="deleteDevice(${device.id})" title="Delete Device">
                    <i class="fas fa-trash"></i> Delete
                </button>
                ${device.is_active
                    ? `<button class="btn-action btn-toggle-inactive" onclick="toggleDeviceField(${device.id}, 'is_active', false)" title="Deactivate">
                           <i class="fas fa-toggle-on"></i> Deactivate
                       </button>`
                    : `<button class="btn-action btn-toggle-active" onclick="toggleDeviceField(${device.id}, 'is_active', true)" title="Activate">
                           <i class="fas fa-toggle-off"></i> Activate
                       </button>`
                }
                ${device.revoked
                    ? `<button class="btn-action btn-toggle-restore" onclick="toggleDeviceField(${device.id}, 'revoked', false)" title="Restore">
                           <i class="fas fa-undo"></i> Restore
                       </button>`
                    : `<button class="btn-action btn-toggle-revoke" onclick="toggleDeviceField(${device.id}, 'revoked', true)" title="Revoke">
                           <i class="fas fa-ban"></i> Revoke
                       </button>`
                }
            </td>
        `;

        tbody.appendChild(row);
    });
}

/**
 * Toggle is_active or revoked using PATCH
 */
async function toggleDeviceField(deviceId, field, value) {
    try {
        const response = await fetchWithAuth(`/api/devices/${deviceId}/`, {
            method: 'PATCH',
            body: JSON.stringify({ [field]: value })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Failed to update: ${response.status}`);
        }

        // Update local cache
        const cached = devicesCache.find(d => d.id === deviceId);
        if (cached) cached[field] = value;

        const label = field === 'is_active' ? 'Status' : 'Revoked';
        showToast(`${label} updated successfully!`, 'success');

        displayDevices(devicesCache);
    } catch (error) {
        console.error(`Error toggling ${field}:`, error);
        showToast(`Error updating device: ${error.message}`, 'error');
    }
}

async function createDevice(deviceData) {
    try {
        const response = await fetchWithAuth('/api/devices', {
            method: 'POST',
            body: JSON.stringify(deviceData)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Failed to create device: ${response.status}`);
        }

        showToast('Device created successfully!', 'success');
        return await response.json();
    } catch (error) {
        console.error('Error creating device:', error);
        throw error;
    }
}

async function updateDevice(deviceId, deviceData) {
    try {
        const response = await fetchWithAuth(`/api/devices/${deviceId}`, {
            method: 'PUT',
            body: JSON.stringify(deviceData)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `Failed to update device: ${response.status}`);
        }

        showToast('Device updated successfully!', 'success');
        return await response.json();
    } catch (error) {
        console.error('Error updating device:', error);
        throw error;
    }
}

async function deleteDevice(deviceId) {
    if (!confirm('Are you sure you want to delete this device? This action cannot be undone.')) return;

    try {
        const response = await fetchWithAuth(`/api/devices/${deviceId}/`, { method: 'DELETE' });

        if (!response.ok) throw new Error(`Failed to delete device: ${response.status}`);

        showToast('Device deleted successfully!', 'success');
        loadDevices();
    } catch (error) {
        console.error('Error deleting device:', error);
        showToast('Error deleting device: ' + error.message, 'error');
    }
}

async function editDevice(deviceId) {
    try {
        let device = devicesCache.find(d => d.id === deviceId);

        if (!device) {
            const response = await fetchWithAuth(`/api/devices/${deviceId}/`);
            if (!response.ok) throw new Error('Device not found');
            device = await response.json();
        }

        document.getElementById('deviceModalTitle').textContent = 'Edit Device';
        document.getElementById('deviceId').value = device.id;
        document.getElementById('pc_id').value = device.pc_id;
        document.getElementById('location').value = device.location;
        document.getElementById('is_active').checked = device.is_active;
        document.getElementById('revoked').checked = device.revoked;
        document.getElementById('device_public_key').value = device.device_public_key || '';

        document.getElementById('deviceModal').style.display = 'flex';
    } catch (error) {
        console.error('Error loading device for edit:', error);
        showToast('Error loading device data: ' + error.message, 'error');
    }
}

function showToast(message, type = 'success') {
    const existing = document.querySelector('.toast-notification');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;
    toast.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
        <span>${message}</span>
    `;
    document.body.appendChild(toast);

    setTimeout(() => toast.classList.add('toast-show'), 10);
    setTimeout(() => {
        toast.classList.remove('toast-show');
        setTimeout(() => toast.remove(), 400);
    }, 3000);
}