"""Diagnose Random regression: why does v5.6 lose 0.19 SPT against Random?"""
from __future__ import annotations

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import axelrod as axl
from zdb_phase0 import get_variant_player

def diagnose_random():
    print("=" * 65)
    print("DIAGNOSING RANDOM REGRESSION (v5.3 vs v5.6)")
    print("=" * 65)

    p53 = get_variant_player("v5.3")
    p56 = get_variant_player("v5.6")

    # Match at 5% noise with seed 42
    m53 = axl.Match((p53, axl.Random()), turns=200, seed=42, noise=0.05)
    m53.play()

    m56 = axl.Match((p56, axl.Random()), turns=200, seed=42, noise=0.05)
    m56.play()

    print(f"Seed 42 | v5.3 score: {m53.final_score()} (SPT: {sum(x[0] for x in m53.scores())/200:.3f})")
    print(f"Seed 42 | v5.6 score: {m56.final_score()} (SPT: {sum(x[0] for x in m56.scores())/200:.3f})")

    # Metrics on internal states
    print("\nInternal state comparison:")
    print(f"v5.3: my_D={p53.my_D}, debt={p53.debt}, is_red_line={p53.is_red_line}, state={p53._state}")
    print(f"v5.6: my_D={p56.my_D}, debt={p56.debt}, is_red_line={p56.is_red_line}, state={p56._state}")
    print(f"v5.6: is_rigid={p56.is_rigid}, nl_evidence={p56.nl_evidence}, echo_forgive={p56.echo_forgive}")

    # Inspect fraction of C vs D played
    c_53 = sum(1 for a in p53.history if a == axl.Action.C)
    d_53 = sum(1 for a in p53.history if a == axl.Action.D)

    c_56 = sum(1 for a in p56.history if a == axl.Action.C)
    d_56 = sum(1 for a in p56.history if a == axl.Action.D)

    print(f"\nMoves played:")
    print(f"v5.3 played: {c_53} C, {d_53} D ({d_53/200*100:.1f}% D)")
    print(f"v5.6 played: {c_56} C, {d_56} D ({d_56/200*100:.1f}% D)")

if __name__ == "__main__":
    diagnose_random()
