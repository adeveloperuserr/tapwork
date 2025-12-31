// API Configuration
const API_BASE = window.location.origin;

// Get token
const token = localStorage.getItem('access_token');
if (!token) {
    window.location.href = 'login.html';
}

const authHeaders = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
};

// State
let roles = [];
let currentRole = null;
let roleToDelete = null;

// DOM Elements
const rolesGrid = document.getElementById('rolesGrid');
const emptyState = document.getElementById('emptyState');
const searchInput = document.getElementById('searchInput');
const createRoleBtn = document.getElementById('createRoleBtn');
const roleModal = document.getElementById('roleModal');
const deleteModal = document.getElementById('deleteModal');
const roleForm = document.getElementById('roleForm');
const modalTitle = document.getElementById('modalTitle');
const closeModal = document.getElementById('closeModal');
const cancelBtn = document.getElementById('cancelBtn');
const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
const logoutBtn = document.getElementById('logoutBtn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadCurrentUser();
    loadRoles();
    updateDateTime();
    setInterval(updateDateTime, 60000);
});

// Update date/time
function updateDateTime() {
    const now = new Date();
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    document.getElementById('currentDate').textContent = now.toLocaleDateString('es-ES', options);
}

// Load current user info
async function loadCurrentUser() {
    try {
        const res = await fetch(`${API_BASE}/api/auth/me`, {
            headers: authHeaders
        });

        if (!res.ok) throw new Error('No autorizado');

        const user = await res.json();
        document.getElementById('sidebarName').textContent = `${user.first_name} ${user.last_name}`;
        document.getElementById('sidebarAvatar').textContent = user.first_name.charAt(0).toUpperCase();
    } catch (error) {
        console.error('Error loading user:', error);
        localStorage.removeItem('access_token');
        window.location.href = 'login.html';
    }
}

// Load all roles
async function loadRoles() {
    try {
        const res = await fetch(`${API_BASE}/api/admin/roles`, {
            headers: authHeaders
        });

        if (!res.ok) throw new Error('Error loading roles');

        roles = await res.json();
        renderRoles(roles);
    } catch (error) {
        console.error('Error loading roles:', error);
        showError('Error al cargar los roles');
    }
}

// Render roles
function renderRoles(rolesData) {
    if (rolesData.length === 0) {
        rolesGrid.classList.add('hidden');
        emptyState.classList.remove('hidden');
        return;
    }

    rolesGrid.classList.remove('hidden');
    emptyState.classList.add('hidden');

    rolesGrid.innerHTML = rolesData.map(role => `
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
            <div class="p-6">
                <div class="flex items-start justify-between mb-4">
                    <div class="flex items-center space-x-3">
                        <div class="flex items-center justify-center w-12 h-12 bg-primary-100 rounded-lg">
                            <svg class="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
                            </svg>
                        </div>
                        <div>
                            <h3 class="font-bold text-lg text-gray-900">${role.name}</h3>
                            <p class="text-sm text-gray-500">Creado: ${new Date(role.created_at).toLocaleDateString('es-ES')}</p>
                        </div>
                    </div>
                </div>

                <p class="text-gray-600 mb-4 min-h-[3rem]">
                    ${role.description || '<span class="text-gray-400 italic">Sin descripción</span>'}
                </p>

                <div class="flex space-x-2 pt-4 border-t border-gray-200">
                    <button onclick="editRole('${role.id}')" class="flex-1 inline-flex items-center justify-center px-3 py-2 bg-primary-50 text-primary-700 font-medium rounded-lg hover:bg-primary-100 transition-colors">
                        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                        </svg>
                        Editar
                    </button>
                    <button onclick="confirmDelete('${role.id}')" class="inline-flex items-center justify-center px-3 py-2 bg-red-50 text-red-700 font-medium rounded-lg hover:bg-red-100 transition-colors">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

// Search functionality
searchInput.addEventListener('input', (e) => {
    const searchTerm = e.target.value.toLowerCase();
    const filtered = roles.filter(role =>
        role.name.toLowerCase().includes(searchTerm) ||
        (role.description && role.description.toLowerCase().includes(searchTerm))
    );
    renderRoles(filtered);
});

// Open create modal
createRoleBtn.addEventListener('click', () => {
    currentRole = null;
    modalTitle.textContent = 'Nuevo Rol';
    roleForm.reset();
    roleModal.classList.remove('hidden');
});

// Edit role
window.editRole = (id) => {
    currentRole = roles.find(r => r.id === id);
    if (!currentRole) return;

    modalTitle.textContent = 'Editar Rol';
    document.getElementById('roleName').value = currentRole.name;
    document.getElementById('roleDescription').value = currentRole.description || '';
    roleModal.classList.remove('hidden');
};

// Close modal handlers
closeModal.addEventListener('click', () => {
    roleModal.classList.add('hidden');
});

cancelBtn.addEventListener('click', () => {
    roleModal.classList.add('hidden');
});

// Form submit
roleForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const payload = {
        name: document.getElementById('roleName').value.trim(),
        description: document.getElementById('roleDescription').value.trim() || null,
        permissions: {}  // Default empty permissions object
    };

    try {
        const url = currentRole
            ? `${API_BASE}/api/admin/roles/${currentRole.id}`
            : `${API_BASE}/api/admin/roles`;

        const method = currentRole ? 'PATCH' : 'POST';

        const res = await fetch(url, {
            method,
            headers: authHeaders,
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const error = await res.json();
            throw new Error(error.detail || 'Error al guardar el rol');
        }

        roleModal.classList.add('hidden');
        loadRoles();
        showSuccess(currentRole ? 'Rol actualizado correctamente' : 'Rol creado correctamente');
    } catch (error) {
        console.error('Error saving role:', error);
        showError(error.message);
    }
});

// Confirm delete
window.confirmDelete = (id) => {
    roleToDelete = id;
    deleteModal.classList.remove('hidden');
};

// Cancel delete
cancelDeleteBtn.addEventListener('click', () => {
    deleteModal.classList.add('hidden');
    roleToDelete = null;
});

// Execute delete
confirmDeleteBtn.addEventListener('click', async () => {
    if (!roleToDelete) return;

    try {
        const res = await fetch(`${API_BASE}/api/admin/roles/${roleToDelete}`, {
            method: 'DELETE',
            headers: authHeaders
        });

        if (!res.ok) {
            const error = await res.json();
            throw new Error(error.detail || 'Error al eliminar el rol');
        }

        deleteModal.classList.add('hidden');
        roleToDelete = null;
        loadRoles();
        showSuccess('Rol eliminado correctamente');
    } catch (error) {
        console.error('Error deleting role:', error);
        showError(error.message);
    }
});

// Logout
logoutBtn.addEventListener('click', () => {
    localStorage.removeItem('access_token');
    window.location.href = 'login.html';
});

// Utility functions
function showToast(message, type = 'success') {
  const existingToast = document.getElementById('toast-notification');
  if (existingToast) existingToast.remove();

  const toast = document.createElement('div');
  toast.id = 'toast-notification';
  toast.className = `fixed bottom-4 right-4 px-6 py-4 rounded-lg shadow-lg transform transition-all duration-300 z-50 ${
    type === 'success' ? 'bg-green-500 text-white' :
    type === 'error' ? 'bg-red-500 text-white' :
    'bg-blue-500 text-white'
  }`;

  toast.innerHTML = `
    <div class="flex items-center gap-3">
      <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        ${type === 'success' ?
          '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>' :
          '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>'
        }
      </svg>
      <span class="font-medium">${message}</span>
    </div>
  `;

  document.body.appendChild(toast);
  setTimeout(() => toast.style.transform = 'translateX(0)', 10);
  setTimeout(() => {
    toast.style.transform = 'translateX(400px)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function showSuccess(message) {
    showToast(message, 'success');
}

function showError(message) {
    showToast('Error: ' + message, 'error');
}
