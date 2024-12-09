let timerInterval;
let startTime;
let activeEntryId;

const timerDisplay = document.getElementById('timer-display');
const startButton = document.getElementById('start-timer');
const stopButton = document.getElementById('stop-timer');
const clientSelect = document.querySelector('select[name="client_id"]');

function updateTimer() {
    const now = new Date();
    const diff = now - startTime;
    const hours = Math.floor(diff / 3600000);
    const minutes = Math.floor((diff % 3600000) / 60000);
    const seconds = Math.floor((diff % 60000) / 1000);
    
    timerDisplay.textContent = 
        `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
}

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
    timerInterval = setInterval(updateTimer, 1000);
    
    startButton.disabled = true;
    stopButton.disabled = false;
    clientSelect.disabled = true;
});

stopButton.addEventListener('click', async () => {
    clearInterval(timerInterval);
    
    await fetch(`/time/stop/${activeEntryId}`, {
        method: 'POST'
    });
    
    timerDisplay.textContent = '00:00:00';
    startButton.disabled = false;
    stopButton.disabled = true;
    clientSelect.disabled = false;
    activeEntryId = null;
});
