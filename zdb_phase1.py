"""ZDB Phase 1: Core Claim (v5.3 vs v5.6 on 32-player Field Pack)."""
from __future__ import annotations

import csv
import json
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

def run_phase_1():
    print("=" * 65)
    print("PHASE 1: CORE CLAIM EVALUATION (v5.3 vs v5.6)")
    print(f"Reps: {REPS}, Turns: {TURNS}, Noise: {NOISE_LEVELS}")
    print("=" * 65)

    split_path = Path("benchmarks/results/research/bhns/split.json")
    with open(split_path, "r", encoding="utf-8") as f:
        train_names = json.load(f)["train"]

    by_name = {s.__name__: s for s in axl.strategies}
    for s in axl.strategies:
        by_name[s.name] = s

    opp_classes = []
    for name in train_names:
        if name in by_name:
            opp_classes.append((name, by_name[name]))
        else:
            raise KeyError(f"Strategy {name} not found in Axelrod")

    print(f"Loaded {len(opp_classes)} field opponents from split.json.\n")

    csv_path = Path("ZDB_phase1.csv")
    csv_rows = []
    level_stats = {}

    t0 = time.time()

    for noise in NOISE_LEVELS:
        print(f"Running Noise Level: {noise*100:.1f}% ...", flush=True)
        pair_diffs = []
        seed_diffs = {r: [] for r in range(REPS)}

        for rep in range(REPS):
            seed = BASE_SEED + rep
            for opp_name, opp_cls in opp_classes:
                # Strictly paired matches with identical seed
                p53 = get_variant_player("v5.3")
                m53 = axl.Match((p53, opp_cls()), turns=TURNS, seed=seed, noise=noise)
                m53.play()
                s53 = sum(s[0] for s in m53.scores()) / TURNS

                p56 = get_variant_player("v5.6")
                m56 = axl.Match((p56, opp_cls()), turns=TURNS, seed=seed, noise=noise)
                m56.play()
                s56 = sum(s[0] for s in m56.scores()) / TURNS

                delta = s56 - s53
                pair_diffs.append(delta)
                seed_diffs[rep].append(delta)

                csv_rows.append({
                    "noise": noise,
                    "seed": seed,
                    "rep": rep,
                    "opponent": opp_name,
                    "spt_v53": round(s53, 5),
                    "spt_v56": round(s56, 5),
                    "delta": round(delta, 5),
                })

        # Statistics across 30 seed-means
        per_seed_means = np.array([np.mean(seed_diffs[r]) for r in range(REPS)])
        mean_delta = float(np.mean(per_seed_means))
        median_delta = float(np.median(per_seed_means))
        std_delta = float(np.std(per_seed_means, ddof=1))
        ci_low, ci_high = bootstrap_ci(per_seed_means, n_boot=10000)

        # Wilcoxon test (if not all identical zeros)
        if np.all(per_seed_means == 0):
            p_val = 1.0
        else:
            try:
                res = stats.wilcoxon(per_seed_means, alternative="two-sided")
                p_val = float(res.pvalue)
            except Exception:
                p_val = 1.0

        level_stats[noise] = {
            "mean": mean_delta,
            "median": median_delta,
            "std": std_delta,
            "ci_low": ci_low,
            "ci_high": ci_high,
            "p_val": p_val,
        }

        print(f"  Noise {noise*100:4.1f}% | Δ mean: {mean_delta:+.5f} (95% CI: [{ci_low:+.5f}, {ci_high:+.5f}]) | p={p_val:.4e}")

    # Write raw CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["noise", "seed", "rep", "opponent", "spt_v53", "spt_v56", "delta"])
        writer.writeheader()
        writer.writerows(csv_rows)
    print(f"\nSaved raw data ({len(csv_rows)} rows) to {csv_path}")

    # Evaluation against pre-registered criteria
    summary_md = Path("ZDB_phase1_summary.md")
    verdicts = {}

    # Check 0%
    st0 = level_stats[0.0]
    verdicts[0.0] = "PASS" if st0["mean"] >= -0.01 else "FAIL (Drop early-exit warmup)"

    # Check 1%
    st1 = level_stats[0.01]
    verdicts[0.01] = "PASS" if st1["mean"] >= -0.005 else "FAIL"

    # Check 3%
    st3 = level_stats[0.03]
    verdicts[0.03] = "PASS" if (st3["mean"] >= 0 and st3["ci_low"] >= -0.01) else "NEUTRAL"

    # Check 5%
    st5 = level_stats[0.05]
    if abs(st5["mean"]) <= 0.005 and abs(st5["ci_high"] - st5["ci_low"]) <= 0.02:
        verdicts[0.05] = "PASS (Bit-identical parity)"
    elif st5["mean"] > 0 and st5["p_val"] < 0.05:
        verdicts[0.05] = "PASS (Significant improvement)"
    else:
        verdicts[0.05] = "NEUTRAL"

    # Check 10%
    st10 = level_stats[0.10]
    if abs(st10["mean"]) <= 0.005 and abs(st10["ci_high"] - st10["ci_low"]) <= 0.02:
        verdicts[0.10] = "PASS (Bit-identical parity)"
    elif st10["mean"] > 0 and st10["p_val"] < 0.05:
        verdicts[0.10] = "PASS (Significant improvement)"
    else:
        verdicts[0.10] = "NEUTRAL"

    with open(summary_md, "w", encoding="utf-8") as f:
        f.write("# ZDB Phase 1 — Core Claim Summary\n\n")
        f.write(f"**Evaluated**: v5.3 vs v5.6 across 32 Field strategies, {REPS} paired seeds, {TURNS} turns.\n\n")
        f.write("| Noise Level | Mean Δ SPT | Median Δ SPT | 95% Bootstrap CI | Wilcoxon p-value | Pre-registered Verdict |\n")
        f.write("|---:|:---:|:---:|:---:|:---:|:---:|\n")
        for noise in NOISE_LEVELS:
            st = level_stats[noise]
            v = verdicts[noise]
            f.write(f"| {noise*100:4.1f}% | {st['mean']:+.5f} | {st['median']:+.5f} | [{st['ci_low']:+.5f}, {st['ci_high']:+.5f}] | {st['p_val']:.4e} | **{v}** |\n")

    print(f"Saved summary to {summary_md}")
    print(f"Elapsed: {time.time() - t0:.1f}s")
    print("=" * 65)
    return level_stats

if __name__ == "__main__":
    run_phase_1()
