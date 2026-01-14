/**
 * Port Manager - Frontend JavaScript
 * Real-time process monitoring using WebSockets
 */

const API_BASE = '';
let socket = null;
let isConnected = false;
let pendingKillPid = null;
let currentFilter = 'all';
let allProcessData = { user: [], system: [] };
let previousPorts = { user: new Set(), system: new Set() };

// App type display names
const APP_TYPE_LABELS = {
    node: 'Node.js',
    react: 'React',
    nextjs: 'Next.js',
    vue: 'Vue',
    angular: 'Angular',
    express: 'Express',
    static: 'Static',
    python: 'Python',
    flask: 'Flask',
    django: 'Django',
    fastapi: 'FastAPI',
    php: 'PHP',
    laravel: 'Laravel',
    java: 'Java',
    spring: 'Spring',
    dotnet: '.NET',
    mysql: 'MySQL',
    postgres: 'Postgres',
    mongodb: 'MongoDB',
    redis: 'Redis',
    nginx: 'Nginx',
    apache: 'Apache',
    browser: 'Browser',
    other: 'Other'
};

// DOM Elements
const elements = {
    refreshBtn: document.getElementById('refreshBtn'),
    autoRefresh: document.getElementById('autoRefresh'),
    adminBadge: document.getElementById('adminBadge'),
    totalCount: document.getElementById('totalCount'),
    userCount: document.getElementById('userCount'),
    systemCount: document.getElementById('systemCount'),
    lastUpdate: document.getElementById('lastUpdate'),
    userBadge: document.getElementById('userBadge'),
    systemBadge: document.getElementById('systemBadge'),
    userProcesses: document.getElementById('userProcesses'),
    systemProcesses: document.getElementById('systemProcesses'),
    toggleSystem: document.getElementById('toggleSystem'),
    systemTableContainer: document.getElementById('systemTableContainer'),
    toast: document.getElementById('toast'),
    toastMessage: document.getElementById('toastMessage'),
    confirmModal: document.getElementById('confirmModal'),
    modalProcessInfo: document.getElementById('modalProcessInfo'),
    cancelKill: document.getElementById('cancelKill'),
    confirmKill: document.getElementById('confirmKill'),
    filterButtons: document.getElementById('filterButtons')
};

/**
 * Initialize the application
 */
function init() {
    // Event listeners
    elements.refreshBtn.addEventListener('click', handleRefresh);
    elements.autoRefresh.addEventListener('change', handleAutoRefreshToggle);
    elements.toggleSystem.addEventListener('click', handleToggleSystem);
    elements.cancelKill.addEventListener('click', hideModal);
    elements.confirmKill.addEventListener('click', handleConfirmKill);

    // Filter button listeners
    if (elements.filterButtons) {
        elements.filterButtons.addEventListener('click', (e) => {
            if (e.target.classList.contains('filter-btn')) {
                handleFilterChange(e.target.dataset.filter);
            }
        });
    }

    // Close modal on overlay click
    elements.confirmModal.addEventListener('click', (e) => {
        if (e.target === elements.confirmModal) {
            hideModal();
        }
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            hideModal();
        }
        if (e.key === 'r' && (e.ctrlKey || e.metaKey)) {
            e.preventDefault();
            handleRefresh();
        }
    });

    // Initialize WebSocket connection
    initWebSocket();
}

/**
 * Initialize WebSocket connection
 */
function initWebSocket() {
    socket = io({
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionAttempts: Infinity,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 5000
    });

    // Connection established
    socket.on('connect', () => {
        console.log('WebSocket connected');
        isConnected = true;
        updateConnectionStatus(true);
        showToast('Connected to server', 'success');
    });

    // Connection lost
    socket.on('disconnect', () => {
        console.log('WebSocket disconnected');
        isConnected = false;
        updateConnectionStatus(false);
        showToast('Disconnected from server', 'error');
    });

    // Receive port updates
    socket.on('ports_update', (data) => {
        if (data.success) {
            allProcessData = data.data;
            renderProcesses(data.data);
            updateStats(data.counts);
            updateAdminBadge(data.is_admin);
            updateLastUpdate();
        }
    });

    // Handle errors
    socket.on('error', (data) => {
        console.error('WebSocket error:', data);
        showToast(data.message || 'Connection error', 'error');
    });

    // Reconnection attempt
    socket.on('reconnect_attempt', (attemptNumber) => {
        console.log(`Reconnection attempt ${attemptNumber}`);
    });

    // Reconnected
    socket.on('reconnect', () => {
        console.log('Reconnected to server');
        showToast('Reconnected to server', 'success');
    });
}

/**
 * Update connection status indicator
 */
function updateConnectionStatus(connected) {
    // Update the auto-refresh toggle label to show connection status
    const autoRefreshLabel = document.querySelector('.auto-refresh-toggle span');
    if (autoRefreshLabel) {
        if (connected) {
            autoRefreshLabel.textContent = 'Live';
            autoRefreshLabel.style.color = '#10b981';
        } else {
            autoRefreshLabel.textContent = 'Offline';
            autoRefreshLabel.style.color = '#ef4444';
        }
    }
}

/**
 * Handle filter change
 */
function handleFilterChange(filter) {
    currentFilter = filter;

    // Update active button
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.filter === filter);
    });

    // Re-render with filter applied
    renderFilteredProcesses();
}

/**
 * Filter processes by app type
 */
function filterProcesses(processes) {
    if (currentFilter === 'all') {
        return processes;
    }
    return processes.filter(p => p.app_type === currentFilter);
}

/**
 * Render filtered processes
 */
function renderFilteredProcesses() {
    const filteredUser = filterProcesses(allProcessData.user);
    const filteredSystem = filterProcesses(allProcessData.system);

    elements.userProcesses.innerHTML = renderProcessRows(filteredUser, previousPorts.user, new Set());
    elements.systemProcesses.innerHTML = renderProcessRows(filteredSystem, previousPorts.system, new Set());

    // Update badge counts with filtered counts
    elements.userBadge.textContent = filteredUser.length;
    elements.systemBadge.textContent = filteredSystem.length;
}

/**
 * Fetch port data from API (fallback)
 */
async function fetchPorts() {
    try {
        const response = await fetch(`${API_BASE}/api/ports`);
        const data = await response.json();

        if (data.success) {
            allProcessData = data.data;
            renderProcesses(data.data);
            updateStats(data.counts);
            updateAdminBadge(data.is_admin);
            updateLastUpdate();
        } else {
            showToast('Failed to fetch port data', 'error');
        }
    } catch (error) {
        console.error('Error fetching ports:', error);
        showToast('Connection error', 'error');
    }
}

/**
 * Render processes to tables
 */
function renderProcesses(data) {
    const newUserPorts = new Set(data.user.map(p => `${p.port}:${p.pid}`));
    const newSystemPorts = new Set(data.system.map(p => `${p.port}:${p.pid}`));

    // Apply filter
    const filteredUser = filterProcesses(data.user);
    const filteredSystem = filterProcesses(data.system);

    elements.userProcesses.innerHTML = renderProcessRows(filteredUser, previousPorts.user, newUserPorts);
    elements.systemProcesses.innerHTML = renderProcessRows(filteredSystem, previousPorts.system, newSystemPorts);

    // Update badge counts with filtered counts
    elements.userBadge.textContent = filteredUser.length;
    elements.systemBadge.textContent = filteredSystem.length;

    // Store current ports for next comparison
    previousPorts = { user: newUserPorts, system: newSystemPorts };
}

/**
 * Render process rows
 */
function renderProcessRows(processes, previousSet, newSet) {
    if (processes.length === 0) {
        return `
            <tr class="empty-row">
                <td colspan="8">No processes found${currentFilter !== 'all' ? ' for this filter' : ''}</td>
            </tr>
        `;
    }

    return processes.map(proc => {
        const key = `${proc.port}:${proc.pid}`;
        const isNew = newSet.size > 0 && !previousSet.has(key);
        const appType = proc.app_type || 'other';
        const appLabel = APP_TYPE_LABELS[appType] || appType;
        const hasParent = proc.has_parent_controller;
        const parentInfo = hasParent ? `Parent: ${proc.parent_name} (${proc.parent_pid})` : '';

        return `
            <tr class="${isNew ? 'new-entry' : ''}" data-pid="${proc.pid}" data-app="${appType}">
                <td class="port-cell">${proc.port}</td>
                <td class="pid-cell">${proc.pid}</td>
                <td class="process-name">
                    ${escapeHtml(proc.name)}
                    ${hasParent ? `<span class="parent-indicator" title="${parentInfo}">&#8635;</span>` : ''}
                </td>
                <td><span class="app-badge ${appType}">${appLabel}</span></td>
                <td class="address-cell">${proc.address}</td>
                <td><span class="type-badge ${proc.type.toLowerCase()}">${proc.type}</span></td>
                <td>${getStatusBadge(proc.conn_status, proc.status)}</td>
                <td class="action-cell">
                    ${hasParent ? `
                        <button class="btn btn-kill-tree" onclick="handleKillTree(${proc.pid}, '${escapeHtml(proc.name)}', ${proc.port}, '${escapeHtml(proc.parent_name || '')}', ${proc.parent_pid || 0})" title="Kill process and parent">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                                <path d="M18 6L6 18M6 6l12 12"></path>
                                <circle cx="12" cy="12" r="10"></circle>
                            </svg>
                            Kill Tree
                        </button>
                    ` : `
                        <button class="btn btn-kill" onclick="handleKill(${proc.pid}, '${escapeHtml(proc.name)}', ${proc.port})">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                                <line x1="18" y1="6" x2="6" y2="18"></line>
                                <line x1="6" y1="6" x2="18" y2="18"></line>
                            </svg>
                            Kill
                        </button>
                    `}
                </td>
            </tr>
        `;
    }).join('');
}

/**
 * Get status badge HTML
 */
function getStatusBadge(connStatus, procStatus) {
    let status = connStatus || procStatus || 'unknown';
    status = status.toLowerCase();

    let className = 'other';
    if (status === 'listen') className = 'listen';
    else if (status === 'established') className = 'established';
    else if (status === 'running') className = 'running';
    else if (status === 'sleeping') className = 'sleeping';

    return `<span class="status-badge ${className}">${status.toUpperCase()}</span>`;
}

/**
 * Update statistics
 */
function updateStats(counts) {
    elements.totalCount.textContent = counts.user + counts.system;
    elements.userCount.textContent = counts.user;
    elements.systemCount.textContent = counts.system;
}

/**
 * Update admin badge visibility
 */
function updateAdminBadge(isAdmin) {
    if (isAdmin) {
        elements.adminBadge.classList.add('visible');
    } else {
        elements.adminBadge.classList.remove('visible');
    }
}

/**
 * Update last update time
 */
function updateLastUpdate() {
    const now = new Date();
    const time = now.toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
    elements.lastUpdate.textContent = time;
}

/**
 * Handle refresh button click
 */
function handleRefresh() {
    elements.refreshBtn.classList.add('spinning');

    if (isConnected && socket) {
        // Request refresh via WebSocket
        socket.emit('request_refresh');
        setTimeout(() => {
            elements.refreshBtn.classList.remove('spinning');
        }, 500);
    } else {
        // Fallback to REST API
        fetchPorts().finally(() => {
            setTimeout(() => {
                elements.refreshBtn.classList.remove('spinning');
            }, 500);
        });
    }
}

/**
 * Handle auto-refresh toggle (now controls WebSocket connection)
 */
function handleAutoRefreshToggle() {
    const enabled = elements.autoRefresh.checked;

    if (enabled) {
        if (!isConnected && socket) {
            socket.connect();
        }
    } else {
        if (isConnected && socket) {
            socket.disconnect();
        }
    }
}

/**
 * Handle toggle system section
 */
function handleToggleSystem() {
    elements.toggleSystem.classList.toggle('collapsed');
    elements.systemTableContainer.classList.toggle('collapsed');
}

/**
 * Handle kill button click - show confirmation
 */
function handleKill(pid, name, port) {
    pendingKillPid = pid;
    elements.modalProcessInfo.innerHTML = `
        <div><strong>Process:</strong> ${escapeHtml(name)}</div>
        <div><strong>PID:</strong> ${pid}</div>
        <div><strong>Port:</strong> ${port}</div>
    `;
    showModal();
}

/**
 * Handle kill tree button click - kill process and its parent
 */
async function handleKillTree(pid, name, port, parentName, parentPid) {
    // Find and animate the row
    const rows = document.querySelectorAll(`tr[data-pid="${pid}"]`);
    rows.forEach(row => {
        row.classList.add('killing');
    });

    try {
        const response = await fetch(`${API_BASE}/api/kill-tree/${pid}`, {
            method: 'POST'
        });
        const data = await response.json();

        if (data.success) {
            showToast(data.message, 'success');
            // Remove the rows immediately after animation
            setTimeout(() => {
                rows.forEach(row => row.remove());
            }, 300);
        } else {
            showToast(data.error, 'error');
            rows.forEach(row => {
                row.classList.remove('killing');
            });
        }
    } catch (error) {
        console.error('Error killing process tree:', error);
        showToast('Failed to kill process tree', 'error');
        rows.forEach(row => {
            row.classList.remove('killing');
        });
    }
}

/**
 * Handle confirm kill
 */
async function handleConfirmKill() {
    if (!pendingKillPid) return;

    const pid = pendingKillPid;
    hideModal();

    // Find and animate the row
    const rows = document.querySelectorAll(`tr[data-pid="${pid}"]`);
    rows.forEach(row => {
        row.classList.add('killing');
    });

    try {
        const response = await fetch(`${API_BASE}/api/kill/${pid}`, {
            method: 'POST'
        });
        const data = await response.json();

        if (data.success) {
            showToast(data.message, 'success');
            // Remove the rows immediately after animation
            setTimeout(() => {
                rows.forEach(row => row.remove());
            }, 300);
        } else {
            showToast(data.error, 'error');
            rows.forEach(row => {
                row.classList.remove('killing');
            });
        }
    } catch (error) {
        console.error('Error killing process:', error);
        showToast('Failed to kill process', 'error');
        rows.forEach(row => {
            row.classList.remove('killing');
        });
    }

    pendingKillPid = null;
}

/**
 * Show confirmation modal
 */
function showModal() {
    elements.confirmModal.classList.add('visible');
}

/**
 * Hide confirmation modal
 */
function hideModal() {
    elements.confirmModal.classList.remove('visible');
    pendingKillPid = null;
}

/**
 * Show toast notification
 */
function showToast(message, type = 'success') {
    elements.toast.className = `toast ${type}`;
    elements.toastMessage.textContent = message;
    elements.toast.classList.add('visible');

    setTimeout(() => {
        elements.toast.classList.remove('visible');
    }, 3000);
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', init);
