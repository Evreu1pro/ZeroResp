"""Loss analysis: where do the strategies above us earn their edge?

For a chosen ZeroResp version and noise level, plays every library opponent
against (a) our version and (b) each rival that ranked above us, same seeds,
and decomposes the total score gap per opponent.

    python benchmarks/loss_analysis.py --version v5.4.2 --noise 0.05 --seeds 30
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

from run_field import build_pack  # noqa: E402
from paired_delta import VERSIONS  # noqa: E402

# Strategies that finished above our best versions in the full-library
# round-robin (fulllib_variants_20261024_104300.json) at 0/5/10%.
RIVALS = [
    "EvolvedLookerUp2_2_2", "Evolved FSM 6", "Evolved HMM 5", "Evolved ANN 5",
    "Evolved ANN", "Evolved FSM 16", "PSO Gambler 2_2_2", "PSO Gambler 1_1_1",
    "Omega TFT", "Evolved ANN 5 Noise 05", "Second by RichardHufford",
    "Second by Borufsen", "Revised Downing", "First by Downing",
]


def category(name: str) -> str:
    n = name.lower()
    if any(k in n for k in ("evolved", "pso gambler", "lookerup", "meta ",
                            "hmm", "ann", "fsm", "memory", "doubler")):
        return "trained"
    if "cycler" in n or "anti" in n:
        return "cycler"
    if "random" in n or "stochastic" in n or "noisy" in n:
        return "stochastic"
    if any(k in n for k in ("hunter", "hopeless", "tricky", "bully", "prober",
                            "calculator", "defector", "troll", "aggrevate",
                            "knowledgeable", "worse")):
        return "exploiter"
    if any(k in n for k in ("cooperator", "forgiv", "apolog", "soft", "grudger",
                            "grim", "tit", "gradual", "pawn")):
        return "reciprocator"
    return "other"


def spt(cls, opp, turns, seed, noise):
    from axelrod import _module_random as mr
    mr.seed(seed * 2)
    m = axl.Match((cls(), opp()), turns=turns, seed=seed, noise=noise)
    m.play()
    return sum(s[0] for s in m.scores()) / turns


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="v5.4.2")
    ap.add_argument("--noise", type=float, default=0.05)
    ap.add_argument("--turns", type=int, default=200)
    ap.add_argument("--seed0", type=int, default=42)
    ap.add_argument("--seeds", type=int, default=30)
    args = ap.parse_args()
    seeds = list(range(args.seed0, args.seed0 + args.seeds))

    ours = VERSIONS[args.version]
    pack = build_pack("full")
    rival_names = [r for r in RIVALS if any(s.__name__ == r or s.name == r
                                            for s in axl.strategies)]
    rivals = {r: cls for r, cls in
              zip(rival_names, build_pack(",".join(rival_names)))}

    our_mean = {}
    rival_mean = {r: {} for r in rival_names}
    t0 = time.time()
    for i, opp in enumerate(pack):
        name = opp.__name__
        our_mean[name] = sum(spt(ours, opp, args.turns, s, args.noise)
                             for s in seeds) / len(seeds)
        for r in rival_names:
            rival_mean[r][name] = sum(spt(rivals[r], opp, args.turns, s,
                                          args.noise)
                                      for s in seeds) / len(seeds)
        if (i + 1) % 40 == 0:
            print(f"  {i+1}/{len(pack)} opponents, {time.time()-t0:.0f}s",
                  flush=True)

    rows = []
    for name in our_mean:
        gaps = {r: rival_mean[r][name] - our_mean[name] for r in rival_names}
        best_rival = max(gaps, key=gaps.get)
        rows.append({
            "opp": name, "cat": category(name),
            "our": round(our_mean[name], 4),
            "mean_gap": round(sum(gaps.values()) / len(gaps), 4),
            "worst_rival": best_rival,
            "worst_gap": round(gaps[best_rival], 4),
            "gaps": {r: round(gaps[r], 4) for r in rival_names},
        })

    total_recovery = sum(max(0.0, r["mean_gap"]) for r in rows) * 0  # placeholder
    cat_agg = {}
    for r in rows:
        c = cat_agg.setdefault(r["cat"], {"n": 0, "gap_sum": 0.0})
        c["n"] += 1
        c["gap_sum"] += r["mean_gap"]

    out = {"config": vars(args), "rows": rows,
           "category_aggregate": {k: {"n": v["n"],
                                      "mean_gap": round(v["gap_sum"] / v["n"], 4)}
                                  for k, v in cat_agg.items()},
           "total_mean_gap_over_pack": round(sum(r["mean_gap"] for r in rows)
                                             / len(rows), 5)}
    d = ROOT / "benchmarks" / "results"
    stamp = time.strftime("%Y%m%d_%H%M%S")
    out["elapsed_sec"] = round(time.time() - t0, 1)
    fn = f"loss_{args.version}_n{int(args.noise*100)}_{stamp}.json"
    (d / fn).write_text(json.dumps(out, indent=1), encoding="utf-8")

    print(f"\n=== {args.version} vs rivals at noise={args.noise:.0%}, "
          f"{len(seeds)} seeds ===")
    print("mean gap over full pack (rival minus ours):",
          out["total_mean_gap_over_pack"])
    print("\nBy category:")
    for k, v in sorted(out["category_aggregate"].items(),
                       key=lambda kv: -kv[1]["mean_gap"]):
        print(f"  {k:12s} n={v['n']:3d}  mean_gap={v['mean_gap']:+.4f}")
    print("\nTop 20 opponents where rivals out-earn us (mean over rivals):")
    for r in sorted(rows, key=lambda r: -r["mean_gap"])[:20]:
        print(f"  {r['opp'][:34]:34s} [{r['cat']:11s}] our={r['our']:.3f} "
              f"gap={r['mean_gap']:+.3f} (worst: {r['worst_rival']} "
              f"{r['worst_gap']:+.3f})")
    print(f"\nsaved {fn}, elapsed {out['elapsed_sec']}s")


if __name__ == "__main__":
    main()
