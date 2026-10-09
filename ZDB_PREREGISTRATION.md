# ZeroResp Definitive Battery (ZDB) — Pre-Registration

**Date**: 2026-10-09  
**Status**: Pre-registered before test execution.

---

## 1. General Protocol Rules

1. **Paired by Seed**: Every run comparing Version A and Version B executes the exact same match with the exact same seed.
2. **Granularity**: All raw output data is recorded `per-opponent, per-seed`. Aggregation is performed in a separate statistical phase.
3. **No Silent Fallback**: Unknown variant flags raise a explicit exception (`raise ValueError`), never falling through to a default.
4. **Deterministic RNG**: Re-running the exact same build with the exact same seed must produce bit-identical results.
5. **Pre-Commit**: This document is committed to git prior to executing any phase benchmarks.

---

## 2. Phase Criteria & Pre-Registered Gates

### Phase 0: Integrity (Gatekeeper)
| Step | Check | Pass Criterion | Failure Action |
|:---|:---|:---|:---|
| 0.1 | SHA256 of source files (v5.3, v5.4, v5.5, v5.6) | All file hashes are strictly distinct | Halt. Fix variant definition. |
| 0.2 | SHA256 of strategy lists in each pool (`split.json`) | Fixed and verified | Halt. |
| 0.3 | Determinism: same build, same seed, 2 runs | Bit-identical outputs | Halt. Fix RNG leaks. |
| 0.4 | Variants differ: v5.4 vs v5.5 at 10% noise | Not bit-identical | Halt. Variant is dead code. |
| 0.5 | Fall-through: `--variant fake` | `raise ValueError`, not silent default | Halt. |
| 0.6 | Git diff of each variant from previous | Saved to `ZDB_variants.diff` | Halt. |

### Phase 1: Core Claim (v5.3 vs v5.6)
* **Pool**: 32-player field pack (`split.json` train).
* **Noise levels**: 0%, 1%, 3%, 5%, 10%.
* **Repetitions**: 30 per level.
* **Match length**: 200 turns.
* **Metric**: $\Delta \text{SPT} = \text{SPT}_{v5.6} - \text{SPT}_{v5.3}$ per (opponent, seed).
* **Pre-registered Acceptance Criteria**:
  - **5%, 10% noise**: $|\Delta \text{mean}| \le 0.005$ and $95\% \text{ CI } |\Delta \text{mean}| \le 0.01 \to$ claim "bit-identical parity". If $\Delta \text{mean} > 0.01$ and $p < 0.05 \to$ claim statistically significant gain.
  - **3% noise**: $\Delta \text{mean} \ge 0$, CI lower $\ge -0.01 \to$ neutral / positive.
  - **1% noise**: $\Delta \text{mean} \ge -0.005 \to$ neutral.
  - **0% noise**: $\Delta \text{mean} \ge -0.01$. If fail $\to$ reject early-exit warmup.

### Phase 2: Ablation
* **Variants**:
  1. `v5.6` (all features ON)
  2. `v5.6_no_impulse` (pulsed harvest OFF)
  3. `v5.6_no_stopcock` (circuit breaker stopcock OFF)
  4. `v5.6_no_earlyexit` (early-exit warmup OFF)
  5. `v5.4` (baseline)
* **Opponents**: Field pack + 6 target strategies (`HardProber`, `TwoTitsForTat`, `Gradual`, `Calculator`, `TrickyCooperator`, `ZDExtort2`).
* **Noise**: 0%, 1%, 5%, 10%, 12 reps, strictly paired.
* **Pre-registered Criteria**:
  - Each mechanism must explain $\ge 30\%$ of claimed effect on $\ge 1$ target opponent.
  - If disabling a mechanism changes $\Delta$ by $\le 0.02$, declare mechanism dead code.
  - If two mechanisms produce identical effects, prune down to one.

### Phase 3: Targeted Deep-Dive
* **Opponents (10)**: `HardProber`, `TwoTitsForTat`, `Gradual`, `Calculator`, `TrickyCooperator`, `ZDExtort2`, `ZDExtort3`, `ZDExtort2v2`, `Random`, `TitForTat`.
* **Noise**: 0%, 1%, 3%, 5%, 10%, 30 reps, paired v5.3 vs v5.6.
* **Pre-registered Criteria**:
  - `HardProber`: $\Delta \ge +0.2$ at 5% noise with 95% CI lower $> 0$.
  - `TwoTitsForTat`: $\Delta \ge +0.2$ at 5% noise.
  - `TrickyCooperator`: $\Delta \ge -0.05$ (otherwise record as structural regression).
  - `ZDExtort2`: $\Delta \ge -0.05$ (otherwise record as structural regression).

### Phase 4: Scope Conditions
* **4.1 Perception-flip**: strictly paired flips, 30 reps $\to |\Delta| \le 0.02$ at 5% and 10%.
* **4.2 Hold-out pool**: 50 hold-out strategies from `split.json`, 12 reps $\to \Delta \ge -0.01$.
* **4.3 Non-Cycler library**: 218 strategies without Cyclers, 12 reps $\to \Delta \ge 0$. If fail $\to$ effect is Cycler-dependent.
* **4.4 Cyclers with jitter**: 1% and 3% jitter, 12 reps $\to$ test detector robustness.
* **4.5 ZD extension**: `ZD-GTFT`, `ZD-Extort-4`, `LookerUp-ZD` $\to$ test responsiveness gating.

### Phase 5: Robustness
* **5.1 Match Length**: 50, 100, 200, 1000 turns $\to$ sign of $\Delta$ invariant across $\ge 2$ lengths.
* **5.2 Payoff Matrix**: Donation game ($R=2, T=3, S=-1, P=0$) $\to$ sign of $\Delta$ invariant.
* **5.3 Sample Power**: Reps sweep (10, 30, 100) $\to p$-value monotonically decreases.
* **5.4 Multi-seed**: Seeds 42, 43, 44, 45 $\to$ sign invariance.
* **5.5 Jackknife**: Delete 1 opponent at a time $\to$ sign of $\Delta$ preserved in $\ge 95\%$ of folds.

### Phase 6: Statistics
* Non-parametric Wilcoxon signed-rank on per-seed mean $\Delta$.
* Bootstrap 95% CI (10,000 resamples).
* Holm-Bonferroni and Benjamini-Hochberg FDR multiplicity corrections.
* Cliff's delta effect sizes.

---

## 3. Reporting Commitment
Final synthesis will be published in `ZDB_MASTER.md`. No claims outside those surviving the pre-registered gates will be admitted.
