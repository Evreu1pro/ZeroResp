"""ZDB Phase 5: Robustness & Invariance Verification."""
from __future__ import annotations

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

BASE_SEED = 42

def run_phase_5():
    print("=" * 65)
    print("PHASE 5: ROBUSTNESS & INVARIANCE")
    print("=" * 65)

    split_path = Path("benchmarks/results/research/bhns/split.json")
    with open(split_path, "r", encoding="utf-8") as f:
        train_names = json.load(f)["train"]

    by_name = {s.__name__: s for s in axl.strategies}
    for s in axl.strategies:
        by_name[s.name] = s

    opp_classes = [(n, by_name[n]) for n in train_names]
    report_lines = []
    report_lines.append("# ZDB Phase 5 — Robustness & Invariance Report\n\n")

    t0 = time.time()

    # --- 5.1 Match Length Sweep ---
    print("5.1 Running Match Length Sweep (50, 100, 200, 1000 turns, noise 5%, 8 reps)...")
    lengths = [50, 100, 200, 1000]
    len_deltas = {}
    for turns in lengths:
        deltas = []
        for rep in range(8):
            seed = BASE_SEED + rep
            for _, opp_cls in opp_classes[:10]: # Top 10 representative opponents
                m53 = axl.Match((get_variant_player("v5.3"), opp_cls()), turns=turns, seed=seed, noise=0.05)
                m53.play()
                s53 = sum(s[0] for s in m53.scores()) / turns

                m56 = axl.Match((get_variant_player("v5.6"), opp_cls()), turns=turns, seed=seed, noise=0.05)
                m56.play()
                s56 = sum(s[0] for s in m56.scores()) / turns
                deltas.append(s56 - s53)
        mean_d = float(np.mean(deltas))
        len_deltas[turns] = mean_d
        print(f"    Turns = {turns:4d}: mean Δ = {mean_d:+.4f}")

    # Sign invariant across >= 2 lengths?
    signs = [np.sign(len_deltas[t]) for t in lengths]
    pos_count = sum(1 for s in signs if s > 0)
    neg_count = sum(1 for s in signs if s < 0)
    len_v = "PASS (Sign preserved across ≥2 lengths)" if (pos_count >= 2 or neg_count >= 2) else "FAIL"
    report_lines.append("## 5.1 Match Length Invariance (Turns: 50, 100, 200, 1000)\n\n")
    for t in lengths:
        report_lines.append(f"- Turns {t:4d}: Δ = {len_deltas[t]:+.4f}\n")
    report_lines.append(f"**Verdict**: {len_v}\n\n")

    # --- 5.2 Payoff Matrix: Donation Game ---
    print("5.2 Running Payoff Matrix Sweep (Donation Game R=2, T=3, S=-1, P=0)...")
    donation_game = axl.Game(r=2, s=-1, t=3, p=0)
    don_deltas = []
    for rep in range(8):
        seed = BASE_SEED + rep
        for _, opp_cls in opp_classes[:10]:
            m53 = axl.Match((get_variant_player("v5.3"), opp_cls()), turns=200, seed=seed, noise=0.05, game=donation_game)
            m53.play()
            s53 = sum(s[0] for s in m53.scores()) / 200

            m56 = axl.Match((get_variant_player("v5.6"), opp_cls()), turns=200, seed=seed, noise=0.05, game=donation_game)
            m56.play()
            s56 = sum(s[0] for s in m56.scores()) / 200
            don_deltas.append(s56 - s53)

    mean_don = float(np.mean(don_deltas))
    print(f"    Donation Game mean Δ = {mean_don:+.4f}\n")
    report_lines.append("## 5.2 Payoff Invariance (Donation Game R=2, T=3, S=-1, P=0)\n\n")
    report_lines.append(f"- Mean Δ = {mean_don:+.4f}\n\n")

    # --- 5.3 Reps Sweep: Power Analysis ---
    print("5.3 Running Reps Sweep (Power: 10, 30, 60 reps)...")
    reps_list = [10, 30, 60]
    p_vals = {}
    for r_count in reps_list:
        diffs = []
        for rep in range(r_count):
            seed = BASE_SEED + rep
            s53 = 0.0
            s56 = 0.0
            for name in ["HardProber", "TwoTitsForTat", "Gradual", "Calculator"]:
                opp_cls = by_name[name]
                m53 = axl.Match((get_variant_player("v5.3"), opp_cls()), turns=200, seed=seed, noise=0.05)
                m53.play()
                s53 += sum(s[0] for s in m53.scores()) / 200

                m56 = axl.Match((get_variant_player("v5.6"), opp_cls()), turns=200, seed=seed, noise=0.05)
                m56.play()
                s56 += sum(s[0] for s in m56.scores()) / 200
            diffs.append((s56 - s53) / 4)

        diffs = np.array(diffs)
        try:
            res = stats.wilcoxon(diffs, alternative="two-sided")
            p_val = float(res.pvalue)
        except Exception:
            p_val = 1.0
        p_vals[r_count] = p_val
        print(f"    Reps = {r_count:2d}: p-value = {p_val:.4e} (mean Δ = {np.mean(diffs):+.4f})")

    report_lines.append("## 5.3 Sample Power Sweep (Reps: 10, 30, 60 on Target Opponents)\n\n")
    for r_count in reps_list:
        report_lines.append(f"- Reps = {r_count:2d}: Wilcoxon p = {p_vals[r_count]:.4e}\n")
    report_lines.append("\n")

    # --- 5.4 Multi-Seed Sweep ---
    print("5.4 Running Multi-Seed Invariance (Seeds 42, 43, 44, 45)...")
    seed_deltas = {}
    for base_s in [42, 43, 44, 45]:
        deltas = []
        for opp_name in ["HardProber", "TwoTitsForTat", "Gradual", "Calculator"]:
            opp_cls = by_name[opp_name]
            m53 = axl.Match((get_variant_player("v5.3"), opp_cls()), turns=200, seed=base_s, noise=0.05)
            m53.play()
            s53 = sum(s[0] for s in m53.scores()) / 200

            m56 = axl.Match((get_variant_player("v5.6"), opp_cls()), turns=200, seed=base_s, noise=0.05)
            m56.play()
            s56 = sum(s[0] for s in m56.scores()) / 200
            deltas.append(s56 - s53)
        seed_deltas[base_s] = float(np.mean(deltas))
        print(f"    Seed {base_s}: mean Δ = {seed_deltas[base_s]:+.4f}")

    all_pos = all(d > 0 for d in seed_deltas.values())
    report_lines.append("## 5.4 Multi-Seed Invariance (Seeds 42, 43, 44, 45)\n\n")
    for s_val, d_val in seed_deltas.items():
        report_lines.append(f"- Seed {s_val}: Δ = {d_val:+.4f}\n")
    report_lines.append(f"**Verdict**: {'PASS (All seeds positive)' if all_pos else 'MIXED'}\n\n")

    # --- 5.5 Jackknife by Opponent ---
    print("5.5 Running Jackknife by Opponent (Leave-One-Out across Field Pack)...")
    # Compute per-opponent mean delta at 5% noise across 10 reps
    opp_means = []
    for _, opp_cls in opp_classes:
        deltas = []
        for rep in range(10):
            seed = BASE_SEED + rep
            m53 = axl.Match((get_variant_player("v5.3"), opp_cls()), turns=200, seed=seed, noise=0.05)
            m53.play()
            s53 = sum(s[0] for s in m53.scores()) / 200

            m56 = axl.Match((get_variant_player("v5.6"), opp_cls()), turns=200, seed=seed, noise=0.05)
            m56.play()
            s56 = sum(s[0] for s in m56.scores()) / 200
            deltas.append(s56 - s53)
        opp_means.append(float(np.mean(deltas)))

    overall_mean = np.mean(opp_means)
    overall_sign = np.sign(overall_mean)
    n_opps = len(opp_means)
    preserved = 0
    for i in range(n_opps):
        jk_mean = np.mean([opp_means[j] for j in range(n_opps) if j != i])
        if np.sign(jk_mean) == overall_sign:
            preserved += 1

    pres_pct = (preserved / n_opps) * 100
    jk_v = "PASS (≥95% folds preserved)" if pres_pct >= 95.0 else f"FAIL ({pres_pct:.1f}% preserved)"
    print(f"    Jackknife stability: {preserved}/{n_opps} ({pres_pct:.1f}%) → {jk_v}\n")

    report_lines.append("## 5.5 Jackknife Stability (Leave-One-Out across 32 Opponents)\n\n")
    report_lines.append(f"- Folds preserving sign: {preserved}/{n_opps} ({pres_pct:.1f}%) → **{jk_v}**\n\n")

    out_md = Path("ZDB_phase5_robustness.md")
    with open(out_md, "w", encoding="utf-8") as f:
        f.writelines(report_lines)

    print(f"Saved Phase 5 report to {out_md} (elapsed {time.time() - t0:.1f}s)\n")

if __name__ == "__main__":
    run_phase_5()
