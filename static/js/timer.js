let timerInterval;
let startTime;
let activeEntryId;

const globalTimerDisplay = document.getElementById('global-timer-display');
const headerTimerDisplay = document.getElementById('header-timer-display');
const dashboardTimerDisplay = document.getElementById('timer-display');
const startButton = document.getElementById('start-timer');
const stopButton = document.getElementById('stop-timer');
const clientSelect = document.querySelector('select[name="client_id"]');

// Load timer state from localStorage
function loadTimerState() {
    const storedStartTime = localStorage.getItem('timerStartTime');
    const storedEntryId = localStorage.getItem('activeEntryId');
    const storedClientId = localStorage.getItem('activeClientId');
    
    if (storedStartTime && storedEntryId) {
        startTime = new Date(parseInt(storedStartTime));
        activeEntryId = storedEntryId;
        headerTimerDisplay.classList.remove('d-none');
        
        if (startButton && stopButton && clientSelect) {
            startButton.disabled = true;
            stopButton.disabled = false;
            clientSelect.disabled = true;
            if (storedClientId) {
                clientSelect.value = storedClientId;
            }
        }
        
        startTimer();
    }
}

function updateTimer() {
    const now = new Date();
    const diff = now - startTime;
    const hours = Math.floor(diff / 3600000);
    const minutes = Math.floor((diff % 3600000) / 60000);
    const seconds = Math.floor((diff % 60000) / 1000);
    
    const timeString = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    
    if (globalTimerDisplay) {
        globalTimerDisplay.textContent = timeString;
    }
    if (dashboardTimerDisplay) {
        dashboardTimerDisplay.textContent = timeString;
    }
}

function startTimer() {
    if (!timerInterval) {
        timerInterval = setInterval(updateTimer, 1000);
        updateTimer();
    }
}

// Initialize timer state when the page loads
document.addEventListener('DOMContentLoaded', loadTimerState);

if (startButton) {
    startButton.addEventListener('click', async () => {
        if (!clientSelect.value) {
            alert('Please select a client first');
            return;
        }
        
        const response = await fetch('/time/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `client_id=${clientSelect.value}`
        });
        
        const data = await response.json();
        activeEntryId = data.id;
        startTime = new Date();
        
        // Store timer state
        localStorage.setItem('timerStartTime', startTime.getTime());
        localStorage.setItem('activeEntryId', activeEntryId);
        localStorage.setItem('activeClientId', clientSelect.value);
        
        headerTimerDisplay.classList.remove('d-none');
        startTimer();
        
        startButton.disabled = true;
        stopButton.disabled = false;
        clientSelect.disabled = true;
    });
}

if (stopButton) {
    stopButton.addEventListener('click', async () => {
        clearInterval(timerInterval);
        timerInterval = null;
        
        await fetch(`/time/stop/${activeEntryId}`, {
            method: 'POST'
        });
        
        // Clear timer state
        localStorage.removeItem('timerStartTime');
        localStorage.removeItem('activeEntryId');
        localStorage.removeItem('activeClientId');
        
        headerTimerDisplay.classList.add('d-none');
        if (globalTimerDisplay) globalTimerDisplay.textContent = '00:00:00';
        if (dashboardTimerDisplay) dashboardTimerDisplay.textContent = '00:00:00';
        
        startButton.disabled = false;
        stopButton.disabled = true;
        clientSelect.disabled = false;
        activeEntryId = null;
    });
}
