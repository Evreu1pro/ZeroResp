"""Full-library round-robin with every ZeroResp version inside the pool.

    python benchmarks/run_fulllib_variants.py --noises 0 0.05 0.1 --turns 200 --seed 42

Each noise level plays one full round-robin: 221 short-run-time library
strategies + 7 ZeroResp entries (v5.2 control, v5.3, v5.4-proto, v5.4.1,
v5.4.2, v5.5, v5.6). Library entries whose class name starts with ZeroResp
are filtered out to avoid duplicates.

Writes benchmarks/results/fulllib_variants_<stamp>.json and .md.
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
from paired_delta import VERSIONS  # noqa: E402


class ZeroRespV52Control(_zr53.ZeroResp):
    name = "ZeroResp v5.2 (ladder off)"

    def __init__(self):
        super().__init__(features=_zr53.Features(noise_ladder=False))


def library_pack():
    return [s for s in axl.short_run_time_strategies
            if not getattr(s, "classifier", {}).get("long_run_time")
            and not s.__name__.startswith("ZeroResp")]


def run_regime(noise, turns, reps, seed):
    ours = [(label, cls()) for label, cls in VERSIONS.items()]
    ours.append(("v5.2", ZeroRespV52Control()))
    lib = [cls() for cls in library_pack()]
    players = [p for _, p in ours] + lib
    our_idx = set(range(len(ours)))
    label_of = {i: label for i, (label, _) in enumerate(ours)}

    t = axl.Tournament(players, turns=turns, repetitions=reps, seed=seed,
                       noise=noise)
    res = t.play(progress_bar=False)

    def display(i):
        return label_of[i] if i in our_idx else players[i].name

    spt_of = {}
    for i in range(len(players)):
        sc = res.scores[i]
        spt_of[i] = round(sum(sc) / len(sc) / turns, 4)
    rows = [{"pos": pos, "idx": idx, "name": display(idx),
             "spt": spt_of[idx]}
            for pos, idx in enumerate(res.ranking, 1)]
    return {"noise": noise, "turns": turns, "reps": reps, "seed": seed,
            "players": len(players), "rows": rows,
            "our_names": sorted(label_of.values())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--noises", nargs="+", type=float, default=[0.0, 0.05, 0.1])
    ap.add_argument("--turns", type=int, default=200)
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    out = {"config": vars(args), "regimes": []}
    t0 = time.time()
    for noise in args.noises:
        print(f"running noise={noise:.0%} ...", flush=True)
        reg = run_regime(noise, args.turns, args.reps, args.seed)
        out["regimes"].append(reg)

        lines = [f"## Full library + ZeroResp variants, noise={noise:.0%}, "
                 f"{reg['players']} players, {args.turns} turns x {args.reps} reps, "
                 f"seed {args.seed}", "",
                 "### Top 15 + our entries", "",
                 "| # | Player | SPT |", "|--:|---|--:|"]
        our_set = set(reg["our_names"])
        shown = [r for r in reg["rows"][:15]]
        rest = [r for r in reg["rows"][15:] if r["name"] in our_set]
        for r in shown + rest:
            mark = " **<- ours**" if r["name"] in our_set else ""
            lines.append(f"| {r['pos']} | {r['name']} | {r['spt']}{mark} |")
        print("\n".join(lines), flush=True)

        lines = ["", "### Our entries by noise", "",
                 "| Version | Rank | of | SPT | Gap to #1 | Gap to best library |",
                 "|---|--:|--:|--:|--:|--:|"]
        best_lib = next(r for r in reg["rows"] if r["name"] not in our_set)
        leader = reg["rows"][0]
        for r in reg["rows"]:
            if r["name"] in our_set:
                lines.append(f"| {r['name']} | {r['pos']} | {reg['players']} | "
                             f"{r['spt']} | {round(r['spt'] - leader['spt'], 3)} | "
                             f"{round(r['spt'] - best_lib['spt'], 3)} |")
        print("\n".join(lines), flush=True)

    d = ROOT / "benchmarks" / "results"
    d.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    out["elapsed_sec"] = round(time.time() - t0, 1)
    (d / f"fulllib_variants_{stamp}.json").write_text(
        json.dumps(out, indent=1, default=str), encoding="utf-8")
    print(f"\nsaved fulllib_variants_{stamp}.json, elapsed {out['elapsed_sec']}s")


if __name__ == "__main__":
    main()
