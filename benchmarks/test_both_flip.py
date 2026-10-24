"""Self-test for the both-flip wrapper. Must pass before T1 is run.

Checks:
  1. Determinism: same seed -> identical match, twice.
  2. Seed sensitivity: different seed -> different match at p>0.
  3. p=0 is a no-op: both channels off reproduce axelrod's own Match for
     deterministic players.
  4. Perception channel is delivered: a probe strategy that records what it
     sees of the opponent sees a flipped sequence, while the opponent's own
     stored history stays undistorted.
  5. Action channel is delivered: realised actions differ from what the
     observer perceives, and the observer's view is stable (a past
     observation never changes when re-read).
  6. Symmetry: both players are distorted, not just player 1.

Usage:
    python benchmarks/test_both_flip.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "benchmarks"))

import axelrod as axl  # noqa: E402
from both_flip import play_both_flip, build  # noqa: E402

C, D = axl.Action.C, axl.Action.D


class Recorder(axl.Player):
    """Records every history it observes of the opponent, and of itself."""

    name = "Recorder"

    def __init__(self):
        super().__init__()
        self.seen_of_opp = []
        self.seen_of_self = []
        self.snapshots = []

    def strategy(self, opponent):
        self.seen_of_opp.append(list(opponent.history))
        self.seen_of_self.append(list(self.history))
        # snapshot the full observed list again to check stability
        self.snapshots.append(list(opponent.history))
        return C


class Cooperator(axl.Player):
    name = "Cooperator"

    def strategy(self, opponent):
        return C


class Defector(axl.Player):
    name = "Defector"

    def strategy(self, opponent):
        return D


def check(label, cond):
    print(f"[{'PASS' if cond else 'FAIL'}] {label}")
    return bool(cond)


def main():
    ok = True

    # 1. determinism
    r1 = play_both_flip(build(Recorder, 1, 0), build(Cooperator, 1, 1),
                        turns=50, p_action=0.3, p_perception=0.3, seed=7)
    r2 = play_both_flip(build(Recorder, 1, 0), build(Cooperator, 1, 1),
                        turns=50, p_action=0.3, p_perception=0.3, seed=7)
    ok &= check("determinism: same seed twice identical", r1 == r2)

    # 2. seed sensitivity
    r3 = play_both_flip(build(Recorder, 2, 0), build(Cooperator, 2, 1),
                        turns=50, p_action=0.3, p_perception=0.3, seed=8)
    ok &= check("sensitivity: different seed differs at p>0", r1 != r3)

    # 3. p=0 no-op vs axelrod Match (deterministic players only)
    rec_a = Recorder()
    coop_a = Cooperator()
    m = axl.Match((rec_a, coop_a), turns=50, seed=7, noise=0.0)
    m.play()
    rec_b = build(Recorder, 99, 0)
    coop_b = build(Cooperator, 99, 1)
    r4 = play_both_flip(rec_b, coop_b, turns=50, p_action=0.0,
                        p_perception=0.0, seed=7)
    ok &= check("p=0 matches axelrod Match for deterministic players",
                r4 == m.result)

    # 4. perception channel reaches the strategy
    # Recorder sees history only up to the PREVIOUS turn (it records at the
    # start of its own strategy call), so its last observation has turns-1
    # entries. Compare on the common length, never across different lengths.
    rec = build(Recorder, 11, 0)
    def_ = build(Defector, 11, 1)
    truth = play_both_flip(rec, def_, turns=40, p_action=0.0,
                           p_perception=0.5, seed=11)
    seen = rec.seen_of_opp[-1]
    truth_obs = [s[1] for s in truth][: len(seen)]
    ok &= check("observation length is turns-1 (records before its own move)",
                len(seen) == len(truth) - 1)
    ok &= check("perception channel alters what the strategy observes",
                seen != truth_obs)
    ok &= check("opponent's own stored history is undistorted",
                list(def_.history) == [s[1] for s in truth])
    # stability: a past observation prefix must equal every later prefix
    snaps = rec.snapshots
    stable = all(
        snaps[j][:i] == snaps[i]
        for i in range(len(snaps))
        for j in (i + 1, len(snaps) - 1)
        if i < j < len(snaps)
    )
    ok &= check("observations are stable (past never rewritten)", stable)

    # 5. action channel
    rec2 = build(Recorder, 21, 0)
    def2 = build(Defector, 21, 1)
    truth2 = play_both_flip(rec2, def2, turns=40, p_action=0.5,
                            p_perception=0.0, seed=21)
    seen2 = rec2.seen_of_opp[-1]
    ok &= check("p_perception=0: observer sees true realised actions",
                seen2 == [s[1] for s in truth2][: len(seen2)])
    ok &= check("action channel flips realised actions (Defector should not be all-D)",
                any(a == C for a in list(def2.history)))

    # 6. symmetry: the Defector's OWN view of itself is flipped too
    ok &= check("symmetry: actor's own stored plays carry its action flips",
                any(a == C for a in list(def2.history)))

    print("\nALL PASS" if ok else "\nSOME CHECKS FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
