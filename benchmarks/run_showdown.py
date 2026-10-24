"""Showdown: all ZeroResp versions + library leaders + difficulty controls
in one shared round-robin, plus paired head-to-head between versions.

    python benchmarks/run_showdown.py --noises 0 0.05 0.1 --turns 200 --reps 3 --seed 42

Writes benchmarks/results/showdown_<stamp>.json and .md.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
for p in (str(ROOT), str(ROOT / "benchmarks")):
    if p not in sys.path:
        sys.path.insert(0, p)

import axelrod as axl  # noqa: E402

import zeroresp as _zr53  # noqa: E402
from run_field import build_pack  # noqa: E402
from paired_delta import VERSIONS  # noqa: E402


class ZeroRespV52Control(_zr53.ZeroResp):
    """v5.2 = v5.3 with the ladder off; renamed so the tournament can tell them apart."""

    name = "ZeroResp v5.2 (ladder off)"

    def __init__(self):
        super().__init__(features=_zr53.Features(noise_ladder=False))


LEADERS = [
    # Top of the full-library stress map across regimes (STRESS_v53.md).
    "Evolved ANN 5 Noise 05", "Evolved FSM 16 Noise 05", "Second by RichardHufford",
    "Evolved FSM 6", "EvolvedLookerUp2_2_2", "Evolved FSM 16", "Evolved HMM 5",
    "PSO Gambler 1_1_1", "Evolved ANN 5", "Evolved ANN", "PSO Gambler Mem1",
    "PSO Gambler 2_2_2", "Evolved FSM 4", "First by Downing", "Revised Downing",
]

CONTROLS = [
    # Difficulty tiers: honest reciprocators, exploiters, stochastic, degenerate.
    "TitForTat", "TwoTitsForTat", "Gradual", "HardProber", "Calculator",
    "TrickyCooperator", "ZDExtort2", "Grudger", "WinStayLoseShift",
    "Alternator", "Random", "CyclerCCD", "Cooperator", "Defector",
]

_display = {}
for _s in axl.strategies:
    _display[_s.__name__] = _s.name
    _display.setdefault(_s.name, _s.name)
LEADERS_DISP = {_display.get(n, n) for n in LEADERS}
CONTROLS_DISP = {_display.get(n, n) for n in CONTROLS}


def our_players():
    """(label, class) pairs; instantiate at use site."""
    players = list(VERSIONS.items())
    players.append(("v5.2", ZeroRespV52Control))
    return players


def run_rr(noise, turns, reps, seed):
    ours = our_players()
    lib = [cls() for cls in build_pack(",".join(LEADERS) + "," + ",".join(CONTROLS))]
    players = [cls() for _, cls in ours] + lib
    t = axl.Tournament(players, turns=turns, repetitions=reps, seed=seed, noise=noise)
    res = t.play(progress_bar=False)
    rows = []
    for i, p in enumerate(players):
        sc = res.scores[i]
        rows.append({"name": p.name, "spt": round(sum(sc) / len(sc) / turns, 4)})
    order = sorted(rows, key=lambda r: -r["spt"])
    for pos, r in enumerate(order, 1):
        r["pos"] = pos
    return {"noise": noise, "players": len(players), "rows": rows,
            "elapsed_sec": None}


def tier_of(name):
    if name in LEADERS_DISP:
        return "leader"
    if name in CONTROLS_DISP:
        return "control"
    return "zeroresp"


def h2h(noise, turns, seeds):
    """Paired direct matches between every pair of our versions."""
    ours = our_players()
    from axelrod import _module_random as mr
    out = {}
    for i in range(len(ours)):
        for j in range(i + 1, len(ours)):
            la, ca = ours[i]
            lb, cb = ours[j]
            sa, sb = [], []
            for seed in seeds:
                mr.seed(seed * 2)
                ma = axl.Match((ca(), cb()), turns=turns, seed=seed, noise=noise)
                ma.play()
                ta = sum(s[0] for s in ma.scores()) / turns
                tb = sum(s[1] for s in ma.scores()) / turns
                sa.append(ta)
                sb.append(tb)
            mean = lambda v: sum(v) / len(v)
            out[f"{la} vs {lb}"] = {
                f"spt_{la}": round(mean(sa), 4), f"spt_{lb}": round(mean(sb), 4),
                f"delta_{la}_minus_{lb}": round(mean(sa) - mean(sb), 4),
            }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--noises", nargs="+", type=float, default=[0.0, 0.05, 0.1])
    ap.add_argument("--turns", type=int, default=200)
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--h2h-seeds", type=int, default=30)
    args = ap.parse_args()

    h2h_seeds = list(range(args.seed, args.seed + args.h2h_seeds))
    out = {"config": vars(args), "round_robin": {}, "h2h": {}}
    t0 = time.time()

    for noise in args.noises:
        rr = run_rr(noise, args.turns, args.reps, args.seed)
        out["round_robin"][str(noise)] = rr
        best = sorted(rr["rows"], key=lambda r: -r["spt"])[0]
        lines = [f"### Round-robin, noise={noise:.0%}, {rr['players']} players, "
                 f"{args.turns} turns x {args.reps} reps, seed {args.seed}", "",
                 "| # | Player | SPT | Tier |", "|--:|---|--:|---|"]
        for r in sorted(rr["rows"], key=lambda r: -r["spt"]):
            mark = " **<- ours**" if r["name"].startswith("ZeroResp") else ""
            lines.append(f"| {r['pos']} | {r['name']} | {r['spt']} | "
                         f"{tier_of(r['name'])}{mark} |")
        print("\n".join(lines), flush=True)

        hh = h2h(noise, args.turns, h2h_seeds)
        out["h2h"][str(noise)] = hh
        lines = ["", f"### Head-to-head between versions, noise={noise:.0%}, "
                     f"{args.h2h_seeds} paired seeds", "",
                 "| Pair | SPT A | SPT B | Delta A-B |", "|---|--:|--:|--:|"]
        for k, v in hh.items():
            a, b = k.split(" vs ")
            lines.append(f"| {k} | {v[f'spt_{a}']} | {v[f'spt_{b}']} | "
                         f"{v[f'delta_{a}_minus_{b}']} |")
        print("\n".join(lines), flush=True)

    d = ROOT / "benchmarks" / "results"
    d.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    out["elapsed_sec"] = round(time.time() - t0, 1)
    (d / f"showdown_{stamp}.json").write_text(json.dumps(out, indent=1, default=str),
                                              encoding="utf-8")
    print(f"\nsaved showdown_{stamp}.json, elapsed {out['elapsed_sec']}s")


if __name__ == "__main__":
    main()
