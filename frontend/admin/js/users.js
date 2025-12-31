const API_BASE = window.location.origin;

// Check authentication
const token = localStorage.getItem('access_token');
if (!token) {
  window.location.href = 'login.html';
}

// Auth headers
const authHeaders = {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
};

// State
let allUsers = [];
let roles = [];
let departments = [];
let shifts = [];
let isEditMode = false;

// DOM Elements
const usersTableBody = document.getElementById('usersTableBody');
const userCount = document.getElementById('userCount');
const searchInput = document.getElementById('searchInput');
const statusFilter = document.getElementById('statusFilter');
const newUserBtn = document.getElementById('newUserBtn');
const userModal = document.getElementById('userModal');
const userForm = document.getElementById('userForm');
const closeModal = document.getElementById('closeModal');
const cancelBtn = document.getElementById('cancelBtn');
const saveBtn = document.getElementById('saveBtn');
const modalTitle = document.getElementById('modalTitle');
const logoutBtn = document.getElementById('logoutBtn');
const barcodeModal = document.getElementById('barcodeModal');
const closeBarcodeModal = document.getElementById('closeBarcodeModal');
const deleteModal = document.getElementById('deleteModal');
const deleteUserNameSpan = document.getElementById('deleteUserName');
const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');

// State for delete operation
let userToDelete = { id: null, name: null };

// Load user info
async function loadUserInfo() {
  try {
    const res = await fetch(`${API_BASE}/api/auth/me`, {
      headers: authHeaders
    });
    const user = await res.json();

    if (!res.ok || !user.role || user.role.name !== 'Admin') {
      throw new Error('No autorizado');
    }

    const userName = document.getElementById('userName');
    const userAvatar = document.getElementById('userAvatar');

    userName.textContent = `${user.first_name} ${user.last_name}`;
    userAvatar.textContent = user.first_name.charAt(0).toUpperCase();
  } catch (error) {
    localStorage.removeItem('access_token');
    window.location.href = 'login.html';
  }
}

// Load all data
async function loadAllData() {
  try {
    const [usersRes, rolesRes, deptsRes, shiftsRes] = await Promise.all([
      fetch(`${API_BASE}/api/admin/users`, { headers: authHeaders }),
      fetch(`${API_BASE}/api/admin/roles`, { headers: authHeaders }),
      fetch(`${API_BASE}/api/admin/departments`, { headers: authHeaders }),
      fetch(`${API_BASE}/api/admin/shifts`, { headers: authHeaders })
    ]);

    if (!usersRes.ok) throw new Error('Error al cargar usuarios');
    if (!rolesRes.ok) throw new Error('Error al cargar roles');
    if (!deptsRes.ok) throw new Error('Error al cargar departamentos');
    if (!shiftsRes.ok) throw new Error('Error al cargar turnos');

    allUsers = await usersRes.json();
    roles = await rolesRes.json();
    departments = await deptsRes.json();
    shifts = await shiftsRes.json();

    // Populate dropdowns
    populateDropdowns();

    // Render table
    renderUsers(allUsers);
  } catch (error) {
    console.error('Error loading data:', error);
    usersTable.innerHTML = `<tr><td colspan="9" class="text-center" style="color: var(--danger);">Error: ${error.message}</td></tr>`;
  }
}

// Populate form dropdowns
function populateDropdowns() {
  const roleSelect = document.getElementById('roleId');
  const deptSelect = document.getElementById('departmentId');
  const shiftSelect = document.getElementById('shiftId');

  console.log('Populating dropdowns:', { roles, departments, shifts });

  roleSelect.innerHTML = '<option value="">Seleccionar rol...</option>' +
    roles.map(r => `<option value="${r.id}">${r.name}</option>`).join('');

  deptSelect.innerHTML = '<option value="">Seleccionar departamento...</option>' +
    departments.map(d => `<option value="${d.id}">${d.name}</option>`).join('');

  shiftSelect.innerHTML = '<option value="">Seleccionar turno...</option>' +
    shifts.map(s => `<option value="${s.id}">${s.name}</option>`).join('');
}

// Render users table
function renderUsers(users) {
  userCount.textContent = users.length;

  if (users.length === 0) {
    usersTableBody.innerHTML = '<tr><td colspan="7" class="px-6 py-8 text-center text-gray-500">No hay usuarios registrados</td></tr>';
    return;
  }

  usersTableBody.innerHTML = users.map(user => `
    <tr class="hover:bg-gray-50 transition-colors">
      <td class="px-6 py-4 whitespace-nowrap">
        <div class="flex items-center">
          <div class="flex-shrink-0 h-10 w-10">
            <div class="h-10 w-10 rounded-full bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center text-white font-semibold">
              ${user.first_name.charAt(0)}${user.last_name.charAt(0)}
            </div>
          </div>
          <div class="ml-4">
            <div class="text-sm font-semibold text-gray-900">${user.first_name} ${user.last_name}</div>
            <div class="text-sm text-gray-500">${user.employee_id}</div>
          </div>
        </div>
      </td>
      <td class="px-6 py-4 whitespace-nowrap">
        <div class="text-sm text-gray-900">${user.email}</div>
      </td>
      <td class="px-6 py-4 whitespace-nowrap">
        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
          ${user.role ? user.role.name : '-'}
        </span>
      </td>
      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
        ${user.department ? user.department.name : '-'}
      </td>
      <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
        ${user.shift ? user.shift.name : '-'}
      </td>
      <td class="px-6 py-4 whitespace-nowrap">
        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
          ${user.is_active ? 'Activo' : 'Inactivo'}
        </span>
      </td>
      <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
        <div class="flex items-center justify-end space-x-2">
          ${user.qr_code ? `
            <button onclick="viewBarcode('${user.id}', '${user.employee_id}')" class="text-gray-600 hover:text-gray-900 transition-colors" title="Ver código">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z"/>
              </svg>
            </button>
          ` : ''}
          <button onclick="editUser('${user.id}')" class="text-primary-600 hover:text-primary-900 transition-colors" title="Editar">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
            </svg>
          </button>
          <button onclick="deleteUser('${user.id}', '${user.first_name} ${user.last_name}')" class="text-red-600 hover:text-red-900 transition-colors" title="Eliminar">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
            </svg>
          </button>
        </div>
      </td>
    </tr>
  `).join('');
}

// Filter users
function filterUsers() {
  const searchTerm = searchInput.value.toLowerCase();
  const status = statusFilter.value;

  let filtered = allUsers;

  // Filter by search
  if (searchTerm) {
    filtered = filtered.filter(user =>
      user.first_name.toLowerCase().includes(searchTerm) ||
      user.last_name.toLowerCase().includes(searchTerm) ||
      user.email.toLowerCase().includes(searchTerm) ||
      user.employee_id.toLowerCase().includes(searchTerm)
    );
  }

  // Filter by status
  if (status === 'active') {
    filtered = filtered.filter(user => user.is_active);
  } else if (status === 'inactive') {
    filtered = filtered.filter(user => !user.is_active);
  }

  renderUsers(filtered);
}

// Open modal for new user
function openNewUserModal() {
  isEditMode = false;
  modalTitle.textContent = 'Nuevo Usuario';
  userForm.reset();
  document.getElementById('userId').value = '';

  // Ocultar toggle de estado (solo para modo edición)
  document.getElementById('statusToggleContainer').classList.add('hidden');

  // Reset button state and update text for create mode
  saveBtn.disabled = false;
  saveBtn.querySelector('.btn-text').textContent = 'Guardar Usuario';
  saveBtn.querySelector('.btn-text').classList.remove('hidden');
  saveBtn.querySelector('.btn-loader').innerHTML = '<span class="spinner"></span> Guardando...';
  saveBtn.querySelector('.btn-loader').classList.add('hidden');

  userModal.classList.remove('hidden');
}

// Edit user
window.editUser = async function(userId) {
  isEditMode = true;
  modalTitle.textContent = 'Editar Usuario';

  const user = allUsers.find(u => u.id === userId);
  if (!user) return;

  document.getElementById('userId').value = user.id;
  document.getElementById('firstName').value = user.first_name;
  document.getElementById('lastName').value = user.last_name;
  document.getElementById('email').value = user.email;
  document.getElementById('roleId').value = user.role_id || '';
  document.getElementById('departmentId').value = user.department_id || '';
  document.getElementById('shiftId').value = user.shift_id || '';
  document.getElementById('isActive').checked = user.is_active;

  // Mostrar toggle de estado
  document.getElementById('statusToggleContainer').classList.remove('hidden');

  // Reset button state and update text for edit mode
  saveBtn.disabled = false;
  saveBtn.querySelector('.btn-text').textContent = 'Actualizar Usuario';
  saveBtn.querySelector('.btn-text').classList.remove('hidden');
  saveBtn.querySelector('.btn-loader').innerHTML = '<span class="spinner"></span> Actualizando...';
  saveBtn.querySelector('.btn-loader').classList.add('hidden');

  userModal.classList.remove('hidden');
};

// Delete user - Open confirmation modal
window.deleteUser = function(userId, userName) {
  userToDelete = { id: userId, name: userName };
  deleteUserNameSpan.textContent = userName;
  deleteModal.classList.remove('hidden');
};

// Confirm delete user
async function confirmDelete() {
  if (!userToDelete.id) return;

  deleteModal.classList.add('hidden');

  try {
    const res = await fetch(`${API_BASE}/api/admin/users/${userToDelete.id}`, {
      method: 'DELETE',
      headers: authHeaders
    });

    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.detail || 'Error al eliminar usuario');
    }

    // Success notification
    showToast(`Usuario ${userToDelete.name} eliminado exitosamente`, 'success');

    // Reset state
    userToDelete = { id: null, name: null };

    // Reload table
    loadAllData();
  } catch (error) {
    showToast(`Error: ${error.message}`, 'error');
    userToDelete = { id: null, name: null };
  }
}

// View barcode
window.viewBarcode = async function(userId, employeeId) {
  try {
    const res = await fetch(`${API_BASE}/api/barcodes/user/${userId}`, {
      headers: authHeaders
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || 'Error al obtener código de barras');
    }

    // Display barcode (base64 image)
    const container = document.getElementById('barcodeContainer');
    const codeEl = document.getElementById('barcodeCode');

    container.innerHTML = `<img src="data:image/png;base64,${data.barcode_base64}" style="max-width: 100%;" alt="Código de barras">`;
    codeEl.textContent = employeeId;

    barcodeModal.classList.remove('hidden');
  } catch (error) {
    showToast(`Error: ${error.message}`, 'error');
  }
};

// Submit form
userForm.addEventListener('submit', async (e) => {
  e.preventDefault();

  const userId = document.getElementById('userId').value;
  const formData = {
    first_name: document.getElementById('firstName').value,
    last_name: document.getElementById('lastName').value,
    employee_id: document.getElementById('employeeId').value,
    email: document.getElementById('email').value,
    role_id: document.getElementById('roleId').value || null,
    department_id: document.getElementById('departmentId').value || null,
    shift_id: document.getElementById('shiftId').value || null,
    notification_preferences: {
      registration: true,
      reset: true,
      attendance: true
    }
  };

  // Agregar is_active solo en modo edición
  if (isEditMode) {
    formData.is_active = document.getElementById('isActive').checked;
  }

  // Loading state
  saveBtn.disabled = true;
  saveBtn.querySelector('.btn-text').classList.add('hidden');
  saveBtn.querySelector('.btn-loader').classList.remove('hidden');

  try {
    let res;
    if (isEditMode) {
      // Update user
      res = await fetch(`${API_BASE}/api/admin/users/${userId}`, {
        method: 'PATCH',
        headers: authHeaders,
        body: JSON.stringify(formData)
      });
    } else {
      // Create user
      res = await fetch(`${API_BASE}/api/admin/users`, {
        method: 'POST',
        headers: authHeaders,
        body: JSON.stringify(formData)
      });
    }

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || 'Error al guardar usuario');
    }

    // Success con toast
    showToast(isEditMode ? 'Usuario actualizado exitosamente' : 'Usuario creado exitosamente', 'success');

    // Close modal y reload data
    userModal.classList.add('hidden');
    loadAllData();
  } catch (error) {
    showToast(error.message, 'error');

    // Reset button
    saveBtn.disabled = false;
    saveBtn.querySelector('.btn-text').classList.remove('hidden');
    saveBtn.querySelector('.btn-loader').classList.add('hidden');
  }
});

// Event listeners
newUserBtn.addEventListener('click', openNewUserModal);
closeModal.addEventListener('click', () => userModal.classList.add('hidden'));
cancelBtn.addEventListener('click', () => userModal.classList.add('hidden'));
closeBarcodeModal.addEventListener('click', () => barcodeModal.classList.add('hidden'));

// Delete modal listeners
cancelDeleteBtn.addEventListener('click', () => {
  deleteModal.classList.add('hidden');
  userToDelete = { id: null, name: null };
});
confirmDeleteBtn.addEventListener('click', confirmDelete);

searchInput.addEventListener('input', filterUsers);
statusFilter.addEventListener('change', filterUsers);

logoutBtn.addEventListener('click', () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('user');
  window.location.href = 'login.html';
});

// Close modal on overlay click
userModal.addEventListener('click', (e) => {
  if (e.target === userModal) {
    userModal.classList.add('hidden');
  }
});

barcodeModal.addEventListener('click', (e) => {
  if (e.target === barcodeModal) {
    barcodeModal.classList.add('hidden');
  }
});

deleteModal.addEventListener('click', (e) => {
  if (e.target === deleteModal) {
    deleteModal.classList.add('hidden');
    userToDelete = { id: null, name: null };
  }
});

// Toast notification system
function showToast(message, type = 'success') {
  // Remove any existing toast
  const existingToast = document.getElementById('toast-notification');
  if (existingToast) existingToast.remove();

  // Create toast element
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

  // Animate in
  setTimeout(() => toast.style.transform = 'translateX(0)', 10);

  // Auto remove after 4 seconds
  setTimeout(() => {
    toast.style.transform = 'translateX(400px)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Initialize
loadUserInfo();
loadAllData();
