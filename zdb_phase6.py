"""ZDB Phase 6: Statistical Analysis & Multiple Testing Corrections."""
from __future__ import annotations

import csv
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
from scipy import stats

BASE_SEED = 42

def bootstrap_ci(arr: np.ndarray, n_boot: int = 10000, alpha: float = 0.05):
    means = np.empty(n_boot)
    n = len(arr)
    rng = np.random.default_rng(BASE_SEED)
    for i in range(n_boot):
        sample = rng.choice(arr, size=n, replace=True)
        means[i] = np.mean(sample)
    low = np.percentile(means, 100 * (alpha / 2))
    high = np.percentile(means, 100 * (1 - alpha / 2))
    return float(low), float(high)

def cliffs_delta(x: np.ndarray) -> float:
    pos = np.sum(x > 0)
    neg = np.sum(x < 0)
    return float((pos - neg) / len(x))

def holm_bonferroni(p_vals: list[float]) -> list[float]:
    m = len(p_vals)
    sorted_indices = np.argsort(p_vals)
    adj_p = np.empty(m)
    current_max = 0.0
    for rank, idx in enumerate(sorted_indices):
        p = p_vals[idx]
        adj = p * (m - rank)
        adj = min(1.0, max(current_max, adj))
        current_max = adj
        adj_p[idx] = adj
    return list(adj_p)

def benjamini_hochberg(p_vals: list[float]) -> list[float]:
    m = len(p_vals)
    sorted_indices = np.argsort(p_vals)
    adj_p = np.empty(m)
    for rank, idx in enumerate(sorted_indices):
        p = p_vals[idx]
        adj = p * m / (rank + 1)
        adj_p[idx] = min(1.0, adj)
    # enforce monotonicity backwards
    for i in range(m - 2, -1, -1):
        idx_curr = sorted_indices[i]
        idx_next = sorted_indices[i + 1]
        adj_p[idx_curr] = min(adj_p[idx_curr], adj_p[idx_next])
    return list(adj_p)

def run_phase_6():
    print("=" * 65)
    print("PHASE 6: STATISTICAL ANALYSIS & CORRECTIONS")
    print("=" * 65)

    # 1. Read Phase 1 raw data
    p1_rows = []
    with open("ZDB_phase1.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            p1_rows.append(r)

    # Group by noise level -> list of 30 seed-mean deltas
    p1_by_noise = {}
    for r in p1_rows:
        noise = float(r["noise"])
        seed = int(r["seed"])
        delta = float(r["delta"])
        p1_by_noise.setdefault(noise, {}).setdefault(seed, []).append(delta)

    family_tests = []

    for noise in sorted(p1_by_noise.keys()):
        seed_means = np.array([np.mean(p1_by_noise[noise][s]) for s in sorted(p1_by_noise[noise].keys())])
        mean_d = float(np.mean(seed_means))
        median_d = float(np.median(seed_means))
        ci_low, ci_high = bootstrap_ci(seed_means)
        cd = cliffs_delta(seed_means)
        try:
            p_val = float(stats.wilcoxon(seed_means, alternative="two-sided").pvalue)
        except Exception:
            p_val = 1.0

        family_tests.append({
            "test_name": f"Field Pack Noise {noise*100:4.1f}%",
            "noise": noise,
            "mean": mean_d,
            "median": median_d,
            "ci_low": ci_low,
            "ci_high": ci_high,
            "cliffs_delta": cd,
            "raw_p": p_val,
        })

    # 2. Add Phase 3 Targeted tests (at 5% noise)
    p3_rows = []
    with open("ZDB_phase3.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            p3_rows.append(r)

    p3_by_opp = {}
    for r in p3_rows:
        if float(r["noise"]) == 0.05:
            opp = r["opponent"]
            delta = float(r["delta"])
            p3_by_opp.setdefault(opp, []).append(delta)

    for opp in sorted(p3_by_opp.keys()):
        deltas = np.array(p3_by_opp[opp])
        mean_d = float(np.mean(deltas))
        median_d = float(np.median(deltas))
        ci_low, ci_high = bootstrap_ci(deltas)
        cd = cliffs_delta(deltas)
        try:
            p_val = float(stats.wilcoxon(deltas, alternative="two-sided").pvalue)
        except Exception:
            p_val = 1.0

        family_tests.append({
            "test_name": f"Targeted: {opp} (5% noise)",
            "noise": 0.05,
            "mean": mean_d,
            "median": median_d,
            "ci_low": ci_low,
            "ci_high": ci_high,
            "cliffs_delta": cd,
            "raw_p": p_val,
        })

    # Multiple Testing Corrections across entire family of 15 tests
    raw_ps = [t["raw_p"] for t in family_tests]
    holm_ps = holm_bonferroni(raw_ps)
    bh_ps = benjamini_hochberg(raw_ps)

    for i, t in enumerate(family_tests):
        t["holm_p"] = holm_ps[i]
        t["bh_p"] = bh_ps[i]
        t["survives_holm"] = holm_ps[i] < 0.05
        t["survives_bh"] = bh_ps[i] < 0.05

    # Generate ZDB_phase6_stats.md
    out_md = Path("ZDB_phase6_stats.md")
    lines = []
    lines.append("# ZDB Phase 6 — Formal Statistics & Multiple Testing Corrections\n\n")
    lines.append(f"Family size: **{len(family_tests)} tests** (5 Field Pack levels + 10 Targeted Opponents at 5% noise).\n\n")
    lines.append("| Hypothesis / Test | Mean Δ SPT | 95% Bootstrap CI | Cliff's δ | Raw p-val | Holm-Bonferroni p | BH-FDR p | Survives Holm? |\n")
    lines.append("|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n")

    for t in family_tests:
        h_verdict = "**YES (p<0.05)**" if t["survives_holm"] else "No"
        lines.append(
            f"| {t['test_name']} | {t['mean']:+.4f} | [{t['ci_low']:+.4f}, {t['ci_high']:+.4f}] | "
            f"{t['cliffs_delta']:+.2f} | {t['raw_p']:.4e} | {t['holm_p']:.4e} | {t['bh_p']:.4e} | {h_verdict} |\n"
        )

    with open(out_md, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"Saved formal statistics to {out_md}\n")
    for t in family_tests:
        print(f"{t['test_name']:<35} | Δ = {t['mean']:+.4f} | Cliff δ = {t['cliffs_delta']:+.2f} | Holm p = {t['holm_p']:.4e} | Survives: {t['survives_holm']}")

    return family_tests

if __name__ == "__main__":
    run_phase_6()
