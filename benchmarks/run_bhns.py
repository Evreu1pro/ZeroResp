"""BHNS: Blind Hold-out & Noise-Model Stress for ZeroResp v5.3 vs v5.2.

Design (scaled from full protocol, statistically equivalent):
- Train pool: field pack (33 opponents, used during tuning).
- Hold-out pool: 40 library strategies, stratified by family, NEVER used
  during tuning. Split frozen in results/research/bhns/split.json.
- Noise models applied to the STRATEGY under test (both versions identically):
    action flip  - intended action inverted with prob p
    random move  - with prob p a random action replaces intended
    trembling    - with prob p a cooperative action becomes D
  Levels: 1%, 5%, 10%, 20%. Channel noise (opponents) is OFF - only the
  strategy under test is perturbed.
- 10 seeds per (model, level). Each seed = one mini round-robin:
  hold-out(40) + baselines(5) + ZR v5.3 + ZR v5.2  -> exact hold-out rank
  per seed; plus pairwise matches vs the 33 train opponents.

Resumable: every run saved as JSON, existing runs skipped.

    python benchmarks/run_bhns.py
"""
from __future__ import annotations

import json
import random
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import axelrod as axl  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from zeroresp import Features, ZeroResp  # noqa: E402

C, D = axl.Action.C, axl.Action.D

OUT = ROOT / "benchmarks" / "results" / "research" / "bhns"
SPLIT_FILE = OUT / "split.json"

NOISE_MODELS = ["action", "random", "trembling", "perception"]
NOISE_LEVELS = [0.01, 0.05, 0.10, 0.20]
KEY_COMBOS = {(m, l) for m in ("action", "random", "trembling") for l in (0.10, 0.20)}
KEY_SEEDS = list(range(30))          # 30 сидов для ключевых комбинаций
BASE_SEEDS = list(range(10))         # 10 сидов для остальных
PERCEPTION_LEVELS = [0.05, 0.10, 0.20]
TURNS = 200
BASELINES = ["TitForTat", "Grudger", "ZDExtort4", "Evolved ANN 5 Noise 05", "Random"]

FAMILY_MATCHERS = [
    ("tft", lambda n: "TitForTat" in n or "TFT" in n or n in ("Gradual", "Firm But Fair", "GTFT")),
    ("grudger", lambda n: "Grudger" in n or "Vengeful" in n),
    ("zd", lambda n: n.startswith("ZD")),
    ("learned", lambda n: any(s in n for s in ("Evolved", "LookerUp", "ANN", "HMM", "PSO", "Gambler", "Meta"))),
    ("exploiter", lambda n: any(s in n for s in ("Prober", "Bully", "Joss", "Tricky", "Calculator",
                                                 "Handshake", "Detective", "Predator", "Aggravater",
                                                 "Cave", "Solution", "Defector"))),
    ("random", lambda n: "Random" in n),
]


def family_of(name: str) -> str:
    for fam, pred in FAMILY_MATCHERS:
        if pred(name):
            return fam
    return "other"


class NoiseZR(ZeroResp):
    """ZeroResp with perturbation of its own actions (both versions get it)."""

    def __init__(self, noise_model="action", p=0.0, ladder=True,
                 base_epoch=25, use_profiles=True, features=None):
        feats = features if features is not None else Features(noise_ladder=ladder)
        super().__init__(base_epoch=base_epoch, use_profiles=use_profiles, features=feats)
        self._nm = noise_model
        self._p = p

    def strategy(self, opponent):
        a = super().strategy(opponent)
        if self._p <= 0:
            return a
        rng = self._random
        if self._nm == "action":
            if rng.random() < self._p:
                return D if a == C else C
            return a
        if self._nm == "random":
            if rng.random() < self._p:
                return C if rng.random() < 0.5 else D
            return a
        if self._nm == "trembling":
            if a == C and rng.random() < self._p:
                return D
            return a
        if self._nm == "perception" and self._p > 0 and opponent.history:
            # perception flip: мы ВИДИМ ходы противника перевёрнутыми;
            # собственные действия не ломаются -> лестница не активируется
            view = _PerceptionView(opponent, self._p, rng)
            return super().strategy(view)
        return a


class _FlipList:
    """History view with deterministic per-index perception flips."""
    def __init__(self, hist, p, rng):
        self._hist = hist
        self._p = p
        self._rng = rng
        self._coins = {}

    def _flipped(self, i):
        if i not in self._coins:
            self._coins[i] = self._rng.random() < self._p
        c = self._coins[i]
        if not c:
            return self._hist[i]
        return C if self._hist[i] == D else D

    def __len__(self):
        return len(self._hist)

    def __getitem__(self, i):
        return self._flipped(i)

    def __iter__(self):
        for i in range(len(self._hist)):
            yield self._flipped(i)

    def __repr__(self):
        return repr([self._flipped(i) for i in range(len(self._hist))])


class _PerceptionView:
    """Delegating proxy: history seen through perception flips."""
    def __init__(self, opp, p, rng):
        self._opp = opp
        self._fliphist = _FlipList(opp.history, p, rng)

    @property
    def history(self):
        return self._fliphist

    def __getattr__(self, name):
        return getattr(self._opp, name)


def make_split():
    """Stratified split: field pack = train, 40 others = hold-out."""
    by = {}
    for s in axl.strategies:
        by[s.__name__] = s
        by.setdefault(s.name, s)
    from run_field import FIELD_PACK  # type: ignore
    field_classes = set()
    for n in FIELD_PACK:
        cls = by.get(n) or by.get(n.replace(" ", ""))
        if cls:
            field_classes.add(cls)
    baselines = {by[b] for b in BASELINES if b in by}
    candidates = [s for s in axl.strategies
                  if s not in field_classes and s not in baselines
                  and not getattr(s, "classifier", {}).get("long_run_time")]
    rng = random.Random(7)
    fams: dict = {}
    for s in candidates:
        fams.setdefault(family_of(s.__name__), []).append(s)
    holdout = []
    target = 40
    per_fam = {f: max(1, round(target * len(v) / len(candidates))) for f, v in fams.items()}
    for f in sorted(fams):
        pool = sorted(fams[f], key=lambda s: s.__name__)
        k = min(per_fam[f], len(pool))
        holdout += rng.sample(pool, k)
    holdout = holdout[:target]
    split = {
        "train": sorted(s.__name__ for s in field_classes),
        "holdout": sorted(s.__name__ for s in holdout),
        "baselines": sorted(s.__name__ for s in baselines),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    SPLIT_FILE.write_text(json.dumps(split, indent=2), encoding="utf-8")
    return split


def get_split():
    if SPLIT_FILE.exists():
        return json.loads(SPLIT_FILE.read_text(encoding="utf-8"))
    return make_split()


def resolve(names):
    by = {}
    for s in axl.strategies:
        by[s.__name__] = s
        by.setdefault(s.name, s)
    out = []
    for n in names:
        cls = by.get(n) or by.get(n.replace(" ", ""))
        if cls is None:
            raise SystemExit(f"cannot resolve: {n}")
        out.append(cls)
    return out


def run_mini_rr(model, level, seed_i, split):
    holdout = resolve(split["holdout"])
    baselines = resolve(split["baselines"])
    players = ([NoiseZR(model, level, ladder=True)]
               + [NoiseZR(model, level, ladder=False)]
               + [cls() for cls in baselines]
               + [cls() for cls in holdout])
    zr53_idx, zr52_idx = 0, 1
    tournament = axl.Tournament(players, turns=TURNS, repetitions=1,
                                seed=1000 + seed_i, noise=0)
    results = tournament.play(progress_bar=False)
    per_spt = {}
    for i in range(len(players)):
        sc = results.scores[i]
        per_spt[i] = sum(sc) / len(sc) / TURNS
    rows = []
    for pos, idx in enumerate(results.ranking, start=1):
        is53 = idx == zr53_idx
        is52 = idx == zr52_idx
        rows.append({"pos": pos, "idx": idx,
                     "name": ("ZR_v53" if is53 else "ZR_v52" if is52
                              else players[idx].name),
                     "spt": round(per_spt[idx], 4),
                     "is_zr53": is53, "is_zr52": is52})
    r53 = next(r for r in rows if r["is_zr53"])
    r52 = next(r for r in rows if r["is_zr52"])
    # direct H2H v5.3 vs v5.2
    match = axl.Match((NoiseZR(model, level, ladder=True),
                       NoiseZR(model, level, ladder=False)),
                      turns=TURNS, seed=5000 + seed_i, noise=0)
    match.play()
    sc = match.scores()
    h2h = {"zr53": round(sum(x[0] for x in sc) / TURNS, 4),
           "zr52": round(sum(x[1] for x in sc) / TURNS, 4)}
    return {"model": model, "level": level, "seed_i": seed_i,
            "players": len(players), "rows": rows,
            "zr53_rank": r53["pos"], "zr53_spt": r53["spt"],
            "zr52_rank": r52["pos"], "zr52_spt": r52["spt"],
            "h2h_direct": h2h}


def run_train(model, level, seed_i, split):
    train = resolve(split["train"])
    out = {"model": model, "level": level, "seed_i": seed_i, "spt": {}}
    for cls in train:
        row = {}
        for ladder in (True, False):
            zr = NoiseZR(model, level, ladder=ladder)
            m = axl.Match((zr, cls()), turns=TURNS, seed=9000 + seed_i, noise=0)
            m.play()
            sc = m.scores()
            row["v53" if ladder else "v52"] = round(sum(x[0] for x in sc) / TURNS, 4)
            if ladder:
                row["ladder_activated"] = zr.nl_my_flips > 0
        out["spt"][cls.__name__] = row
    return out


def main():
    split = get_split()
    print(f"train={len(split['train'])} holdout={len(split['holdout'])}", flush=True)
    for model in NOISE_MODELS:
        levels = PERCEPTION_LEVELS if model == "perception" else NOISE_LEVELS
        for level in levels:
            seeds = KEY_SEEDS if (model, level) in KEY_COMBOS else BASE_SEEDS
            for seed_i in seeds:
                tag = f"{model}_p{int(level*100)}_s{seed_i}"
                f_rr = OUT / f"rr_{tag}.json"
                f_tr = OUT / f"train_{tag}.json"
                if not f_rr.exists():
                    res = run_mini_rr(model, level, seed_i, split)
                    f_rr.write_text(json.dumps(res), encoding="utf-8")
                    print(f"rr {tag}: zr53 #{res['zr53_rank']} ({res['zr53_spt']:.3f}) "
                          f"zr52 #{res['zr52_rank']} ({res['zr52_spt']:.3f})", flush=True)
                if not f_tr.exists():
                    res = run_train(model, level, seed_i, split)
                    f_tr.write_text(json.dumps(res), encoding="utf-8")
                    print(f"train {tag} done", flush=True)
    print("BHNS_RUNS_DONE")


if __name__ == "__main__":
    main()
