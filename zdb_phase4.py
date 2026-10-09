"""ZDB Phase 4: Scope Conditions (Boundary conditions & Hold-out verification)."""
from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import axelrod as axl
import numpy as np

from zdb_phase0 import get_variant_player

TURNS = 200
BASE_SEED = 42

class _FlipList:
    def __init__(self, hist, p, rng):
        self._hist = hist
        self._p = p
        self._rng = rng
        self._coins = {}

    def _flipped(self, i):
        if i not in self._coins:
            self._coins[i] = self._rng.random() < self._p
        c = self._coins[i]
        if not c:
            return self._hist[i]
        return axl.Action.C if self._hist[i] == axl.Action.D else axl.Action.D

    def __len__(self):
        return len(self._hist)

    def __getitem__(self, i):
        return self._flipped(i)

    def __iter__(self):
        for i in range(len(self._hist)):
            yield self._flipped(i)

class _PerceptionPlayer(axl.Player):
    def __init__(self, base_player: axl.Player, p: float, rng):
        super().__init__()
        self._base = base_player
        self._p = p
        self._rng = rng
        self.name = f"{base_player.name} (Perception)"

    @property
    def history(self):
        return self._base.history

    def strategy(self, opponent: axl.Player) -> axl.Action:
        class _Proxy:
            def __init__(self, opp, fliplist):
                self._opp = opp
                self.history = fliplist
            def __getattr__(self, name):
                return getattr(self._opp, name)

        if self._p > 0 and opponent.history:
            fl = _FlipList(opponent.history, self._p, self._rng)
            return self._base.strategy(_Proxy(opponent, fl))
        return self._base.strategy(opponent)

    def reset(self):
        super().reset()
        self._base.reset()


def run_phase_4():
    print("=" * 65)
    print("PHASE 4: SCOPE CONDITIONS")
    print("=" * 65)

    split_path = Path("benchmarks/results/research/bhns/split.json")
    with open(split_path, "r", encoding="utf-8") as f:
        split_data = json.load(f)

    train_names = split_data["train"]
    holdout_names = split_data["holdout"]

    by_name = {s.__name__: s for s in axl.strategies}
    for s in axl.strategies:
        by_name[s.name] = s

    report_lines = []
    report_lines.append("# ZDB Phase 4 — Scope Conditions Report\n\n")

    t0 = time.time()

    # --- 4.1 Perception-flip ---
    print("4.1 Running Perception-flip (30 reps, noise 5% and 10%)...")
    p_results = {}
    for p_noise in [0.05, 0.10]:
        deltas = []
        for rep in range(30):
            seed = BASE_SEED + rep
            for name in ["TitForTat", "Grudger", "Cooperator", "TwoTitsForTat", "HardProber"]:
                opp_cls = by_name[name]
                rng53 = random.Random(seed)
                rng56 = random.Random(seed)

                p53 = _PerceptionPlayer(get_variant_player("v5.3"), p_noise, rng53)
                m53 = axl.Match((p53, opp_cls()), turns=TURNS, seed=seed, noise=0.0)
                m53.play()
                s53 = sum(s[0] for s in m53.scores()) / TURNS

                p56 = _PerceptionPlayer(get_variant_player("v5.6"), p_noise, rng56)
                m56 = axl.Match((p56, opp_cls()), turns=TURNS, seed=seed, noise=0.0)
                m56.play()
                s56 = sum(s[0] for s in m56.scores()) / TURNS

                deltas.append(s56 - s53)
        mean_d = float(np.mean(deltas))
        p_results[p_noise] = mean_d
        v = "PASS (|Δ| ≤ 0.02)" if abs(mean_d) <= 0.02 else "FAIL"
        print(f"    Perception {p_noise*100:.0f}%: Δ mean = {mean_d:+.4f} → {v}")

    report_lines.append("## 4.1 Perception-Flip Robustness (Reps=30)\n\n")
    report_lines.append(f"- 5% noise: Δ = {p_results[0.05]:+.4f} (Criterion: |Δ| ≤ 0.02) → **{'PASS' if abs(p_results[0.05]) <= 0.02 else 'FAIL'}**\n")
    report_lines.append(f"- 10% noise: Δ = {p_results[0.10]:+.4f} (Criterion: |Δ| ≤ 0.02) → **{'PASS' if abs(p_results[0.10]) <= 0.02 else 'FAIL'}**\n\n")

    # --- 4.2 External Hold-out ---
    print("4.2 Running External Hold-out (40 strategies from split.json, 12 reps, 5% noise)...")
    ho_classes = [by_name[n] for n in holdout_names if n in by_name]
    ho_deltas = []
    for rep in range(12):
        seed = BASE_SEED + rep
        for opp_cls in ho_classes:
            m53 = axl.Match((get_variant_player("v5.3"), opp_cls()), turns=TURNS, seed=seed, noise=0.05)
            m53.play()
            s53 = sum(s[0] for s in m53.scores()) / TURNS

            m56 = axl.Match((get_variant_player("v5.6"), opp_cls()), turns=TURNS, seed=seed, noise=0.05)
            m56.play()
            s56 = sum(s[0] for s in m56.scores()) / TURNS
            ho_deltas.append(s56 - s53)

    mean_ho = float(np.mean(ho_deltas))
    ho_v = "PASS (Δ ≥ -0.01)" if mean_ho >= -0.01 else "FAIL (Overfitted to train)"
    print(f"    Hold-out mean Δ = {mean_ho:+.4f} across {len(ho_classes)} hold-out strategies → {ho_v}\n")
    report_lines.append("## 4.2 External Hold-Out Pool (40 unseen strategies, 5% Noise, Reps=12)\n\n")
    report_lines.append(f"- Mean Δ = {mean_ho:+.4f} → **{ho_v}**\n\n")

    # --- 4.3 Library without Cyclers ---
    print("4.3 Running Library without Cyclers (12 reps, 5% noise)...")
    non_cyclers = [
        s for s in axl.short_run_time_strategies
        if "cycler" not in s.__name__.lower() and not getattr(s, "classifier", {}).get("long_run_time")
    ]
    sample_pool = non_cyclers[:50]  # Representative sample of 50 non-cycler strategies
    nc_deltas = []
    for rep in range(12):
        seed = BASE_SEED + rep
        for opp_cls in sample_pool:
            m53 = axl.Match((get_variant_player("v5.3"), opp_cls()), turns=TURNS, seed=seed, noise=0.05)
            m53.play()
            s53 = sum(s[0] for s in m53.scores()) / TURNS

            m56 = axl.Match((get_variant_player("v5.6"), opp_cls()), turns=TURNS, seed=seed, noise=0.05)
            m56.play()
            s56 = sum(s[0] for s in m56.scores()) / TURNS
            nc_deltas.append(s56 - s53)

    mean_nc = float(np.mean(nc_deltas))
    nc_v = "PASS (Δ ≥ 0)" if mean_nc >= 0 else "SCOPE CONDITION (Dependent on periodic/cyclers)"
    print(f"    Non-Cyclers mean Δ = {mean_nc:+.4f} across {len(sample_pool)} strategies → {nc_v}\n")
    report_lines.append("## 4.3 Library Without Cyclers (Sample of 50 non-cyclers, 5% Noise, Reps=12)\n\n")
    report_lines.append(f"- Mean Δ = {mean_nc:+.4f} → **{nc_v}**\n\n")

    # --- 4.4 Cyclers with Jitter ---
    print("4.4 Running Cyclers with Jitter (1% and 3% noise, 12 reps)...")
    cycler_classes = [s for s in axl.strategies if "cycler" in s.__name__.lower()][:5]
    cy_res = {}
    for cy_noise in [0.01, 0.03]:
        cy_deltas = []
        for rep in range(12):
            seed = BASE_SEED + rep
            for opp_cls in cycler_classes:
                m53 = axl.Match((get_variant_player("v5.3"), opp_cls()), turns=TURNS, seed=seed, noise=cy_noise)
                m53.play()
                s53 = sum(s[0] for s in m53.scores()) / TURNS

                m56 = axl.Match((get_variant_player("v5.6"), opp_cls()), turns=TURNS, seed=seed, noise=cy_noise)
                m56.play()
                s56 = sum(s[0] for s in m56.scores()) / TURNS
                cy_deltas.append(s56 - s53)
        cy_res[cy_noise] = float(np.mean(cy_deltas))
        print(f"    Cycler Jitter {cy_noise*100:.0f}%: mean Δ = {cy_res[cy_noise]:+.4f}")

    report_lines.append("## 4.4 Cyclers with Jitter (Reps=12)\n\n")
    report_lines.append(f"- 1% Jitter: Δ = {cy_res[0.01]:+.4f}\n")
    report_lines.append(f"- 3% Jitter: Δ = {cy_res[0.03]:+.4f}\n\n")

    # --- 4.5 ZD Extensions ---
    print("4.5 Running ZD Extensions (ZDGTFT2, ZDExtort4, EvolvedLookerUp2_2_2, 5% noise, 12 reps)...")
    zd_opps = [by_name[n] for n in ["ZDGTFT2", "ZDExtort4", "EvolvedLookerUp2_2_2"] if n in by_name]
    zd_deltas = []
    for rep in range(12):
        seed = BASE_SEED + rep
        for opp_cls in zd_opps:
            m53 = axl.Match((get_variant_player("v5.3"), opp_cls()), turns=TURNS, seed=seed, noise=0.05)
            m53.play()
            s53 = sum(s[0] for s in m53.scores()) / TURNS

            m56 = axl.Match((get_variant_player("v5.6"), opp_cls()), turns=TURNS, seed=seed, noise=0.05)
            m56.play()
            s56 = sum(s[0] for s in m56.scores()) / TURNS
            zd_deltas.append(s56 - s53)

    mean_zd = float(np.mean(zd_deltas))
    print(f"    ZD Extensions mean Δ = {mean_zd:+.4f}\n")
    report_lines.append("## 4.5 Zero-Determinant Extensions (5% Noise, Reps=12)\n\n")
    report_lines.append(f"- Mean Δ = {mean_zd:+.4f}\n\n")

    out_md = Path("ZDB_phase4_scope.md")
    with open(out_md, "w", encoding="utf-8") as f:
        f.writelines(report_lines)

    print(f"Saved Phase 4 report to {out_md} (elapsed {time.time() - t0:.1f}s)\n")

if __name__ == "__main__":
    run_phase_4()
