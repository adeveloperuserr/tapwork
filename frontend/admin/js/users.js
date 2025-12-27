const API_BASE = 'http://localhost:8000';

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
const usersTable = document.getElementById('usersTable');
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
    usersTable.innerHTML = '<tr><td colspan="9" class="text-center">No hay usuarios</td></tr>';
    return;
  }

  usersTable.innerHTML = users.map(user => `
    <tr>
      <td><strong>${user.employee_id}</strong></td>
      <td>${user.first_name} ${user.last_name}</td>
      <td>${user.email}</td>
      <td>${user.role ? user.role.name : '-'}</td>
      <td>${user.department ? user.department.name : '-'}</td>
      <td>${user.shift ? user.shift.name : '-'}</td>
      <td>
        ${user.qr_code ?
          `<button class="btn btn-secondary btn-sm" onclick="viewBarcode('${user.id}', '${user.employee_id}')">Ver Código</button>` :
          '<span class="badge badge-warning">Sin código</span>'
        }
      </td>
      <td>
        <span class="badge ${user.is_active ? 'badge-success' : 'badge-danger'}">
          ${user.is_active ? 'Activo' : 'Inactivo'}
        </span>
      </td>
      <td>
        <div class="flex gap-2">
          <button class="btn btn-secondary btn-sm btn-icon" onclick="editUser('${user.id}')" title="Editar">
            ✏️
          </button>
          <button class="btn btn-danger btn-sm btn-icon" onclick="deleteUser('${user.id}', '${user.first_name} ${user.last_name}')" title="Eliminar">
            🗑️
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
