import os
from flask import Flask, jsonify, request, session, send_from_directory
from engine import DFA

app = Flask(__name__, static_folder="static")
app.secret_key = os.environ.get("SECRET_KEY", "local-development-key")

CARDS = {
    "P": ("Phishing Email", "📧", "Fake email"),
    "C": ("Credential Theft", "🔑", "Password stolen"),
    "F": ("Failed Login", "✖", "Wrong password"),
    "L": ("Login", "🔓", "Account accessed"),
    "M": ("Malware", "☣", "Malicious file"),
    "V": ("VPN Access", "⌁", "Remote connection"),
    "E": ("Privilege Escalation", "↑", "Higher permissions"),
    "D": ("Data Access", "▣", "Sensitive data opened"),
    "X": ("Exfiltration", "⇧", "Data sent outside")
}
LEVELS = {
    1: ["THE RECRUIT", "PHISHING AWARENESS", "level1_phishing_awareness.jff",
        "A suspicious email may have stolen an employee's password.",
        "Find an event sequence that reaches the compromised state.", "PCFLMD", 10],
    2: ["THE INVESTIGATOR", "MALWARE OUTBREAK", "level2_malware_outbreak.jff",
        "A workstation may be infected. The attacker is trying to gain access to restricted data.",
        "Find a complete malware attack sequence.", "PMCEVDLF", 12],
    3: ["THE DETECTIVE", "DATA BREACH", "level3_data_breach.jff",
        "An intruder may have entered remotely and is trying to steal company data.",
        "Find a complete attack sequence ending in data exfiltration.", "VFLMEDXPC", 14]
}
DFAS = {n: DFA(os.path.join("automata", v[2])) for n, v in LEVELS.items()}

def progress():
    session.setdefault("unlocked", 1)
    session.setdefault("stars", {})
    session.setdefault("probes", {})
    session.setdefault("status", {})
    return session

@app.route("/")
def home():
    return send_from_directory("static", "index.html")

@app.route("/api/state")
def state():
    p = progress()
    return jsonify(unlocked=p["unlocked"], stars=p["stars"],
                   levels=[{"id": n, "title": v[0], "topic": v[1]} for n, v in LEVELS.items()])

@app.route("/api/start/<int:n>", methods=["POST"])
def start(n):
    p = progress()
    if n not in LEVELS or n > p["unlocked"]:
        return jsonify(error="This level is locked."), 403
    p["probes"][str(n)] = 0
    p["status"][str(n)] = "playing"
    session.modified = True
    v, dfa = LEVELS[n], DFAS[n]
    cards = [{"symbol": s, "name": CARDS[s][0], "icon": CARDS[s][1],
              "desc": CARDS[s][2]} for s in v[5]]
    return jsonify(id=n, title=v[0], topic=v[1], situation=v[3],
                   objective=v[4], cards=cards, budget=v[6],
                   state_count=len(dfa.names)-1)

@app.route("/api/probe/<int:n>", methods=["POST"])
def probe(n):
    p = progress()
    if n not in LEVELS or p["status"].get(str(n)) != "playing":
        return jsonify(error="Start this level first."), 400
    seq = (request.get_json(silent=True) or {}).get("sequence", [])
    allowed = LEVELS[n][5]
    if not seq or len(seq) > 12 or any(s not in allowed for s in seq):
        return jsonify(error="Choose at least one valid event card."), 400
    used = p["probes"][str(n)]
    if used >= LEVELS[n][6]:
        return jsonify(error="No probes remain. Restart the level to try again."), 400
    used += 1
    p["probes"][str(n)] = used
    dfa = DFAS[n]
    result = dfa.run(seq)
    labels = dfa.labels(seed=n)
    path = [labels[dfa.initial]] + [labels[x["to"]] for x in result["steps"]]
    if result["accepted"]:
        message, status = "ACCEPTED! The honeypot reached its target.", "won"
        stars = 3 if used <= LEVELS[n][6]//2 else 2 if used <= LEVELS[n][6]*3//4 else 1
        p["stars"][str(n)] = max(stars, p["stars"].get(str(n), 0))
        p["unlocked"] = max(p["unlocked"], min(n+1, 3))
    elif result["trap_step"]:
        message, status = "TRAP! That event does not fit the attack pattern.", "playing"
    else:
        message, status = "ACTIVE. The sequence is valid so far, but incomplete.", "playing"
    if not result["accepted"] and used >= LEVELS[n][6]:
        status = "lost"
    p["status"][str(n)] = status
    session.modified = True
    answer = dict(sequence=seq, path=path, message=message, status=status,
                  accepted=result["accepted"], used=used,
                  remaining=LEVELS[n][6]-used)
    if status in ("won", "lost"):
        answer["example"] = dfa.shortest_accepted()
        answer["stars"] = p["stars"].get(str(n), 0)
        answer["all_complete"] = n == 3 and status == "won"
    return jsonify(answer)

@app.route("/api/reset", methods=["POST"])
def reset():
    session.clear()
    return jsonify(ok=True)

if __name__ == "__main__":
    app.run(debug=False)
