"""
ZDB Validation Runner for ZeroResp v5.4.1 across pre-registered hypotheses H1-H8.
"""
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

from zeroresp import ZeroResp as ZeroRespV53
from zeroresp_v54 import ZeroRespV54Full as ZeroRespV54
from zeroresp_v541 import ZeroRespV541

TURNS = 200
REPS = 30
BASE_SEED = 42

def play_match(p1_cls, p2_cls, turns, noise, seed, p1_kwargs=None):
    kw = p1_kwargs or {}
    p1 = p1_cls(**kw)
    p1.set_seed(seed)
    p2 = p2_cls()
    m = axl.Match((p1, p2), turns=turns, noise=noise, seed=seed)
    m.play()
    return m.final_score_per_turn()[0]

def run_v541_validation():
    print("=" * 70)
    print("ZDB VALIDATION SUITE: ZeroResp v5.4.1 (H1 - H8)")
    print("=" * 70)

    # Load splits
    split_path = Path("benchmarks/results/research/bhns/split.json")
    with open(split_path, "r", encoding="utf-8") as f:
        splits = json.load(f)
    train_names = splits["train"]
    test_names = splits["holdout"]

    by_name = {s.__name__: s for s in axl.strategies}
    for s in axl.strategies:
        by_name[s.name] = s

    field_opps = [(n, by_name[n]) for n in train_names]
    holdout_opps = [(n, by_name[n]) for n in test_names]

    results = {}

    # -------------------------------------------------------------
    # H1: 0% and 1% noise parity on Field Pack vs v5.3 (Delta >= -0.005)
    # -------------------------------------------------------------
    print("\n>>> Testing H1: Low-Noise Parity vs v5.3 (Field Pack, 30 seeds)")
    h1_results = {}
    for noise in [0.0, 0.01]:
        diffs = []
        s53_list, s541_list = [], []
        for rep in range(REPS):
            seed = BASE_SEED + rep
            for name, opp_cls in field_opps:
                s53 = play_match(ZeroRespV53, opp_cls, TURNS, noise, seed)
                s541 = play_match(ZeroRespV541, opp_cls, TURNS, noise, seed)
                diffs.append(s541 - s53)
                s53_list.append(s53)
                s541_list.append(s541)
        mean_diff = float(np.mean(diffs))
        p_val = float(stats.ttest_rel(s541_list, s53_list).pvalue)
        h1_results[noise] = {
            "mean_v53": float(np.mean(s53_list)),
            "mean_v541": float(np.mean(s541_list)),
            "delta": mean_diff,
            "p_val": p_val,
            "pass": mean_diff >= -0.005
        }
        print(f"Noise {noise*100:4.1f}%: v5.3 = {np.mean(s53_list):.4f}, v5.4.1 = {np.mean(s541_list):.4f}, Delta = {mean_diff:+.4f} (p={p_val:.4e}) -> Pass: {h1_results[noise]['pass']}")
    results["H1"] = h1_results

    # -------------------------------------------------------------
    # H2: TwoTitsForTat at 5% noise: RedLine spin <= 5% seeds, Delta >= +0.20
    # -------------------------------------------------------------
    print("\n>>> Testing H2: TwoTitsForTat at 5% Noise (RedLine Prevention & SPT)")
    ttft_cls = axl.TwoTitsForTat
    ttft_s53, ttft_s541 = [], []
    for rep in range(REPS):
        seed = BASE_SEED + rep
        ttft_s53.append(play_match(ZeroRespV53, ttft_cls, TURNS, 0.05, seed))
        ttft_s541.append(play_match(ZeroRespV541, ttft_cls, TURNS, 0.05, seed))
    
    ttft_spin_53 = sum(1 for s in ttft_s53 if s <= 2.20) / REPS
    ttft_spin_541 = sum(1 for s in ttft_s541 if s <= 2.20) / REPS
    ttft_delta = float(np.mean(ttft_s541) - np.mean(ttft_s53))
    results["H2"] = {
        "v53_mean": float(np.mean(ttft_s53)),
        "v541_mean": float(np.mean(ttft_s541)),
        "delta": ttft_delta,
        "v53_spin_rate": ttft_spin_53,
        "v541_spin_rate": ttft_spin_541,
        "pass_spin": ttft_spin_541 <= 0.05,
        "pass_delta": ttft_delta >= 0.20,
        "pass": (ttft_spin_541 <= 0.05 and ttft_delta >= 0.20)
    }
    print(f"TTFT Spin Rate: v5.3 = {ttft_spin_53*100:.1f}%, v5.4.1 = {ttft_spin_541*100:.1f}% (<= 5%: {results['H2']['pass_spin']})")
    print(f"TTFT Mean SPT: v5.3 = {np.mean(ttft_s53):.4f}, v5.4.1 = {np.mean(ttft_s541):.4f}, Delta = {ttft_delta:+.4f} (>= +0.20: {results['H2']['pass_delta']})")

    # -------------------------------------------------------------
    # H3: Gradual at 5% noise: RedLine spin <= 20% seeds, Delta >= +0.20
    # -------------------------------------------------------------
    print("\n>>> Testing H3: Gradual at 5% Noise (RedLine Prevention & SPT)")
    gradual_cls = axl.Gradual
    grad_s53, grad_s541 = [], []
    for rep in range(REPS):
        seed = BASE_SEED + rep
        grad_s53.append(play_match(ZeroRespV53, gradual_cls, TURNS, 0.05, seed))
        grad_s541.append(play_match(ZeroRespV541, gradual_cls, TURNS, 0.05, seed))

    grad_spin_53 = sum(1 for s in grad_s53 if s <= 2.00) / REPS
    grad_spin_541 = sum(1 for s in grad_s541 if s <= 2.00) / REPS
    grad_delta = float(np.mean(grad_s541) - np.mean(grad_s53))
    results["H3"] = {
        "v53_mean": float(np.mean(grad_s53)),
        "v541_mean": float(np.mean(grad_s541)),
        "delta": grad_delta,
        "v53_spin_rate": grad_spin_53,
        "v541_spin_rate": grad_spin_541,
        "pass_spin": grad_spin_541 <= 0.20,
        "pass_delta": grad_delta >= 0.20,
        "pass": (grad_spin_541 <= 0.20 and grad_delta >= 0.20)
    }
    print(f"Gradual Spin Rate: v5.3 = {grad_spin_53*100:.1f}%, v5.4.1 = {grad_spin_541*100:.1f}% (<= 20%: {results['H3']['pass_spin']})")
    print(f"Gradual Mean SPT: v5.3 = {np.mean(grad_s53):.4f}, v5.4.1 = {np.mean(grad_s541):.4f}, Delta = {grad_delta:+.4f} (>= +0.20: {results['H3']['pass_delta']})")

    # -------------------------------------------------------------
    # H4: Locality vs v5.4 at 0% noise
    # -------------------------------------------------------------
    print("\n>>> Testing H4: Locality vs v5.4 at 0% Noise")
    h4_diffs = {}
    h4_pass = True
    for name, opp_cls in field_opps:
        s54_scores, s541_scores = [], []
        for rep in range(REPS):
            seed = BASE_SEED + rep
            s54 = play_match(ZeroRespV54, opp_cls, TURNS, 0.0, seed)
            s541 = play_match(ZeroRespV541, opp_cls, TURNS, 0.0, seed)
            s54_scores.append(s54)
            s541_scores.append(s541)
        mean_d = float(np.mean(s541_scores) - np.mean(s54_scores))
        h4_diffs[name] = mean_d
        if name in ("Calculator", "Alternator"):
            if mean_d < -1e-4:
                h4_pass = False
        elif name == "Random":
            # Random is repaired by the gate; must not regress
            if mean_d < -1e-4:
                h4_pass = False
        else:
            if abs(mean_d) > 1e-4:
                h4_pass = False
    
    print(f"Alternator Delta vs v5.4: {h4_diffs.get('Alternator', 0):+.4f}")
    print(f"Calculator Delta vs v5.4: {h4_diffs.get('Calculator', 0):+.4f}")
    print(f"Random Delta vs v5.4: {h4_diffs.get('Random', 0):+.4f}")
    non_target_max_abs = max(abs(d) for k, d in h4_diffs.items() if k not in ("Calculator", "Alternator", "Random"))
    print(f"Max |Delta| on 29 remaining opponents vs v5.4: {non_target_max_abs:.6f}")
    results["H4"] = {
        "alternator_delta": h4_diffs.get("Alternator", 0),
        "calculator_delta": h4_diffs.get("Calculator", 0),
        "random_delta": h4_diffs.get("Random", 0),
        "non_target_max_abs": non_target_max_abs,
        "pass": h4_pass and non_target_max_abs <= 1e-4
    }
    print(f"H4 Pass: {results['H4']['pass']}")

    # -------------------------------------------------------------
    # H5: Hyperparameter Sensitivity on Gate (3x3 grid)
    # -------------------------------------------------------------
    print("\n>>> Testing H5: Hyperparameter Sensitivity Grid (live_coop x opp_len)")
    from zeroresp_v54 import Features, ZeroResp
    grid_coop = [0.55, 0.60, 0.65]
    grid_len = [10, 15, 20]
    
    # Custom runner for sensitivity
    class ParamZR(ZeroResp):
        def __init__(self, base_epoch: int = 25, use_profiles: bool = True, features: Features | None = None, coop_thresh: float = 0.60, len_thresh: int = 15):
            super().__init__(base_epoch=base_epoch, use_profiles=use_profiles, features=features)
            self._g_coop = coop_thresh
            self._g_len = len_thresh

        def strategy(self, opponent):
            if self.features.balance_apology and self.nl_balance <= self.NL_BALANCE_FLOOR:
                can_apologize = not (self.opp_len >= self._g_len and self._live_coop_rate() < self._g_coop)
                if can_apologize:
                    self.nl_scheduled = []
                    self.nl_harvest_left = 0
                    self.nl_harvest_scheduled_at = 0
                    self.nl_harvest_postponed = 0
                    self.nl_harvest_size = 0
                    self.nl_evidence = 0
                    self.nl_window.clear()
                    self.echo_forgive = max(self.echo_forgive, 2)
                    self.warmth = max(self.warmth, 0.6)
                    self.target_warmth = max(self.target_warmth, 0.6)
            
            old_ba = self.features.balance_apology
            self.features.balance_apology = False
            res = super().strategy(opponent)
            self.features.balance_apology = old_ba
            return res

    sens_targets = [("Random", axl.Random), ("TwoTitsForTat", axl.TwoTitsForTat), ("Gradual", axl.Gradual)]
    grid_means = []
    feats_sens = Features(adaptive_harvest=True, balance_apology=True, tactical_prefilter=True, profile_memory=True)
    for c_th in grid_coop:
        for l_th in grid_len:
            t_scores = []
            for t_name, t_cls in sens_targets:
                for rep in range(15):
                    s = play_match(ParamZR, t_cls, TURNS, 0.05, BASE_SEED + rep, {"coop_thresh": c_th, "len_thresh": l_th, "features": feats_sens})
                    t_scores.append(s)
            grid_means.append((c_th, l_th, float(np.mean(t_scores))))
    
    baseline_sens = next(m for c, l, m in grid_means if c == 0.60 and l == 15)
    max_shift = max(abs(m - baseline_sens) for _, _, m in grid_means)
    print(f"Baseline (0.60, 15) Mean: {baseline_sens:.4f}")
    print(f"Max absolute shift across 9 configurations: {max_shift:.4f} (criterion: <= 0.02)")
    results["H5"] = {
        "grid_means": grid_means,
        "max_shift": max_shift,
        "pass": max_shift <= 0.02
    }
    print(f"H5 Pass: {results['H5']['pass']}")

    # -------------------------------------------------------------
    # H6: Cycler Family Preservation at 0% Noise (Delta >= +1.0 vs v5.3)
    # -------------------------------------------------------------
    print("\n>>> Testing H6: Cycler Family Preservation (0% Noise)")
    cycler_classes = [
        ("Cycler CCD", axl.CyclerCCD),
        ("Cycler CCCD", axl.CyclerCCCD),
        ("Cycler CCCCCD", axl.CyclerCCCCCD),
    ]
    h6_deltas = []
    for c_name, c_cls in cycler_classes:
        s53_c = play_match(ZeroRespV53, c_cls, TURNS, 0.0, BASE_SEED)
        s541_c = play_match(ZeroRespV541, c_cls, TURNS, 0.0, BASE_SEED)
        d = s541_c - s53_c
        h6_deltas.append(d)
        print(f"{c_name}: v5.3 = {s53_c:.4f}, v5.4.1 = {s541_c:.4f}, Delta = {d:+.4f}")
    
    results["H6"] = {
        "mean_delta": float(np.mean(h6_deltas)),
        "min_delta": float(min(h6_deltas)),
        "pass": bool(min(h6_deltas) >= 1.0)
    }
    print(f"H6 Pass: {results['H6']['pass']}")

    # -------------------------------------------------------------
    # H7: Holdout Pack (40 strategies, 5% noise, Delta >= -0.010 vs v5.3)
    # -------------------------------------------------------------
    print("\n>>> Testing H7: Holdout Generalization (40 strategies, 5% noise, 30 reps)")
    holdout_diffs = []
    h_s53_list, h_s541_list = [], []
    for rep in range(REPS):
        seed = BASE_SEED + rep
        for name, opp_cls in holdout_opps:
            s53 = play_match(ZeroRespV53, opp_cls, TURNS, 0.05, seed)
            s541 = play_match(ZeroRespV541, opp_cls, TURNS, 0.05, seed)
            holdout_diffs.append(s541 - s53)
            h_s53_list.append(s53)
            h_s541_list.append(s541)
    
    holdout_mean_delta = float(np.mean(holdout_diffs))
    h7_pval = float(stats.ttest_rel(h_s541_list, h_s53_list).pvalue)
    print(f"Holdout 40 Mean: v5.3 = {np.mean(h_s53_list):.4f}, v5.4.1 = {np.mean(h_s541_list):.4f}")
    print(f"Holdout Delta: {holdout_mean_delta:+.4f} (p={h7_pval:.4e}, criterion: >= -0.010)")
    results["H7"] = {
        "v53_mean": float(np.mean(h_s53_list)),
        "v541_mean": float(np.mean(h_s541_list)),
        "delta": holdout_mean_delta,
        "p_val": h7_pval,
        "pass": holdout_mean_delta >= -0.010
    }
    print(f"H7 Pass: {results['H7']['pass']}")

    # -------------------------------------------------------------
    # H8: Random Defense at 5% Noise (Mean Delta >= -0.05, max seed drop <= -0.30)
    # -------------------------------------------------------------
    print("\n>>> Testing H8: Random Defense at 5% Noise")
    rnd_cls = axl.Random
    rnd_s53, rnd_s541 = [], []
    rnd_diffs = []
    for rep in range(REPS):
        seed = BASE_SEED + rep
        s53 = play_match(ZeroRespV53, rnd_cls, TURNS, 0.05, seed)
        s541 = play_match(ZeroRespV541, rnd_cls, TURNS, 0.05, seed)
        rnd_s53.append(s53)
        rnd_s541.append(s541)
        rnd_diffs.append(s541 - s53)
    
    rnd_mean_delta = float(np.mean(rnd_diffs))
    rnd_min_delta = float(min(rnd_diffs))
    print(f"Random Mean: v5.3 = {np.mean(rnd_s53):.4f}, v5.4.1 = {np.mean(rnd_s541):.4f}")
    print(f"Random Delta: {rnd_mean_delta:+.4f} (criterion: >= -0.05)")
    print(f"Random Min Seed Delta: {rnd_min_delta:+.4f} (criterion: >= -0.30)")
    results["H8"] = {
        "v53_mean": float(np.mean(rnd_s53)),
        "v541_mean": float(np.mean(rnd_s541)),
        "mean_delta": rnd_mean_delta,
        "min_delta": rnd_min_delta,
        "pass_mean": rnd_mean_delta >= -0.05,
        "pass_min": rnd_min_delta >= -0.30,
        "pass": (rnd_mean_delta >= -0.05 and rnd_min_delta >= -0.30)
    }
    print(f"H8 Pass: {results['H8']['pass']}")

    # Save summary json
    with open("ZDB_v541_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 70)
    print("SUMMARY OF PRE-REGISTERED HYPOTHESES (H1-H8)")
    print("=" * 70)
    for h in ["H1", "H2", "H3", "H4", "H5", "H6", "H7", "H8"]:
        res = results[h]
        p = res.get("pass", False) if h != "H1" else (res[0.0]["pass"] and res[0.01]["pass"])
        print(f"  [{'PASS' if p else 'FAIL'}] {h}")
    print("=" * 70)

if __name__ == "__main__":
    t0 = time.time()
    run_v541_validation()
    print(f"\nCompleted in {time.time() - t0:.1f}s")
