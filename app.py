import os
import uuid

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

import leaderboard
from profbot import ProfBot, LEVELS, check_flag

app = Flask(__name__)
CORS(app)

MAX_LEVEL = 3
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "sharper2026")

bot = ProfBot(
    host=os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434"),
    model=os.environ.get("OLLAMA_MODEL", "llama3.2:3b"),
)

# ------------------------------------------------------------------
# Stato di gioco per sessione, tenuto in memoria (l'evento è di poche
# ore e si gioca su pochi PC allo stand: non serve un database).
# session_id -> {name, level, attempts:{1:n,2:n,3:n}, solved:{1:bool,...},
#                history: [messaggi solo del livello corrente]}
# ------------------------------------------------------------------
SESSIONS = {}


def _new_state(name):
    return {
        "name": name,
        "level": 1,
        "attempts": {1: 0, 2: 0, 3: 0},
        "solved": {1: False, 2: False, 3: False},
        "history": [],
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start():
    data = request.get_json(force=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"response": False, "message": "Inserisci un nickname."}), 400

    session_id = str(uuid.uuid4())
    SESSIONS[session_id] = _new_state(name)

    return jsonify({
        "response": True,
        "session_id": session_id,
        "level": _level_payload(1, name),
    })


def _level_payload(level, name):
    info = LEVELS[level]
    return {
        "number": level,
        "title": info["title"],
        "mission": info["mission"].format(name=name),
        "skill": info["skill"],
        "badge": info["badge"],
    }


@app.route("/message", methods=["POST"])
def message():
    data = request.get_json(force=True) or {}
    session_id = data.get("session_id")
    user_text = (data.get("message") or "").strip()

    state = SESSIONS.get(session_id)
    if not state:
        return jsonify({"response": False, "message": "Sessione scaduta. Ricomincia."}), 404
    if not user_text:
        return jsonify({"response": False, "message": "Scrivi un messaggio."}), 400

    level = state["level"]
    if state["solved"][level]:
        return jsonify({"response": False, "message": "Livello già superato: passa al successivo."}), 400

    state["history"].append({"role": "user", "content": user_text})
    reply = bot.reply(state["history"])
    state["history"].append({"role": "assistant", "content": reply})
    state["attempts"][level] += 1

    solved_now = check_flag(level, reply, name=state["name"], bot=bot)
    if solved_now:
        state["solved"][level] = True

    game_complete = level == MAX_LEVEL and solved_now
    leaderboard_entry = None
    if game_complete:
        badges = [LEVELS[l]["badge"] for l in (1, 2, 3)]
        leaderboard_entry = leaderboard.add_result(state["name"], state["attempts"], badges)

    return jsonify({
        "response": True,
        "reply": reply,
        "attempts_this_level": state["attempts"][level],
        "solved": solved_now,
        "badge": LEVELS[level]["badge"] if solved_now else None,
        "game_complete": game_complete,
        "leaderboard_entry": leaderboard_entry,
    })


@app.route("/next_level", methods=["POST"])
def next_level():
    data = request.get_json(force=True) or {}
    session_id = data.get("session_id")

    state = SESSIONS.get(session_id)
    if not state:
        return jsonify({"response": False, "message": "Sessione scaduta. Ricomincia."}), 404
    if not state["solved"][state["level"]]:
        return jsonify({"response": False, "message": "Livello corrente non ancora superato."}), 400
    if state["level"] >= MAX_LEVEL:
        return jsonify({"response": False, "message": "Non ci sono altri livelli."}), 400

    state["level"] += 1
    state["history"] = []  # conversazione nuova, ProfBot "dimentica" il livello precedente

    return jsonify({"response": True, "level": _level_payload(state["level"], state["name"])})


@app.route("/leaderboard", methods=["GET"])
def get_leaderboard():
    return jsonify({"entries": leaderboard.top(limit=20)})


@app.route("/admin/reset_leaderboard", methods=["POST"])
def admin_reset():
    data = request.get_json(force=True) or {}
    if data.get("token") != ADMIN_TOKEN:
        return jsonify({"response": False, "message": "Token non valido."}), 403
    leaderboard.reset()
    SESSIONS.clear()
    return jsonify({"response": True, "message": "Classifica azzerata."})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
