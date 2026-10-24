## What

Adds **ZeroResp**, an adaptive long-memory strategy for the iterated Prisoner's Dilemma (implementation revision **v2.2**).

## Why

ZeroResp combines:

1. **Dynamic epoch extension** — retaliation debt keeps the epoch open until compensated.
2. **Short adaptive retaliation buffer** (delay **1–2**, collapse to **1** under hostility) — reduces cascade wars while remaining responsive to soft-majority / Downing-style opponents.
3. **Noise-aware forgiveness** — echo-forgive after own strikes; limited one-shot forgive after long clean mutual cooperation.
4. **Deadlock recovery** — break CD↔DC alternation spirals by offering cooperation.
5. **Red line** — permanent defection after systemic abuse (dynamic threshold 2–3).
6. **Anti-raider** — late-game exploit patterns trigger an immediate ban.
7. **Smart finite-horizon harvest / grim probe** — only when match length is known; cautious against never-defectors.

### Pre-submission evidence (external sandbox)

| Setting | Result |
|---------|--------|
| Higher League Top-40 · 400×2 · 7 seeds | **avg rank #2** (avg/r ≈ 2.760); best seed **#1** |
| Endurance Top-40 · 1501 turns · 5 seeds | stable **#2–#3** (avg rank 2.40) |
| H2H vs Omega TFT · 1000 / 5000 turns | mutual coop ~99.7–99.9%; near-parity scores |
| Survival elimination to Top-5 | **#1 every round**, final avg/r ≈ 3.000 |

Details and CSV aggregates ship in the companion package under `benchmarks/`.

## How to test

```bash
pytest axelrod/tests/strategies/test_zeroresp.py -q
# or
python -m unittest axelrod.tests.strategies.test_zeroresp -v
```

Smoke check:

```python
import axelrod as axl
m = axl.Match((axl.ZeroResp(), axl.TitForTat()), turns=100, seed=0)
m.play()
print(m.final_score())
```

## Coverage

- First move, cooperator / defector / TFT / alternator paths
- Seed reproducibility for stochastic delays
- Reset / clone init kwargs
- Buffered (non-immediate) retaliation
- Unknown match length disables end-game harvest

## Risks

- Stochastic → seed-dependent trajectories (standard for the library)
- Uses known match length when available (`makes_use_of` length via attribute access)
- Not a memory-one strategy (`memory_depth: inf`)
- Under sustained channel noise (1–3%) placement drops relative to Omega TFT

## Breaking

No — additive strategy only. No migration.
