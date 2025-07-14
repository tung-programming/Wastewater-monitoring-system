document.addEventListener('DOMContentLoaded', (event) => {
    const socket = io();
    const timerEl = document.getElementById('countdown-timer');
    let countdownInterval;

    // Function to start or reset the countdown timer
    function startCountdown() {
        clearInterval(countdownInterval); // Clear any existing timer
        let countdown = 5;
        timerEl.textContent = `Next update in ${countdown}s...`;

        countdownInterval = setInterval(() => {
            countdown--;
            if (countdown > 0) {
                timerEl.textContent = `Next update in ${countdown}s...`;
            } else {
                timerEl.textContent = 'Receiving new data...';
                clearInterval(countdownInterval);
            }
        }, 1000); // Update every second
    }

    socket.on('connect', () => {
        console.log('Connected to server!');
        document.getElementById('training-status-bar').textContent = "Waiting for initial data...";
    });

    function updateValue(elementId, value) {
        const element = document.getElementById(elementId);
        if (element.textContent !== String(value)) {
            element.textContent = value;
            element.classList.add('value-update');
            setTimeout(() => {
                element.classList.remove('value-update');
            }, 500);
        }
    }

    // This is the main function that runs every 5 seconds when data arrives
    socket.on('update_data', function(data) {
        console.log('Received data:', data);

        // --- Start the visual countdown for the next update ---
        startCountdown();

        // Update Input Values
        updateValue('ph-value', data.inputs.pH);
        updateValue('tds-value', data.inputs.TDS);
        updateValue('turbidity-value', data.inputs.Turbidity);
        updateValue('temp-value', data.inputs.Temperature);
        
        // Update Predicted Values
        updateValue('bod-value', data.predictions.BOD);
        updateValue('cod-value', data.predictions.COD);
        updateValue('do-value', data.predictions.DO);

        // Update Quality Status
        const qualityStatusEl = document.getElementById('quality-status');
        const qualityReasonsEl = document.getElementById('quality-reasons');
        qualityStatusEl.textContent = data.quality.status;
        qualityStatusEl.className = '';
        qualityStatusEl.classList.add(data.quality.status.toLowerCase());
        
        let reasonsHtml = '<ul>';
        data.quality.reasons.forEach(reason => {
            reasonsHtml += `<li>${reason}</li>`;
        });
        reasonsHtml += '</ul>';
        qualityReasonsEl.innerHTML = reasonsHtml;

        // Update Feature Importances with better formatting
        const importancesContainer = document.getElementById('importances-container');
        let importanceHtml = `
            <div class="importance-section">
                <strong>For BOD:</strong>
                <span class="details">${Object.entries(data.importances.BOD).map(([k,v]) => `${k}: ${v}%`).join(', ')}</span>
            </div>
            <div class="importance-section">
                <strong>For COD:</strong>
                <span class="details">${Object.entries(data.importances.COD).map(([k,v]) => `${k}: ${v}%`).join(', ')}</span>
            </div>
            <div class="importance-section">
                <strong>For DO:</strong>
                <span class="details">${Object.entries(data.importances.DO).map(([k,v]) => `${k}: ${v}%`).join(', ')}</span>
            </div>
        `;
        importancesContainer.innerHTML = importanceHtml;
    });

    socket.on('training_status', function(data) {
        console.log('Training status:', data.status);
        const statusBar = document.getElementById('training-status-bar');
        statusBar.textContent = data.status;
    });
});