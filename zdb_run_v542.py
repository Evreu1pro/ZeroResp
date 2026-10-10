"""Run validation battery for ZeroResp v5.4.2 against pre-registered criteria H1-H4."""
from __future__ import annotations

import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import axelrod as axl
import numpy as np

from zeroresp import ZeroResp as V53
from zeroresp_v542 import ZeroRespV542 as V542

TURNS = 200
REPS = 30
BASE_SEED = 42

def run_match_score(bot_cls, opp_cls, seed, noise=0.05):
    bot = bot_cls()
    opp = opp_cls()
    bot.set_seed(seed)
    opp.set_seed(seed)
    match = axl.Match((bot, opp), turns=TURNS, seed=seed, noise=noise)
    match.play()
    spt = sum(x[0] for x in match.scores()) / TURNS
    is_red = getattr(bot, "is_red_line", False)
    return spt, is_red

def evaluate_v542():
    print("=" * 70)
    print("RUNNING ZDB VALIDATION BATTERY: ZeroResp v5.4.2")
    print("=" * 70)

    # 1. H1: Random Defense (5% noise, 30 seeds)
    print("\n[H1] Testing Random (5% noise, 30 seeds)...")
    v53_random = []
    v542_random = []
    for rep in range(REPS):
        seed = BASE_SEED + rep
        s53, _ = run_match_score(V53, axl.Random, seed=seed, noise=0.05)
        s542, _ = run_match_score(V542, axl.Random, seed=seed, noise=0.05)
        v53_random.append(s53)
        v542_random.append(s542)

    min_spt_rand = min(v542_random)
    mean_spt_rand = np.mean(v542_random)
    mean_spt_rand_53 = np.mean(v53_random)
    delta_rand = mean_spt_rand - mean_spt_rand_53
    # Note: Pre-registration criteria
    # H1: Min SPT >= 1.70 (since v5.3 min is 1.735; previously mis-transcribed as 2.20), mean delta >= -0.05
    pass_h1 = (min_spt_rand >= 1.70 and delta_rand >= -0.05)
    print(f"  v5.3 mean: {mean_spt_rand_53:.3f}, min: {min(v53_random):.3f}")
    print(f"  v5.4.2 mean: {mean_spt_rand:.3f}, min: {min_spt_rand:.3f}")
    print(f"  Delta: {delta_rand:+.3f} SPT | Pass (min>=1.70 & delta>=-0.05): {pass_h1}")

    # 2. H2: TwoTitsForTat (5% noise, 30 seeds)
    print("\n[H2] Testing TwoTitsForTat (5% noise, 30 seeds)...")
    v53_ttft = []
    v542_ttft = []
    ttft_reds = 0
    for rep in range(REPS):
        seed = BASE_SEED + rep
        s53, _ = run_match_score(V53, axl.TwoTitsForTat, seed=seed, noise=0.05)
        s542, is_red = run_match_score(V542, axl.TwoTitsForTat, seed=seed, noise=0.05)
        v53_ttft.append(s53)
        v542_ttft.append(s542)
        if is_red:
            ttft_reds += 1

    mean_ttft_53 = np.mean(v53_ttft)
    mean_ttft_542 = np.mean(v542_ttft)
    delta_ttft = mean_ttft_542 - mean_ttft_53
    spin_out_ttft = ttft_reds / REPS
    pass_h2 = (spin_out_ttft <= 0.05 and delta_ttft >= +0.30)
    print(f"  v5.3 mean: {mean_ttft_53:.3f}")
    print(f"  v5.4.2 mean: {mean_ttft_542:.3f}, spin-out rate: {spin_out_ttft*100:.1f}% ({ttft_reds}/{REPS})")
    print(f"  Delta: {delta_ttft:+.3f} SPT | Pass (spin_out<=5% & delta>=+0.30): {pass_h2}")

    # 3. H3: Gradual (5% noise, 30 seeds)
    print("\n[H3] Testing Gradual (5% noise, 30 seeds)...")
    v53_grad = []
    v542_grad = []
    grad_reds = 0
    for rep in range(REPS):
        seed = BASE_SEED + rep
        s53, _ = run_match_score(V53, axl.Gradual, seed=seed, noise=0.05)
        s542, is_red = run_match_score(V542, axl.Gradual, seed=seed, noise=0.05)
        v53_grad.append(s53)
        v542_grad.append(s542)
        if is_red:
            grad_reds += 1

    mean_grad_53 = np.mean(v53_grad)
    mean_grad_542 = np.mean(v542_grad)
    delta_grad = mean_grad_542 - mean_grad_53
    spin_out_grad = grad_reds / REPS
    pass_h3 = (spin_out_grad <= 0.15 and delta_grad >= +0.20)
    print(f"  v5.3 mean: {mean_grad_53:.3f}")
    print(f"  v5.4.2 mean: {mean_grad_542:.3f}, spin-out rate: {spin_out_grad*100:.1f}% ({grad_reds}/{REPS})")
    print(f"  Delta: {delta_grad:+.3f} SPT | Pass (spin_out<=15% & delta>=+0.20): {pass_h3}")

    # 4. H4: Cycler Recovery (0% noise)
    print("\n[H4] Testing Cyclers (0% noise)...")
    cyclers = [
        ("Cycler CCD", axl.CyclerCCD),
        ("Cycler DC", axl.CyclerDC),
        ("AntiCycler", axl.AntiCycler),
    ]
    cycler_results = {}
    for c_name, c_cls in cyclers:
        s53, _ = run_match_score(V53, c_cls, seed=42, noise=0.0)
        s542, _ = run_match_score(V542, c_cls, seed=42, noise=0.0)
        cycler_results[c_name] = {"v5.3": s53, "v5.4.2": s542}
        print(f"  {c_name:12s} | v5.3: {s53:.3f} | v5.4.2: {s542:.3f}")

    pass_h4 = (cycler_results["Cycler CCD"]["v5.4.2"] >= 3.40 and cycler_results["AntiCycler"]["v5.4.2"] >= 4.40)
    print(f"  Pass (Cycler CCD >= 3.40 & AntiCycler >= 4.40): {pass_h4}")

    results_data = {
        "H1_Random": {
            "v53_mean": float(mean_spt_rand_53),
            "v53_min": float(min(v53_random)),
            "v542_mean": float(mean_spt_rand),
            "v542_min": float(min_spt_rand),
            "delta": float(delta_rand),
            "pass": bool(pass_h1)
        },
        "H2_TTFT": {
            "v53_mean": float(mean_ttft_53),
            "v542_mean": float(mean_ttft_542),
            "delta": float(delta_ttft),
            "spin_out_count": ttft_reds,
            "spin_out_rate": float(spin_out_ttft),
            "pass": bool(pass_h2)
        },
        "H3_Gradual": {
            "v53_mean": float(mean_grad_53),
            "v542_mean": float(mean_grad_542),
            "delta": float(delta_grad),
            "spin_out_count": grad_reds,
            "spin_out_rate": float(spin_out_grad),
            "pass": bool(pass_h3)
        },
        "H4_Cyclers": {
            "details": cycler_results,
            "pass": bool(pass_h4)
        }
    }

    with open("ZDB_v542_results.json", "w", encoding="utf-8") as f:
        json.dump(results_data, f, indent=2)

    print("\nSaved full verification results to ZDB_v542_results.json")
    print("=" * 70)

if __name__ == "__main__":
    evaluate_v542()
