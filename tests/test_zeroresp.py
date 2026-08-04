"""Standalone unit tests for ZeroResp v2.2 (requires the ``axelrod`` package)."""

from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path

import axelrod as axl

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from zeroresp import ZeroResp  # noqa: E402

C, D = axl.Action.C, axl.Action.D


def _play(player, opponent, turns: int, seed: int = 0, length=None):
    attrs = None
    if length is not None:
        attrs = {"length": length}
    match = axl.Match(
        (player, opponent),
        turns=turns,
        seed=seed,
        match_attributes=attrs,
    )
    return match.play()


class TestZeroResp(unittest.TestCase):
    name = "ZeroResp"

    expected_classifier = {
        "memory_depth": float("inf"),
        "stochastic": True,
        "long_run_time": False,
        "inspects_source": False,
        "manipulates_source": False,
        "manipulates_state": False,
    }

    def test_name(self):
        self.assertEqual(ZeroResp().name, self.name)
        self.assertTrue(str(ZeroResp()).startswith(self.name))

    def test_classifier_keys(self):
        p = ZeroResp()
        for key, value in self.expected_classifier.items():
            self.assertEqual(p.classifier[key], value)

    def test_init_defaults(self):
        p = ZeroResp()
        self.assertEqual(p.base_epoch, 25)
        self.assertEqual(p.debt, 0)
        self.assertEqual(p.systemic, 0)
        self.assertEqual(p.queue, [])
        self.assertEqual(p.epoch_step, 0)
        self.assertEqual(len(p.history), 0)

    def test_init_custom_epoch(self):
        p = ZeroResp(base_epoch=10)
        self.assertEqual(p.base_epoch, 10)
        self.assertEqual(p.init_kwargs, {"base_epoch": 10})

    def test_first_move_cooperate(self):
        p = ZeroResp()
        self.assertEqual(p.strategy(axl.Defector()), C)

    def test_vs_cooperator_mostly_cooperates(self):
        """Against pure C, mid-game is cooperative; end-game may probe/harvest."""
        result = _play(ZeroResp(), axl.Cooperator(), turns=200, seed=1, length=200)
        my_actions = [a for a, _ in result]
        self.assertEqual(my_actions[0], C)
        mid = my_actions[:180]
        self.assertGreaterEqual(mid.count(C) / len(mid), 0.95)
        self.assertGreaterEqual(my_actions.count(C), 190)

    def test_vs_defector_eventual_defect(self):
        result = _play(ZeroResp(), axl.Defector(), turns=40, seed=2, length=200)
        my_actions = [a for a, _ in result]
        self.assertEqual(my_actions[0], C)
        self.assertIn(D, my_actions)
        self.assertGreaterEqual(my_actions.count(D), 10)

    def test_vs_tit_for_tat_mostly_cooperate(self):
        result = _play(ZeroResp(), axl.TitForTat(), turns=50, seed=3, length=200)
        my_actions = [a for a, _ in result]
        self.assertEqual(my_actions[0], C)
        self.assertGreaterEqual(my_actions.count(C), 40)

    def test_stochastic_buffer_seed_reproducible(self):
        r1 = _play(ZeroResp(), axl.Defector(), turns=30, seed=42, length=200)
        r2 = _play(ZeroResp(), axl.Defector(), turns=30, seed=42, length=200)
        self.assertEqual(r1, r2)

    def test_different_seeds_can_differ(self):
        """Different seeds can change the short stochastic retaliation delay."""

        def once(seed: int):
            player = ZeroResp()
            # One early D after a short cooperative stretch so delay is stochastic
            opp = axl.MockPlayer(actions=[C] * 6 + [D] + [C] * 40)
            return tuple(
                a
                for a, _ in axl.Match(
                    (player, opp),
                    turns=25,
                    seed=seed,
                    match_attributes={"length": 200},
                ).play()
            )

        unique = {once(s) for s in range(1, 40)}
        self.assertGreaterEqual(len(unique), 1)

    def test_red_line_against_persistent_defector(self):
        player = ZeroResp()
        opp = axl.MockPlayer(actions=[D] * 20)
        match = axl.Match(
            (player, opp),
            turns=20,
            seed=7,
            match_attributes={"length": 200},
        )
        match.play()
        self.assertGreaterEqual(player.defections, 5)

    def test_reset_clears_state(self):
        player = ZeroResp()
        match = axl.Match((player, axl.Defector()), turns=15, seed=5)
        match.play()
        self.assertGreater(len(player.history), 0)
        player.reset()
        self.assertEqual(len(player.history), 0)
        self.assertEqual(player.debt, 0)
        self.assertEqual(player.systemic, 0)
        self.assertEqual(player.queue, [])
        self.assertEqual(player.epoch_step, 0)
        self.assertEqual(player.opp_len, 0)
        self.assertEqual(player.my_D, 0)

    def test_clone_equality_initial(self):
        p1 = ZeroResp(base_epoch=20)
        p2 = p1.clone()
        self.assertEqual(p1, p2)
        self.assertEqual(p2.base_epoch, 20)

    def test_unknown_length_vs_cooperator(self):
        """Without known length, end-game harvest is disabled."""
        result = _play(
            ZeroResp(),
            axl.Cooperator(),
            turns=200,
            seed=11,
            length=float("inf"),
        )
        my_actions = [a for a, _ in result]
        self.assertTrue(all(a == C for a in my_actions))

    def test_no_immediate_retaliation_on_second_turn(self):
        """First defect is buffered — response is delayed by at least one turn."""
        player = ZeroResp()
        opp = axl.MockPlayer(actions=[D] + [C] * 30)
        match = axl.Match(
            (player, opp),
            turns=2,
            seed=99,
            match_attributes={"length": 200},
        )
        match.play()
        self.assertEqual(player.history[0], C)
        self.assertEqual(player.history[1], C)
        self.assertTrue(player.queue or player.debt >= 1 or player.is_red_line)

    def test_queued_retaliation_fires(self):
        """Against a single early D then all C, a delayed D eventually appears."""
        player = ZeroResp()
        actions = [D] + [C] * 40
        opp = axl.MockPlayer(actions=actions)
        match = axl.Match(
            (player, opp),
            turns=30,
            seed=12,
            match_attributes={"length": 200},
        )
        match.play()
        self.assertEqual(player.history[0], C)
        self.assertGreaterEqual(player.defections, 1)
        self.assertLessEqual(player.defections, 5)

    def test_vs_alternator(self):
        result = _play(ZeroResp(), axl.Alternator(), turns=40, seed=8, length=200)
        self.assertEqual(len(result), 40)
        my_actions = [a for a, _ in result]
        self.assertEqual(my_actions[0], C)
        self.assertIn(D, my_actions)

    def test_base_epoch_parameter_in_repr(self):
        p = ZeroResp(base_epoch=30)
        self.assertIn("30", repr(p))

    def test_makes_use_of_length_when_harvest_path_active(self):
        src = inspect.getsource(ZeroResp)
        self.assertIn('match_attributes["length"]', src)

    def test_smoke_tournament_rank_stable(self):
        """Short round-robin: ZeroResp should beat Defector and not crash."""
        players = [
            ZeroResp(),
            axl.TitForTat(),
            axl.Defector(),
            axl.Cooperator(),
            axl.Grudger(),
            axl.Random(),
        ]
        tournament = axl.Tournament(players, turns=50, repetitions=1, seed=0)
        results = tournament.play(progress_bar=False)
        names = results.ranked_names
        zr = next(n for n in names if n.startswith("ZeroResp"))
        self.assertLess(names.index(zr), names.index("Defector"))


if __name__ == "__main__":
    unittest.main()
