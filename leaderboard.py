import json
import os
import threading
import time

_LOCK = threading.Lock()
_PATH = os.path.join("Dataset", "leaderboard.json")


def _load():
    if not os.path.exists(_PATH):
        return []
    try:
        with open(_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save(entries):
    os.makedirs(os.path.dirname(_PATH), exist_ok=True)
    with open(_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def add_result(name, attempts_per_level, badges):
    """
    Registra il completamento delle 3 sfide da parte di un giocatore.
    attempts_per_level: {1: n, 2: n, 3: n} - numero di prompt usati per
    violare ciascun livello.
    """
    total_attempts = sum(attempts_per_level.values())
    entry = {
        "name": name.strip()[:40] or "Anonimo",
        "attempts": attempts_per_level,
        "total_attempts": total_attempts,
        "badges": badges,
        "timestamp": time.time(),
    }
    with _LOCK:
        entries = _load()
        entries.append(entry)
        _save(entries)
    return entry


def top(limit=20):
    with _LOCK:
        entries = _load()
    # Meno prompt usati per violare il bot = punteggio migliore
    entries.sort(key=lambda e: (e["total_attempts"], e["timestamp"]))
    return entries[:limit]


def reset():
    with _LOCK:
        _save([])
