/**
 * Access logs functions
 * Read-only access to access logs for security auditing
 */

let logsCache = [];

/**
 * Load access logs with optional filtering
 * @param {string} queryParams - Optional query parameters
 */
async function loadLogs(queryParams = '') {
    try {
        const url = queryParams ? `/api/access-logs?${queryParams}` : '/api/access-logs';
        const response = await fetchWithAuth(url);
        
        if (!response.ok) {
            throw new Error(`Failed to load logs: ${response.status}`);
        }
        
        const data = await response.json();
        logsCache = data.logs;
        
        displayLogs(logsCache);
    } catch (error) {
        console.error('Error loading logs:', error);
        alert('Error loading access logs: ' + error.message);
    }
}

/**
 * Display access logs in the table
 * @param {Array} logs - Array of log objects
 */
function displayLogs(logs) {
    const tbody = document.querySelector('#logsTable tbody');
    tbody.innerHTML = '';
    
    if (logs.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td colspan="7" style="text-align: center; padding: 2rem;">
                No access logs found for the selected period.
            </td>
        `;
        tbody.appendChild(row);
        return;
    }
    
    logs.forEach(log => {
        const row = document.createElement('tr');
        
        row.innerHTML = `
            <td>${log.id}</td>
            <td>${new Date(log.timestamp).toLocaleString()}</td>
            <td>${log.user_fio || 'Unknown User'}</td>
            <td>${log.device_pc_id || 'Unknown Device'}</td>
            <td>${log.action || 'Access Attempt'}</td>
            <td>
                <span class="${log.success ? 'status-active' : 'status-inactive'}">
                    ${log.success ? 'Success' : 'Failed'}
                </span>
            </td>
            <td>
                ${log.details || 'No additional details'}
            </td>
        `;
        
        tbody.appendChild(row);
    });
}

/**
 * Export logs to CSV (client-side)
 */
function exportLogsToCSV() {
    if (logsCache.length === 0) {
        alert('No logs to export');
        return;
    }
    
    try {
        // Define CSV headers
        const headers = ['ID', 'Timestamp', 'User', 'Device', 'Action', 'Success', 'Details'];
        
        // Convert logs to CSV rows
        const csvRows = [
            headers.join(','),
            ...logsCache.map(log => [
                log.id,
                `"${new Date(log.timestamp).toISOString()}"`,
                `"${log.user_fio || ''}"`,
                `"${log.device_pc_id || ''}"`,
                `"${log.action || ''}"`,
                log.success ? 'true' : 'false',
                `"${(log.details || '').replace(/"/g, '""')}"`
            ].join(','))
        ];
        
        // Create CSV content
        const csvContent = csvRows.join('\n');
        
        // Create download link
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `access-logs-${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        
    } catch (error) {
        console.error('Error exporting logs:', error);
        alert('Error exporting logs: ' + error.message);
    }
}

// Add export button if needed
document.addEventListener('DOMContentLoaded', () => {
    // You can add an export button to the logs page if needed
    // const exportBtn = document.createElement('button');
    // exportBtn.className = 'btn-secondary';
    // exportBtn.innerHTML = '<i class="fas fa-download"></i> Export CSV';
    // exportBtn.onclick = exportLogsToCSV;
    // document.querySelector('.content-box .header .form-actions').appendChild(exportBtn);
});