# ZeroResp

**Adaptive strategy for the Iterated Prisoner's Dilemma**  
Version **2.2** · Compatible with [Axelrod-Python](https://github.com/Axelrod-Python/Axelrod)

[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Axelrod](https://img.shields.io/badge/axelrod-4.x-green.svg)](https://axelrod.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Upstream PR](https://img.shields.io/badge/Axelrod%20PR-1496-blue.svg)](https://github.com/Axelrod-Python/Axelrod/pull/1496)

**Upstream submission:** [Axelrod-Python/Axelrod#1496](https://github.com/Axelrod-Python/Axelrod/pull/1496) — ZeroResp + ZeroResp v2 (rev 2.2)

ZeroResp is a long-memory state-machine strategy designed for tournament evaluation: delayed adaptive retaliation, epoch-based debt accounting, noise-tolerant forgiveness, deadlock recovery, and cautious finite-horizon end-game logic.

---

## Highlights

| Property | Value |
|----------|--------|
| Class name | `ZeroResp` |
| Memory | Infinite (`memory_depth: inf`) |
| Stochastic | Yes (short retaliation delay 1–2; end-game probe) |
| Uses match length | Yes, when finite (`match_attributes["length"]`) |
| Source inspection / state manipulation | No |

---

## Pre-submission benchmarks

Results from an independent PD sandbox (Top-40 pool: classic jailers, Axelrod elites, and family variants). Full tables: [`benchmarks/RESULTS.md`](benchmarks/RESULTS.md).

### Higher League (Stage 1)

- **Pool:** 40 strategies  
- **Match length:** 400 rounds · **reps:** 2 · **seeds:** 7  

| Rank (avg) | Strategy | Avg score / round | Coop % |
|------------|----------|-------------------|--------|
| **#2** | **ZeroResp v2.2** | **2.760** | **79.3%** |
| #1 | Omega TFT | 2.761 | 79.8% |
| #3 | ZeroResp v2.1 | 2.758 | 79.8% |
| #4 | Generous TFT | 2.721 | 87.0% |

Best single seed (42): **#1 / 40** (avg 2.760, win rate 79.5%).

### Deep validation (summary)

| Block | Setting | Outcome for ZeroResp v2.2 |
|-------|---------|---------------------------|
| H2H titans | vs Omega TFT, 1000 & 5000 turns | Near-ideal mutual C (~2.999 avg/r); tiny edge via end-game |
| Endurance | Top-40 × 1501 × 5 seeds | Stable **#2–#3** (avg rank 2.40); no memory collapse |
| Noise | 0% / 1% / 3% flip noise | Strong at 0%; degrades under sustained 1–3% noise |
| Survival league | Eliminate bottom-5 until Top-5 | **#1 every round**; final avg/r ≈ 3.000, coop ≈ 99.5% |

**Strengths:** elite placement (#1–#3), clean H2H with Omega TFT, survival champion in cooperator markets.  
**Limitation:** channel noise 1–3% hurts more than Omega TFT; not claimed as noise-optimal.

---

## Quick start

```bash
pip install axelrod
```

```python
import axelrod as axl
from zeroresp import ZeroResp

match = axl.Match((ZeroResp(), axl.TitForTat()), turns=200, seed=0)
match.play()
print(match.final_score())
# → e.g. (600, 600) under mutual cooperation
```

### Unit tests

```bash
python -m unittest tests.test_zeroresp -v
```

---

## Algorithm (v2.2)

1. **Dynamic epochs** (`base_epoch=25`) — systemic counters reset only when debt and the retaliation queue are empty.  
2. **Short adaptive buffer** — retaliate after **1–2** turns (delay **1** under hostility / late pressure).  
3. **Noise-aware forgiveness** — echo-forgive after own strike; limited one-shot forgive after long clean peace.  
4. **Deadlock break** — detect CD↔DC alternation; offer cooperation to exit spirals.  
5. **Red line** — permanent `D` after 2–3 systemic abuse events (threshold tightens under hostility).  
6. **Anti-raider** — ≥2 late-game opponent defects → immediate red line.  
7. **Smart harvest / grim probe** — only with known finite length and short remaining horizon; cautious vs never-defectors.

---

## Repository layout

```
.
├── zeroresp.py                 # Canonical strategy module
├── tests/test_zeroresp.py      # Standalone unit tests
├── axelrod/
│   ├── strategies/zeroresp.py  # Drop-in for Axelrod-Python
│   └── tests/strategies/...
├── benchmarks/
│   ├── RESULTS.md              # Commission-ready summary
│   └── data/                   # Aggregate rankings & executive summary
├── REGISTRATION.md             # How to register in Axelrod
├── PR_BODY.md                  # Pull-request template
├── LICENSE
└── README.md
```

---

## Axelrod-Python submission status

| Item | Link / status |
|------|----------------|
| Upstream PR | [**#1496**](https://github.com/Axelrod-Python/Axelrod/pull/1496) (open, CI re-running after rev 2.2) |
| Superseded PR | [#1495](https://github.com/Axelrod-Python/Axelrod/pull/1495) closed (merged into #1496) |
| Contributing guide | [Adding a strategy](https://axelrod.readthedocs.io/en/stable/tutorials/contributing/strategy/index.html) |

Local drop-in copies live under `axelrod/` for offline inspection. Registration snippets: [`REGISTRATION.md`](REGISTRATION.md).

---

## Classifier

| Key | Value |
|-----|--------|
| `memory_depth` | `inf` |
| `stochastic` | `True` |
| `long_run_time` | `False` |
| `inspects_source` | `False` |
| `manipulates_source` | `False` |
| `manipulates_state` | `False` |

---

## Parameter

| Name | Default | Meaning |
|------|---------|---------|
| `base_epoch` | `25` | Clean epoch length before systemic reset |

---

## Author

**Evreu1pro** · [github.com/Evreu1pro](https://github.com/Evreu1pro)

Prepared as a professional submission package for independent evaluation and possible inclusion in public strategy lists / Axelrod-Python.

## License

MIT — see [LICENSE](LICENSE).
