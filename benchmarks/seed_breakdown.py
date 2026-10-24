"""Per-opponent breakdown of v5.3 vs another variant for chosen seeds.

For each seed and each opponent, plays both variants on identical match
settings and records the SPT difference. Reports how many opponents give
identical outcomes (feature not activated) and the largest differences.

Usage:
    python benchmarks/seed_breakdown.py --b v5.5 --seeds 43 61 71 --noise 0.1
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "benchmarks"))

import axelrod as axl  # noqa: E402
from run_field import build_pack  # noqa: E402
from paired_delta import VERSIONS  # noqa: E402


def build(cls, seed, role, **kw):
    """Construct a player with its initial RNG state fixed by (seed, role).

    Player.__init__ (and ZeroResp.__init__ via warmth) draws from the module
    generator when no seed is given. Seeding it right before construction makes
    the initial state depend only on (seed, role), not on construction order.
    """
    from axelrod import _module_random as mr
    mr.seed(seed * 2 + role)
    return cls(**kw)


def match_spt(zr_cls, opp_cls, turns, seed, noise):
    m = axl.Match((build(zr_cls, seed, role=0), build(opp_cls, seed, role=1)),
                  turns=turns, seed=seed, noise=noise)
    m.play()
    sc = m.scores()
    return sum(s[0] for s in sc) / turns, [tuple(map(str, s)) for s in m.result]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", default="v5.3")
    ap.add_argument("--b", default="v5.5")
    ap.add_argument("--seeds", nargs="+", type=int, required=True)
    ap.add_argument("--pack", default="full")
    ap.add_argument("--turns", type=int, default=200)
    ap.add_argument("--noise", type=float, default=0.1)
    args = ap.parse_args()

    pack = build_pack(args.pack)
    A, B = VERSIONS[args.a], VERSIONS[args.b]
    report = {"config": vars(args), "seeds": {}}
    t0 = time.time()
    for s in args.seeds:
        rows = []
        for opp in pack:
            a_spt, a_hist = match_spt(A, opp, args.turns, s, args.noise)
            b_spt, b_hist = match_spt(B, opp, args.turns, s, args.noise)
            rows.append({
                "opp": opp.__name__,
                "d": round(b_spt - a_spt, 5),
                "identical_history": a_hist == b_hist,
            })
        ident = sum(r["identical_history"] for r in rows)
        rows_sorted = sorted(rows, key=lambda r: r["d"])
        report["seeds"][s] = {
            "identical_history_count": ident,
            "opponents": len(rows),
            "mean_d": round(sum(r["d"] for r in rows) / len(rows), 5),
            "worst5": rows_sorted[:5],
            "best5": rows_sorted[-5:],
        }
        print(f"seed {s}: identical={ident}/{len(rows)} mean_d="
              f"{report['seeds'][s]['mean_d']}", flush=True)
        for r in rows_sorted[:5] + rows_sorted[-5:]:
            print(f"   {r['opp']:<28} d={r['d']:+.4f} identical={r['identical_history']}")

    report["elapsed_sec"] = round(time.time() - t0, 1)
    d = ROOT / "benchmarks" / "results"
    d.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    (d / f"seedbreak_{args.a}_vs_{args.b}_{stamp}.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    print("saved breakdown json")


if __name__ == "__main__":
    main()

