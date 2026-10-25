# ZeroResp — a long-memory IPD strategy with a noise ladder

[![tests](https://img.shields.io/badge/tests-passing-brightgreen)](#)
[![python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org)
[![license](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)
[![axelrod](https://img.shields.io/badge/axelrod-compatible-orange)](https://axelrod.readthedocs.io)
[![Site](https://img.shields.io/badge/site-evreu1pro.github.io%2FZeroResp-2fd6f2.svg)](https://evreu1pro.github.io/ZeroResp/)

**Project site:** [evreu1pro.github.io/ZeroResp](https://evreu1pro.github.io/ZeroResp/) · **Research notebook:** [v5.4.x deep dive](https://evreu1pro.github.io/ZeroResp/research.html)

**ZeroResp is an Iterated Prisoner's Dilemma player built around epoch debt, delayed retaliation, noise-aware forgiveness, opening disambiguation, and finite-horizon harvest.**

**Current version: 5.4.4** — the v5.3 noise ladder, plus responsiveness-gated apology and a cycler contour (periods 2–6, noise-tolerant, mirror-guarded). Display name: `ZeroResp v5.4.4`.

| Version | Role | One-line |
| :--- | :--- | :--- |
| **v5.4.4** | **current** | Cycler contour; best of ours at 5% noise (full library #2, seed 42) |
| v5.4.3 | honest negative | Noise-level contour switch; under channel noise converges to v5.4.2 |
| v5.4.2 | research | Responsiveness gate ΔP_resp ≥ 0.35 |
| v5.4.1 | research | Spin-out / `balance_apology` vs TTFT & Gradual |
| v5.4 | dead end | Bit-identical to v5.3 on 26 520 matches — not a release |
| v5.3 | previous production | Proven-noise ladder; still a valid baseline (`zeroresp_v53.py`) |
| v5.2 | pre-ladder | Base long-memory player |

The full ZDB trail (pre-registrations, JSON artifacts, runners) lives on branch [`research/v54x`](https://github.com/Evreu1pro/ZeroResp/tree/research/v54x) — that branch is the research notebook, not an archive of “the current site”.

---

### Attribution / Use of AI tools

**Basis.** Production through v5.3 is the human-directed ZeroResp line (noise ladder).

**v5.4.x.** Built on that v5.3 basis with AI coding agents under human direction: the human set hypotheses, review criteria, and every release decision; agents implemented runners, ran batteries, and drafted reports.

**Tools.** Primary coding agent for the v5.4.x cycle: **GLM (Z.ai)**. Site updates, GitHub packaging, CI/monitoring and publication support: **Grok Bot**. Autocomplete and spelling fixes do not count.

The maintainer of this repo is responsible for the contribution and can explain the strategy decisions.

---

### Scope & Limitations

> **Read this first.** ZeroResp's ladder is a cooperation mechanism for a noisy channel between two fallible players. It is not a shield against one-sided exploitation, and it is not a general-purpose "better than TFT".

**✅ Works in:**
- mutual channel noise ≥5–10%, long horizon (≥200 turns), standard PD payoffs (R=3, T=5, S=0, P=1)

**❌ Fails in:**
- **one-sided noise** (only ZeroResp perturbed, opponents clean)
- **perception-flip noise** (ladder detects own C→D flips)
- **clean environments** at the very top of the full library (handwritten families still compete; Evolved ANN Noise variants lead under noise)

> If you need a strategy for a clean or one-sided-noise environment, use TitForTat. ZeroResp is for the mutual-noise regime.

---

### Install

```bash
pip install git+https://github.com/Evreu1pro/ZeroResp.git   # pulls axelrod>=4.12
```

Or from a checkout:

```bash
git clone https://github.com/Evreu1pro/ZeroResp.git
cd ZeroResp
pip install -e .
```

Tests: `python -m unittest discover -s tests`. Not on PyPI yet — see [PUBLISH.md](PUBLISH.md) for the upload checklist.

### Quick start

```python
import axelrod as axl
from zeroresp import ZeroResp

match = axl.Match((ZeroResp(), axl.TitForTat()), turns=200, seed=0)
match.play()
print(match.final_score())
# ZeroResp().name == "ZeroResp v5.4.4"
```

Disable the noise ladder (recover pre-ladder base behaviour):

```python
from zeroresp import Features, ZeroResp
ZeroResp(features=Features(noise_ladder=False))
```

Historical v5.3 freeze: `from zeroresp_v53 import ZeroResp`.

---

### Evidence (headline)

Full-library round-robin with our versions inside the pool (~230 players, 200 turns × 1 rep, paired seeds). Seed 42:

| Noise | v5.4.4 | v5.4.2 | v5.4.1 | v5.3 | leader SPT |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 0% | #9 | #10 | #16 | #6 | 664.2 |
| 5% | **#2** | #8 | #4 | #5 | 592.2 |
| 10% | #3 | #8 | #5 | #4 | 553.9 |

Rank stability at 5% (seeds 42 / 43 / 44): v5.4.4 #2 / #5 / #11; family holds top-10 on every draw. Cycler contour recovers +0.36 SPT vs v5.4.2 on CyclerCCD (fresh seeds). Details and honesty audit: [research page](https://evreu1pro.github.io/ZeroResp/research.html).

#### Historical field pack (v5.3 production)

Mean SPT, 32-strategy pack, `200 turns × 8 reps × seed 42`:

| Noise | v5.3 | v5.2 | Δ | Self-match v5.3 → v5.2 |
| :--- | :--- | :--- | :--- | :--- |
| 0% | 3.0374 | 3.0371 | +0.0003 | 598 → 598 |
| 3% | 2.7681 | 2.7338 | +0.0342 | 592 → 590 |
| 5% | 2.6504 | 2.6444 | +0.0060 | **592.5 → 550.2** |

Older library tables: [`RESEARCH_v53.md`](RESEARCH_v53.md), raw runs in [`benchmarks/results/`](benchmarks/results/).

BHNS (blind hold-out + noise-model stress, v5.3 vs v5.2: frozen 40-strategy hold-out, action / random / trembling / perception noise at 1–20%, 10–30 seeds) is on branch `research/v54x`: results in [`BHNS_v53.md`](https://github.com/Evreu1pro/ZeroResp/blob/research/v54x/BHNS_v53.md) (Russian), runner [`benchmarks/run_bhns.py`](https://github.com/Evreu1pro/ZeroResp/blob/research/v54x/benchmarks/run_bhns.py), analysis [`benchmarks/analyze_bhns.py`](https://github.com/Evreu1pro/ZeroResp/blob/research/v54x/benchmarks/analyze_bhns.py), frozen split [`split.json`](https://github.com/Evreu1pro/ZeroResp/blob/research/v54x/benchmarks/results/research/bhns/split.json). Full-library stress map: [`STRESS_v53.md`](https://github.com/Evreu1pro/ZeroResp/blob/research/v54x/STRESS_v53.md).

---

### Reproduce

```bash
# Unit tests
python -m unittest tests.test_zeroresp tests.test_noise_ladder -v

# Field pack benchmark
python benchmarks/run_field.py --pack field --turns 200 --reps 8 --seed 42 --noise 0 0.05
```

Full-library / ZDB runners and JSON: branch `research/v54x`. BHNS from there:

```bash
git checkout research/v54x
pip install scipy                     # analyze_bhns.py needs it
python benchmarks/analyze_bhns.py     # rebuilds BHNS_v53.md from the stored JSON
python benchmarks/run_bhns.py         # resumable: skips runs whose JSON already exists
```

Sanity check (2026-10-25, axelrod 4.14.0): `analyze_bhns.py` regenerates `BHNS_v53.md` byte-for-byte; re-running two hold-out round-robins from scratch (`action` 10% seed 0, `random` 5% seed 1) gives the same ranks for both versions, SPT within 0.05 of the stored runs.

---

### Algorithm (current)

**ZeroResp v5.4.4 = v5.3 ladder + responsiveness-gated apology + cycler contour.**

- **Base (v5.2):** opening D retort, contrite / bad standing, generous forgiveness, red-line cooldown, end-game harvest, class-level profiles.
- **v5.3 — noise ladder:** proven-noise gate; unexplained-D evidence; delayed pardonable retaliation.
- **v5.4.1–2 — apology gates:** `balance_apology` with ΔP_resp ≥ 0.35 so Random does not trigger spin-out recovery.
- **v5.4.4 — cycler contour:** fixed-period detection (2–6, window 18) blocks apology against proven cyclers.

Negative results (shipped as such): v5.4 bit-identical dead end; v5.4.3 noise-level contour converges to v5.4.2 under channel noise.

---

### Repository layout

```
.
├── zeroresp.py                          # Canonical v5.4.4 module
├── zeroresp_v544.py                     # Same as research v5.4.4 source
├── zeroresp_v53.py                      # Frozen previous production
├── axelrod/                             # Drop-in copy for an Axelrod-Python checkout
├── tests/
├── benchmarks/
├── docs/                                # GitHub Pages (index = current, research = deep dive)
├── RESEARCH_v53.md                      # v5.3 vs v5.2 evidence summary
├── CITATION.cff
├── LICENSE
├── pyproject.toml
└── README.md
```

Research artifacts for the v5.4.x cycle: [`research/v54x`](https://github.com/Evreu1pro/ZeroResp/tree/research/v54x).

---

### Citation

```bibtex
@software{zeroresp_v544,
  author = {Evreu1pro},
  title = {ZeroResp v5.4.4: noise ladder, responsiveness gates, and cycler contour},
  year = {2026},
  version = {5.4.4},
  url = {https://github.com/Evreu1pro/ZeroResp}
}
```

See `CITATION.cff` for a machine-readable entry. The v5.4.x research cycle was developed with GLM (Z.ai) under human direction; see the [research page](https://evreu1pro.github.io/ZeroResp/research.html) attribution section.

### License

MIT — see LICENSE.
