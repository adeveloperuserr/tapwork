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

// Current user data
let currentUser = null;

// Load user info
async function loadUserInfo() {
  try {
    const res = await fetch(`${API_BASE}/api/auth/me`, {
      headers: authHeaders
    });

    if (!res.ok) throw new Error('No autorizado');

    currentUser = await res.json();

    // Update UI
    document.getElementById('userName').textContent = `${currentUser.first_name} ${currentUser.last_name}`;
    document.getElementById('userAvatar').textContent = currentUser.first_name.charAt(0).toUpperCase();

    document.getElementById('fullName').textContent = `${currentUser.first_name} ${currentUser.last_name}`;
    document.getElementById('email').textContent = currentUser.email;
    document.getElementById('employeeId').textContent = currentUser.employee_id;
    document.getElementById('department').textContent = currentUser.department ? currentUser.department.name : '-';
    document.getElementById('shift').textContent = currentUser.shift ? currentUser.shift.name : '-';
    document.getElementById('role').textContent = currentUser.role ? currentUser.role.name : '-';

    // Load barcode
    loadBarcode();
  } catch (error) {
    console.error('Error loading user:', error);
    localStorage.removeItem('access_token');
    window.location.href = 'login.html';
  }
}

// Load barcode
function loadBarcode() {
  if (!currentUser || !currentUser.employee_id) return;

  try {
    JsBarcode("#barcodeCanvas", currentUser.employee_id, {
      format: "CODE128",
      width: 2,
      height: 100,
      displayValue: true,
      fontSize: 20
    });
    document.querySelector('.barcode-id').textContent = currentUser.employee_id;
  } catch (error) {
    console.error('Error generating barcode:', error);
  }
}

// Download barcode
window.downloadBarcode = function() {
  const canvas = document.getElementById('barcodeCanvas');
  const link = document.createElement('a');
  link.download = `barcode_${currentUser.employee_id}.png`;
  link.href = canvas.toDataURL();
  link.click();
};

// Resend barcode email
window.resendBarcodeEmail = async function() {
  try {
    const res = await fetch(`${API_BASE}/api/user/resend-barcode`, {
      method: 'POST',
      headers: authHeaders
    });

    if (!res.ok) throw new Error('Error al enviar email');

    const success = document.getElementById('barcodeSuccess');
    success.textContent = 'Código de barras enviado a tu email';
    success.classList.remove('hidden');
    setTimeout(() => success.classList.add('hidden'), 5000);
  } catch (error) {
    alert('Error al enviar el código de barras: ' + error.message);
  }
};

// Change password form
document.getElementById('passwordForm').addEventListener('submit', async (e) => {
  e.preventDefault();

  const currentPassword = document.getElementById('currentPassword').value;
  const newPassword = document.getElementById('newPassword').value;
  const confirmPassword = document.getElementById('confirmPassword').value;

  const errorDiv = document.getElementById('passwordError');
  const successDiv = document.getElementById('passwordSuccess');

  errorDiv.classList.add('hidden');
  successDiv.classList.add('hidden');

  // Validations
  if (newPassword !== confirmPassword) {
    errorDiv.textContent = 'Las contraseñas no coinciden';
    errorDiv.classList.remove('hidden');
    return;
  }

  if (newPassword.length < 8) {
    errorDiv.textContent = 'La contraseña debe tener al menos 8 caracteres';
    errorDiv.classList.remove('hidden');
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/user/change-password`, {
      method: 'POST',
      headers: authHeaders,
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword
      })
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || 'Error al cambiar la contraseña');
    }

    successDiv.textContent = '¡Contraseña actualizada exitosamente!';
    successDiv.classList.remove('hidden');
    document.getElementById('passwordForm').reset();
  } catch (error) {
    errorDiv.textContent = error.message;
    errorDiv.classList.remove('hidden');
  }
});

// Load attendance history
async function loadAttendance() {
  try {
    const res = await fetch(`${API_BASE}/api/user/attendance-history`, {
      headers: authHeaders
    });

    if (!res.ok) throw new Error('Error al cargar asistencias');

    const records = await res.json();

    const tbody = document.getElementById('attendanceTable');

    if (records.length === 0) {
      tbody.innerHTML = '<tr><td colspan="4" class="text-center">No hay registros de asistencia</td></tr>';
      return;
    }

    tbody.innerHTML = records.map(record => {
      const checkIn = new Date(record.check_in);
      const checkOut = record.check_out ? new Date(record.check_out) : null;

      let hoursWorked = '-';
      if (checkOut) {
        const diff = checkOut - checkIn;
        const hours = Math.floor(diff / 1000 / 60 / 60);
        const minutes = Math.floor((diff / 1000 / 60) % 60);
        hoursWorked = `${hours}h ${minutes}m`;
      }

      return `
        <tr>
          <td>${checkIn.toLocaleDateString()}</td>
          <td>${checkIn.toLocaleTimeString()}</td>
          <td>${checkOut ? checkOut.toLocaleTimeString() : '-'}</td>
          <td>${hoursWorked}</td>
        </tr>
      `;
    }).join('');
  } catch (error) {
    console.error('Error loading attendance:', error);
    document.getElementById('attendanceTable').innerHTML =
      '<tr><td colspan="4" class="text-center text-danger">Error al cargar asistencias</td></tr>';
  }
}

// Show section
window.showSection = function(section) {
  // Hide all sections
  document.getElementById('profileSection').classList.add('hidden');
  document.getElementById('passwordSection').classList.add('hidden');
  document.getElementById('barcodeSection').classList.add('hidden');
  document.getElementById('attendanceSection').classList.add('hidden');

  // Remove active from all nav links
  document.querySelectorAll('.nav-link').forEach(link => {
    link.classList.remove('active');
  });

  // Show selected section
  if (section === 'password') {
    document.getElementById('passwordSection').classList.remove('hidden');
  } else if (section === 'barcode') {
    document.getElementById('barcodeSection').classList.remove('hidden');
  } else if (section === 'attendance') {
    document.getElementById('attendanceSection').classList.remove('hidden');
    loadAttendance();
  } else {
    document.getElementById('profileSection').classList.remove('hidden');
  }
};

// Logout
document.getElementById('logoutBtn').addEventListener('click', () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('user');
  window.location.href = 'login.html';
});

// Load initial data
loadUserInfo();
