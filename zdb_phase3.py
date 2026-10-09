"""ZDB Phase 3: Targeted Deep-Dive (Verification of Claims on 10 Key Opponents)."""
from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import axelrod as axl
import numpy as np
from scipy import stats

from zdb_phase0 import get_variant_player

TURNS = 200
REPS = 30
BASE_SEED = 42
NOISE_LEVELS = [0.0, 0.01, 0.03, 0.05, 0.10]

TARGET_OPPONENTS = [
    "HardProber",
    "TwoTitsForTat",
    "Gradual",
    "Calculator",
    "TrickyCooperator",
    "ZDExtort2",
    "ZDExtort3",
    "ZDExtort2v2",
    "Random",
    "TitForTat",
]

def bootstrap_ci(diffs: np.ndarray, n_boot: int = 10000, alpha: float = 0.05):
    means = np.empty(n_boot)
    n = len(diffs)
    rng = np.random.default_rng(BASE_SEED)
    for i in range(n_boot):
        sample = rng.choice(diffs, size=n, replace=True)
        means[i] = np.mean(sample)
    low = np.percentile(means, 100 * (alpha / 2))
    high = np.percentile(means, 100 * (1 - alpha / 2))
    return float(low), float(high)

def run_phase_3():
    print("=" * 65)
    print("PHASE 3: TARGETED DEEP-DIVE (v5.3 vs v5.6, 10 Opponents)")
    print(f"Reps: {REPS}, Turns: {TURNS}, Noise: {NOISE_LEVELS}")
    print("=" * 65)

    by_name = {s.__name__: s for s in axl.strategies}
    for s in axl.strategies:
        by_name[s.name] = s

    opp_classes = [(n, by_name[n]) for n in TARGET_OPPONENTS]

    csv_path = Path("ZDB_phase3.csv")
    csv_rows = []
    summary_data = {noise: {} for noise in NOISE_LEVELS}

    t0 = time.time()

    for noise in NOISE_LEVELS:
        print(f"Testing Targeted Opponents at Noise {noise*100:.1f}% ...", flush=True)
        for opp_name, opp_cls in opp_classes:
            deltas = []
            s53_list = []
            s56_list = []

            for rep in range(REPS):
                seed = BASE_SEED + rep
                p53 = get_variant_player("v5.3")
                m53 = axl.Match((p53, opp_cls()), turns=TURNS, seed=seed, noise=noise)
                m53.play()
                s53 = sum(s[0] for s in m53.scores()) / TURNS

                p56 = get_variant_player("v5.6")
                m56 = axl.Match((p56, opp_cls()), turns=TURNS, seed=seed, noise=noise)
                m56.play()
                s56 = sum(s[0] for s in m56.scores()) / TURNS

                d = s56 - s53
                deltas.append(d)
                s53_list.append(s53)
                s56_list.append(s56)

                csv_rows.append({
                    "noise": noise,
                    "seed": seed,
                    "rep": rep,
                    "opponent": opp_name,
                    "spt_v53": round(s53, 5),
                    "spt_v56": round(s56, 5),
                    "delta": round(d, 5),
                })

            d_arr = np.array(deltas)
            mean_d = float(np.mean(d_arr))
            ci_low, ci_high = bootstrap_ci(d_arr)
            summary_data[noise][opp_name] = {
                "mean_53": float(np.mean(s53_list)),
                "mean_56": float(np.mean(s56_list)),
                "mean_d": mean_d,
                "ci_low": ci_low,
                "ci_high": ci_high,
            }

    # Write raw CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["noise", "seed", "rep", "opponent", "spt_v53", "spt_v56", "delta"])
        writer.writeheader()
        writer.writerows(csv_rows)

    # Pre-registered criteria evaluation
    out_md = Path("ZDB_phase3_targeted.md")
    lines = []
    lines.append("# ZDB Phase 3 — Targeted Deep-Dive Summary\n\n")
    lines.append("## Results at 5% Noise (Reps=30, Turns=200)\n\n")
    lines.append("| Opponent | v5.3 SPT | v5.6 SPT | Δ SPT | 95% Bootstrap CI | Pre-registered Verdict |\n")
    lines.append("|---|:---:|:---:|:---:|:---:|:---:|\n")

    res_5 = summary_data[0.05]
    for opp_name in TARGET_OPPONENTS:
        st = res_5[opp_name]
        d = st["mean_d"]
        ci_str = f"[{st['ci_low']:+.4f}, {st['ci_high']:+.4f}]"

        # Check pre-registered criteria
        if opp_name == "HardProber":
            v = "CONFIRMED (Δ ≥ +0.2)" if (d >= 0.2 and st["ci_low"] > 0) else "REFUTED (Previous +0.346 was seed noise)"
        elif opp_name == "TwoTitsForTat":
            v = "CONFIRMED (Δ ≥ +0.2)" if d >= 0.2 else "REFUTED (Δ < +0.2)"
        elif opp_name == "TrickyCooperator":
            v = "TOLERABLE (Δ ≥ -0.05)" if d >= -0.05 else "STRUCTURAL REGRESSION (Δ < -0.05)"
        elif opp_name == "ZDExtort2":
            v = "TOLERABLE (Δ ≥ -0.05)" if d >= -0.05 else "STRUCTURAL REGRESSION (Δ < -0.05)"
        else:
            v = f"Δ = {d:+.4f}"

        lines.append(f"| **{opp_name}** | {st['mean_53']:.4f} | {st['mean_56']:.4f} | {d:+.4f} | {ci_str} | **{v}** |\n")

    lines.append("\n## Full Breakdown Across Noise Levels\n\n")
    lines.append("| Opponent | Δ at 0% | Δ at 1% | Δ at 3% | Δ at 5% | Δ at 10% |\n")
    lines.append("|---|:---:|:---:|:---:|:---:|:---:|\n")
    for opp_name in TARGET_OPPONENTS:
        row = f"| **{opp_name}** | " + " | ".join(f"{summary_data[n][opp_name]['mean_d']:+.4f}" for n in NOISE_LEVELS) + " |\n"
        lines.append(row)

    with open(out_md, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print("".join(lines[:18]))
    print(f"Saved Phase 3 report to {out_md} (elapsed {time.time() - t0:.1f}s)\n")
    return summary_data

if __name__ == "__main__":
    run_phase_3()
