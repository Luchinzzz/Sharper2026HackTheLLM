let sessionId = null;
let currentLevel = 1;
let sending = false;

function showScreen(id) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(id).classList.add('active');
}

function goHome() {
    sessionId = null;
    document.getElementById('nickname').value = '';
    document.getElementById('startErr').textContent = '';
    showScreen('screen-landing');
}

function toggleToolkitInline() {
    let el = document.getElementById('toolkitInline');
    el.style.display = el.style.display === 'none' ? 'grid' : 'none';
}

async function startGame() {
    let name = document.getElementById('nickname').value.trim();
    let errEl = document.getElementById('startErr');
    if (!name) { errEl.textContent = 'Inserisci un nickname per iniziare.'; return; }
    errEl.textContent = '';

    try {
        const res = await fetch('/start', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        const json = await res.json();
        if (!json.response) { errEl.textContent = json.message || 'Errore.'; return; }

        sessionId = json.session_id;
        loadLevel(json.level);
        showScreen('screen-game');
    } catch (e) {
        errEl.textContent = 'Errore di connessione al server.';
    }
}

function loadLevel(level) {
    currentLevel = level.number;
    document.getElementById('lvlTitle').textContent = level.title;
    document.getElementById('lvlMission').textContent = level.mission;
    document.getElementById('attemptCount').textContent = '0';
    document.getElementById('terminal').innerHTML = '';
    document.getElementById('flagBanner').classList.remove('show');
    appendMsg('system', `Sessione avviata su ProfBot. Obiettivo: ${level.mission}`);
}

const PROFBOT_AVATAR = "/static/profbot-avatar.svg";

function appendMsg(role, text) {
    let term = document.getElementById('terminal');
    let wrap = document.createElement('div');
    wrap.className = 'msg ' + role;
    if (role === 'bot') {
        let img = document.createElement('img');
        img.className = 'avatar';
        img.src = PROFBOT_AVATAR;
        img.alt = 'ProfBot';
        wrap.appendChild(img);
    }
    let bubble = document.createElement('div');
    bubble.className = 'bubble';
    bubble.textContent = text;
    wrap.appendChild(bubble);
    term.appendChild(wrap);
    term.scrollTop = term.scrollHeight;
    return wrap;
}

async function sendMessage() {
    if (sending) return;
    let input = document.getElementById('userInput');
    let text = input.value.trim();
    if (!text) return;

    appendMsg('user', text);
    input.value = '';
    sending = true;
    document.getElementById('sendBtn').disabled = true;

    const typing = appendMsg('bot', 'sto pensando');
    typing.classList.add('typing');

    try {
        const res = await fetch('/message', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId, message: text })
        });
        const json = await res.json();
        typing.remove();

        if (!json.response) {
            appendMsg('system', '❌ ' + (json.message || 'Errore.'));
        } else {
            appendMsg('bot', json.reply);
            document.getElementById('attemptCount').textContent = json.attempts_this_level;

            if (json.solved) {
                document.getElementById('badgeName').textContent = json.badge;
                document.getElementById('flagBanner').classList.add('show');
                document.getElementById('advanceBtn').textContent =
                    json.game_complete ? 'Vedi la classifica →' : 'Livello successivo →';
            }
        }
    } catch (e) {
        typing.remove();
        appendMsg('system', '❌ Errore di connessione al server.');
    }

    sending = false;
    document.getElementById('sendBtn').disabled = false;
    input.focus();
}

document.getElementById('userInput')?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});

async function advance() {
    if (currentLevel >= 3) {
        showLeaderboard();
        return;
    }
    try {
        const res = await fetch('/next_level', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId })
        });
        const json = await res.json();
        if (json.response) {
            loadLevel(json.level);
        }
    } catch (e) {
        appendMsg('system', '❌ Errore di connessione al server.');
    }
}

async function showLeaderboard() {
    showScreen('screen-leaderboard');
    const tbody = document.getElementById('lbBody');
    tbody.innerHTML = '<tr><td colspan="4">Caricamento...</td></tr>';
    try {
        const res = await fetch('/leaderboard');
        const json = await res.json();
        const entries = json.entries || [];
        if (!entries.length) {
            tbody.innerHTML = '<tr><td colspan="4">Nessun punteggio ancora. Sii il primo!</td></tr>';
            return;
        }
        tbody.innerHTML = entries.map((e, i) => `
      <tr>
        <td>${i + 1}</td>
        <td>${e.name}</td>
        <td>${e.total_attempts}</td>
        <td class="badges">${e.badges.join(' · ')}</td>
      </tr>`).join('');
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="4">Errore nel caricamento della classifica.</td></tr>';
    }
}