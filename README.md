# ZeroResp — a long-memory IPD strategy with a noise ladder

[[tests](https://img.shields.io/badge/tests-passing-brightgreen)](#)
[[python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org)
[[license](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)
[[axelrod](https://img.shields.io/badge/axelrod-compatible-orange)](https://axelrod.readthedocs.io)

**ZeroResp is an Iterated Prisoner's Dilemma player built around epoch debt, delayed retaliation, noise-aware forgiveness, opening disambiguation, and finite-horizon harvest.**

`v5.3 = v5.2 + a noise ladder` that activates only after channel noise has been proven. With the ladder disabled, v5.3 is bit-for-bit v5.2.

---

### Scope & Limitations

> **Read this first.** ZeroResp's ladder is a cooperation mechanism for a noisy channel between two fallible players. It is not a shield against one-sided exploitation, and it is not a general-purpose "better than TFT".

**✅ Works in:**
- mutual channel noise ≥10%, long horizon (≥200 turns), standard PD payoffs (R=3, T=5, S=0, P=1)

**❌ Fails in:**
- **one-sided noise** (only ZeroResp perturbed, opponents clean). In that regime both v5.3 and v5.2 fall behind TitForTat and Grudger.
- **perception-flip noise.** The ladder detects its own C→D flips; if the flips are on the input side, it never activates, and the v5.3 advantage is exactly 0.00.
- **clean environments.** TitForTat ≥ ZeroResp at 0% noise on the full library (rank 12/222 for both v5.3 and v5.2).

**⚠️ Caveats:**
- Rank-neutral on the full library. At 10% noise both v5.3 and v5.2 are #2/222. The improvement is measurable in SPT, not in rank.
- `trembling-hand` at 10% is on the significance boundary (BH q=0.096). Likely needs n>30 to settle.
- External hold-out is not yet done. All reported results use the same 221-strategy pool used for tuning. This affects H1 (top-5 hold-out) only, not H2/H3/H5.

> If you need a strategy for a clean or one-sided-noise environment, use TitForTat. ZeroResp is for the mutual-noise regime.

---

### Install

```bash
pip install axelrod
pip install -e .
```

### Quick start

```python
import axelrod as axl
from zeroresp import ZeroResp

match = axl.Match((ZeroResp(), axl.TitForTat()), turns=200, seed=0)
match.play()
print(match.final_score())
```

Disable the v5.3 ladder (recover v5.2 behavior exactly):

```python
from zeroresp import Features, ZeroResp
ZeroResp(features=Features(noise_ladder=False))
```

---

### Evidence

All results use `R=3, T=5, S=0, P=1, 200 turns`, and are reproducible from `benchmarks/`.
Statistics and raw data: `docs/RESEARCH_v53.md`, `docs/BHNS_v53.md`, `docs/STRESS_v53.md`.

#### 1. Full library round-robin (222 strategies)

Score-per-turn (SPT) and rank. Round-robin over the full Axelrod library with all players subject to the same channel noise.

| Noise | v5.3 rank | v5.2 rank | v5.3 SPT | v5.2 SPT |
| :--- | :--- | :--- | :--- | :--- |
| 0% | 12 / 222 | 12 / 222 | 627.2 | 627.2 |
| 1% | 5 / 222 | 5 / 222 | 575.9 | 575.2 |
| 3% | 5 / 222 | 5 / 222 | 549.3 | 548.0 |
| 5% | 4 / 222 | 3 / 222 | 536.9 | 539.7 |
| 10% | 2 / 222 | 2 / 222 | 516.5 | 513.3 |

Reading: the dirtier the channel, the higher ZeroResp ranks. At 10% only one strategy sits above it — **Evolved ANN 5 Noise 05**, an evolutionary machine trained specifically for noise. Every handwritten family (TFT, Grudger, ZD, Prober) is below.

#### 2. Field pack (32 strategies)

Mean SPT over the field pack, `200 turns × 8 reps × seed 42`.

| Noise | v5.3 | v5.2 | Δ | Self-match v5.3 → v5.2 |
| :--- | :--- | :--- | :--- | :--- |
| 0% | 3.0374 | 3.0371 | +0.0003 | 598 → 598 |
| 1% | 2.8871 | 2.8856 | +0.0016 | 590 → 591 |
| 3% | 2.7681 | 2.7338 | +0.0342 | 592 → 590 |
| 5% | 2.6504 | 2.6444 | +0.0060 | 592.5 → 550.2 |
| 10% | 2.4845 | 2.4787 | +0.0058 | 544 → 539 |

> Round-robin rank on the field pack: 1/33 at 0% and 5% for both builds.

The largest single effect at 5% noise is **self-match (+42 points)**: the ladder stops the strategy from fighting itself. HardProber improves by ~+0.35 SPT; the known soft regression is TrickyCooperator (−0.24 SPT).

#### 3. Head-to-head: v5.3 vs v5.2 under matched noise (BHNS)

Blind hold-out & noise-model stress, 30 seeds per key cell. Unit of analysis is the per-seed mean SPT, not per-opponent pairs — a naive pooled Wilcoxon over 990 correlated pairs inflates significance by ~7 orders of magnitude (p=7.5e-21 naive vs p=6.1e-04 correct). Holm–Bonferroni over the family of 15 tests; effect size is Cliff's δ.

| Noise model | 10% | 20% |
| :--- | :--- | :--- |
| **action flip** | +0.02 (p_Holm=0.007, δ=0.19) | +0.05 (p_Holm=0.041) |
| **random move** | +0.01 (p_Holm<0.0001, δ=0.21) | +0.02 (p_Holm=0.0014) |
| **trembling hand** | ns (BH q=0.096) | +0.07 (p_Holm=0.0033) |
| **perception flip** | 0.00 (p=0.38–0.88) | 0.00 |

Values are median Δ score-per-turn between v5.3 and v5.2 (positive = v5.3 better). At 1–5% noise, both models are at parity — the ladder does not activate, and there is nothing to gain.

**Falsifiable prediction (perception flip):** the ladder detects the strategy's own C→D flips. Under perception-flip noise those flips never happen, so the ladder should never activate, so the v5.3 advantage should be zero. Measured result: Δ = 0.00 across all noise levels. This is the strongest single piece of evidence that the effect is a mechanism and not a parameter artifact.

**Robustness.** Jackknife over opponents: the sign of Δ is stable in 32/32 leave-one-out folds across all six key cells. The effect does not rest on one or two convenient opponents.

**Practical significance — honest version.** At 10% noise, Δ ≈ +0.025 score-per-turn ≈ +5 points per 200-turn match ≈ +0.95% of base SPT. On the full library this does not change the rank (both versions #2/222). The value is concentrated in specific head-to-heads and grows with match length (e.g. HardProber: +0.71 SPT at 1000 turns). This is an academic result with targeted practical value, not a general performance leap.

#### Why trembling-hand 10% does not survive correction

Working hypothesis was "the ladder requires action-flip noise." Data disproves it: the effect size is the same as for action flip (median +0.016 vs +0.025, δ=+0.19 in both). The failure to survive Holm is a variance story: std 0.083 vs 0.065, negative seeds 8/30 vs 5/30. Mechanism: trembling-hand flips are all C→D and fully detectable, but each one is a pure loss (no "useful" random D→C), which inflates variance across seeds. Prediction: with n>30 this cell should settle positive. Status: hypothesis, not result.

---

### Reproduce the evidence

```bash
# Field pack benchmark
python benchmarks/run_field.py --pack field --turns 200 --reps 8 --seed 42 --noise 0 0.05
python benchmarks/run_field.py --pack field --turns 200 --reps 8 --seed 42 --noise 0 0.05 --no-ladder
python benchmarks/compare_runs.py OLD.json NEW.json

# Full BHNS battery + statistics
python benchmarks/bhns_runner.py --config benchmarks/bhns_config.json
python benchmarks/bhns_analyze.py --raw benchmarks/results/research/bhns/ --out docs/BHNS_v53.md

# Unit tests
python -m unittest tests.test_zeroresp tests.test_noise_ladder -v
```

The frozen train / hold-out split used by BHNS is in `benchmarks/split.json`. Raw per-seed data: `benchmarks/results/research/bhns/` (hosted on [Zenodo/OSF] — link TBD).

---

### Algorithm

**ZeroResp v5.3 = ZeroResp v5.2 + noise ladder.** `--no-ladder` recovers v5.2 bit-for-bit; every claimed effect is a paired difference under identical seed and noise.

**Base (v5.2):**
- Opening D retort — answer an opening D on turn 2; resync with C if their second move was C.
- Contrite / bad standing — if our intended C was realized as D by match noise, the opponent's reply D is not treated as an attack.
- Generous forgiveness — under estimated noise, stochastic forgive; hard-forgive very high cooperation rates.
- Red-line cooldown — under noise, grim is temporary with periodic C probes.
- End-game harvest — only with known finite length and a short remaining window.
- Profiles — class-level memory across rematches in a tournament process.

**New in v5.3 — noise ladder:**
- Proven-noise gate. The ladder stays dormant at 0% noise; behavior matches v5.2 exactly.
- Unexplained-D evidence ladder. Opponent D after our realized C accumulates evidence; early strikes are deferred and pardonable.
- Delayed pardonable retaliation (v5.3-I). Planned strike with random delay; cancelled if the opponent clears with a clean C streak.

#### What we did not ship

Negative results are results. These were tried and rejected.

| Idea | Why it died |
| :--- | :--- |
| Handshake = play C,D after their C | +~400 vs Handshake, grim-triggers Grudger |
| Cycle-break D on turn ~20 vs AllC | Calculator hunter; Joss-lock / 5% self-match collapse |
| WSLS "C after DD" | Nukes Alternator / Negation |
| v5.3 cycle-break when opp_defects == 0 | Grudger 602 → 239 |

---

### Repository layout

```
.
├── zeroresp.py                          # Canonical v5.3 module
├── axelrod/strategies/zeroresp.py       # Symlink → ../../zeroresp.py
├── tests/
│   ├── test_zeroresp.py
│   └── test_noise_ladder.py
├── benchmarks/
│   ├── run_field.py
│   ├── compare_runs.py
│   ├── bhns_runner.py
│   ├── bhns_analyze.py
│   ├── bhns_config.json
│   ├── split.json                       # Frozen train/hold-out split
│   └── results/                         # Raw JSON/CSV (gitignored or LFS)
├── docs/
│   ├── RESEARCH_v53.md                  # v5.3 vs v5.2 evidence summary
│   ├── BHNS_v53.md                      # Blind hold-out & noise-model stress
│   ├── STRESS_v53.md                    # Full-library stress map
│   └── REGISTRATION.md
├── .github/
│   └── workflows/tests.yml
├── CITATION.cff
├── LICENSE
├── pyproject.toml
└── README.md
```

---

### Citation

```bibtex
@software{zeroresp_v53,
  author = {},
  title = {ZeroResp v5.3: a long-memory IPD strategy with a noise ladder},
  year = {2026},
  version = {5.3.0},
  url = {https://github.com/USER/zeroresp}
}
```

If you use the BHNS protocol or the perception-flip control in your own work, please cite the repository directly. See `CITATION.cff` for a machine-readable entry.

### License

MIT — see LICENSE.
