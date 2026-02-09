/**
 * Device management functions
 * Handles CRUD operations for devices
 */

let devicesCache = [];

/**
 * Load all devices and display in table
 */
async function loadDevices() {
    try {
        const response = await fetchWithAuth('/api/devices');
        
        if (!response.ok) {
            throw new Error(`Failed to load devices: ${response.status}`);
        }
        
        const devices = await response.json();
        devicesCache = devices;
        
        displayDevices(devices);
    } catch (error) {
        console.error('Error loading devices:', error);
        alert('Error loading devices: ' + error.message);
    }
}

/**
 * Display devices in the table
 * @param {Array} devices - Array of device objects
 */
function displayDevices(devices) {
    const tbody = document.querySelector('#devicesTable tbody');
    tbody.innerHTML = '';
    
    devices.forEach(device => {
        const row = document.createElement('tr');
        
        row.innerHTML = `
            <td>${device.id}</td>
            <td><strong>${device.pc_id}</strong></td>
            <td>${device.location}</td>
            <td>${device.created_at ? new Date(device.created_at).toLocaleDateString() : 'N/A'}</td>
            <td>${device.last_access ? new Date(device.last_access).toLocaleString() : 'Never'}</td>
            <td class="actions">
                <button class="btn-primary btn-sm" onclick="editDevice(${device.id})">
                    <i class="fas fa-edit"></i> Edit
                </button>
                <button class="btn-danger btn-sm" onclick="deleteDevice(${device.id})">
                    <i class="fas fa-trash"></i> Delete
                </button>
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

/**
 * Create a new device
 * @param {Object} deviceData - Device data {pc_id, location}
 */
async function createDevice(deviceData) {
    try {
        const response = await fetchWithAuth('/api/devices', {
            method: 'POST',
            body: JSON.stringify(deviceData)
        });
        
        if (!response.ok) {
            throw new Error(`Failed to create device: ${response.status}`);
        }
        
        alert('Device created successfully!');
        return await response.json();
    } catch (error) {
        console.error('Error creating device:', error);
        throw error;
    }
}

/**
 * Update an existing device
 * @param {number} deviceId - Device ID
 * @param {Object} deviceData - Updated device data
 */
async function updateDevice(deviceId, deviceData) {
    try {
        const response = await fetchWithAuth(`/api/devices/${deviceId}`, {
            method: 'PUT',
            body: JSON.stringify(deviceData)
        });
        
        if (!response.ok) {
            throw new Error(`Failed to update device: ${response.status}`);
        }
        
        alert('Device updated successfully!');
        return await response.json();
    } catch (error) {
        console.error('Error updating device:', error);
        throw error;
    }
}

/**
 * Delete a device
 * @param {number} deviceId - Device ID to delete
 */
async function deleteDevice(deviceId) {
    if (!confirm('Are you sure you want to delete this device?')) {
        return;
    }
    
    try {
        const response = await fetchWithAuth(`/api/devices/${deviceId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) {
            throw new Error(`Failed to delete device: ${response.status}`);
        }
        
        alert('Device deleted successfully!');
        loadDevices();
    } catch (error) {
        console.error('Error deleting device:', error);
        alert('Error deleting device: ' + error.message);
    }
}

/**
 * Edit device - populate modal with device data
 * @param {number} deviceId - Device ID to edit
 */
async function editDevice(deviceId) {
    try {
        const device = devicesCache.find(d => d.id === deviceId);
        
        if (!device) {
            // Fetch device if not in cache
            const response = await fetchWithAuth(`/api/devices/${deviceId}`);
            if (!response.ok) {
                throw new Error('Device not found');
            }
            device = await response.json();
        }
        
        // Populate modal
        document.getElementById('deviceModalTitle').textContent = 'Edit Device';
        document.getElementById('deviceId').value = device.id;
        document.getElementById('pc_id').value = device.pc_id;
        document.getElementById('location').value = device.location;
        
        // Show modal
        document.getElementById('deviceModal').style.display = 'flex';
    } catch (error) {
        console.error('Error loading device for edit:', error);
        alert('Error loading device data: ' + error.message);
    }
}