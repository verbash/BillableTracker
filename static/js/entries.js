document.addEventListener('DOMContentLoaded', function() {
    // Initialize date filters with current week
    const today = new Date();
    const startOfWeek = new Date(today.setDate(today.getDate() - today.getDay()));
    const endOfWeek = new Date(today.setDate(today.getDate() - today.getDay() + 6));
    
    document.getElementById('start-date').value = startOfWeek.toISOString().split('T')[0];
    document.getElementById('end-date').value = endOfWeek.toISOString().split('T')[0];
    
    loadTimeEntries();
    
    // Event listeners for period buttons
    document.querySelectorAll('[data-period]').forEach(button => {
        button.addEventListener('click', function() {
            const period = this.dataset.period;
            const today = new Date();
            let start, end;
            
            if (period === 'week') {
                start = new Date(today.setDate(today.getDate() - today.getDay()));
                end = new Date(today.setDate(today.getDate() - today.getDay() + 6));
            } else if (period === 'month') {
                start = new Date(today.getFullYear(), today.getMonth(), 1);
                end = new Date(today.getFullYear(), today.getMonth() + 1, 0);
            }
            
            document.getElementById('start-date').value = start.toISOString().split('T')[0];
            document.getElementById('end-date').value = end.toISOString().split('T')[0];
            loadTimeEntries();
        });
    });
    
    // Filter button click handler
    document.getElementById('filter-dates').addEventListener('click', loadTimeEntries);
    
    // Edit entry form submission
    document.getElementById('editEntryForm').addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        const entryId = formData.get('entry_id');
        
        fetch(`/time/edit/${entryId}`, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                bootstrap.Modal.getInstance(document.getElementById('editEntryModal')).hide();
                loadTimeEntries();
            }
        });
    });
});

function formatDateTime(isoString) {
    const date = new Date(isoString);
    const options = {
        timeZone: userTimezone,
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    };
    return new Intl.DateTimeFormat('en-US', options).format(date);
}

function formatTime(isoString) {
    if (!isoString) return '-';
    const date = new Date(isoString);
    const options = {
        timeZone: userTimezone,
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    };
    return new Intl.DateTimeFormat('en-US', options).format(date);
}

function formatDate(isoString) {
    const date = new Date(isoString);
    const options = {
        timeZone: userTimezone,
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    };
    return new Intl.DateTimeFormat('en-US', options).format(date);
}

function loadTimeEntries() {
    const startDate = document.getElementById('start-date').value;
    const endDate = document.getElementById('end-date').value;
    
    fetch(`/time/entries?start=${startDate}&end=${endDate}`)
        .then(response => response.json())
        .then(data => {
            const tbody = document.getElementById('entries-table-body');
            tbody.innerHTML = '';
            let totalHours = 0;
            
            data.entries.forEach(entry => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${formatDate(entry.start_time)}</td>
                    <td>${entry.client_name}</td>
                    <td>${formatTime(entry.start_time)}</td>
                    <td>${formatTime(entry.end_time)}</td>
                    <td>${entry.duration ? entry.duration.toFixed(2) : '-'}</td>
                    <td>${entry.notes || ''}</td>
                    <td>
                        <div class="btn-group">
                            <button class="btn btn-sm btn-outline-secondary" onclick="editEntry(${entry.id})">
                                <i data-feather="edit-2"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="deleteEntry(${entry.id})">
                                <i data-feather="trash-2"></i>
                            </button>
                        </div>
                    </td>
                `;
                
                totalHours += entry.duration || 0;
                tbody.appendChild(row);
            });
            
            document.getElementById('total-hours').textContent = totalHours.toFixed(2);
            feather.replace();
        });
}

function editEntry(entryId) {
    fetch(`/time/entry/${entryId}`)
        .then(response => response.json())
        .then(data => {
            const form = document.getElementById('editEntryForm');
            form.elements.entry_id.value = data.id;
            form.elements.start_time.value = data.start_time.slice(0, 16);
            if (data.end_time) {
                form.elements.end_time.value = data.end_time.slice(0, 16);
            }
            form.elements.notes.value = data.notes || '';
            
            new bootstrap.Modal(document.getElementById('editEntryModal')).show();
        });
}

function deleteEntry(entryId) {
    if (confirm('Are you sure you want to delete this time entry?')) {
        fetch(`/time/delete/${entryId}`, { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    loadTimeEntries();
                }
            });
    }
}
