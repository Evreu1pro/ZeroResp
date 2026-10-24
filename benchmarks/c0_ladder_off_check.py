"""C0: bit-exact check that Features(noise_ladder=False) equals the reference.

Test A: zeroresp.ZeroResp(features=Features(noise_ladder=False))
Test B: zeroresp_noladder_ref.ZeroResp()  (all ladder gates hard-coded to False)

Compares the full per-turn action history of both players on every match:
30 seeds x 221 opponents x 200 turns, 10% iid action noise.
Zero mismatches required. Any mismatch is recorded with its position.

Usage:
    python benchmarks/c0_ladder_off_check.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "benchmarks"))

import axelrod as axl  # noqa: E402
from run_field import build_pack  # noqa: E402
import zeroresp as zr  # noqa: E402
import zeroresp_noladder_ref as ref  # noqa: E402

TURNS = 200
NOISE = 0.10
SEEDS = list(range(42, 72))  # 30 seeds
PACK = "full"


def build(cls, seed, role, **kw):
    """Construct a player with its initial RNG state fixed by (seed, role).

    See seed_breakdown.build: construction order must not change the result.
    """
    from axelrod import _module_random as mr
    mr.seed(seed * 2 + role)
    return cls(**kw)


def play(player, opp_cls, seed):
    opp = build(opp_cls, seed, role=1)
    m = axl.Match((player, opp), turns=TURNS, seed=seed, noise=NOISE)
    m.play()
    # full per-turn realised actions, as strings, for both players
    return [(str(a), str(b)) for a, b in m.result]


def main():
    pack = build_pack(PACK)
    assert len(pack) == 221, f"expected 221 opponents, got {len(pack)}"
    total = mismatches = 0
    first_bad = []
    t0 = time.time()
    for seed in SEEDS:
        for opp in pack:
            a = play(build(zr.ZeroResp, seed, role=0,
                           features=zr.Features(noise_ladder=False)), opp, seed)
            b = play(build(ref.ZeroResp, seed, role=0), opp, seed)
            total += 1
            if a != b:
                mismatches += 1
                if len(first_bad) < 20:
                    pos = next(i for i, (x, y) in enumerate(zip(a, b)) if x != y)
                    first_bad.append({"seed": seed, "opp": opp.__name__, "turn": pos})
    result = {
        "check": "C0",
        "matches": total,
        "expected_matches": len(SEEDS) * 221,
        "mismatches": mismatches,
        "first_mismatches": first_bad,
        "passed": mismatches == 0 and total == len(SEEDS) * 221,
        "elapsed_sec": round(time.time() - t0, 1),
    }
    out = ROOT / "benchmarks" / "results"
    out.mkdir(parents=True, exist_ok=True)
    (out / "C0_ladder_off_check.json").write_text(json.dumps(result, indent=2),
                                                  encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
