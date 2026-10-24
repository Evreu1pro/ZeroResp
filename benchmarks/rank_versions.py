"""Rank every ZeroResp variant on the same round-robin protocol.

Usage:
    python benchmarks/rank_versions.py --noise 0.1 --turns 200 --reps 2 --seed 42

Writes benchmarks/results/versions_<stamp>.json and .md.
Variants: v5.3 (zeroresp.py), v5.4, v5.4.1, v5.4.2, v5.5, v5.6.
Protocol matches run_field.run_round_robin, but the player is swapped per variant.
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

import zeroresp as _zr53  # noqa: E402
import zeroresp_v54 as _zr54  # noqa: E402
import zeroresp_v541 as _zr541  # noqa: E402
import zeroresp_v542 as _zr542  # noqa: E402
import zeroresp_v55 as _zr55  # noqa: E402
import zeroresp_v56 as _zr56  # noqa: E402

# Explicit map: version label -> player factory from its own module. The
# prototype modules keep their new features OFF by default, so the version is
# the module factory (zdb_phase0 convention), not the bare class.
VERSIONS = {
    "v5.3": _zr53.ZeroResp,
    "v5.4": _zr54.ZeroRespV54Full,
    "v5.4.1": _zr541.ZeroRespV541,
    "v5.4.2": _zr542.ZeroRespV542,
    "v5.5": _zr55.ZeroRespV55Full,
    "v5.6": _zr56.ZeroRespV56Full,
}

_classes = list(VERSIONS.values())
assert len({id(c) for c in _classes}) == len(_classes), "variant classes must be distinct"


def rank_one(zr_cls, pack, turns, reps, seed, noise):
    players = [zr_cls()] + [cls() for cls in pack]
    t = axl.Tournament(players, turns=turns, repetitions=reps, seed=seed,
                       noise=noise)
    res = t.play(progress_bar=False)
    zr_idx = 0
    totals = res.scores[zr_idx]
    return {
        "rank": res.ranking.index(zr_idx) + 1,
        "of": len(players),
        # Score per turn per match: total over all matches / (matches * turns).
        "spt": round(sum(totals) / len(totals) / ((len(players) - 1) * turns), 4),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pack", default="full")
    ap.add_argument("--turns", type=int, default=200)
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--noise", type=float, default=0.1)
    ap.add_argument("--only", nargs="*", default=None)
    args = ap.parse_args()

    pack = build_pack(args.pack)
    out = {"config": vars(args), "pack_size": len(pack), "variants": {}}
    t0 = time.time()
    if args.only:
        unknown = [v for v in args.only if v not in VERSIONS]
        if unknown:
            raise ValueError(f"unknown version(s) {unknown}; choose from {list(VERSIONS)}")
    for label, cls in VERSIONS.items():
        if args.only and label not in args.only:
            continue
        out["variants"][label] = rank_one(cls, pack, args.turns,
                                          args.reps, args.seed, args.noise)
        print(label, out["variants"][label], flush=True)
    out["elapsed_sec"] = round(time.time() - t0, 1)

    d = ROOT / "benchmarks" / "results"
    d.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    (d / f"versions_{stamp}.json").write_text(json.dumps(out, indent=2),
                                              encoding="utf-8")
    lines = [f"# Version ranks, noise={args.noise}, turns={args.turns}, "
             f"reps={args.reps}, pack={args.pack} ({len(pack)})", "",
             "| Variant | Rank | of | SPT/turn |", "|---|---|---|---|"]
    for label, r in out["variants"].items():
        lines.append(f"| {label} | {r['rank']} | {r['of']} | {r['spt']} |")
    (d / f"versions_{stamp}.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"elapsed {out['elapsed_sec']}s")


if __name__ == "__main__":
    main()
