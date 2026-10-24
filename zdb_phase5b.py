"""ZDB Phase 5b: Per-Seed Delta Distribution & Variance Diagnosis."""
from __future__ import annotations

import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import axelrod as axl
import numpy as np

from zdb_phase0 import get_variant_player

TURNS = 200
REPS = 30
BASE_SEED = 42

def run_phase_5b():
    print("=" * 65)
    print("PHASE 5b: PER-SEED DISTRIBUTION ON KEY RECIPROCATORS")
    print(f"Noise: 5%, Reps: {REPS}, Turns: {TURNS}")
    print("=" * 65)

    by_name = {s.__name__: s for s in axl.strategies}
    for s in axl.strategies:
        by_name[s.name] = s

    opponents = ["TwoTitsForTat", "Gradual", "Calculator", "HardProber"]
    seed_deltas = {opp: [] for opp in opponents}

    t0 = time.time()
    for rep in range(REPS):
        seed = BASE_SEED + rep
        for opp in opponents:
            opp_cls = by_name[opp]
            p53 = get_variant_player("v5.3")
            m53 = axl.Match((p53, opp_cls()), turns=TURNS, seed=seed, noise=0.05)
            m53.play()
            s53 = sum(x[0] for x in m53.scores()) / TURNS

            p56 = get_variant_player("v5.6")
            m56 = axl.Match((p56, opp_cls()), turns=TURNS, seed=seed, noise=0.05)
            m56.play()
            s56 = sum(x[0] for x in m56.scores()) / TURNS

            d = s56 - s53
            seed_deltas[opp].append((seed, d, s53, s56))

    out_md = Path("ZDB_phase5b_distribution.md")
    lines = []
    lines.append("# ZDB Phase 5b — Per-Seed Delta Distribution Report\n\n")

    for opp in opponents:
        arr = np.array([x[1] for x in seed_deltas[opp]])
        lines.append(f"## {opp} (Mean Δ = {np.mean(arr):+.4f}, Median = {np.median(arr):+.4f}, Std = {np.std(arr):.4f})\n\n")

        # Binned histogram text
        # Bins: < 0, 0 to 0.1, 0.1 to 0.3, > 0.3
        b_neg = np.sum(arr < 0.0)
        b_zero = np.sum((arr >= 0.0) & (arr < 0.10))
        b_mid = np.sum((arr >= 0.10) & (arr < 0.30))
        b_high = np.sum(arr >= 0.30)

        lines.append("### Distribution Bins:\n")
        lines.append(f"- **Δ < 0.00** (Regressions): {b_neg} seeds ({b_neg/REPS*100:.1f}%)\n")
        lines.append(f"- **0.00 ≤ Δ < 0.10** (Near Zero / Neutral): {b_zero} seeds ({b_zero/REPS*100:.1f}%)\n")
        lines.append(f"- **0.10 ≤ Δ < 0.30** (Moderate Gains): {b_mid} seeds ({b_mid/REPS*100:.1f}%)\n")
        lines.append(f"- **Δ ≥ 0.30** (High Impact): {b_high} seeds ({b_high/REPS*100:.1f}%)\n\n")

        lines.append("### Seed-by-Seed Listing:\n")
        lines.append("| Seed | v5.3 SPT | v5.6 SPT | Δ SPT |\n")
        lines.append("|:---:|:---:|:---:|:---:|\n")
        for s, d, s53, s56 in seed_deltas[opp]:
            lines.append(f"| {s} | {s53:.4f} | {s56:.4f} | {d:+.4f} |\n")
        lines.append("\n---\n\n")

    with open(out_md, "w", encoding="utf-8") as f:
        f.writelines(lines)

    for opp in opponents:
        arr = np.array([x[1] for x in seed_deltas[opp]])
        b_neg = np.sum(arr < 0.0)
        b_zero = np.sum((arr >= 0.0) & (arr < 0.10))
        b_high = np.sum(arr >= 0.30)
        print(f"{opp:<15} | Mean = {np.mean(arr):+.4f} | <0: {b_neg:2d} | [0, 0.1): {b_zero:2d} | ≥0.3: {b_high:2d}")

    print(f"\nSaved distribution analysis to {out_md} in {time.time() - t0:.1f}s\n")
    return seed_deltas

if __name__ == "__main__":
    run_phase_5b()
