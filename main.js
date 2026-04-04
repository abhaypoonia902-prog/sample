// ============== ZETATECH HMS - MAIN JAVASCRIPT ==============

const API_BASE_URL = 'http://localhost:8000';

// ============== AUTH UTILITIES ==============

function getToken() {
    return localStorage.getItem('token');
}

function getUser() {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    window.location.href = 'index.html';
}

function checkAuth(requiredRole = null) {
    const token = getToken();
    const user = getUser();
    
    if (!token || !user) {
        window.location.href = 'index.html';
        return false;
    }
    
    if (requiredRole && user.role !== requiredRole) {
        window.location.href = 'index.html';
        return false;
    }
    
    return true;
}

// ============== API UTILITIES ==============

async function apiRequest(endpoint, options = {}) {
    const token = getToken();
    
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` })
        }
    };
    
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers
        }
    });
    
    if (response.status === 401) {
        logout();
        return null;
    }
    
    return response;
}

// ============== UI UTILITIES ==============

function showAlert(containerId, message, type = 'info') {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="alert alert-${type}">
                <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
                ${message}
            </div>
        `;
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            container.innerHTML = '';
        }, 5000);
    }
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function getStatusBadge(status) {
    const statusClasses = {
        'pending': 'pending',
        'approved': 'approved',
        'rejected': 'rejected',
        'completed': 'completed'
    };
    return `<span class="status-badge ${statusClasses[status] || 'pending'}">${status}</span>`;
}

function showLoading(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="loading">
                <div class="spinner"></div>
            </div>
        `;
    }
}

function showEmptyState(containerId, icon, title, message) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas ${icon}"></i>
                <h4>${title}</h4>
                <p>${message}</p>
            </div>
        `;
    }
}

// ============== MODAL UTILITIES ==============

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
    }
}

// ============== SIDEBAR INITIALIZATION ==============

function initSidebar(user) {
    const userName = document.getElementById('userName');
    const userRole = document.getElementById('userRole');
    const userAvatar = document.getElementById('userAvatar');
    
    if (userName) userName.textContent = user.full_name;
    if (userRole) userRole.textContent = user.role;
    if (userAvatar) userAvatar.textContent = user.full_name.charAt(0).toUpperCase();
    
    // Logout button
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
}

// ============== NOTIFICATIONS ==============

let notificationCount = 0;

function updateNotificationBadge(count) {
    notificationCount = count;
    const badge = document.getElementById('notificationBadge');
    if (badge) {
        badge.textContent = count;
        badge.style.display = count > 0 ? 'block' : 'none';
    }
}

// ============== EXPORT ==============
window.ZetaTech = {
    API_BASE_URL,
    getToken,
    getUser,
    logout,
    checkAuth,
    apiRequest,
    showAlert,
    formatDate,
    getStatusBadge,
    showLoading,
    showEmptyState,
    openModal,
    closeModal,
    initSidebar,
    updateNotificationBadge
};
