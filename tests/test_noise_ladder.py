"""Unit tests for the v5.3 noise_ladder feature (features.noise_ladder).

Run: python -m unittest tests.test_noise_ladder -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import axelrod as axl

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from zeroresp import Features, ZeroResp  # noqa: E402

C, D = axl.Action.C, axl.Action.D


def _match(player, opponent, turns, seed=42, noise=0.0, length=None):
    attrs = {"length": length} if length is not None else None
    m = axl.Match((player, opponent), turns=turns, seed=seed, noise=noise,
                  match_attributes=attrs)
    m.play()
    return m


def _by_name(name):
    by = {}
    for s in axl.strategies:
        by[s.__name__] = s
        by.setdefault(s.name, s)
    return by[name]()


class TestNoiseLadder(unittest.TestCase):
    def _ladder(self, **over):
        kw = {"noise_ladder": True}
        kw.update(over)
        return ZeroResp(features=Features(**kw))

    def test_flag_off_ladder_dormant(self):
        p = ZeroResp(features=Features(noise_ladder=False))
        _match(p, axl.MockPlayer(actions=[C] * 6 + [D] + [C] * 40),
               turns=40, seed=1, length=200)
        self.assertEqual(p.nl_evidence, 0)
        self.assertEqual(p.nl_scheduled, [])
        self.assertEqual(p.nl_pardoned, 0)

    def test_deterministic_with_same_seed(self):
        def once(seed):
            p = self._ladder()
            m = _match(p, axl.MockPlayer(actions=[C] * 5 + [D] + [C] * 50),
                       turns=60, seed=seed, length=200)
            return tuple(a for a, _ in m.scores())
        self.assertEqual(once(7), once(7))

    def test_single_defection_pardoned_under_channel_noise(self):
        # Помилование возможно только после доказанного канального шума,
        # поэтому матч идёт с 5% шумом; перебираем сиды, пока не найдём
        # вариант с нашим флипом и последующим помилованием.
        for seed in range(1, 9):
            p = self._ladder()
            _match(p, axl.MockPlayer(actions=[C] * 5 + [D] + [C] * 60),
                   turns=70, seed=seed, noise=0.05, length=200)
            if p.nl_my_flips >= 1 and p.nl_pardoned >= 1:
                self.assertGreaterEqual(p.nl_debt_ledger, 1)
                break
        else:
            self.fail("no pardon observed in seeds 1..8 at 5% noise")

    def test_persistent_defector_hits_red_line(self):
        p = self._ladder()
        _match(p, axl.MockPlayer(actions=[D] * 30), turns=30, seed=4, length=200)
        self.assertTrue(p.is_red_line)

    def test_ladder_dormant_at_zero_noise(self):
        # Без доказанного канального шума (0% noise) флаг on обязан дать
        # траекторию, идентичную v5.2 (флаг off), на «умеренных» оппонентах.
        import hashlib
        import json

        def traj(flag, opp_name):
            p = ZeroResp(features=Features(noise_ladder=flag))
            _match(p, _by_name(opp_name), turns=200, seed=42, length=200)
            blob = json.dumps([str(a) for a in p.history]).encode()
            return hashlib.sha256(blob).hexdigest()

        for opp in ("Alternator", "TrickyCooperator", "Calculator", "Random"):
            self.assertEqual(traj(True, opp), traj(False, opp),
                             f"ladder must be dormant at 0% vs {opp}")

    def test_ladder_defers_first_unexplained_defection(self):
        # Детерминированный unit-тест ядра (теория I): первая улика прощается,
        # вторая планирует ОТЛОЖЕННОЕ возмездие со случайной задержкой; удар
        # не немедленный, а чистому оппоненту на исполнении будет помилован.
        p = self._ladder()
        p.nl_my_flips = 1                       # канал «доказан»
        p.opp_len, p.opp_defects = 10, 0        # coop 1.0 -> не агрессивный
        p._nl_ladder(20)                         # evidence 1 -> прощение
        self.assertEqual(p.nl_pardoned, 1)
        self.assertEqual(p.nl_debt_ledger, 1)
        self.assertEqual(p._pending_reason, "nl_deferred")
        self.assertEqual(p.nl_scheduled, [])     # на первой улике плана нет
        self.assertEqual(p.queue, [])
        p._nl_ladder(21)                         # evidence 2 -> план возмездия
        self.assertEqual(p.nl_evidence, 2)
        self.assertEqual(p.nl_pardoned, 2)
        self.assertEqual(p.nl_debt_ledger, 2)
        self.assertEqual(p._pending_reason, "nl_deferred")
        self.assertEqual(p.queue, [])            # немедленного удара нет
        self.assertEqual(len(p.nl_scheduled), 1)
        self.assertEqual(p.nl_scheduled[0]["kind"], "strike")
        self.assertGreaterEqual(p.nl_scheduled[0]["turn"], 21 + p.NL_DELAY_MIN)

    def test_strikes_only_via_scheduled_pardonable_plan(self):
        # Теория I: немедленных ударов по необъяснимым D нет; план возмездия
        # ровно один на окно, и исполняется он позже (в strategy) - чистому
        # помилование, грязному удар через очередь.
        for opp_len, opp_defects in ((60, 3), (60, 30), (60, 48)):
            p = self._ladder()
            p.nl_my_flips = 1
            p.opp_len, p.opp_defects = opp_len, opp_defects
            for step in range(20, 30):
                p._pending_reason = None
                p._nl_ladder(step)
                self.assertEqual(p.queue, [],
                                 f"queue filled from ladder at step {step}")
                self.assertLessEqual(len(p.nl_scheduled), 1)

    def test_ladder_redlines_hostile_at_three(self):
        p = self._ladder()
        p.nl_my_flips = 1
        p.opp_len, p.opp_defects = 60, 48       # coop 0.20 < 0.40 -> вражд
        p._nl_ladder(20)
        p._nl_ladder(21)
        p._nl_ladder(22)
        self.assertTrue(p.is_red_line,
                        "3 unexplained D vs hostile co-op must enter red line")

    def test_own_flips_feed_noise_est(self):
        for seed in range(1, 9):
            p = self._ladder()
            _match(p, axl.MockPlayer(actions=[C] * 80),
                   turns=80, seed=seed, noise=0.1, length=200)
            if p.nl_my_flips >= 1:
                self.assertGreater(p.p_noise_est, 0.0)
                break
        else:
            self.fail("no own flip observed in seeds 1..8 at 10% noise")

    def test_balance_negative_vs_defector(self):
        p = self._ladder()
        _match(p, axl.Defector(), turns=50, seed=6, length=200)
        self.assertLess(p.nl_balance, 0)

    def test_first_move_and_classifier_untouched(self):
        p = self._ladder()
        self.assertEqual(p.strategy(axl.Defector()), C)
        self.assertEqual(p.classifier["memory_depth"], float("inf"))
        self.assertTrue(p.classifier["stochastic"])


if __name__ == "__main__":
    unittest.main()
