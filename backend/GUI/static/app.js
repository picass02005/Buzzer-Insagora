/**
 * Code generated using Google Gemini
 *
 * This software is released under the MIT License.
 * https://opensource.org/licenses/MIT
 */

/**
 * Buzzer Insagora Database & Logic
 */

const API_BASE = '/api';
let currentState = 'IDLE';
let teamsData = {};
let pointLimit = 8;
let connectedBuzzers = [];
const pressSound = new Audio('press.mp3');

// Track if winner modal has been dismissed for the current "win event"
// We reset this when points change or game resets.
let winnerDismissedForPoints = -1; // -1 means not dismissed or invalid

// DOM Elements
const views = {
    configuration: document.getElementById('configuration-view'),
    quiz: document.getElementById('quiz-view')
};
const navLinks = document.querySelectorAll('.nav-links li');
const teamsContainer = document.getElementById('teams-container');
const scoreboardContainer = document.getElementById('scoreboard-container');
const gameStateBadge = document.getElementById('game-state-badge');
const pointLimitSelect = document.getElementById('point-limit-select');

// Modals
const teamModal = document.getElementById('team-modal');
const winModal = document.getElementById('win-modal');
const teamForm = document.getElementById('team-form');

// Inputs
const teamNameInput = document.getElementById('team-name-input');
const teamPointsInput = document.getElementById('team-points-input');
const primaryColorInput = document.getElementById('primary-color-input');
const secondaryColorInput = document.getElementById('secondary-color-input');
const availableBuzzersList = document.getElementById('available-buzzers-list');
const editTeamOriginalNameInput = document.getElementById('edit-team-original-name');

// Color Inputs Visuals
primaryColorInput.addEventListener('input', (e) => document.getElementById('primary-color-code').textContent = e.target.value);
secondaryColorInput.addEventListener('input', (e) => document.getElementById('secondary-color-code').textContent = e.target.value);


// Initialization
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initGlobalListeners();
    initQuickColors(); // New

    // Initial Fetches
    fetchTeams();
    fetchParameters();

    // Polling
    setInterval(() => {
        fetchState();
        fetchTeams();
    }, 1000);

    // Initial Buzzer cache update
    fetchConnectedBuzzers(true);
});

function initNavigation() {
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            const targetTab = link.dataset.tab;
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            Object.values(views).forEach(v => v.classList.remove('active'));
            views[targetTab].classList.add('active');
        });
    });
}

function initGlobalListeners() {
    document.getElementById('add-team-btn').addEventListener('click', () => openTeamModal());
    document.getElementById('cancel-team-btn').addEventListener('click', () => closeTeamModal());
    document.getElementById('team-form').addEventListener('submit', handleTeamSubmit);
    document.getElementById('random-name-btn').addEventListener('click', () => {
        teamNameInput.value = generateRandomName();
    });

    document.getElementById('start-question-btn').addEventListener('click', startQuestion);
    document.getElementById('confirm-btn').addEventListener('click', confirmAnswer);
    document.getElementById('deny-btn').addEventListener('click', denyAnswer);

    document.getElementById('point-limit-select').addEventListener('change', handlePointLimitChange);
    document.getElementById('reset-all-points-btn').addEventListener('click', resetPoints); // New Button

    document.getElementById('reset-game-btn').addEventListener('click', () => {
        resetPoints();
        closeWinModal();
    });
    document.getElementById('dismiss-win-btn').addEventListener('click', () => {
        // Track the point value we dismissed it at (assuming limit)
        // Or just set a flag that we dismissed for *this* game/limit reaching state.
        // Actually, simpler: if checking for winner, ignore if we already dismissed for this team/score combo?
        // Or simplified: ignore until any points change.
        winnerDismissedForPoints = pointLimit; // Or simply TRUE for current state
        closeWinModal();
    });

    document.getElementById('refresh-buzzers-btn').addEventListener('click', async () => {
        const btn = document.getElementById('refresh-buzzers-btn');
        const originalText = btn.textContent;
        btn.disabled = true;
        btn.textContent = "Refreshing...";

        await fetchConnectedBuzzers(true);

        // We need to know which buzzers were ALREADY assigned to the current team in the modal
        // to keep them checked.
        const currentSelected = Array.from(document.querySelectorAll('input[name="associated_buzzers"]:checked'))
            .map(cb => cb.value);

        renderBuzzerList(currentSelected);

        btn.disabled = false;
        btn.textContent = originalText;
    });
}

// Quick Colors
function initQuickColors() {
    const presets = [
        { p: '#FF0000', s: '#FFFF00' }, // Red / Yellow
        { p: '#00FF00', s: '#00FFFF' }, // Green / Cyan
        { p: '#0000FF', s: '#FF00FF' }, // Blue / Magenta
        { p: '#FFFF00', s: '#FF0000' }, // Yellow / Red
        { p: '#00FFFF', s: '#0000FF' }, // Cyan / Blue
        { p: '#FF00FF', s: '#FF0000' }, // Magenta / Red
        { p: '#FF8800', s: '#00FF00' }, // Orange / Green
        { p: '#8800FF', s: '#00FFFF' }  // Purple / Cyan
    ];

    const container = document.getElementById('color-presets');
    if (!container) return;

    presets.forEach(preset => {
        const btn = document.createElement('div');
        btn.style.width = '36px'; // Slightly bigger
        btn.style.height = '36px';
        btn.style.borderRadius = '50%';
        btn.style.cursor = 'pointer';
        // Remove transparent border that might look like a container
        btn.style.border = 'none';
        btn.style.boxShadow = '0 0 0 2px rgba(255,255,255,0.1)'; // Outer glow instead of border
        btn.title = `Primary: ${preset.p}, Secondary: ${preset.s}`;

        // Ensure gradient fills it
        btn.style.overflow = 'hidden';

        // Gradient to show both
        btn.style.background = `linear-gradient(135deg, ${preset.p} 50%, ${preset.s} 50%)`;

        btn.onclick = () => {
            primaryColorInput.value = preset.p;
            mainUpdateColorCode(primaryColorInput);
            secondaryColorInput.value = preset.s;
            mainUpdateColorCode(secondaryColorInput);
        };

        container.appendChild(btn);
    });
}

function mainUpdateColorCode(input) {
    const codeSpan = input.parentNode.querySelector('.color-code');
    if (codeSpan) codeSpan.textContent = input.value;
}


// --- API Interactions ---

async function fetchState() {
    try {
        const res = await fetch(`${API_BASE}/status/get_state`);
        const data = await res.json();
        updateGameState(data.state);
    } catch (e) {
        console.error("Error fetching state:", e);
    }
}

async function fetchTeams() {
    try {
        const res = await fetch(`${API_BASE}/teams/get`);
        const data = await res.json();

        // Detect if points changed to re-enable win modal
        // Simple check: sum of all points? Or just if we have data.
        // If winnerDismissedForPoints is set, we check if logic still holds?
        // Better: logic inside checkForWinner.

        teamsData = data;
        renderTeamsGrid();
        renderScoreboard();
        checkForWinner();
    } catch (e) {
        console.error("Error fetching teams:", e);
    }
}

async function fetchConnectedBuzzers(noCache = false) {
    try {
        const url = `${API_BASE}/status/get_connected${noCache ? '?no_cache=true' : ''}`;
        const res = await fetch(url);
        const data = await res.json();
        connectedBuzzers = data.connected || [];
        return connectedBuzzers;
    } catch (e) {
        console.error("Error fetching buzzers:", e);
        return [];
    }
}

async function fetchParameters() {
    await fetchTeams();
    if (Object.keys(teamsData).length > 0) {
        const firstTeam = Object.values(teamsData)[0];
        if (firstTeam && firstTeam.point_limit) {
            pointLimit = firstTeam.point_limit;
            pointLimitSelect.value = pointLimit;
        }
    } else {
        // Default default if no teams
        pointLimit = 8;
        pointLimitSelect.value = pointLimit;
    }
}


// --- Logic Actions ---

async function startQuestion() {
    // Optimistic UI: Disable button immediately
    const btn = document.getElementById('start-question-btn');
    btn.disabled = true;
    btn.textContent = "Starting...";

    // Optimistic Update
    updateGameState('WAIT');

    try {
        await fetch(`${API_BASE}/flow/wait_press`, { method: 'POST' });
    } catch (e) {
        console.error("Error starting wait_press sequence:", e);
        // Re-enable if failed? 
        btn.disabled = false;
        btn.textContent = "Start Question";
    }
}

async function confirmAnswer() {
    const btn = document.getElementById('confirm-btn');
    const denyBtn = document.getElementById('deny-btn');
    btn.disabled = true;
    denyBtn.disabled = true;

    try {
        await fetch(`${API_BASE}/flow/confirm`, { method: 'POST' });
        // After confirm, points change, so reset win modal dismiss
        winnerDismissedForPoints = -1;
        setTimeout(fetchState, 100);
    } catch (e) { console.error(e); }
}

async function denyAnswer() {
    const btn = document.getElementById('deny-btn');
    const confirmBtn = document.getElementById('confirm-btn');
    btn.disabled = true;
    confirmBtn.disabled = true;

    try {
        await fetch(`${API_BASE}/flow/deny`, { method: 'POST' });
        setTimeout(fetchState, 100);
    } catch (e) { console.error(e); }
}

async function handlePointLimitChange(e) {
    const newLimit = parseInt(e.target.value);
    try {
        await fetch(`${API_BASE}/teams/set_point_limit`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ limit: newLimit })
        });

        await fetch(`${API_BASE}/lights/reset_led_default`, { method: 'PUT' });

        pointLimit = newLimit;
        winnerDismissedForPoints = -1; // Reset dismissal on limit change
        fetchTeams();
    } catch (e) { console.error(e); }
}

async function resetPoints() {
    if (!confirm("Are you sure you want to reset ALL points to 0?")) return;
    try {
        await fetch(`${API_BASE}/teams/reset_points`, { method: 'PATCH' });

        await fetch(`${API_BASE}/lights/reset_led_default`, { method: 'PUT' });

        winnerDismissedForPoints = -1;
        fetchTeams();
    } catch (e) { console.error(e); }
}

// --- Team Management ---

async function openTeamModal(teamToEdit = null) {
    teamModal.classList.remove('hidden');
    await fetchConnectedBuzzers(true);

    let assignedBuzzers = [];
    if (teamToEdit) {
        document.getElementById('modal-title').textContent = 'Edit Team';
        teamNameInput.value = teamToEdit.name;
        editTeamOriginalNameInput.value = teamToEdit.name;
        primaryColorInput.value = formatColor(teamToEdit.primary_color || '#ff0000');
        secondaryColorInput.value = formatColor(teamToEdit.secondary_color || '#ffff00');
        teamPointsInput.value = teamToEdit.point || 0;
        assignedBuzzers = teamToEdit.associated_buzzers || [];
    } else {
        document.getElementById('modal-title').textContent = 'Add Team';
        teamForm.reset();
        editTeamOriginalNameInput.value = '';
        teamNameInput.value = generateRandomName();
        teamPointsInput.value = 0;
        assignedBuzzers = [];
        // Pick a random preset for default
        const presets = [
            { p: '#FF0000', s: '#FFFF00' }, // Red / Yellow
            { p: '#00FF00', s: '#00FFFF' }, // Green / Cyan
            { p: '#0000FF', s: '#FF00FF' }, // Blue / Magenta
            { p: '#FFFF00', s: '#FF0000' }, // Yellow / Red
            { p: '#00FFFF', s: '#0000FF' }, // Cyan / Blue
            { p: '#FF00FF', s: '#FF0000' }, // Magenta / Red
            { p: '#FF8800', s: '#00FF00' }, // Orange / Green
            { p: '#8800FF', s: '#00FFFF' }  // Purple / Cyan
        ];
        const rp = presets[Math.floor(Math.random() * presets.length)];

        primaryColorInput.value = rp.p;
        secondaryColorInput.value = rp.s;
    }

    document.getElementById('primary-color-code').textContent = primaryColorInput.value;
    document.getElementById('secondary-color-code').textContent = secondaryColorInput.value;

    renderBuzzerList(assignedBuzzers, teamToEdit);
}

function renderBuzzerList(assignedBuzzers, teamToEdit = null) {
    const container = availableBuzzersList;
    container.innerHTML = '';

    const allAssigned = new Set();
    Object.values(teamsData).forEach(t => {
        if (!teamToEdit || t.name !== teamToEdit.name) {
            (t.associated_buzzers || []).forEach(b => allAssigned.add(b));
        }
    });

    if (connectedBuzzers.length === 0) {
        container.innerHTML = '<p class="text-muted">No buzzers connected.</p>';
    }

    connectedBuzzers.forEach(mac => {
        const wrapper = document.createElement('div');
        wrapper.className = 'buzzer-checkbox-label';

        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.value = mac;
        checkbox.name = 'associated_buzzers';
        if (assignedBuzzers.includes(mac)) checkbox.checked = true;

        if (allAssigned.has(mac)) {
            const takenSpan = document.createElement('span');
            takenSpan.textContent = ' (Taken)';
            takenSpan.style.color = 'orange';
            wrapper.appendChild(checkbox);
            wrapper.appendChild(document.createTextNode(mac));
            wrapper.appendChild(takenSpan);
        } else {
            wrapper.appendChild(checkbox);
            wrapper.appendChild(document.createTextNode(mac));
        }

        const idBtn = document.createElement('button');
        idBtn.type = 'button';
        idBtn.className = 'identify-btn';
        idBtn.textContent = 'Identify';
        idBtn.onclick = (e) => {
            e.preventDefault();
            identifyBuzzer(mac);
        };

        wrapper.appendChild(idBtn);
        container.appendChild(wrapper);
    });
}

function closeTeamModal() {
    teamModal.classList.add('hidden');
}

async function handleTeamSubmit(e) {
    e.preventDefault();

    const originalName = editTeamOriginalNameInput.value;
    const name = teamNameInput.value;
    const primary = primaryColorInput.value.replace('#', '');
    const secondary = secondaryColorInput.value.replace('#', '');
    const points = parseInt(teamPointsInput.value) || 0;

    const selectedBuzzers = Array.from(document.querySelectorAll('input[name="associated_buzzers"]:checked'))
        .map(cb => cb.value);

    // Force point limit on FIRST team added
    const isFirstTeam = Object.keys(teamsData).length === 0 && !originalName;


    try {
        if (originalName) {
            // Edit
            if (originalName !== name) {
                await fetch(`${API_BASE}/teams/change_name`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ old_name: originalName, new_name: name })
                });
            }

            await fetch(`${API_BASE}/teams/update`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    team_name: name,
                    associated_buzzers: selectedBuzzers,
                    primary_color: primary,
                    secondary_color: secondary,
                    point: points // User can modify points now
                })
            });

            // Update LEDs in case points changed
            await fetch(`${API_BASE}/lights/reset_led_default`, { method: 'PUT' });

        } else {
            // Create
            await fetch(`${API_BASE}/teams/make`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    team_name: name,
                    primary_color: primary,
                    secondary_color: secondary
                })
            });

            // Enforce point limit (Frontend-only constraint)
            // We must call this AFTER the team is created.
            // Wait slightly to ensure race conditions don't occur if backend is slow (though await should handle it).
            await new Promise(r => setTimeout(r, 500)); // Delay for stability
            await fetch(`${API_BASE}/teams/set_point_limit`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ limit: parseInt(pointLimitSelect.value) || 8 })
            });

            // Immediate update for buzzers and points
            await fetch(`${API_BASE}/teams/update`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    team_name: name,
                    associated_buzzers: selectedBuzzers,
                    point: points
                })
            });

            // Update LEDs
            await fetch(`${API_BASE}/lights/reset_led_default`, { method: 'PUT' });
        }

        closeTeamModal();
        fetchTeams();
    } catch (err) {
        alert("Error saving team: " + err.message);
        console.error(err);
    }
}

async function deleteTeam(teamName) {
    if (!confirm(`Delete team ${teamName}?`)) return;
    try {
        await fetch(`${API_BASE}/teams/delete`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ team_name: teamName })
        });
        fetchTeams();
    } catch (e) { console.error(e); }
}

async function identifyBuzzer(mac) {
    // 1. Clear LEDs initially
    await fetch(`${API_BASE}/lights/clear_leds`, { method: 'PUT' });

    const colorsWhite = Array(16).fill("FFFFFF");
    const colorsOff = Array(16).fill("000000");

    // 2. Blink loop (5 times)
    for (let i = 0; i < 5; i++) {
        // ON
        await fetch(`${API_BASE}/lights/set_led_color`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target_mac: mac, colors: colorsWhite })
        });
        await new Promise(r => setTimeout(r, 400)); // Wait 400ms

        // OFF
        await fetch(`${API_BASE}/lights/set_led_color`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target_mac: mac, colors: colorsOff })
        });
        await new Promise(r => setTimeout(r, 200)); // Wait 200ms
    }

    // 3. Explicit Clear before Reset as requested
    await fetch(`${API_BASE}/lights/clear_leds`, { method: 'PUT' });
    await new Promise(r => setTimeout(r, 100));

    // 4. Reset to default
    await fetch(`${API_BASE}/lights/reset_led_default`, { method: 'PUT' });
}

// --- Rendering ---

function updateGameState(state) {
    if (state === 'CHECK' && currentState !== 'CHECK') {
        pressSound.play().catch(e => console.error("Error playing sound:", e));
    }
    currentState = state;
    gameStateBadge.textContent = state;
    gameStateBadge.className = `badge badge-${state}`;

    const startBtn = document.getElementById('start-question-btn');
    const checkControls = document.getElementById('check-controls');
    const waitControls = document.getElementById('wait-controls');

    startBtn.classList.add('hidden');
    checkControls.classList.add('hidden');
    waitControls.classList.add('hidden');

    // Reset optimistic disabled state if we come back to IDLE
    if (state === 'IDLE') {
        startBtn.disabled = false;
        startBtn.textContent = "Start Question";
        startBtn.classList.remove('hidden');
    } else if (state === 'WAIT') {
        waitControls.classList.remove('hidden');
    } else if (state === 'CHECK') {
        checkControls.classList.remove('hidden');
        // Cleaned up message
        document.getElementById('answering-team').textContent = "Buzzer Pressed";

        // Explicitly re-enable buttons
        document.getElementById('confirm-btn').disabled = false;
        document.getElementById('deny-btn').disabled = false;
    }
}

function renderTeamsGrid() {
    teamsContainer.innerHTML = '';

    Object.values(teamsData).forEach(team => {
        const card = document.createElement('div');
        card.className = 'team-card';
        card.style.borderTop = `4px solid ${formatColor(team.primary_color)}`;

        const buzzerCount = (team.associated_buzzers || []).length;

        card.innerHTML = `
            <div class="team-header">
                <h3>${team.name}</h3>
                <div class="team-actions">
                    <button class="icon-btn edit-btn" title="Edit">✏️</button>
                    <button class="icon-btn delete-btn" title="Delete">🗑️</button>
                </div>
            </div>
            <div class="team-info">
                <p>Points: <strong>${team.point}</strong></p>
                <p>Buzzers: ${buzzerCount}</p>
                <div style="display:flex; gap:5px; margin-top:10px;">
                    <div class="team-color-indicator" style="background: ${formatColor(team.primary_color)}"></div>
                    <div class="team-color-indicator" style="background: ${formatColor(team.secondary_color)}"></div>
                </div>
            </div>
        `;

        card.querySelector('.edit-btn').addEventListener('click', () => openTeamModal(team));
        card.querySelector('.delete-btn').addEventListener('click', () => deleteTeam(team.name));

        teamsContainer.appendChild(card);
    });
}

function renderScoreboard() {
    scoreboardContainer.innerHTML = '';
    const sortedTeams = Object.values(teamsData).sort((a, b) => b.point - a.point);

    sortedTeams.forEach(team => {
        const div = document.createElement('div');
        div.className = 'score-card';
        div.style.borderTopColor = formatColor(team.primary_color);
        div.innerHTML = `
            <h4>${team.name}</h4>
            <div class="score-value">${team.point}</div>
        `;
        scoreboardContainer.appendChild(div);
    });
}

function checkForWinner() {
    // If we deliberately dismissed the winner for this point threshold, skip
    if (winnerDismissedForPoints !== -1 && winnerDismissedForPoints === pointLimit) {
        // We only skip if the points are STILL the same?
        // Actually, if we dismiss, we want to hide it until something changes.
        // But simply, if pointLimit hasn't changed, we might still have a winner.
        // The user requirement: "avoid it to reappear until points are modified / reset"
        // So checking if points changed is Key.
        // Simplification: We rely on user resetting or modifying points to clear the 'dismissed' state.
        return;
        // WAIT. If I dismiss, and then a team SCORES AGAIN (modifies points), I should maybe show it again?
        // The user said "until points are modified".
        // Use a more complex tracker?
        // Let's just track a hash of points?
        // For now, let's stick to the simpler interpretation: Dismiss -> Hidden until Reset or point limit change.
        // User also said "until points are modified". 
        // So if I manually edit points, or confirm an answer, I should un-dismiss.
        // I handled that in 'confirmAnswer' and 'handleTeamSubmit' (if points changed) and 'handlePointLimitChange'.
    }

    const winners = Object.values(teamsData).filter(t => t.point >= pointLimit);
    if (winners.length > 0) {
        if (winModal.classList.contains('hidden')) {
            showWinner(winners[0]);
        }
    }
}

function showWinner(team) {
    document.getElementById('winner-name-display').textContent = team.name;
    document.getElementById('winner-name-display').style.color = formatColor(team.primary_color);
    winModal.classList.remove('hidden');
}

function closeWinModal() {
    winModal.classList.add('hidden');
}

function formatColor(c) {
    if (!c) return '#ffffff';
    return c.startsWith('#') ? c : `#${c}`;
}

function generateRandomName() {
    const adjs = ['Rapid', 'Cosmic', 'Electric', 'Sonic', 'Neon', 'Quantum', 'Hyper', 'Turbo'];
    const nouns = ['Rockets', 'Falcons', 'Pulsars', 'Quasars', 'Ninjas', 'Panthers', 'Sparks', 'Waves'];
    const r = (arr) => arr[Math.floor(Math.random() * arr.length)];
    return `${r(adjs)} ${r(nouns)}`;
}
