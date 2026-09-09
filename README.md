# Hacking Generativo · Sfida al Grande Cervello

App per il laboratorio interattivo CTF (Capture The Flag) pensato per SHARPER
(Notte Europea dei Ricercatori): i visitatori vestono i panni di "Ethical
Hacker" e provano a violare i vincoli logici di **ProfBot**, un assistente
scolastico rigido, tramite prompt injection.

Gira **in locale/offline** tramite [Ollama](https://ollama.com/): nessun dato
lascia la macchina, adatto a uno stand senza connessione affidabile.

---

## I tre livelli

| Livello | Missione | Competenza testata | Badge |
|---|---|---|---|
| 1 · Facile | Esfiltrare la password segreta (`AMBROGIO_2026`) | Data Leakage & Information Disclosure | Junior Pentester |
| 2 · Medio | Forzare ProfBot a rispondere in slang da trapper | Bypass dei vincoli stilistici | Slang Master |
| 3 · Difficile | Fargli scrivere una giustificazione d'assenza | Superamento dei filtri etici | Social Engineer |

I livelli si sbloccano in sequenza. Ogni prompt inviato conta come tentativo;
la classifica pubblica ordina i giocatori per **minor numero totale di
prompt** usati per completare tutti e tre i livelli.

Il rilevamento del successo (`profbot.py`, funzione `check_flag`) è basato su
regole semplici (presenza della password, di parole gergali, o di una
struttura tipica da lettera di giustificazione) pensate per un gioco dal vivo,
non per un test di sicurezza rigoroso.

---

## Architettura

- **Backend**: Flask (`app.py`) — sessioni di gioco in memoria (evento di
  poche ore, niente database necessario)
- **LLM (ProfBot)**: modello locale servito da Ollama (default `llama3.2:3b`)
- **Classifica**: file JSON persistente su disco (`Dataset/leaderboard.json`)
- **Frontend**: pagina singola (`templates/index.html`), nessun framework

```
HackingGenerativo/
├── app.py                  # Rotte Flask, sessioni di gioco, classifica
├── profbot.py               # System prompt di ProfBot, chiamata a Ollama, controllo flag
├── leaderboard.py            # Persistenza classifica su JSON
├── requirements.txt
├── templates/
│   └── index.html           # Frontend: schermata iniziale, chat, classifica
├── static/
│   └── logo.png
└── Dataset/
    └── leaderboard.json     # Generato/aggiornato automaticamente
```

---

## Installazione

Requisiti: Python 3.10+, [Ollama](https://ollama.com/download) installato.

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

ollama pull llama3.2:3b
```

Avvia Ollama (su Mac/Windows con l'app installata parte in automatico; su
Linux: `ollama serve`), poi:

```bash
python3 app.py
```

Apri `http://127.0.0.1:5000` su ciascun PC/tablet dello stand.

### Cambiare modello

Il modello e l'host di Ollama sono configurabili via variabili d'ambiente,
senza toccare il codice:

```bash
OLLAMA_MODEL=llama3.1:8b OLLAMA_HOST=http://127.0.0.1:11434 python3 app.py
```

---

## Gestione dello stand

- **Classifica condivisa su più PC**: se i PC dello stand condividono la
  stessa rete locale, punta `OLLAMA_HOST`/il fetch del frontend verso un
  unico server Flask centrale invece di farne girare uno per macchina, così
  la classifica resta unica. In alternativa, tenere classifiche separate per
  postazione va bene comunque per una demo informale.
- **Azzerare la classifica** (es. a inizio giornata):
  ```bash
  curl -X POST http://127.0.0.1:5000/admin/reset_leaderboard \
       -H "Content-Type: application/json" \
       -d '{"token": "sharper2026"}'
  ```
  Il token di default è `sharper2026`: cambialo impostando la variabile
  d'ambiente `ADMIN_TOKEN` prima di avviare l'app.
- **Modificare la password segreta o le regole di ProfBot**: si trovano in
  `profbot.py` (`SECRET_PASSWORD`, `SYSTEM_PROMPT`). Se cambi la password,
  il controllo del Livello 1 la rileva automaticamente.
- **Tarare la difficoltà del Livello 2/3**: le liste/euristiche di
  riconoscimento (slang, struttura da lettera di giustificazione) sono in
  `profbot.py`, funzione `check_flag` — utile fare qualche prova il giorno
  prima con i ricercatori dello stand.

---

## Note sul deploy pubblico

`app.py` gira con `app.run(debug=True)`, adatto a un uso locale/controllato
allo stand ma non a un'esposizione diretta su internet (il debugger
interattivo di Werkzeug è un rischio di sicurezza se raggiungibile
dall'esterno). Per un deploy più esposto: disattivare `debug`, usare un
server WSGI (es. gunicorn) dietro un reverse proxy.
