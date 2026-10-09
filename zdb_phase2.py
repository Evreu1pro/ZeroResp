"""ZDB Phase 2: Ablation Study (Deconstructing mechanism contributions)."""
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

from zdb_phase0 import get_variant_player

TURNS = 200
REPS = 12
BASE_SEED = 42
NOISE_LEVELS = [0.0, 0.01, 0.05, 0.10]

TARGET_OPPONENTS = [
    "HardProber",
    "TwoTitsForTat",
    "Gradual",
    "Calculator",
    "TrickyCooperator",
    "ZDExtort2",
]

VARIANTS = [
    "v5.6",
    "v5.6_no_impulse",
    "v5.6_no_stopcock",
    "v5.6_no_earlyexit",
    "v5.4",
]

def run_phase_2():
    print("=" * 65)
    print("PHASE 2: ABLATION STUDY")
    print(f"Variants: {VARIANTS}")
    print(f"Reps: {REPS}, Turns: {TURNS}, Noise: {NOISE_LEVELS}")
    print("=" * 65)

    split_path = Path("benchmarks/results/research/bhns/split.json")
    with open(split_path, "r", encoding="utf-8") as f:
        train_names = json.load(f)["train"]

    all_opp_names = list(dict.fromkeys(train_names + TARGET_OPPONENTS))

    by_name = {s.__name__: s for s in axl.strategies}
    for s in axl.strategies:
        by_name[s.name] = s

    opp_classes = [(n, by_name[n]) for n in all_opp_names]
    print(f"Evaluating {len(opp_classes)} total unique opponents (field + 6 target).\n")

    # Storage: data[variant][noise][opp_name] -> list of rep SPTs
    data = {v: {noise: {n: [] for n in all_opp_names} for noise in NOISE_LEVELS} for v in VARIANTS}

    t0 = time.time()

    for noise in NOISE_LEVELS:
        print(f"Running Ablation at Noise {noise*100:.1f}% ...", flush=True)
        for rep in range(REPS):
            seed = BASE_SEED + rep
            for opp_name, opp_cls in opp_classes:
                for v in VARIANTS:
                    p = get_variant_player(v)
                    m = axl.Match((p, opp_cls()), turns=TURNS, seed=seed, noise=noise)
                    m.play()
                    s = sum(x[0] for x in m.scores()) / TURNS
                    data[v][noise][opp_name].append(s)

    print(f"Simulation completed in {time.time() - t0:.1f}s. Computing ablations...\n")

    # Focus on 5% noise and 10% noise on the 6 target opponents
    ablation_lines = []
    ablation_lines.append("# ZDB Phase 2 — Ablation Study\n\n")
    ablation_lines.append("## Target Opponents Breakdown (at 5% Noise, Reps=12)\n\n")
    ablation_lines.append("| Opponent | v5.4 Baseline | v5.6 Full | Δ (v5.6 - v5.4) | Drop when No Impulse | Drop when No Stopcock | Drop when No EarlyExit |\n")
    ablation_lines.append("|---|:---:|:---:|:---:|:---:|:---:|:---:|\n")

    evaluations = {
        "impulse": {"max_effect": 0.0, "opp": None, "alive": False},
        "stopcock": {"max_effect": 0.0, "opp": None, "alive": False},
        "earlyexit": {"max_effect": 0.0, "opp": None, "alive": False},
    }

    for opp_name in TARGET_OPPONENTS:
        s_54 = np.mean(data["v5.4"][0.05][opp_name])
        s_56 = np.mean(data["v5.6"][0.05][opp_name])
        delta_total = s_56 - s_54

        # Impact of removing impulse: v5.6 - v5.6_no_impulse
        s_no_imp = np.mean(data["v5.6_no_impulse"][0.05][opp_name])
        drop_imp = s_56 - s_no_imp

        # Impact of removing stopcock: v5.6 - v5.6_no_stopcock
        s_no_sc = np.mean(data["v5.6_no_stopcock"][0.05][opp_name])
        drop_sc = s_56 - s_no_sc

        # Impact of removing earlyexit: v5.6 - v5.6_no_earlyexit
        s_no_ee = np.mean(data["v5.6_no_earlyexit"][0.05][opp_name])
        drop_ee = s_56 - s_no_ee

        ablation_lines.append(
            f"| **{opp_name}** | {s_54:.4f} | {s_56:.4f} | {delta_total:+.4f} | "
            f"{drop_imp:+.4f} | {drop_sc:+.4f} | {drop_ee:+.4f} |\n"
        )

        for mech, drop in [("impulse", drop_imp), ("stopcock", drop_sc), ("earlyexit", drop_ee)]:
            if abs(drop) > evaluations[mech]["max_effect"]:
                evaluations[mech]["max_effect"] = abs(drop)
                evaluations[mech]["opp"] = opp_name
            if abs(drop) > 0.02:
                evaluations[mech]["alive"] = True

    ablation_lines.append("\n## Mechanism Health Check (Pre-registered criteria)\n\n")
    ablation_lines.append("* **Rule**: If disabling mechanism changes Δ by ≤ 0.02 across all targets → declared **DEAD CODE**.\n")
    ablation_lines.append("* **Rule**: Each mechanism must explain ≥30% of effect on ≥1 target opponent.\n\n")

    for mech, ev in evaluations.items():
        verdict = "ACTIVE & ALIVE" if ev["alive"] else "DEAD CODE (Effect ≤ 0.02)"
        ablation_lines.append(f"- **{mech}**: Max effect = {ev['max_effect']:.4f} on {ev['opp']} → **{verdict}**\n")

    out_md = Path("ZDB_phase2_ablation.md")
    with open(out_md, "w", encoding="utf-8") as f:
        f.writelines(ablation_lines)

    print("".join(ablation_lines))
    print(f"Saved Phase 2 results to {out_md}\n")
    return evaluations

if __name__ == "__main__":
    run_phase_2()
