"""Per-version SPT by difficulty tier: leaders vs controls, paired seeds.

    python benchmarks/tier_scores.py --noises 0 0.05 0.1 --seeds 30

For every ZeroResp version (canonical factories, paired_delta.VERSIONS) and
every opponent in the leaders/controls tiers, plays a direct axl.Match with
the seed_breakdown seeding convention and reports mean SPT per tier.
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

from run_showdown import LEADERS, CONTROLS, our_players  # noqa: E402
from run_field import build_pack  # noqa: E402


def spt(cls_a, cls_b, turns, seed, noise):
    from axelrod import _module_random as mr
    mr.seed(seed * 2)
    m = axl.Match((cls_a(), cls_b()), turns=turns, seed=seed, noise=noise)
    m.play()
    return sum(s[0] for s in m.scores()) / turns


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--noises", nargs="+", type=float, default=[0.0, 0.05, 0.1])
    ap.add_argument("--turns", type=int, default=200)
    ap.add_argument("--seed0", type=int, default=42)
    ap.add_argument("--seeds", type=int, default=30)
    args = ap.parse_args()
    seeds = list(range(args.seed0, args.seed0 + args.seeds))

    leaders = build_pack(",".join(LEADERS))
    controls = build_pack(",".join(CONTROLS))
    out = {"config": vars(args), "versions": {}}
    t0 = time.time()

    for label, cls in our_players():
        rec = {}
        for tier_name, pack in (("leaders", leaders), ("controls", controls)):
            per_noise = {}
            for noise in args.noises:
                vals = []
                for opp in pack:
                    for s in seeds:
                        vals.append(spt(cls, opp, args.turns, s, noise))
                per_noise[str(noise)] = round(sum(vals) / len(vals), 4)
            rec[tier_name] = per_noise
            print(f"{label:8s} {tier_name:9s} " +
                  " ".join(f"n{float(n):.0%}={v}" for n, v in per_noise.items()),
                  flush=True)
        out["versions"][label] = rec

    d = ROOT / "benchmarks" / "results"
    stamp = time.strftime("%Y%m%d_%H%M%S")
    out["elapsed_sec"] = round(time.time() - t0, 1)
    (d / f"tier_scores_{stamp}.json").write_text(json.dumps(out, indent=1),
                                                 encoding="utf-8")
    print(f"saved tier_scores_{stamp}.json, elapsed {out['elapsed_sec']}s")


if __name__ == "__main__":
    main()
