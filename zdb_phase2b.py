"""ZDB Phase 2b: True Factorial Ablation on is_rigid and min_d gates."""
from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import axelrod as axl
import numpy as np

# We subclass ZeroResp to strictly control the two lines
from zeroresp_v56 import ZeroResp as ZeroRespBase

class ZeroRespAblation(ZeroRespBase):
    def __init__(self, rigid_mode: str = "new", mind_mode: str = "new", base_epoch: int = 25, use_profiles: bool = True, features=None):
        super().__init__(base_epoch=base_epoch, use_profiles=use_profiles, features=features)
        self.rigid_mode = rigid_mode  # "old" or "new"
        self.mind_mode = mind_mode    # "old" or "new"
        self.init_kwargs = {
            "rigid_mode": rigid_mode,
            "mind_mode": mind_mode,
            "base_epoch": base_epoch,
            "use_profiles": use_profiles,
            "features": features,
        }

    def _nl_ladder(self, step: int) -> bool:
        if self.nl_window and (step - self.nl_window[-1]) > self.NL_WINDOW_TURNS:
            self.nl_evidence = 0
            self.nl_window.clear()
        self.nl_evidence += 1
        self.nl_window.append(step)

        if self.nl_pardon_step and (step - self.nl_pardon_step) <= 6:
            self._forgiveness_exploiter += 1
            self.nl_pardon_step = 0

        if self.nl_evidence == 1:
            self.nl_pardoned += 1
            self.nl_debt_ledger += 1
            self._pending_reason = "nl_deferred"
            return True

        if self.nl_evidence >= 2 and self.nl_harvest_scheduled_at == 0 and self.nl_harvest_left == 0:
            self.nl_pardoned += 1
            self.nl_debt_ledger += 1
            self._pending_reason = "nl_deferred"

            if not any(r.get("kind") == "strike" for r in self.nl_scheduled):
                self.nl_scheduled.append({
                    "turn": step + self._random.randint(self.NL_DELAY_MIN, self.NL_DELAY_MAX),
                    "kind": "strike",
                })

            forg = self.opp_coops_after_my_D / max(1, self.my_D)

            # FACTOR B: min_d
            if self.mind_mode == "old":
                min_d = self.my_D >= 3
            else:
                min_d = self.my_D >= 2

            if self.features.profile_memory and self._known_soft_opponent:
                min_d = self.my_D >= 1

            blocked_tactical = (
                self.features.tactical_prefilter
                and self.tactical in ("aggressor", "grudger")
            )

            # FACTOR A: is_rigid
            in_warmup = self.features.warmup_calibration and (step <= self.WARMUP_TURNS) and not self.warmup_early_exited
            if self.rigid_mode == "old":
                if self.opp_defects_after_my_D > 0 and self.my_D <= 3:
                    self.is_rigid = True
            else:
                if self.my_D >= 2 and (self.opp_defects_after_my_D / self.my_D) > 0.50:
                    self.is_rigid = True

            can_harvest = (
                not in_warmup
                and not self.is_rigid
                and min_d
                and not blocked_tactical
                and self.nl_balance >= 0
            )

            is_noisy = self._is_noisy_regime()

            if can_harvest and is_noisy and self.features.pulsed_harvest:
                softness = (forg - self.NL_SOFTNESS_FLOOR) / (1.0 - self.NL_SOFTNESS_FLOOR)
                softness = max(0.0, min(1.0, softness))
                if (
                    softness > 0.4
                    and (step - self.last_pulse_step >= self.PULSE_COOLDOWN)
                    and self._random.random() < softness
                ):
                    self.nl_harvest_size = 1
                    self.nl_harvest_left = 0
                    self.nl_harvest_postponed = 0
                    self.nl_harvest_scheduled_at = step + self._random.randint(4, 8)
                    self.last_pulse_step = step
            elif can_harvest and not is_noisy:
                softness = (forg - self.NL_SOFTNESS_FLOOR) / (1.0 - self.NL_SOFTNESS_FLOOR)
                softness = max(0.0, min(1.0, softness))
                if softness > 0 and self._random.random() < softness:
                    size = int(round(
                        self.NL_HARVEST_MIN + softness * (self.NL_HARVEST_MAX - self.NL_HARVEST_MIN)
                    ))
                    self.nl_harvest_size = max(self.NL_HARVEST_MIN, size)
                    self.nl_harvest_left = 0
                    self.nl_harvest_postponed = 0
                    self.nl_harvest_scheduled_at = step + self._random.randint(6, 10)

            return True

        if self.nl_evidence >= 3:
            if (self._live_coop_rate() < self._HOSTILE_COOP_THRESHOLD
                    and (not self._is_noisy_regime() or self.nl_evidence >= 8)):
                self._enter_red_line()
                return False
        return None

TARGET_OPPONENTS = [
    "TwoTitsForTat",
    "Gradual",
    "HardProber",
    "Calculator",
    "TitForTat",
]

CONFIGS = [
    ("base_old", "old", "old"),
    ("only_new_rigid", "new", "old"),
    ("only_new_mind", "old", "new"),
    ("both_new", "new", "new"),
]

def run_phase_2b():
    print("=" * 65)
    print("PHASE 2b: TRUE FACTORIAL ABLATION (is_rigid vs min_d)")
    print(f"Noise: 5%, Reps: 30, Turns: 200, Opponents: {TARGET_OPPONENTS}")
    print("=" * 65)

    by_name = {s.__name__: s for s in axl.strategies}
    for s in axl.strategies:
        by_name[s.name] = s

    # Storage: data[cfg_name][opp_name] -> list of 30 rep scores
    scores = {name: {opp: [] for opp in TARGET_OPPONENTS} for name, _, _ in CONFIGS}

    t0 = time.time()
    for rep in range(30):
        seed = 42 + rep
        for opp_name in TARGET_OPPONENTS:
            opp_cls = by_name[opp_name]
            for cfg_name, r_mode, m_mode in CONFIGS:
                bot = ZeroRespAblation(rigid_mode=r_mode, mind_mode=m_mode)
                m = axl.Match((bot, opp_cls()), turns=200, seed=seed, noise=0.05)
                m.play()
                s = sum(x[0] for x in m.scores()) / 200
                scores[cfg_name][opp_name].append(s)

    lines = []
    lines.append("# ZDB Phase 2b — Factorial Ablation on Gating Lines\n\n")
    lines.append("| Opponent | Base (Old Both) | Only New Rigid | Only New Min_D | Both New (v5.6) | Effect of is_rigid | Effect of min_d |\n")
    lines.append("|---|:---:|:---:|:---:|:---:|:---:|:---:|\n")

    for opp in TARGET_OPPONENTS:
        s_base = float(np.mean(scores["base_old"][opp]))
        s_rig = float(np.mean(scores["only_new_rigid"][opp]))
        s_min = float(np.mean(scores["only_new_mind"][opp]))
        s_both = float(np.mean(scores["both_new"][opp]))

        eff_rigid = s_rig - s_base
        eff_mind = s_min - s_base

        lines.append(
            f"| **{opp}** | {s_base:.4f} | {s_rig:.4f} | {s_min:.4f} | {s_both:.4f} | "
            f"{eff_rigid:+.4f} | {eff_mind:+.4f} |\n"
        )

    out_md = Path("ZDB_phase2b_ablation.md")
    with open(out_md, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print("".join(lines))
    print(f"Saved to {out_md} in {time.time() - t0:.1f}s\n")
    return scores

if __name__ == "__main__":
    run_phase_2b()
