"""T1 under the both-flip channel, per benchmarks/preregistrations/T1_both_flip.md.

Two parts:

  paired  (H2, H3)  ZeroResp vs each of 221 opponents, cheap. H2 compares
                    v5.3 against v5.3 with ladder off (does the ladder do
                    anything under both-flip?). H3 compares v5.5 against v5.3
                    (does the iid regression persist?).

  rank    (H1)      Full round-robin of 222 players to get ZeroResp's rank.
                    Expensive: 24531 matches per seed per noise level.

Usage:
    python benchmarks/run_t1_both_flip.py --part paired --noise 0.10
    python benchmarks/run_t1_both_flip.py --part rank   --noise 0.10 --seeds 30
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
from both_flip import play_both_flip, build  # noqa: E402
import zeroresp as _zr53  # noqa: E402
import zeroresp_v55 as _zr55  # noqa: E402


def ladder_off():
    """v5.3 with the noise ladder switched off (verified equivalent to the
    all-gates-False reference by C0, 0/6630 mismatches)."""
    return _zr53.ZeroResp(features=_zr53.Features(noise_ladder=False))


def spt(result, turn_idx):
    """Total score per turn for player 1 (index 0) from a realised history."""
    game = axl.Game()
    return sum(game.score(pair)[turn_idx] for pair in result) / len(result)


def mean_spt_over_pack(factory, pack, turns, seed, p, role=0):
    """Mean SPT per turn of our player against every opponent, one seed.

    `factory` is a zero-argument callable returning a FRESH player instance.
    Every player is built through both_flip.build so the initial RNG state
    depends only on (seed, role), never on construction order.
    """
    vals = []
    for j, opp in enumerate(pack):
        me = build_factory(factory, seed, role)
        them = build(opp, seed, role=1)
        r = play_both_flip(me, them, turns=turns, p_action=p,
                           p_perception=p, seed=seed * 100003 + j)
        vals.append(spt(r, 0))
    return sum(vals) / len(vals)


def build_factory(factory, seed, role):
    """Seed the module generator, then let the factory build the instance."""
    from axelrod import _module_random as mr
    mr.seed(seed * 2 + role)
    return factory()


def run_paired(pack, turns, seeds, p):
    a_vals, b_vals, c_vals = [], [], []
    for s in seeds:
        a = mean_spt_over_pack(lambda: _zr53.ZeroResp(), pack, turns, s, p)
        b = mean_spt_over_pack(ladder_off, pack, turns, s, p)
        c = mean_spt_over_pack(lambda: _zr55.ZeroResp(), pack, turns, s, p)
        a_vals.append(a)
        b_vals.append(b)
        c_vals.append(c)
        print(f"seed {s}: v5.3={a:.4f} ladder_off={b:.4f} v5.5={c:.4f}", flush=True)
    d2 = [b - a for a, b in zip(a_vals, b_vals)]
    d3 = [c - a for a, c in zip(a_vals, c_vals)]
    return {
        "part": "paired", "noise": p, "seeds": list(seeds),
        "mean_v53": round(sum(a_vals) / len(a_vals), 4),
        "mean_ladder_off": round(sum(b_vals) / len(b_vals), 4),
        "mean_v55": round(sum(c_vals) / len(c_vals), 4),
        "delta_ladder_off_minus_v53": round(sum(d2) / len(d2), 5),
        "delta_v55_minus_v53": round(sum(d3) / len(d3), 5),
    }


def run_rank(pack, turns, seeds, p):
    """Full round-robin under both-flip; rank of v5.3 among 222."""
    ranks, spts = [], []
    for s in seeds:
        n = len(pack) + 1
        totals = [0.0] * n
        for i in range(n):
            for j in range(i + 1, n):
                if i == 0:
                    me = build(_zr53.ZeroResp, s, role=0)
                    them = build(pack[j - 1], s, role=1)
                    r = play_both_flip(me, them, turns=turns, p_action=p,
                                       p_perception=p, seed=s * 100003 + j)
                    totals[0] += spt(r, 0)
                    totals[j] += spt(r, 1)
                else:
                    me = build(pack[i - 1], s, role=0)
                    them = build(pack[j - 1], s, role=1)
                    r = play_both_flip(me, them, turns=turns, p_action=p,
                                       p_perception=p, seed=s * 100003 + j * 7 + i)
                    totals[i] += spt(r, 0)
                    totals[j] += spt(r, 1)
        order = sorted(range(n), key=lambda k: -totals[k])
        ranks.append(order.index(0) + 1)
        spts.append(totals[0] / (n - 1) / turns)
        print(f"seed {s}: rank {ranks[-1]}/{n} spt {spts[-1]:.4f}", flush=True)
    return {
        "part": "rank", "noise": p, "seeds": list(seeds),
        "of": len(pack) + 1,
        "mean_rank": round(sum(ranks) / len(ranks), 3),
        "median_rank": sorted(ranks)[len(ranks) // 2],
        "mean_spt": round(sum(spts) / len(spts), 4),
        "ranks": ranks,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", choices=["paired", "rank"], required=True)
    ap.add_argument("--noise", type=float, default=0.10)
    ap.add_argument("--turns", type=int, default=200)
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--seed0", type=int, default=42)
    args = ap.parse_args()

    pack = build_pack("full")
    seeds = range(args.seed0, args.seed0 + args.seeds)
    t0 = time.time()
    out = run_paired(pack, args.turns, seeds, args.noise) if args.part == "paired" \
        else run_rank(pack, args.turns, seeds, args.noise)
    out["pack_size"] = len(pack)
    out["elapsed_sec"] = round(time.time() - t0, 1)

    d = ROOT / "benchmarks" / "results"
    d.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    (d / f"t1_bothflip_{args.part}_p{args.noise}_{stamp}.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
