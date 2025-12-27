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

    // Update header
    document.getElementById('headerName').textContent = `${currentUser.first_name} ${currentUser.last_name}`;
    document.getElementById('headerEmail').textContent = currentUser.email;
    document.getElementById('headerEmployeeId').textContent = currentUser.employee_id;
    document.getElementById('headerAvatar').textContent = currentUser.first_name.charAt(0).toUpperCase();

    // Update profile info
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
      width: 3,
      height: 120,
      displayValue: true,
      fontSize: 20,
      margin: 10
    });
    document.getElementById('barcodeEmployeeId').textContent = currentUser.employee_id;
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
    success.textContent = '✅ Código de barras enviado a tu email exitosamente';
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
    errorDiv.textContent = '❌ Las contraseñas no coinciden';
    errorDiv.classList.remove('hidden');
    return;
  }

  if (newPassword.length < 8) {
    errorDiv.textContent = '❌ La contraseña debe tener al menos 8 caracteres';
    errorDiv.classList.remove('hidden');
    return;
  }

  if (!/[A-Z]/.test(newPassword) || !/[a-z]/.test(newPassword) || !/[0-9]/.test(newPassword)) {
    errorDiv.textContent = '❌ La contraseña debe incluir mayúsculas, minúsculas y números';
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

    successDiv.textContent = '✅ ¡Contraseña actualizada exitosamente!';
    successDiv.classList.remove('hidden');
    document.getElementById('passwordForm').reset();

    // Auto hide after 5 seconds
    setTimeout(() => successDiv.classList.add('hidden'), 5000);
  } catch (error) {
    errorDiv.textContent = '❌ ' + error.message;
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
      tbody.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 40px; color: #6b7280;">No hay registros de asistencia en los últimos 30 días</td></tr>';
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
          <td><strong>${checkIn.toLocaleDateString('es-MX', { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' })}</strong></td>
          <td>${checkIn.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' })}</td>
          <td>${checkOut ? checkOut.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' }) : '<span style="color: #ef4444;">Sin salida</span>'}</td>
          <td><strong>${hoursWorked}</strong></td>
        </tr>
      `;
    }).join('');
  } catch (error) {
    console.error('Error loading attendance:', error);
    document.getElementById('attendanceTable').innerHTML =
      '<tr><td colspan="4" style="text-align: center; padding: 40px; color: #ef4444;">❌ Error al cargar asistencias</td></tr>';
  }
}

// Show section
window.showSection = function(section) {
  // Hide all sections
  document.getElementById('profileSection').classList.add('section-hidden');
  document.getElementById('passwordSection').classList.add('section-hidden');
  document.getElementById('barcodeSection').classList.add('section-hidden');
  document.getElementById('attendanceSection').classList.add('section-hidden');

  // Remove active from all nav buttons
  document.querySelectorAll('.profile-nav-btn').forEach(btn => {
    btn.classList.remove('active');
  });

  // Show selected section and activate button
  const buttons = document.querySelectorAll('.profile-nav-btn');
  if (section === 'profile') {
    document.getElementById('profileSection').classList.remove('section-hidden');
    buttons[0].classList.add('active');
  } else if (section === 'password') {
    document.getElementById('passwordSection').classList.remove('section-hidden');
    buttons[1].classList.add('active');
  } else if (section === 'barcode') {
    document.getElementById('barcodeSection').classList.remove('section-hidden');
    buttons[2].classList.add('active');
  } else if (section === 'attendance') {
    document.getElementById('attendanceSection').classList.remove('section-hidden');
    buttons[3].classList.add('active');
    loadAttendance();
  }
};

// Logout
document.getElementById('logoutBtn').addEventListener('click', () => {
  if (confirm('¿Estás seguro de que deseas cerrar sesión?')) {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    window.location.href = 'login.html';
  }
});

// Load initial data
loadUserInfo();
