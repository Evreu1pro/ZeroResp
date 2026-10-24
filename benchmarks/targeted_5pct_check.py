"""Targeted 5%-noise verification of v5.4.1 / v5.4.2 fixes vs v5.3 under the
standard axl.Match harness, in two seeding conventions:

- "paired":   module RNG seeded (seed*2+role) before each construction
              (canonical seed_breakdown.py convention);
- "zdb":      p1.set_seed(seed) after construction (ZDB zdb_run_v541.py
              convention) — used for the original H2/H3 PASS claims.

Spin-out thresholds follow ZDB: TTFT SPT <= 2.20, Gradual SPT <= 2.00.

    python benchmarks/targeted_5pct_check.py --seeds 42 71
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

from paired_delta import VERSIONS  # noqa: E402

TARGETS = {
    "TwoTitsForTat": (axl.TwoTitsForTat, 2.20),
    "Gradual": (axl.Gradual, 2.00),
    "HardProber": (axl.HardProber, None),
    "Calculator": (axl.Calculator, None),
    "Random": (axl.Random, None),
}
SPIN_THRESHOLDS = {"TwoTitsForTat": 2.20, "Gradual": 2.00}


def build(cls, seed, role):
    from axelrod import _module_random as mr
    mr.seed(seed * 2 + role)
    return cls()


def spt_paired(zr_cls, opp_cls, turns, seed, noise):
    m = axl.Match((build(zr_cls, seed, 0), build(opp_cls, seed, 1)),
                  turns=turns, seed=seed, noise=noise)
    m.play()
    sc = m.scores()
    return sum(s[0] for s in sc) / turns


def spt_zdb(zr_cls, opp_cls, turns, seed, noise):
    p1 = zr_cls()
    p1.set_seed(seed)
    m = axl.Match((p1, opp_cls()), turns=turns, noise=noise, seed=seed)
    m.play()
    return m.final_score_per_turn()[0]


def wilcoxon(xs, ys):
    try:
        from scipy.stats import wilcoxon
        st = wilcoxon(xs, ys)
        return float(st.pvalue)
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--noise", type=float, default=0.05)
    ap.add_argument("--turns", type=int, default=200)
    ap.add_argument("--seed0", type=int, default=42)
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--variants", nargs="+", default=["v5.4.1", "v5.4.2"])
    args = ap.parse_args()
    seeds = list(range(args.seed0, args.seed0 + args.seeds))

    report = {"config": vars(args), "results": {}}
    t0 = time.time()
    for variant in args.variants:
        B = VERSIONS[variant]
        for opp_name, (opp_cls, _) in TARGETS.items():
            for conv, fn in (("paired", spt_paired), ("zdb", spt_zdb)):
                a_vals, b_vals = [], []
                for s in seeds:
                    a_vals.append(fn(VERSIONS["v5.3"], opp_cls,
                                     args.turns, s, args.noise))
                    b_vals.append(fn(B, opp_cls, args.turns, s, args.noise))
                mean = lambda v: sum(v) / len(v)
                thr = SPIN_THRESHOLDS.get(opp_name)
                rec = {
                    "v53_mean": round(float(mean(a_vals)), 4),
                    f"{variant}_mean": round(float(mean(b_vals)), 4),
                    "delta": round(float(mean(b_vals) - mean(a_vals)), 4),
                    "v53_spin_rate": (round(sum(v <= thr for v in a_vals) / len(a_vals), 3)
                                      if thr else None),
                    f"{variant}_spin_rate": (round(sum(v <= thr for v in b_vals) / len(b_vals), 3)
                                             if thr else None),
                    "wilcoxon_p": (float(p) if (p := wilcoxon(b_vals, a_vals)) is not None
                                   and p == p else None),
                    "seeds_negative_delta": int(sum(b - a < 0 for a, b in zip(a_vals, b_vals))),
                }
                report["results"][f"{variant}|{opp_name}|{conv}"] = rec
                p = rec["wilcoxon_p"]
                print(f"{variant:7s} {opp_name:15s} {conv:7s} "
                      f"v53={rec['v53_mean']:.4f} {variant}={rec[f'{variant}_mean']:.4f} "
                      f"d={rec['delta']:+.4f} p={p if p is None else round(p, 5)} "
                      f"neg={rec['seeds_negative_delta']}/{len(seeds)}", flush=True)

    d = ROOT / "benchmarks" / "results"
    stamp = time.strftime("%Y%m%d_%H%M%S")
    report["elapsed_sec"] = round(time.time() - t0, 1)
    (d / f"targeted5pct_{stamp}.json").write_text(json.dumps(report, indent=1),
                                                  encoding="utf-8")
    print(f"saved targeted5pct_{stamp}.json, elapsed {report['elapsed_sec']}s")


if __name__ == "__main__":
    main()
