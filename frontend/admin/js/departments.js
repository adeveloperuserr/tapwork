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
let departments = [];
let currentDepartment = null;
let departmentToDelete = null;

// DOM Elements
const departmentsGrid = document.getElementById('departmentsGrid');
const emptyState = document.getElementById('emptyState');
const searchInput = document.getElementById('searchInput');
const createDeptBtn = document.getElementById('createDeptBtn');
const deptModal = document.getElementById('deptModal');
const deleteModal = document.getElementById('deleteModal');
const deptForm = document.getElementById('deptForm');
const modalTitle = document.getElementById('modalTitle');
const closeModal = document.getElementById('closeModal');
const cancelBtn = document.getElementById('cancelBtn');
const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
const logoutBtn = document.getElementById('logoutBtn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadCurrentUser();
    loadDepartments();
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

// Load all departments
async function loadDepartments() {
    try {
        const res = await fetch(`${API_BASE}/api/admin/departments`, {
            headers: authHeaders
        });

        if (!res.ok) throw new Error('Error loading departments');

        departments = await res.json();
        renderDepartments(departments);
    } catch (error) {
        console.error('Error loading departments:', error);
        showError('Error al cargar los departamentos');
    }
}

// Render departments
function renderDepartments(depts) {
    if (depts.length === 0) {
        departmentsGrid.classList.add('hidden');
        emptyState.classList.remove('hidden');
        return;
    }

    departmentsGrid.classList.remove('hidden');
    emptyState.classList.add('hidden');

    departmentsGrid.innerHTML = depts.map(dept => `
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
            <div class="p-6">
                <div class="flex items-start justify-between mb-4">
                    <div class="flex items-center space-x-3">
                        <div class="flex items-center justify-center w-12 h-12 bg-primary-100 rounded-lg">
                            <svg class="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
                            </svg>
                        </div>
                        <div>
                            <h3 class="font-bold text-lg text-gray-900">${dept.name}</h3>
                            <p class="text-sm text-gray-500">Creado: ${new Date(dept.created_at).toLocaleDateString('es-ES')}</p>
                        </div>
                    </div>
                </div>

                <p class="text-gray-600 mb-4 min-h-[3rem]">
                    ${dept.description || '<span class="text-gray-400 italic">Sin descripción</span>'}
                </p>

                <div class="flex space-x-2 pt-4 border-t border-gray-200">
                    <button onclick="editDepartment('${dept.id}')" class="flex-1 inline-flex items-center justify-center px-3 py-2 bg-primary-50 text-primary-700 font-medium rounded-lg hover:bg-primary-100 transition-colors">
                        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                        </svg>
                        Editar
                    </button>
                    <button onclick="confirmDelete('${dept.id}')" class="inline-flex items-center justify-center px-3 py-2 bg-red-50 text-red-700 font-medium rounded-lg hover:bg-red-100 transition-colors">
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
    const filtered = departments.filter(dept =>
        dept.name.toLowerCase().includes(searchTerm) ||
        (dept.description && dept.description.toLowerCase().includes(searchTerm))
    );
    renderDepartments(filtered);
});

// Open create modal
createDeptBtn.addEventListener('click', () => {
    currentDepartment = null;
    modalTitle.textContent = 'Nuevo Departamento';
    deptForm.reset();
    deptModal.classList.remove('hidden');
});

// Edit department
window.editDepartment = (id) => {
    currentDepartment = departments.find(d => d.id === id);
    if (!currentDepartment) return;

    modalTitle.textContent = 'Editar Departamento';
    document.getElementById('deptName').value = currentDepartment.name;
    document.getElementById('deptDescription').value = currentDepartment.description || '';
    deptModal.classList.remove('hidden');
};

// Close modal handlers
closeModal.addEventListener('click', () => {
    deptModal.classList.add('hidden');
});

cancelBtn.addEventListener('click', () => {
    deptModal.classList.add('hidden');
});

// Form submit
deptForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const payload = {
        name: document.getElementById('deptName').value.trim(),
        description: document.getElementById('deptDescription').value.trim() || null
    };

    try {
        const url = currentDepartment
            ? `${API_BASE}/api/admin/departments/${currentDepartment.id}`
            : `${API_BASE}/api/admin/departments`;

        const method = currentDepartment ? 'PATCH' : 'POST';

        const res = await fetch(url, {
            method,
            headers: authHeaders,
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const error = await res.json();
            throw new Error(error.detail || 'Error al guardar el departamento');
        }

        deptModal.classList.add('hidden');
        loadDepartments();
        showSuccess(currentDepartment ? 'Departamento actualizado correctamente' : 'Departamento creado correctamente');
    } catch (error) {
        console.error('Error saving department:', error);
        showError(error.message);
    }
});

// Confirm delete
window.confirmDelete = (id) => {
    departmentToDelete = id;
    deleteModal.classList.remove('hidden');
};

// Cancel delete
cancelDeleteBtn.addEventListener('click', () => {
    deleteModal.classList.add('hidden');
    departmentToDelete = null;
});

// Execute delete
confirmDeleteBtn.addEventListener('click', async () => {
    if (!departmentToDelete) return;

    try {
        const res = await fetch(`${API_BASE}/api/admin/departments/${departmentToDelete}`, {
            method: 'DELETE',
            headers: authHeaders
        });

        if (!res.ok) {
            const error = await res.json();
            throw new Error(error.detail || 'Error al eliminar el departamento');
        }

        deleteModal.classList.add('hidden');
        departmentToDelete = null;
        loadDepartments();
        showSuccess('Departamento eliminado correctamente');
    } catch (error) {
        console.error('Error deleting department:', error);
        showError(error.message);
    }
});

// Logout
logoutBtn.addEventListener('click', () => {
    localStorage.removeItem('access_token');
    window.location.href = 'login.html';
});

// Utility functions
function showSuccess(message) {
    // Simple alert for now - could be improved with toast notifications
    alert(message);
}

function showError(message) {
    alert('Error: ' + message);
}
