# ZeroResp — a long-memory IPD strategy with a noise ladder

[![tests](https://github.com/USER/zeroresp/actions/workflows/tests.yml/badge.svg)](https://github.com/USER/zeroresp/actions/workflows/tests.yml)
[![python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![axelrod](https://img.shields.io/badge/axelrod-4.x-blueviolet)](https://github.com/Axelrod-Python/Axelrod)

ZeroResp is an Iterated Prisoner's Dilemma player built around epoch debt,
delayed retaliation, noise-aware forgiveness, opening disambiguation, and
finite-horizon harvest. **v5.3 = v5.2 + a noise ladder** that activates only
after channel noise has been proven. With the ladder disabled, v5.3 is
bit-for-bit v5.2.

---

## Scope & Limitations

Read this first. ZeroResp's ladder is a **cooperation mechanism for a noisy
channel between two fallible players**. It is not a shield against one-sided
exploitation, and it is not a general-purpose "better than TFT".

- ✅ **Works in:** mutual channel noise ≥10%, long horizon (≥200 turns),
  standard PD payoffs (R=3, T=5, S=0, P=1).
- ❌ **Fails in:** one-sided noise (only ZeroResp perturbed, opponents clean).
  In that regime both v5.3 and v5.2 fall behind TitForTat and Grudger.
- ❌ **Fails in:** perception-flip noise. The ladder detects its own C→D
  flips; if the flips are on the *input* side, it never activates, and the
  v5.3 advantage is exactly **0.00**.
- ❌ **Fails in:** clean environments. TitForTat ≥ ZeroResp at 0% noise on the
  full library (rank 12/222 for both v5.3 and v5.2).
- ⚠️ **Rank-neutral on the full library.** At 10% noise both v5.3 and v5.2
  are #2/222. The improvement is measurable in SPT, not in rank.
- ⚠️ **trembling-hand at 10% is on the significance boundary** (BH q=0.096).
  Likely needs n>30 to settle.
- ❌ **External hold-out is not yet done.** All reported results use the same
  221-strategy pool used for tuning. This affects H1 (top-5 hold-out) only,
  not H2/H3/H5.

If you need a strategy for a clean or one-sided-noise environment, use
TitForTat. ZeroResp is for the mutual-noise regime.

---

## Install

```bash
pip install axelrod
pip install -e .
