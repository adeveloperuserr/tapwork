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
let shifts = [];
let currentShift = null;
let shiftToDelete = null;

// Day names mapping
const dayNames = {
    0: 'Dom',
    1: 'Lun',
    2: 'Mar',
    3: 'Mié',
    4: 'Jue',
    5: 'Vie',
    6: 'Sáb'
};

// DOM Elements
const shiftsGrid = document.getElementById('shiftsGrid');
const emptyState = document.getElementById('emptyState');
const searchInput = document.getElementById('searchInput');
const createShiftBtn = document.getElementById('createShiftBtn');
const shiftModal = document.getElementById('shiftModal');
const deleteModal = document.getElementById('deleteModal');
const shiftForm = document.getElementById('shiftForm');
const modalTitle = document.getElementById('modalTitle');
const closeModal = document.getElementById('closeModal');
const cancelBtn = document.getElementById('cancelBtn');
const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
const logoutBtn = document.getElementById('logoutBtn');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadCurrentUser();
    loadShifts();
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

// Load all shifts
async function loadShifts() {
    try {
        const res = await fetch(`${API_BASE}/api/admin/shifts`, {
            headers: authHeaders
        });

        if (!res.ok) throw new Error('Error loading shifts');

        shifts = await res.json();
        renderShifts(shifts);
    } catch (error) {
        console.error('Error loading shifts:', error);
        showError('Error al cargar los turnos');
    }
}

// Format time for display
function formatTime(timeStr) {
    if (!timeStr) return '-';
    // timeStr comes as "HH:MM:SS" from backend
    const [hours, minutes] = timeStr.split(':');
    return `${hours}:${minutes}`;
}

// Format working days
function formatWorkingDays(days) {
    if (!days || days.length === 0) return 'Ninguno';
    return days.sort((a, b) => a - b).map(d => dayNames[d]).join(', ');
}

// Render shifts
function renderShifts(shiftsData) {
    if (shiftsData.length === 0) {
        shiftsGrid.classList.add('hidden');
        emptyState.classList.remove('hidden');
        return;
    }

    shiftsGrid.classList.remove('hidden');
    emptyState.classList.add('hidden');

    shiftsGrid.innerHTML = shiftsData.map(shift => `
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 hover:shadow-md transition-shadow">
            <div class="p-6">
                <div class="flex items-start justify-between mb-4">
                    <div class="flex items-center space-x-3">
                        <div class="flex items-center justify-center w-12 h-12 bg-primary-100 rounded-lg">
                            <svg class="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                            </svg>
                        </div>
                        <div>
                            <h3 class="font-bold text-lg text-gray-900">${shift.name}</h3>
                            <p class="text-sm text-gray-500">Creado: ${new Date(shift.created_at).toLocaleDateString('es-ES')}</p>
                        </div>
                    </div>
                </div>

                <div class="space-y-3 mb-4">
                    <div class="flex items-center text-sm">
                        <svg class="w-4 h-4 mr-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                        <span class="text-gray-600">Horario:</span>
                        <span class="ml-2 font-semibold text-gray-900">${formatTime(shift.start_time)} - ${formatTime(shift.end_time)}</span>
                    </div>

                    <div class="flex items-center text-sm">
                        <svg class="w-4 h-4 mr-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                        <span class="text-gray-600">Gracia:</span>
                        <span class="ml-2 font-semibold text-gray-900">${shift.grace_period_minutes} min</span>
                    </div>

                    <div class="flex items-start text-sm">
                        <svg class="w-4 h-4 mr-2 mt-0.5 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                        </svg>
                        <div class="flex-1">
                            <span class="text-gray-600">Días:</span>
                            <div class="mt-1">
                                <span class="font-medium text-gray-900">${formatWorkingDays(shift.working_days)}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="flex space-x-2 pt-4 border-t border-gray-200">
                    <button onclick="editShift('${shift.id}')" class="flex-1 inline-flex items-center justify-center px-3 py-2 bg-primary-50 text-primary-700 font-medium rounded-lg hover:bg-primary-100 transition-colors">
                        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                        </svg>
                        Editar
                    </button>
                    <button onclick="confirmDelete('${shift.id}')" class="inline-flex items-center justify-center px-3 py-2 bg-red-50 text-red-700 font-medium rounded-lg hover:bg-red-100 transition-colors">
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
    const filtered = shifts.filter(shift =>
        shift.name.toLowerCase().includes(searchTerm)
    );
    renderShifts(filtered);
});

// Open create modal
createShiftBtn.addEventListener('click', () => {
    currentShift = null;
    modalTitle.textContent = 'Nuevo Turno';
    shiftForm.reset();

    // Set default working days (Mon-Fri)
    document.querySelectorAll('.day-checkbox').forEach(cb => {
        cb.checked = ['1', '2', '3', '4', '5'].includes(cb.value);
    });

    shiftModal.classList.remove('hidden');
});

// Edit shift
window.editShift = (id) => {
    currentShift = shifts.find(s => s.id === id);
    if (!currentShift) return;

    modalTitle.textContent = 'Editar Turno';
    document.getElementById('shiftName').value = currentShift.name;
    document.getElementById('startTime').value = formatTime(currentShift.start_time);
    document.getElementById('endTime').value = formatTime(currentShift.end_time);
    document.getElementById('gracePeriod').value = currentShift.grace_period_minutes;

    // Set working days
    document.querySelectorAll('.day-checkbox').forEach(cb => {
        cb.checked = currentShift.working_days.includes(parseInt(cb.value));
    });

    shiftModal.classList.remove('hidden');
};

// Close modal handlers
closeModal.addEventListener('click', () => {
    shiftModal.classList.add('hidden');
});

cancelBtn.addEventListener('click', () => {
    shiftModal.classList.add('hidden');
});

// Form submit
shiftForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    // Get selected working days
    const workingDays = Array.from(document.querySelectorAll('.day-checkbox:checked'))
        .map(cb => parseInt(cb.value));

    if (workingDays.length === 0) {
        showError('Debes seleccionar al menos un día laboral');
        return;
    }

    const payload = {
        name: document.getElementById('shiftName').value.trim(),
        start_time: document.getElementById('startTime').value + ':00',  // Add seconds
        end_time: document.getElementById('endTime').value + ':00',      // Add seconds
        grace_period_minutes: parseInt(document.getElementById('gracePeriod').value) || 0,
        working_days: workingDays
    };

    try {
        const url = currentShift
            ? `${API_BASE}/api/admin/shifts/${currentShift.id}`
            : `${API_BASE}/api/admin/shifts`;

        const method = currentShift ? 'PATCH' : 'POST';

        const res = await fetch(url, {
            method,
            headers: authHeaders,
            body: JSON.stringify(payload)
        });

        if (!res.ok) {
            const error = await res.json();
            throw new Error(error.detail || 'Error al guardar el turno');
        }

        shiftModal.classList.add('hidden');
        loadShifts();
        showSuccess(currentShift ? 'Turno actualizado correctamente' : 'Turno creado correctamente');
    } catch (error) {
        console.error('Error saving shift:', error);
        showError(error.message);
    }
});

// Confirm delete
window.confirmDelete = (id) => {
    shiftToDelete = id;
    deleteModal.classList.remove('hidden');
};

// Cancel delete
cancelDeleteBtn.addEventListener('click', () => {
    deleteModal.classList.add('hidden');
    shiftToDelete = null;
});

// Execute delete
confirmDeleteBtn.addEventListener('click', async () => {
    if (!shiftToDelete) return;

    try {
        const res = await fetch(`${API_BASE}/api/admin/shifts/${shiftToDelete}`, {
            method: 'DELETE',
            headers: authHeaders
        });

        if (!res.ok) {
            const error = await res.json();
            throw new Error(error.detail || 'Error al eliminar el turno');
        }

        deleteModal.classList.add('hidden');
        shiftToDelete = null;
        loadShifts();
        showSuccess('Turno eliminado correctamente');
    } catch (error) {
        console.error('Error deleting shift:', error);
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
