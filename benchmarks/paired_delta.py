"""Paired SPT difference between two ZeroResp variants over the same matches.

For each opponent and each seed, plays variant A and variant B against the
same opponent with the same seed and noise. Reports per-seed mean SPT over the
pack for each variant, the paired difference, Wilcoxon signed-rank p-value and
a bootstrap 95% CI.

Usage:
    python benchmarks/paired_delta.py --a v5.3 --b v5.5 --noise 0.1 --seeds 30
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "benchmarks"))

import axelrod as axl  # noqa: E402
from run_field import build_pack  # noqa: E402
import zeroresp as _zr53  # noqa: E402
import zeroresp_v54 as _zr54  # noqa: E402
import zeroresp_v541 as _zr541  # noqa: E402
import zeroresp_v542 as _zr542  # noqa: E402
import zeroresp_v543 as _zr543  # noqa: E402
import zeroresp_v544 as _zr544  # noqa: E402
import zeroresp_v55 as _zr55  # noqa: E402
import zeroresp_v56 as _zr56  # noqa: E402

# Canonical version definitions follow zdb_phase0.get_variant_player: the
# prototype modules keep their new features OFF by default, so the bare
# ZeroResp class is NOT the version — the module factory is. v5.3 has no
# factory (plain class = released v5.3).
VERSIONS = {
    "v5.3": _zr53.ZeroResp,
    "v5.4": _zr54.ZeroRespV54Full,
    "v5.4.1": _zr541.ZeroRespV541,
    "v5.4.2": _zr542.ZeroRespV542,
    "v5.4.3": _zr543.ZeroRespV543,
    "v5.4.4": _zr544.ZeroRespV544,
    "v5.5": _zr55.ZeroRespV55Full,
    "v5.6": _zr56.ZeroRespV56Full,
}


def mean_spt_over_pack(zr_cls, pack, turns, seed, noise):
    """Mean SPT per turn of zr_cls against every opponent in pack, one seed."""
    vals = []
    for opp_cls in pack:
        # Seed the module RNG before each construction so the initial state
        # (ZeroResp warmth) depends only on (seed, role), not construction order.
        from axelrod import _module_random as _mr
        _mr.seed(seed * 2)
        zp = zr_cls()
        _mr.seed(seed * 2 + 1)
        op = opp_cls()
        match = axl.Match((zp, op), turns=turns, seed=seed,
                          noise=noise)
        match.play()
        scores = match.scores()
        vals.append(sum(s[0] for s in scores) / turns)
    return sum(vals) / len(vals)


def wilcoxon_p(diffs):
    """Two-sided Wilcoxon signed-rank p-value (normal approximation)."""
    try:
        from scipy.stats import wilcoxon
        return float(wilcoxon(diffs).pvalue)
    except Exception:
        return None


def bootstrap_ci(diffs, n=5000, alpha=0.05, rng_seed=0):
    rng = random.Random(rng_seed)
    k = len(diffs)
    means = sorted(sum(rng.choice(diffs) for _ in range(k)) / k for _ in range(n))
    return means[int(alpha / 2 * n)], means[int((1 - alpha / 2) * n) - 1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", default="v5.3", help="base variant")
    ap.add_argument("--b", default="v5.5", help="comparison variant")
    ap.add_argument("--pack", default="full")
    ap.add_argument("--turns", type=int, default=200)
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--seed0", type=int, default=42)
    ap.add_argument("--noise", type=float, default=0.1)
    args = ap.parse_args()

    for v in (args.a, args.b):
        if v not in VERSIONS:
            raise ValueError(f"unknown version {v}; choose from {list(VERSIONS)}")
    if VERSIONS[args.a] is VERSIONS[args.b]:
        raise ValueError("A and B resolve to the same class")

    pack = build_pack(args.pack)
    seeds = [args.seed0 + i for i in range(args.seeds)]
    diffs, a_vals, b_vals = [], [], []
    t0 = time.time()
    for s in seeds:
        a = mean_spt_over_pack(VERSIONS[args.a], pack, args.turns, s, args.noise)
        b = mean_spt_over_pack(VERSIONS[args.b], pack, args.turns, s, args.noise)
        a_vals.append(a)
        b_vals.append(b)
        diffs.append(b - a)
        print(f"seed {s}: {args.a}={a:.4f} {args.b}={b:.4f} d={b - a:+.4f}", flush=True)

    mean_d = sum(diffs) / len(diffs)
    p = wilcoxon_p(diffs)
    lo, hi = bootstrap_ci(diffs)
    result = {
        "config": vars(args),
        "pack_size": len(pack),
        "seeds": seeds,
        "mean_a": round(sum(a_vals) / len(a_vals), 4),
        "mean_b": round(sum(b_vals) / len(b_vals), 4),
        "delta_b_minus_a": round(mean_d, 5),
        "ci95": [round(lo, 5), round(hi, 5)],
        "wilcoxon_p": p,
        "elapsed_sec": round(time.time() - t0, 1),
    }
    d = ROOT / "benchmarks" / "results"
    d.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    (d / f"paired_{args.a}_vs_{args.b}_{stamp}.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
