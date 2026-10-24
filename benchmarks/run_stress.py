"""Stress test: ZeroResp position map across noise regimes vs whole library.

For each noise level and each ladder state runs a full round-robin against
every short-run-time strategy in the library and records the complete
ranking. Output: results/research/stress/*.json

    python benchmarks/run_stress.py            # all regimes, both versions
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import axelrod as axl  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from zeroresp import Features, ZeroResp  # noqa: E402

NOISES = [0.0, 0.01, 0.03, 0.05, 0.1]
TURNS = 200
SEED = 42
OUT = ROOT / "benchmarks" / "results" / "research" / "stress"


def full_pack():
    return [s for s in axl.short_run_time_strategies
            if not getattr(s, "classifier", {}).get("long_run_time")]


def run_regime(noise: float, ladder: bool) -> dict:
    zr_factory = (lambda: ZeroResp(features=Features(noise_ladder=ladder)))
    players = [zr_factory()] + [cls() for cls in full_pack()]
    t = axl.Tournament(players, turns=TURNS, repetitions=1, seed=SEED, noise=noise)
    results = t.play(progress_bar=False)
    zr_idx = next(i for i, p in enumerate(players) if isinstance(p, ZeroResp))

    per_spt = {}
    for i in range(len(players)):
        sc = results.scores[i]
        per_spt[i] = sum(sc) / len(sc) / TURNS

    rows = []
    for pos, idx in enumerate(results.ranking, start=1):
        rows.append({
            "pos": pos,
            "name": results.ranked_names[pos - 1],
            "spt": round(per_spt[idx], 4),
            "is_zr": idx == zr_idx,
        })
    zr_row = next(r for r in rows if r["is_zr"])
    return {
        "noise": noise,
        "ladder": ladder,
        "turns": TURNS,
        "seed": SEED,
        "players": len(players),
        "zr_rank": zr_row["pos"],
        "zr_spt": zr_row["spt"],
        "rows": rows,
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for noise in NOISES:
        for ladder in (True, False):
            tag = f"noise{int(noise*100):02d}_{'lad' if ladder else 'nolad'}"
            out_file = OUT / f"{tag}.json"
            if out_file.exists():
                print(f"skip {tag} (exists)")
                continue
            print(f"running {tag} ...", flush=True)
            res = run_regime(noise, ladder)
            out_file.write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
            print(f"  done: rank {res['zr_rank']}/{res['players']}, spt {res['zr_spt']:.4f}", flush=True)


if __name__ == "__main__":
    main()
