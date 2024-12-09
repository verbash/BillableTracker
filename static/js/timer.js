// Timer Module - Only initialize if not already defined
if (typeof window.TimerModule === 'undefined') {
    window.TimerModule = (function() {
        let timerInterval = null;
        let startTime = null;
        let activeEntryId = null;

        const elements = {
            globalTimerDisplay: document.getElementById('global-timer-display'),
            headerTimerDisplay: document.getElementById('header-timer-display'),
            dashboardTimerDisplay: document.getElementById('timer-display'),
            startButton: document.getElementById('start-timer'),
            stopButton: document.getElementById('stop-timer'),
            clientSelect: document.querySelector('select[name="client_id"]')
        };

        function loadTimerState() {
            const storedStartTime = localStorage.getItem('timerStartTime');
            const storedEntryId = localStorage.getItem('activeEntryId');
            const storedClientId = localStorage.getItem('activeClientId');
            
            if (storedStartTime && storedEntryId) {
                startTime = new Date(parseInt(storedStartTime));
                activeEntryId = storedEntryId;
                
                if (elements.headerTimerDisplay) {
                    elements.headerTimerDisplay.classList.remove('d-none');
                }
                
                if (elements.startButton && elements.stopButton && elements.clientSelect) {
                    elements.startButton.disabled = true;
                    elements.stopButton.disabled = false;
                    elements.clientSelect.disabled = true;
                    if (storedClientId) {
                        elements.clientSelect.value = storedClientId;
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
            
            if (elements.globalTimerDisplay) {
                elements.globalTimerDisplay.textContent = timeString;
            }
            if (elements.dashboardTimerDisplay) {
                elements.dashboardTimerDisplay.textContent = timeString;
            }
        }

        function startTimer() {
            if (!timerInterval) {
                timerInterval = setInterval(updateTimer, 1000);
                updateTimer();
            }
        }

        function initializeEventListeners() {
            if (elements.startButton) {
                elements.startButton.addEventListener('click', async () => {
                    if (!elements.clientSelect.value) {
                        alert('Please select a client first');
                        return;
                    }
                    
                    const response = await fetch('/time/start', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                        },
                        body: `client_id=${elements.clientSelect.value}`
                    });
                    
                    const data = await response.json();
                    activeEntryId = data.id;
                    startTime = new Date();
                    
                    localStorage.setItem('timerStartTime', startTime.getTime());
                    localStorage.setItem('activeEntryId', activeEntryId);
                    localStorage.setItem('activeClientId', elements.clientSelect.value);
                    
                    if (elements.headerTimerDisplay) {
                        elements.headerTimerDisplay.classList.remove('d-none');
                    }
                    startTimer();
                    
                    elements.startButton.disabled = true;
                    elements.stopButton.disabled = false;
                    elements.clientSelect.disabled = true;
                });
            }

            if (elements.stopButton) {
                elements.stopButton.addEventListener('click', async () => {
                    clearInterval(timerInterval);
                    timerInterval = null;
                    
                    await fetch(`/time/stop/${activeEntryId}`, {
                        method: 'POST'
                    });
                    
                    localStorage.removeItem('timerStartTime');
                    localStorage.removeItem('activeEntryId');
                    localStorage.removeItem('activeClientId');
                    
                    if (elements.headerTimerDisplay) {
                        elements.headerTimerDisplay.classList.add('d-none');
                    }
                    if (elements.globalTimerDisplay) {
                        elements.globalTimerDisplay.textContent = '00:00:00';
                    }
                    if (elements.dashboardTimerDisplay) {
                        elements.dashboardTimerDisplay.textContent = '00:00:00';
                    }
                    
                    elements.startButton.disabled = false;
                    elements.stopButton.disabled = true;
                    elements.clientSelect.disabled = false;
                    activeEntryId = null;
                });
            }
        }

        // Initialize when DOM is loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                loadTimerState();
                initializeEventListeners();
            });
        } else {
            loadTimerState();
            initializeEventListeners();
        }

        // Return public methods if needed
        return {
            loadTimerState,
            startTimer
        };
    })();
}
