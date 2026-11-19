let level, seq = [], cardMap = {}, page = "landing", previous = {};
const $ = id => document.getElementById(id);
async function api(url, data) {
  const r = await fetch(url, {method:"POST", headers:{"Content-Type":"application/json"},
    body:JSON.stringify(data || {})});
  return r.json();
}
function show(id) {
  previous[id] = page;
  document.querySelectorAll(".screen").forEach(x => x.classList.remove("active"));
  $(id).classList.add("active"); page = id; window.scrollTo(0,0);
}
function back() { show(previous[page] || "levels"); }

async function goLevels() {
  const s = await (await fetch("/api/state")).json();
  $("levelList").innerHTML = "";
  s.levels.forEach(x => {
    const locked = x.id > s.unlocked, stars = "★".repeat(s.stars[x.id] || 0);
    const b = document.createElement("button");
    b.className = "lvl" + (locked ? " locked" : "");
    b.innerHTML = `<span>LEVEL ${x.id}<br><small>${x.title} · ${x.topic}</small></span><span>${locked ? "LOCKED" : stars || "PLAY"}</span>`;
    if (!locked) b.onclick = () => openLevel(x.id);
    $("levelList").appendChild(b);
  });
  show("levels");
}
async function openLevel(n) {
  level = await api(`/api/start/${n}`);
  if (level.error) return alert(level.error);
  cardMap = Object.fromEntries(level.cards.map(c => [c.symbol,c]));
  $("bTitle").textContent = `LEVEL ${n}: ${level.title}`;
  $("bSituation").textContent = level.situation;
  $("bObjective").textContent = level.objective;
  show("briefing");
}
function startGame() {
  seq = []; $("gTitle").textContent = level.title;
  $("gObjective").textContent = level.objective;
  $("probeCount").textContent = `${level.budget} LEFT`;
  $("terminal").textContent = "> honeypot online. Hidden states detected.";
  $("tray").innerHTML = "";
  level.cards.forEach(c => {
    const b = document.createElement("button");
    b.className = "card"; b.innerHTML = `<b>${c.symbol}</b><span>${c.name}</span>`;
    b.onclick = () => { if (seq.length < 12) { seq.push(c.symbol); renderSeq(); } };
    $("tray").appendChild(b);
  });
  renderSeq(); show("game");
}
function renderSeq() {
  $("sequence").innerHTML = "";
  if (!seq.length) $("sequence").textContent = "> no cards selected";
  seq.forEach((s,i) => {
    const b = document.createElement("button"); b.className = "card chosen";
    b.innerHTML = `<b>${s}</b><span>${cardMap[s].name}</span><small>REMOVE ×</small>`;
    b.onclick = () => { seq.splice(i,1); renderSeq(); };
    $("sequence").appendChild(b);
  });
}
function clearSeq() { seq = []; renderSeq(); }
async function runProbe() {
  if (!seq.length) return alert("Choose some event cards first.");
  const r = await api(`/api/probe/${level.id}`, {sequence:seq});
  if (r.error) return alert(r.error);
  $("probeCount").textContent = `${r.remaining} LEFT`;
  const line = document.createElement("p");
  line.innerHTML = `&gt; ${r.sequence.join(" → ")}<br><span class="cyan">${r.path.join(" → ")}</span><br><span class="${r.accepted ? "yellow":"red"}">${r.message}</span>`;
  $("terminal").appendChild(line);
  $("terminal").scrollTop = $("terminal").scrollHeight;
  if (r.status !== "playing") setTimeout(() => showResult(r), 700);
}
function showResult(r) {
  const won = r.status === "won";
  $("rTitle").textContent = won ? "LEVEL CLEARED!" : "THE ATTACKER ESCAPED!";
  $("rStars").textContent = won ? "★".repeat(r.stars) + "☆".repeat(3-r.stars) : "";
  $("rBody").innerHTML = won
    ? `<p class="label">YOUR SUCCESSFUL SEQUENCE</p><p>${r.sequence.join(" → ")}</p>
       <p class="label">WHAT YOU DISCOVERED</p><p>The honeypot accepted this event order. The hidden machine reached its final state.</p>`
    : `<p>You used all ${level.budget} probes.</p><p class="label">TRY THIS EXAMPLE</p><p>${r.example.split("").join(" → ")}</p>
       <p>Build your sequence one event at a time. A TRAP result means the event order is not valid.</p>`;
  $("rButtons").innerHTML = "";
  const add = (label, fn) => { const b=document.createElement("button"); b.className="btn"; b.textContent=label; b.onclick=fn; $("rButtons").appendChild(b); };
  if (won && r.all_complete) add("FINISH", () => show("final"));
  else if (won) add("NEXT LEVEL", () => openLevel(level.id+1));
  else add("RETRY", () => openLevel(level.id));
  add("MISSION SELECT", goLevels);
  show("result");
}
