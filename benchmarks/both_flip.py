"""Both-flip noise channel: action flip + perception flip, symmetric, seeded.

This is NOT axelrod's `noise=`. Axelrod flips only the realised action, and
only AFTER `strategy()` has already returned (`Match.simultaneous_play`), so
a player never misperceives its opponent. Perception flip must be injected
BEFORE `strategy()` runs, which means replacing the opponent object the
strategy receives with a view.

Channel definition (registered in benchmarks/preregistrations/T1_both_flip.md,
section 2):

* Action channel. After both strategies return, each realised action is
  flipped independently with probability `p_action`. This is what the world
  records, and what each player stores as its OWN play (`_history._plays`).
  A player therefore sees its own action flips (this is the normal Axelrod
  action-noise channel).

* Perception channel. Each player's OBSERVATION of the opponent's realised
  action is flipped independently with probability `p_perception`. The flip
  is drawn once per turn per observer and stored, so a past observation does
  not change when re-read. The strategy is handed a `PerceptionView` of the
  opponent whose `.history` returns the flipped plays.

* Symmetry. Both players are treated identically: each one's action is
  flipped, and each one misperceives the other.

* Determinism. All flip bits come from a single `random.Random(seed)` drawn
  in a fixed order (action p1, action p2, perception p1-of-p2, perception
  p2-of-p1) per turn. Two runs with the same seed produce identical matches,
  and two different variants played with the same seed see the SAME flip
  stream, so paired comparisons stay paired.

* Truth kept. Each player's own `_history._plays` store realised actions and
  its `_history._coplays` store the opponent's realised actions, exactly as
  in Axelrod. Only the observer-facing view is distorted. Strategies that
  read `history.state_distribution` (metadata, not an observation channel)
  see the undistorted truth; this matches Axelrod's own treatment and is
  documented rather than hidden.
"""
from __future__ import annotations

import random
from typing import List, Tuple

import axelrod as axl

C, D = axl.Action.C, axl.Action.D
Action = axl.Action


class _FlippedHistory(axl.history.History):
    """A real History whose `_plays` are the observer's perception.

    It subclasses History so `opponent.history == self.history` keeps working
    (History.__eq__ rejects foreign types with a TypeError, and Axelrod's own
    strategies do that comparison). `_plays` are the observer's perception of
    the opponent; `_coplays` are the opponent's perception of the observer,
    which is what the opponent's own History would carry.
    """

    __slots__ = ()

    def __init__(self, plays, coplays):
        super().__init__(plays=list(plays), coplays=list(coplays))


class PerceptionView:
    """Proxy for the opponent: `.history` is perception-flipped.

    Every other attribute is forwarded to the real opponent, so strategies
    reading `opponent.name`, `opponent.classifier`, `opponent.cooperations`
    etc. keep working. Only the observation channel is distorted.
    """

    def __init__(self, real, observed_plays, observed_coplays):
        object.__setattr__(self, "_real", real)
        object.__setattr__(self, "_obs", observed_plays)
        object.__setattr__(self, "_obs_cop", observed_coplays)

    @property
    def history(self):
        return _FlippedHistory(object.__getattribute__(self, "_obs"),
                               object.__getattribute__(self, "_obs_cop"))

    @property
    def cooperations(self):
        return self.history.cooperations

    @property
    def defections(self):
        return self.history.defections

    @property
    def state_distribution(self):
        return self.history.state_distribution

    def __getattr__(self, name):
        return getattr(object.__getattribute__(self, "_real"), name)


def play_both_flip(p1, p2, turns: int, p_action: float, p_perception: float,
                   seed: int, match_attributes=None
                   ) -> List[Tuple[Action, Action]]:
    """Play one both-flip match. Returns realised (s1, s2) per turn.

    `match_attributes` is passed to both players exactly as Axelrod's Match
    does (`length`, `game`, `noise`). `noise` is reported as `p_action` only
    so strategies reading `match_attributes["noise"]` see a sane value; the
    perception channel is not visible there, by design.
    """
    rng = random.Random(seed)
    if match_attributes is None:
        match_attributes = {"length": turns, "game": axl.Game(), "noise": 0.0}

    for p in (p1, p2):
        p.reset()
        p.set_match_attributes(**match_attributes)
        if axl.Classifiers["stochastic"](p):
            p.set_seed(rng.randrange(2**31))

    obs_of_p2: List[Action] = []  # what p1 sees of p2's actions
    obs_of_p1: List[Action] = []  # what p2 sees of p1's actions
    # A view's History._plays are the observer's perception of the subject;
    # .coplays are the subject's perception of the observer, matching what a
    # real History would carry for that subject.
    view_of_p2 = PerceptionView(p2, obs_of_p2, obs_of_p1)
    view_of_p1 = PerceptionView(p1, obs_of_p1, obs_of_p2)

    result: List[Tuple[Action, Action]] = []
    for _ in range(turns):
        # Strategies read the perception-flipped view of the opponent.
        s1 = p1.strategy(view_of_p2)
        s2 = p2.strategy(view_of_p1)

        # Action channel: flip realised actions.
        if rng.random() < p_action:
            s1 = s1.flip()
        if rng.random() < p_action:
            s2 = s2.flip()

        # Perception channel: each observer misperceives, drawn once per turn.
        o2_for_p1 = s2.flip() if rng.random() < p_perception else s2
        o1_for_p2 = s1.flip() if rng.random() < p_perception else s1

        # Store truth for each player (own realised action, opponent realised).
        p1.update_history(s1, s2)
        p2.update_history(s2, s1)
        obs_of_p2.append(o2_for_p1)
        obs_of_p1.append(o1_for_p2)
        result.append((s1, s2))

    return result


def build(cls, seed, role, **kwargs):
    """Construct a player with its initial RNG state fixed by (seed, role).

    `Player.__init__` (and ZeroResp's `warmth`) draws from the module-level
    generator when no seed is given. Seeding it right before construction
    makes the initial state depend only on (seed, role), not on construction
    order. See benchmarks/preregistrations/C0_ladder_off_equivalence.md.
    """
    from axelrod import _module_random as mr
    mr.seed(seed * 2 + role)
    return cls(**kwargs)
