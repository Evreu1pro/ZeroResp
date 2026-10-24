"""Trajectory-equivalence checker for ZeroResp refactors.

Runs a fixed battery of matches and hashes every full trajectory.
Used to prove a code change is behavior-preserving: run with --out before
the edit and --compare after; hashes must match exactly.

Also has --instrument mode: counts executions of suspected-dead branches
inside ZeroResp (via an instrumented subclass) over the same battery.

The module-level axelrod RNG is seeded and construction order is fixed,
so hashes are reproducible across processes.

Examples:
    python benchmarks/trajectory_check.py --instrument
    python benchmarks/trajectory_check.py --out benchmarks/results/traj_before.json
    python benchmarks/trajectory_check.py --compare benchmarks/results/traj_before.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

import axelrod as axl  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from zeroresp import Features, ZeroResp  # noqa: E402

C, D = axl.Action.C, axl.Action.D  # noqa: F841 - used by instrumented subclass

RNG_SEED = 2026
NOISES = [0.0, 0.01, 0.02, 0.05, 0.1]
SEEDS = [42, 43, 44, 45]
TURNS = 200

OPPONENT_NAMES = [
    "Cooperator", "Defector", "TitForTat", "Grudger", "Random", "Alternator",
    "TitFor2Tats", "TwoTitsForTat", "SuspiciousTitForTat", "Bully",
    "GTFT", "SoftJoss", "Prober", "Prober2", "Prober3", "HardProber",
    "Calculator", "Handshake", "OnceBitten", "Punisher",
    "TrickyCooperator", "TrickyDefector", "GrudgerAlternator",
    "FirstByGrofman", "FirmButFair", "SoftGrudger", "ContriteTitForTat",
    "SlowTitForTwoTats2", "Gradual", "ShortMem",
    "HardTitForTat", "HardTitFor2Tats",
    "ZDExtort2", "ZDExtort4", "ZDExtortion", "ZDGTFT2",
    "CollectiveStrategy", "TF1", "TF2", "Predator",
    "GradualKiller", "Winner21", "Aggravater", "UsuallyDefects",
    "Detective", "DoubleCrosser", "EasyGo", "Hopeless",
]

# Smaller opponent set for feature-flag variants (each variant re-runs these).
VARIANT_OPPONENT_NAMES = [
    "Cooperator", "Defector", "TitForTat", "Grudger", "Alternator",
    "Prober", "Calculator", "Handshake", "ZDExtort4", "CollectiveStrategy",
    "Gradual", "Random",
]

VARIANT_NOISE = 0.05
VARIANT_SEEDS = [42, 43]

VARIANT_FEATURES = [
    ("v_noise_extra", {"noise_extra": True}),
    ("v_contrite_off", {"contrite_full": False}),
    ("v_noise_adaptive_off", {"noise_adaptive": False}),
    ("v_generous_off", {"generous": False}),
    ("v_no_cooldown", {"red_line_cooldown": False}),
    ("v_apology_off", {"apology": False}),
    ("v_est_endgame_off", {"estimated_endgame": False}),
    ("v_no_jitter", {"harvest_jitter": False}),
]


def resolve_opponents(names):
    by_name = {}
    for s in axl.strategies:
        by_name[s.__name__] = s
        by_name.setdefault(s.name, s)
    missing = [n for n in names if n not in by_name]
    if missing:
        raise SystemExit(f"Unknown strategies: {missing}")
    return [by_name[n] for n in names]


def play_one(zero_resp_factory, opp_cls, noise, seed):
    p1 = zero_resp_factory()
    p2 = opp_cls()
    match = axl.Match(
        (p1, p2), turns=TURNS, seed=seed, noise=noise,
        match_attributes={"length": TURNS},
    )
    match.play()
    scores = match.scores()
    my_total = sum(s[0] for s in scores)
    opp_total = sum(s[1] for s in scores)
    return (p1.history[:], p2.history[:], my_total, opp_total)


def run_battery(zero_resp_cls=None, hash_it=True):
    """Plays the fixed battery; returns dict label -> trajectory hash."""
    zcls = zero_resp_cls if zero_resp_cls is not None else ZeroResp
    results = {}
    opponents = resolve_opponents(OPPONENT_NAMES)
    variant_opponents = resolve_opponents(VARIANT_OPPONENT_NAMES)

    def record(label, payload):
        if not hash_it:
            return
        blob = json.dumps([label] + list(payload),
                          default=lambda o: str(o)).encode()
        results[label] = hashlib.sha256(blob).hexdigest()[:16]

    def factory(features=None, use_profiles=True, base_epoch=25):
        def make():
            return zcls(features=Features() if features is None
                        else Features(**features),
                        use_profiles=use_profiles,
                        base_epoch=base_epoch)
        return make

    # Main battery: default ZeroResp vs every opponent + self-match.
    for noise in NOISES:
        for seed in SEEDS:
            for opp in opponents:
                key = f"default|{opp.__name__}|n={noise}|s={seed}"
                record(key, play_one(factory(), opp, noise, seed))
            key = f"default|SELF|n={noise}|s={seed}"
            record(key, play_one(factory(), zcls, noise, seed))

    # Feature variants on the smaller opponent set.
    variant_factories = [
        (f"v_{name}", factory(feats)) for name, feats in VARIANT_FEATURES
    ] + [
        ("v_no_profiles", factory(use_profiles=False)),
        ("v_epoch10", factory(base_epoch=10)),
    ]
    for vname, f in variant_factories:
        for seed in VARIANT_SEEDS:
            for opp in variant_opponents:
                key = f"{vname}|{opp.__name__}|n={VARIANT_NOISE}|s={seed}"
                record(key, play_one(f, opp, VARIANT_NOISE, seed))

    return results


def instrumented_run():
    counts = {"on_defect_total": 0, "b1_intC_realD": 0, "b2_bad_standing": 0,
              "b3_noise_recheck": 0, "b4_contrite": 0}

    class Instrumented(ZeroResp):
        def _on_defect(self, step, opp_action):
            counts["on_defect_total"] += 1
            if self._intended_prev == C and self._realized_prev == D:
                counts["b1_intC_realD"] += 1
            if self._bad_standing:
                counts["b2_bad_standing"] += 1
            if (self.history and self.history[-1] != self._intended_prev
                    and self.history[-1] == D):
                counts["b3_noise_recheck"] += 1
            if self._contrite:
                counts["b4_contrite"] += 1
            return super()._on_defect(step, opp_action)

    run_battery(zero_resp_cls=Instrumented, hash_it=False)
    return counts


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--instrument", action="store_true",
                    help="count suspected-dead branch executions")
    ap.add_argument("--out", help="write trajectory hashes to this JSON")
    ap.add_argument("--compare", help="compare against a previous JSON")
    args = ap.parse_args()

    axl._module_random.seed(RNG_SEED)

    if args.instrument:
        print(json.dumps(instrumented_run(), indent=2))
        return

    hashes = run_battery()

    if args.out:
        Path(args.out).write_text(json.dumps(hashes, indent=2, sort_keys=True),
                                  encoding="utf-8")
        print(f"{len(hashes)} trajectory hashes written to {args.out}")

    if args.compare:
        old = json.loads(Path(args.compare).read_text(encoding="utf-8"))
        missing = sorted(set(old) - set(hashes))
        added = sorted(set(hashes) - set(old))
        changed = sorted(k for k in set(old) & set(hashes)
                         if old[k] != hashes[k])
        print(f"compared {len(hashes)} hashes: "
              f"{len(changed)} changed, {len(missing)} missing, "
              f"{len(added)} added")
        for k in changed[:20]:
            print(f"  CHANGED {k}: {old[k]} -> {hashes[k]}")
        for k in (missing + added)[:20]:
            print(f"  KEY MISMATCH {k}")
        if changed or missing or added:
            sys.exit(1)
        print("OK: all trajectories identical")


if __name__ == "__main__":
    main()
