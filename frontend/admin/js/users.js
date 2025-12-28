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
const usersGrid = document.getElementById('usersGrid');
const emptyState = document.getElementById('emptyState');
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
const formError = document.getElementById('formError');
const formSuccess = document.getElementById('formSuccess');
const logoutBtn = document.getElementById('logoutBtn');
const barcodeModal = document.getElementById('barcodeModal');
const closeBarcodeModal = document.getElementById('closeBarcodeModal');

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
    usersGrid.classList.add('hidden');
    emptyState.classList.remove('hidden');
    return;
  }

  usersGrid.classList.remove('hidden');
  emptyState.classList.add('hidden');

  usersGrid.innerHTML = users.map(user => `
    <div class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
      <div class="p-6">
        <div class="flex items-start justify-between mb-4">
          <div class="flex items-center space-x-3">
            <div class="flex items-center justify-center w-12 h-12 bg-gradient-to-br from-primary-500 to-primary-600 rounded-full text-white font-bold text-lg">
              ${user.first_name.charAt(0).toUpperCase()}${user.last_name.charAt(0).toUpperCase()}
            </div>
            <div>
              <h3 class="font-bold text-lg text-gray-900">${user.first_name} ${user.last_name}</h3>
              <p class="text-sm text-gray-500">${user.employee_id}</p>
            </div>
          </div>
          <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
            ${user.is_active ? 'Activo' : 'Inactivo'}
          </span>
        </div>

        <div class="space-y-2 mb-4">
          <div class="flex items-center text-sm">
            <svg class="w-4 h-4 mr-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
            </svg>
            <span class="text-gray-600">${user.email}</span>
          </div>

          <div class="flex items-center text-sm">
            <svg class="w-4 h-4 mr-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>
            </svg>
            <span class="text-gray-600">Rol: </span>
            <span class="ml-1 font-semibold text-gray-900">${user.role ? user.role.name : '-'}</span>
          </div>

          <div class="flex items-center text-sm">
            <svg class="w-4 h-4 mr-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/>
            </svg>
            <span class="text-gray-600">Depto: </span>
            <span class="ml-1 font-semibold text-gray-900">${user.department ? user.department.name : '-'}</span>
          </div>

          <div class="flex items-center text-sm">
            <svg class="w-4 h-4 mr-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <span class="text-gray-600">Turno: </span>
            <span class="ml-1 font-semibold text-gray-900">${user.shift ? user.shift.name : '-'}</span>
          </div>
        </div>

        <div class="flex space-x-2 pt-4 border-t border-gray-200">
          ${user.qr_code ?
            `<button onclick="viewBarcode('${user.id}', '${user.employee_id}')" class="flex-1 inline-flex items-center justify-center px-3 py-2 bg-gray-50 text-gray-700 font-medium rounded-lg hover:bg-gray-100 transition-colors">
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z"/>
              </svg>
              Código
            </button>` :
            '<div class="flex-1"></div>'
          }
          <button onclick="editUser('${user.id}')" class="inline-flex items-center justify-center px-3 py-2 bg-primary-50 text-primary-700 font-medium rounded-lg hover:bg-primary-100 transition-colors">
            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
            </svg>
            Editar
          </button>
          <button onclick="deleteUser('${user.id}', '${user.first_name} ${user.last_name}')" class="inline-flex items-center justify-center px-3 py-2 bg-red-50 text-red-700 font-medium rounded-lg hover:bg-red-100 transition-colors">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
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
  document.getElementById('password').required = true;
  document.getElementById('passwordGroup').querySelector('small').textContent = 'Mínimo 8 caracteres';

  // Reset button state and update text for create mode
  saveBtn.disabled = false;
  saveBtn.querySelector('.btn-text').textContent = 'Guardar Usuario';
  saveBtn.querySelector('.btn-text').classList.remove('hidden');
  saveBtn.querySelector('.btn-loader').innerHTML = '<span class="spinner"></span> Guardando...';
  saveBtn.querySelector('.btn-loader').classList.add('hidden');

  formError.classList.add('hidden');
  formSuccess.classList.add('hidden');
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
  document.getElementById('employeeId').value = user.employee_id;
  document.getElementById('email').value = user.email;
  document.getElementById('password').value = '';
  document.getElementById('password').required = false;
  document.getElementById('roleId').value = user.role_id || '';
  document.getElementById('departmentId').value = user.department_id || '';
  document.getElementById('shiftId').value = user.shift_id || '';

  document.getElementById('passwordGroup').querySelector('small').textContent =
    'Dejar en blanco para mantener la contraseña actual';

  // Reset button state and update text for edit mode
  saveBtn.disabled = false;
  saveBtn.querySelector('.btn-text').textContent = 'Actualizar Usuario';
  saveBtn.querySelector('.btn-text').classList.remove('hidden');
  saveBtn.querySelector('.btn-loader').innerHTML = '<span class="spinner"></span> Actualizando...';
  saveBtn.querySelector('.btn-loader').classList.add('hidden');

  formError.classList.add('hidden');
  formSuccess.classList.add('hidden');
  userModal.classList.remove('hidden');
};

// Delete user
window.deleteUser = async function(userId, userName) {
  if (!confirm(`¿Estás seguro de eliminar a ${userName}?\n\nEsta acción no se puede deshacer.`)) {
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/admin/users/${userId}`, {
      method: 'DELETE',
      headers: authHeaders
    });

    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.detail || 'Error al eliminar usuario');
    }

    alert(`Usuario ${userName} eliminado exitosamente`);
    loadAllData(); // Reload table
  } catch (error) {
    alert(`Error: ${error.message}`);
  }
};

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
    alert(`Error: ${error.message}`);
  }
};

// Submit form
userForm.addEventListener('submit', async (e) => {
  e.preventDefault();

  formError.classList.add('hidden');
  formSuccess.classList.add('hidden');

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

  const password = document.getElementById('password').value;
  if (password || !isEditMode) {
    formData.password = password;
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

    // Success
    formSuccess.textContent = isEditMode ? 'Usuario actualizado exitosamente' : 'Usuario creado exitosamente';
    formSuccess.classList.remove('hidden');

    // Reload data after 1 second
    setTimeout(() => {
      userModal.classList.add('hidden');
      loadAllData();
    }, 1000);
  } catch (error) {
    formError.textContent = error.message;
    formError.classList.remove('hidden');

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

// Initialize
loadUserInfo();
loadAllData();
