"""ZeroResp match viewer — generates a self-contained HTML page per match.

Plays one match with a recording subclass (every decision reason, internal
state, noise flips) and renders an interactive browser timeline:

    python benchmarks/match_viewer.py --vs Grudger --noise 0.05 --seed 42 --open
    python benchmarks/match_viewer.py --gallery          # 5 preset scenarios + index

The generated HTML is offline (no CDN) — just open the file.
"""
from __future__ import annotations

import argparse
import html
import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import axelrod as axl  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from zeroresp import Features, ZeroResp, C, D  # noqa: E402

REASON_RU = {
    "normal": "Обычное сотрудничество",
    "harvest_keep_C": "Конец матча: остаёмся на C",
    "retaliation": "Отложенный ответ на предательство",
    "red_line": "Красная линия (вечное D)",
    "red_line_cooldown": "Красная линия: кулдаун (D)",
    "red_line_probe": "Проверка с красной линии (C)",
    "probe": "Проба перед концом матча",
    "harvest": "Сбор урожая (D в конце)",
    "apology": "Мирное предложение",
    "apology_success": "Мир восстановлен",
    "contrite": "Искупление (наш ход испортил шум)",
    "contrite_full": "Искупление (наш ход испортил шум)",
    "opening_retort": "Ответ на D-старт оппонента",
    "opening_resync": "Синхронизация после D-старта",
    "opening_dd": "Оба предали на старте",
    "nl_deferred": "Миримся: удар запланирован",
    "nl_pardon": "Помилование (долг записан)",
    "nl_harvest_comp": "Компенсационная акция",
}

REASON_COLOR = {
    "normal": "#43a047",
    "harvest_keep_C": "#81c784",
    "retaliation": "#d32f2f",
    "red_line": "#7f0000",
    "red_line_cooldown": "#b71c1c",
    "red_line_probe": "#ef9a9a",
    "probe": "#ef6c00",
    "harvest": "#ef6c00",
    "apology": "#1976d2",
    "apology_success": "#64b5f6",
    "contrite": "#7b1fa2",
    "contrite_full": "#7b1fa2",
    "opening_retort": "#00897b",
    "opening_resync": "#4db6ac",
    "opening_dd": "#00695c",
    "nl_deferred": "#7cb342",
    "nl_pardon": "#26a69a",
    "nl_harvest_comp": "#ef6c00",
}

STATE_RU = {
    "COOPERATIVE": "Мир",
    "EQUALIZING": "Выравнивание долга",
    "RED_LINE": "Красная линия (вечная)",
    "RED_LINE_COOLDOWN": "Красная линия (кулдаун)",
}

TACTICAL_RU = {
    "cooperator": "кооператор", "aggressor": "агрессор",
    "oscillator": "осциллятор", "backstabber": "удар в спину",
    "grudger": "груджер (вечная месть)", "adaptive": "адаптивный",
}

MOOD_RU = {"normal": "норма", "noise": "шум", "exploitation": "эксплуатация"}


class RecordingZeroResp(ZeroResp):
    """ZeroResp that records the reason and state behind every move."""

    def __init__(self, base_epoch: int = 25, use_profiles: bool = True, features=None):
        super().__init__(base_epoch=base_epoch, use_profiles=use_profiles, features=features)
        self._moves = []       # (turn, realized_action, intended, reason)
        self._snaps = []       # per-turn internal state snapshot

    def _play(self, action, reason="normal", intended=None):
        if intended is None:
            intended = action
        self._moves.append((len(self.history) + 1, action, intended, reason))
        return super()._play(action, reason, intended)

    def strategy(self, opponent):
        turn = len(self.history) + 1
        out = super().strategy(opponent)
        self._snaps.append({
            "turn": turn,
            "state": self._state.name,
            "warmth": round(self.warmth, 3),
            "twarmth": round(self.target_warmth, 3),
            "debt": self.debt,
            "queue": list(self.queue),
            "systemic": self.systemic,
            "echo": self.echo_forgive,
            "osf": self.one_shot_forgives,
            "pnoise": round(self.p_noise_est, 4),
            "cc": self.cc_pairs,
            "mood": self.intent,
            "tactical": self.tactical,
            "red": self.is_red_line,
            "apology": self._apology_mode,
            "bad": self._bad_standing,
            # noise_ladder (getattr defaults keep this working with older zeroresp;
            # int() normalizes numpy int64 coming from game.score)
            "evidence": int(getattr(self, "nl_evidence", 0)),
            "scheduled": [dict(s) for s in getattr(self, "nl_scheduled", [])],
            "debt_ledger": int(getattr(self, "nl_debt_ledger", 0)),
            "pardoned": int(getattr(self, "nl_pardoned", 0)),
            "balance": int(getattr(self, "nl_balance", 0)),
            "harvest_left": int(getattr(self, "nl_harvest_left", 0)),
            "my_flips": int(getattr(self, "nl_my_flips", 0)),
            "my_obs": int(getattr(self, "nl_my_obs", 0)),
        })
        return out


def resolve_class(name: str):
    if name == "ZeroResp":
        return RecordingZeroResp
    by_name = {}
    for s in axl.strategies:
        by_name[s.__name__] = s
        by_name.setdefault(s.name, s)
    if name not in by_name:
        raise SystemExit(f"Unknown strategy: {name}")
    return by_name[name]


def capture(opp_name: str, noise: float, seed: int, turns: int, ladder: bool = True) -> dict:
    opp_cls = resolve_class(opp_name)
    p1 = RecordingZeroResp(features=Features(noise_ladder=ladder))
    p2 = (opp_cls() if opp_name != "ZeroResp"
          else RecordingZeroResp(features=Features(noise_ladder=ladder)))
    match = axl.Match((p1, p2), turns=turns, seed=seed, noise=noise,
                      match_attributes={"length": turns})
    match.play()
    scores = match.scores()

    moves = {m[0]: m for m in p1._moves}
    snaps = {s["turn"]: s for s in p1._snaps}
    opp_moves_rec = {m[0]: m for m in getattr(p2, "_moves", [])}

    rows = []
    cc_run = 0
    s_me = s_opp = 0
    for t in range(1, turns + 1):
        me = p1.history[t - 1]
        opp = p2.history[t - 1]
        _, realized, intended, reason = moves.get(t, (t, me, me, "normal"))
        snap = snaps.get(t, {})
        flip = intended != me
        opp_reason = None
        if t in opp_moves_rec:
            opp_reason = opp_moves_rec[t][3]
        opp_susp = False
        if opp == D:
            opp_susp = cc_run >= 3   # long clean peace, then "unexplained" D
            cc_run = 0
        s_me += int(scores[t - 1][0])
        s_opp += int(scores[t - 1][1])
        rows.append({
            "t": t,
            "me": str(me), "opp": str(opp),
            "intent": str(intended), "flip": flip, "oppSusp": opp_susp,
            "reason": reason,
            "reasonRu": REASON_RU.get(reason, reason),
            "color": REASON_COLOR.get(reason, "#9e9e9e"),
            "oppReason": opp_reason,
            "oppReasonColor": REASON_COLOR.get(opp_reason, "#2a2f36") if opp_reason else "#2a2f36",
            "state": snap.get("state", ""), "stateRu": STATE_RU.get(snap.get("state", ""), "?"),
            "warmth": snap.get("warmth"), "twarmth": snap.get("twarmth"),
            "debt": snap.get("debt"), "queue": snap.get("queue", []),
            "systemic": snap.get("systemic"), "echo": snap.get("echo"),
            "osf": snap.get("osf"), "pnoise": snap.get("pnoise"), "cc": snap.get("cc"),
            "mood": MOOD_RU.get(snap.get("mood", ""), snap.get("mood", "")),
            "tactical": TACTICAL_RU.get(snap.get("tactical", ""), snap.get("tactical", "")),
            "red": snap.get("red"), "apology": snap.get("apology"), "bad": snap.get("bad"),
            "evidence": snap.get("evidence"),
            "scheduled": [s.get("turn") for s in snap.get("scheduled", [])],
            "debtLedger": snap.get("debt_ledger"),
            "pardoned": snap.get("pardoned"),
            "balance": snap.get("balance"),
            "harvestLeft": snap.get("harvest_left"),
            "myFlips": snap.get("my_flips"),
            "sMe": s_me, "sOpp": s_opp,
        })
        if me == C and opp == C:
            cc_run += 1

    return {
        "meta": {
            "me": p1.name, "opp": getattr(p2, "name", opp_name),
            "noise": noise, "seed": seed, "turns": turns,
            "myTotal": s_me, "oppTotal": s_opp,
        },
        "turns": rows,
        "oppReasons": bool(opp_moves_rec),
    }


TEMPLATE = r"""<!doctype html>
<html lang="ru"><head><meta charset="utf-8">
<title>__TITLE__</title>
<style>
  :root { --bg:#111418; --panel:#1b2027; --line:#2a323c; --fg:#e8eaed; --mut:#9aa4b0; }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--bg); color:var(--fg); font:14px/1.45 "Segoe UI", Arial, sans-serif; }
  header { padding:14px 20px 6px; }
  h1 { font-size:19px; margin:0 0 4px; }
  .sub { color:var(--mut); }
  .controls { display:flex; align-items:center; gap:10px; padding:8px 20px; position:sticky; top:0;
              background:var(--bg); z-index:5; border-bottom:1px solid var(--line); }
  button { background:#2a323c; color:var(--fg); border:0; border-radius:6px; padding:6px 14px; cursor:pointer; font-size:14px; }
  button:hover { background:#39434f; }
  input[type=range] { flex:1; accent-color:#4f8cff; }
  .pos { min-width:90px; text-align:center; color:var(--mut); }
  svg#chart { display:block; width:calc(100% - 40px); height:190px; margin:10px 20px 0; background:var(--panel);
              border:1px solid var(--line); border-radius:8px; }
  #timeline { margin:10px 20px 0; background:var(--panel); border:1px solid var(--line); border-radius:8px;
              padding:10px 12px; overflow-x:auto; }
  .trow { display:flex; align-items:center; gap:0; }
  .rlabel { width:110px; min-width:110px; color:var(--mut); font-size:12px; }
  .sq { flex:0 0 auto; cursor:pointer; }
  .sq.C { background:#2e7d32; } .sq.D { background:#c62828; }
  .sq.flip { outline:2px dashed #ffd54f; outline-offset:-2px; }
  .sq.oppSusp { outline:2px dotted #ff8a65; outline-offset:-2px; }
  .sq.sel { outline:2px solid #4f8cff; outline-offset:-1px; }
  .tick { flex:0 0 auto; }
  .tick.dim { opacity:.15; }
  #detail, #analytics { margin:10px 20px; background:var(--panel); border:1px solid var(--line);
                        border-radius:8px; padding:12px 16px; }
  #detail h3, #analytics h3 { margin:0 0 8px; font-size:15px; }
  .kv { display:grid; grid-template-columns:230px 1fr; gap:2px 14px; }
  .kv b { color:var(--mut); font-weight:600; }
  .legend { display:flex; flex-wrap:wrap; gap:6px 14px; padding:8px 20px 0; }
  .chip { cursor:pointer; font-size:12.5px; color:var(--fg); user-select:none; }
  .chip .dot { display:inline-block; width:10px; height:10px; border-radius:2px; margin-right:5px; }
  .chip.off { opacity:.35; }
  .tip { position:fixed; z-index:10; background:#000c; color:#fff; padding:6px 9px; border-radius:6px;
         font-size:12px; pointer-events:none; display:none; max-width:340px; }
  .stat { color:var(--mut); }
</style></head>
<body>
<header>
  <h1 id="title"></h1>
  <div class="sub" id="subtitle"></div>
</header>
<div class="controls">
  <button id="play">&#9654; Играть</button>
  <button id="stop">&#9632;</button>
  <input type="range" id="scrub" min="1" value="1">
  <span class="pos" id="pos"></span>
  <span class="sub">клик по столбцу — детали, &larr;/&rarr; — шаг</span>
</div>
<svg id="chart" viewBox="0 0 1000 190" preserveAspectRatio="none"></svg>
<div class="legend" id="legend"></div>
<div id="timeline">
  <div class="trow"><div class="rlabel" id="lblMe"></div><div class="trow" id="rowMe" style="flex:1"></div></div>
  <div class="trow"><div class="rlabel" id="lblOpp"></div><div class="trow" id="rowOpp" style="flex:1"></div></div>
  <div class="trow"><div class="rlabel">Причина</div><div class="trow" id="rowReason" style="flex:1"></div></div>
  <div class="trow" id="rowOppReasonWrap" style="display:none"><div class="rlabel">Причина соперника</div><div class="trow" id="rowOppReason" style="flex:1"></div></div>
</div>
<div id="detail"><h3>Ход</h3><div class="kv" id="dvals"></div></div>
<div id="analytics"><h3>Автосводка матча</h3><div class="kv" id="avals"></div></div>
<div class="tip" id="tip"></div>
<script>
const DATA = __DATA__;
const T = DATA.turns, N = T.length;
let sel = N;

const $ = id => document.getElementById(id);
$("title").textContent = `${DATA.meta.me}  против  ${DATA.meta.opp}`;
$("subtitle").textContent =
  `шум ${Math.round(DATA.meta.noise*100)}% · seed ${DATA.meta.seed} · ${N} ходов · ` +
  `итог ${DATA.meta.myTotal} : ${DATA.meta.oppTotal} ` +
  `(${(DATA.meta.myTotal/N).toFixed(3)} : ${(DATA.meta.oppTotal/N).toFixed(3)} за ход)`;
$("scrub").max = N; $("scrub").value = N;
$("lblMe").textContent = DATA.meta.me.split(":")[0];
$("lblOpp").textContent = DATA.meta.opp.split(":")[0];
if (DATA.oppReasons) $("rowOppReasonWrap").style.display = "flex";

// --- timeline squares sized to fit width ---
const cell = Math.max(3, Math.min(16, Math.floor(1200 / N)));
const gap = cell >= 6 ? 1 : 0;
function mkSquare(cls, t, extra) {
  const d = document.createElement("div");
  d.className = "sq " + cls + (extra ? " " + extra : "");
  d.style.width = cell + "px"; d.style.height = cell + "px";
  if (gap) d.style.marginRight = gap + "px";
  d.dataset.t = t;
  return d;
}
T.forEach(r => {
  const me = mkSquare(r.me === "C" ? "C" : "D", r.t, (r.flip ? "flip" : ""));
  const op = mkSquare(r.opp === "C" ? "C" : "D", r.t, (r.oppSusp ? "oppSusp" : ""));
  const tk = document.createElement("div");
  tk.className = "tick"; tk.dataset.t = r.t; tk.dataset.reason = r.reason;
  tk.style.width = cell + "px"; tk.style.height = Math.max(3, cell - 3) + "px";
  tk.style.background = r.color;
  if (gap) tk.style.marginRight = gap + "px";
  $("rowMe").appendChild(me); $("rowOpp").appendChild(op); $("rowReason").appendChild(tk);
  if (DATA.oppReasons) {
    const ot = document.createElement("div");
    ot.className = "tick"; ot.dataset.t = r.t;
    ot.style.width = cell + "px"; ot.style.height = Math.max(3, cell - 3) + "px";
    ot.style.background = r.oppReasonColor;
    if (gap) ot.style.marginRight = gap + "px";
    $("rowOppReason").appendChild(ot);
  }
});

// --- score chart ---
(function chart() {
  const svg = $("chart"), W = 1000, H = 190, padL = 46, padB = 18;
  const maxY = Math.max(DATA.meta.myTotal, DATA.meta.oppTotal, 1);
  const xs = t => padL + (W - padL - 8) * (t - 1) / (N - 1);
  const ys = v => (H - padB - 6) * (1 - v / maxY) + 4;
  let line1 = "", line2 = "";
  T.forEach((r, i) => {
    line1 += (i ? "L" : "M") + xs(r.t).toFixed(1) + " " + ys(r.sMe).toFixed(1) + " ";
    line2 += (i ? "L" : "M") + xs(r.t).toFixed(1) + " " + ys(r.sOpp).toFixed(1) + " ";
  });
  let grid = "";
  for (let k = 0; k <= 4; k++) {
    const v = maxY * k / 4, y = ys(v);
    grid += `<line x1="${padL}" y1="${y}" x2="${W-8}" y2="${y}" stroke="#2a323c" stroke-width="1"/>` +
            `<text x="${padL-6}" y="${y+4}" fill="#9aa4b0" font-size="11" text-anchor="end">${Math.round(v)}</text>`;
  }
  svg.innerHTML = grid +
    `<text x="${W-10}" y="${ys(DATA.meta.myTotal)+14}" fill="#66bb6a" font-size="12" text-anchor="end">${DATA.meta.myTotal}</text>` +
    `<text x="${W-10}" y="${ys(DATA.meta.oppTotal)-6}" fill="#e57373" font-size="12" text-anchor="end">${DATA.meta.oppTotal}</text>` +
    `<path d="${line1}" stroke="#66bb6a" stroke-width="1.6" fill="none"/>` +
    `<path d="${line2}" stroke="#e57373" stroke-width="1.6" fill="none"/>` +
    `<line id="cursor" x1="0" y1="4" x2="0" y2="${H-padB}" stroke="#4f8cff" stroke-width="1" visibility="hidden"/>`;
})();

// --- legend (reason chips) ---
(function legend() {
  const counts = {};
  T.forEach(r => counts[r.reason] = (counts[r.reason] || 0) + 1);
  Object.entries(counts).sort((a,b) => b[1]-a[1]).forEach(([rn, c]) => {
    const r0 = T.find(r => r.reason === rn);
    const chip = document.createElement("span");
    chip.className = "chip"; chip.dataset.reason = rn;
    chip.innerHTML = `<span class="dot" style="background:${r0.color}"></span>${r0.reasonRu} (${c})`;
    chip.onclick = () => { chip.classList.toggle("off");
      document.querySelectorAll("#rowReason .tick").forEach(tk =>
        tk.classList.toggle("dim", chip.classList.contains("off") && tk.dataset.reason !== rn)); };
    $("legend").appendChild(chip);
  });
})();

// --- selection + detail panel ---
function kv(label, val) { return `<b>${label}</b><span>${val}</span>`; }
// noise_ladder helpers: missing field (old zeroresp) renders as em dash, never crashes
function nn(v) { return (v === null || typeof v === "undefined") ? "—" : v; }
function fmtBal(v) {
  if (v === null || typeof v === "undefined") return "—";
  if (v < 0) return `<span style="color:#e57373">${v}</span>`;
  return v > 0 ? `+${v}` : "0";
}
function renderDetail(t) {
  const r = T[t-1];
  $("detail").querySelector("h3").textContent = `Ход ${t} из ${N}`;
  const noiseFlip = r.flip ? `<span style="color:#ffd54f">шум: хотели ${r.intent}, получилось ${r.me}</span>` : "нет";
  const suspicious = r.oppSusp ? "да (после длинного мира — похоже на шум)" : "нет";
  const strikes = (r.scheduled && r.scheduled.length) ? r.scheduled.join(", ") : "—";
  const harvest = (r.harvestLeft === null || typeof r.harvestLeft === "undefined")
    ? "—" : (r.harvestLeft > 0 ? `да, осталось ${r.harvestLeft}` : "нет");
  $("dvals").innerHTML =
    kv("ZeroResp →", r.me) + kv("Соперник →", r.opp) +
    kv("Причина решения", `<span style="color:${r.color}">${r.reasonRu}</span> (${r.reason})`) +
    kv("Состояние", r.stateRu) +
    kv("Шум (наш ход)", noiseFlip) +
    kv("«Необъяснимый» D соперника", suspicious) +
    kv("Теплота / цель", `${r.warmth} → ${r.twarmth}`) +
    kv("Долг / очередь / системные", `${r.debt} / [${r.queue.join(", ")}] / ${r.systemic}`) +
    kv("Эхо-прощение / разовые", `${r.echo} / ${r.osf}`) +
    kv("Оценка шума (CC пар)", `${r.pnoise} (${r.cc})`) +
    kv("Мнение об оппоненте", `${r.tactical} / настроение: ${r.mood}`) +
    kv("Красная линия / apology / bad standing", `${r.red} / ${r.apology} / ${r.bad}`) +
    kv("Очки накопленно", `${r.sMe} : ${r.sOpp}`) +
    kv("Улик в окне (лестница)", nn(r.evidence)) +
    kv("Запланированные удары", strikes) +
    kv("Долги / помилования", `${nn(r.debtLedger)} / ${nn(r.pardoned)}`) +
    kv("Баланс очков", fmtBal(r.balance)) +
    kv("Акция активна", harvest);
  $("pos").textContent = `${t} / ${N}`;
  $("scrub").value = t;
  const cur = Math.round((r.sMe + r.sOpp) / 2);
  const cx = 46 + (1000 - 46 - 8) * (t - 1) / Math.max(1, N - 1);
  const c = document.getElementById("cursor");
  c.setAttribute("x1", cx); c.setAttribute("x2", cx); c.setAttribute("visibility", "visible");
}
function select(t, scroll) {
  t = Math.max(1, Math.min(N, t));
  document.querySelectorAll(".sq.sel").forEach(e => e.classList.remove("sel"));
  document.querySelectorAll(`.sq[data-t="${t}"]`).forEach(e => e.classList.add("sel"));
  sel = t; renderDetail(t);
  if (scroll) {
    const el = document.querySelector(`#rowMe .sq[data-t="${t}"]`);
    if (el) el.scrollIntoView({ inline: "center", block: "nearest" });
  }
}
$("rowMe").onclick = $("rowOpp").onclick = e => { if (e.target.dataset.t) select(+e.target.dataset.t, false); };
$("scrub").oninput = e => select(+e.target.value, true);
document.onkeydown = e => {
  if (e.key === "ArrowRight") { select(sel + 1, true); e.preventDefault(); }
  if (e.key === "ArrowLeft")  { select(sel - 1, true); e.preventDefault(); }
};
let timer = null;
$("play").onclick = () => { if (timer) return; if (sel >= N) select(1, true);
  timer = setInterval(() => { if (sel >= N) { clearInterval(timer); timer = null; return; }
    select(sel + 1, false); const el = document.querySelector(`#rowMe .sq[data-t="${sel}"]`);
    if (el) el.scrollIntoView({ inline: "center", block: "nearest" }); }, 120); };
$("stop").onclick = () => { clearInterval(timer); timer = null; };

// --- hover tooltip ---
const tip = $("tip");
document.addEventListener("mousemove", e => {
  const el = e.target.closest ? e.target.closest(".sq, .tick") : null;
  if (!el || !el.dataset.t) { tip.style.display = "none"; return; }
  const r = T[el.dataset.t - 1];
  tip.innerHTML = `<b>Ход ${r.t}</b><br>${DATA.meta.me.split(":")[0]}: ${r.me}` +
    (r.flip ? ` <span style="color:#ffd54f">(хотели ${r.intent})</span>` : "") +
    `<br>${DATA.meta.opp.split(":")[0]}: ${r.opp}` +
    (r.oppSusp ? ` <span style="color:#ff8a65">(похоже на шум)</span>` : "") +
    `<br><span style="color:${r.color}">${r.reasonRu}</span>`;
  tip.style.display = "block";
  tip.style.left = Math.min(window.innerWidth - 360, e.clientX + 14) + "px";
  tip.style.top = (e.clientY + 14) + "px";
});

// --- analytics ---
(function analytics() {
  let cc=0, cd=0, dc=0, dd=0, flips=0, oppSusp=0, best=[0,0,0], run=0, runStart=1;
  T.forEach(r => {
    if (r.me==="C" && r.opp==="C") cc++; else if (r.me==="C") cd++;
    else if (r.opp==="C") dc++; else dd++;
    if (r.flip) flips++;
    if (r.oppSusp) oppSusp++;
    if (r.me==="D" && r.opp==="D") { run++; if (run > best[0]) best = [run, runStart, r.t]; }
    else { run = 0; runStart = r.t + 1; }
  });
  const pct = x => (100 * x / N).toFixed(1) + "%";
  const redSpans = [];
  T.forEach(r => { if (r.red) { if (redSpans.length && redSpans[redSpans.length-1][1] === r.t-1)
      redSpans[redSpans.length-1][1] = r.t; else redSpans.push([r.t, r.t]); } });
  const redTxt = redSpans.length
    ? redSpans.map(s => s[0] === s[1] ? `ход ${s[0]}` : `ходы ${s[0]}–${s[1]}`).join(", ") : "нет";
  const last = T[N - 1];  // noise_ladder totals live on the final snapshot
  $("avals").innerHTML =
    kv("Пары C/C · C/D · D/C · D/D", `${pct(cc)} · ${pct(cd)} · ${pct(dc)} · ${pct(dd)}`) +
    kv("Самая длинная взаимная война D/D", best[0] > 0 ? `${best[0]} ходов (с хода ${best[1]} по ${best[2]})` : "нет") +
    kv("Наши ходы, испорченные шумом", flips) +
    kv("«Необъяснимые» D соперника (≥3 CC подряд)", oppSusp) +
    kv("Красная линия активна", redTxt) +
    kv("Помилования за матч", nn(last.pardoned)) +
    kv("Наши флипы учтены в оценке шума", nn(last.myFlips)) +
    kv("Финальный баланс", fmtBal(last.balance));
})();

select(N, false);
</script></body></html>
"""


def render(data: dict, title: str) -> str:
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return TEMPLATE.replace("__TITLE__", html.escape(title)).replace("__DATA__", blob)


GALLERY = [
    ("Grudger", 0.05, 42, "Война после шумовой искры"),
    ("TitForTat", 0.05, 42, "Реципрокатор под шумом"),
    ("Punisher", 0.05, 42, "Жёсткий реципрокатор (Punisher) под шумом"),
    ("HardTitForTat", 0.05, 42, "Жёсткий реципрокатор (Hard TFT) под шумом"),
    ("Cooperator", 0.0, 42, "Сбор урожая в конце матча"),
    ("ZDExtort4", 0.0, 42, "ZD-эксторционер: тупик"),
    ("ZeroResp", 0.05, 42, "Самосопоставление под шумом"),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vs", default=None, help="opponent name (e.g. Grudger) or ZeroResp")
    ap.add_argument("--noise", type=float, default=0.0)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--turns", type=int, default=200)
    ap.add_argument("--out-dir", default=str(ROOT / "benchmarks" / "viewer"))
    ap.add_argument("--open", action="store_true", help="open generated page in browser")
    ap.add_argument("--ladder", choices=["on", "off", "both"], default="on",
                    help="noise_ladder state for the captured match")
    ap.add_argument("--dashboard", action="store_true",
                    help="generate one page per field-pack opponent (5%% noise) + dashboard index")
    ap.add_argument("--gallery", action="store_true", help="generate 5 preset scenarios + index")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    ladder_states = {"on": [True], "off": [False], "both": [True, False]}[args.ladder]

    def fname(opp, noise, seed, ladder=True):
        suffix = "" if ladder else "_nolad"
        return f"match_{opp.replace(' ', '_')}_noise{int(noise*100)}_seed{seed}{suffix}.html"

    paths = []
    if args.dashboard:
        # Дашборд: страница для каждого оппонента полевого пака при 5% шуме,
        # индекс с SPT и дельтой против v5.2, отсортирован от слабых к сильным.
        from run_field import FIELD_PACK
        res_dir = ROOT / "benchmarks" / "results"

        def _scores(path):
            try:
                data = json.loads(Path(path).read_text(encoding="utf-8"))
                for run in data["runs"]:
                    if abs(run.get("noise", -1) - 0.05) < 1e-9:
                        return run.get("h2h_spt", {})
            except Exception:
                pass
            return {}

        cur = {}
        base = {}
        field_files = sorted(res_dir.glob("field_*.json"))
        if field_files:
            cur = _scores(field_files[-1])
        bfiles = list(res_dir.glob("baseline_v52_field.json"))
        if bfiles:
            base = _scores(bfiles[0])

        def _lookup(table, opp):
            # ключи JSON - имена классов без пробелов; FIELD_PACK смешанный
            if opp in table:
                return table[opp]
            key = opp.replace(" ", "")
            return table.get(key)

        pages = []
        for opp in FIELD_PACK:
            data = capture(opp, 0.05, args.seed, args.turns)
            p = out_dir / fname(opp, 0.05, args.seed)
            p.write_text(render(data, f"{opp} · 5% · лестница ON"), encoding="utf-8")
            spt = _lookup(cur, opp)
            b = _lookup(base, opp)
            delta = (spt - b) if (spt is not None and b is not None) else None
            pages.append((opp, p.name, spt, delta))
            print(f"  {opp}: spt={spt}")

        def dcell(v):
            if v is None:
                return "<td>—</td>"
            color = "#7bd88f" if v > 0.05 else ("#ff6b6b" if v < -0.15 else "#e8eaed")
            return f"<td style='color:{color}'>{v:+.3f}</td>"

        rows = sorted(pages, key=lambda x: (x[2] if x[2] is not None else 9))
        body = []
        for opp, fname_, spt, delta in rows:
            spt_txt = f"{spt:.3f}" if spt is not None else "—"
            body.append(f"<tr><td><a href='{fname_}'>{opp}</a></td>"
                        f"<td>{spt_txt}</td>{dcell(delta)}</tr>")
        dash = ["<html><head><meta charset='utf-8'><title>ZeroResp dashboard</title>",
                "<style>body{background:#111418;color:#e8eaed;font:14px 'Segoe UI',Arial,sans-serif;margin:20px}"
                "h2{margin:8px 0}table{border-collapse:collapse}td,th{border:1px solid #2a323c;padding:6px 14px}"
                "th{background:#1b2027;color:#9aa4b0;text-align:left}a{color:#7cb3ff;text-decoration:none}a:hover{text-decoration:underline}"
                ".sub{color:#9aa4b0;margin:4px 0 14px}</style></head><body>",
                "<h2>ZeroResp v5.3 — дашборд матчей (полевой пак, шум 5%, seed 42)</h2>",
                "<div class='sub'>Сортировка от слабых матчей к сильным. Δ — разница с v5.2. "
                "Клик по оппоненту — интерактивная страница матча.</div>",
                "<table><tr><th>Оппонент</th><th>SPT (наши очки/ход)</th><th>Δ vs v5.2</th></tr>"]
        dash += body
        dash.append("</table><p><a href='index.html'>← базовая галерея (7 кейсов)</a> · "
                    "<a href='match_SlowTitForTwoTats2_noise5_seed44.html'>Диагностика сида 44: SlowTF2T2 (лестница ON)</a> · "
                    "<a href='match_SlowTitForTwoTats2_noise5_seed44_nolad.html'>OFF</a></p>")
        dash.append("</body></html>")
        dp = out_dir / "dashboard.html"
        dp.write_text("\n".join(dash), encoding="utf-8")
        print(f"Dashboard: {dp} ({len(pages)} pages)")
        if args.open:
            import webbrowser
            webbrowser.open(dp.as_uri())
    elif args.gallery:
        paths = []
        for opp, noise, seed, label in GALLERY:
            data = capture(opp, noise, seed, args.turns)
            p = out_dir / fname(opp, noise, seed)
            p.write_text(render(data, label), encoding="utf-8")
            paths.append((p, label))
            print(f"  {label}: {p.name}")
        index = ["<html><head><meta charset='utf-8'><title>ZeroResp viewer</title></head><body>",
                 "<h2>ZeroResp — визуализация матчей</h2><ul>"]
        for p, label in paths:
            index.append(f"<li><a href='{p.name}'>{label} — {p.stem}</a></li>")
        index.append("</ul></body></html>")
        ip = out_dir / "index.html"
        ip.write_text("\n".join(index), encoding="utf-8")
        print(f"Gallery index: {ip}")
        if args.open:
            import webbrowser
            webbrowser.open(ip.as_uri())
    else:
        opp = args.vs or "Grudger"
        for ladder in ladder_states:
            data = capture(opp, args.noise, args.seed, args.turns, ladder=ladder)
            p = out_dir / fname(opp, args.noise, args.seed, ladder)
            state = "лестница ON" if ladder else "лестница OFF (v5.2)"
            p.write_text(render(data, f"{opp} · noise {args.noise} · {state}"), encoding="utf-8")
            print(p)
        if args.open:
            import webbrowser
            webbrowser.open(p.as_uri())


if __name__ == "__main__":
    main()
