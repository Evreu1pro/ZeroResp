# ZDB MASTER REPORT

## Integrity: PASS
- **0.1 SHA256 of sources**: PASS. All 4 source hashes are strictly distinct (`v5.3`, `v5.4`, `v5.5`, `v5.6`).
- **0.2 Strategy list SHA256**: PASS. `split.json` hash verified (32 train, 40 holdout).
- **0.3 Determinism**: PASS. Re-running with identical seed produces bit-identical trajectories.
- **0.4 Variants differ**: PASS. `v5.4` vs `v5.5` produced distinct outcomes at 10% noise (650 vs 664 on TrickyDefector).
- **0.5 Anti-fallthrough**: PASS. `--variant fake` explicitly raises `ValueError`.
- **0.6 Git diff**: PASS. 518 lines of diff between successive versions saved in `ZDB_variants.diff`.

---

## Core claim: MIXED / CONDITIONAL
Evaluated across 32 field strategies, 30 paired seeds, 200 turns (4,800 matches):
- **0.0% noise**: Mean $\Delta = -0.0566$ (95% CI: [-0.0690, -0.0445], $p = 3.18 \times 10^{-6}$) $\to$ **FAIL** (Warmup delay causes structural regression on cooperative strategies).
- **1.0% noise**: Mean $\Delta = -0.0426$ (95% CI: [-0.0553, -0.0294], $p = 5.14 \times 10^{-6}$) $\to$ **FAIL**.
- **3.0% noise**: Mean $\Delta = -0.0178$ (95% CI: [-0.0451, +0.0178], $p = 0.0093$) $\to$ **NEUTRAL**.
- **5.0% noise**: Mean $\Delta = +0.0108$ (95% CI: [-0.0138, +0.0416], $p = 0.824$) $\to$ **PARITY / NEUTRAL** on the aggregate field.
- **10.0% noise**: Mean $\Delta = -0.0100$ (95% CI: [-0.0301, +0.0118], $p = 0.213$) $\to$ **PARITY / NEUTRAL** on the aggregate field.

---

## Ablation: DISCONFIRMED AT 5% NOISE
Deconstruction of individual mechanisms (`pulsed_harvest`, `circuit_breaker`, `early_exit_warmup`) on the 6 target strategies at 5% noise:
- Disabling `pulsed_harvest` alone changed $\Delta$ by at most $0.0004$.
- Disabling `circuit_breaker` alone changed $\Delta$ by $0.0000$.
- Disabling `early_exit_warmup` alone changed $\Delta$ by $0.0000$.
- **Finding**: Across 5% noise on the target set, no individual mechanism explains $>30\%$ of the variance above the `v5.4` baseline. The primary gains over `v5.3` stem from the core architectural changes inherited through `v5.4` (`tactical_prefilter` and `profile_memory`).

---

## Targeted: SELECTIVELY CONFIRMED
Deep-dive on 10 specific strategies across 30 paired seeds at 5% noise:
- **TwoTitsForTat**: $\Delta = +0.3718$ (95% CI: [+0.1948, +0.5765], Holm $p = 1.27 \times 10^{-4}$) $\to$ **CONFIRMED ($\Delta \ge +0.20$)**.
- **Calculator**: $\Delta = +0.4003$ (95% CI: [+0.0995, +0.6938], Holm $p = 0.0452$) $\to$ **CONFIRMED**.
- **Gradual**: $\Delta = +0.2577$ (95% CI: [+0.1708, +0.3520], Holm $p = 4.26 \times 10^{-4}$) $\to$ **CONFIRMED**.
- **HardProber**: $\Delta = +0.1873$ (95% CI: [+0.0572, +0.3580], Holm $p = 4.16 \times 10^{-4}$) $\to$ **REFUTED FOR $\ge +0.20$** (Statistically significant positive effect confirmed at $+0.19$, but previous claim of $+0.346$ was sample variance).
- **TitForTat**: $\Delta = +0.1003$ (95% CI: [+0.0095, +0.2340], Holm $p = 3.83 \times 10^{-3}$) $\to$ **CONFIRMED POSITIVE**.
- **TrickyCooperator**: $\Delta = +0.0175$ (95% CI: [-0.1175, +0.1890]) $\to$ **TOLERABLE ($\Delta \ge -0.05$)**.
- **ZDExtort2**: $\Delta = +0.0702$ (95% CI: [-0.0170, +0.1748]) $\to$ **TOLERABLE ($\Delta \ge -0.05$)**.
- **Random**: $\Delta = -0.1902$ (95% CI: [-0.3513, -0.0582], Holm $p = 2.89 \times 10^{-3}$) $\to$ **STRUCTURAL REGRESSION against stochastic noise**.

---

## Scope: STRICT BOUNDARY CONDITIONS IDENTIFIED
1. **Perception noise**: $\Delta = +0.204$ (5%) and $+0.349$ (10%). The mechanism breaks parity under perceptual inversion.
2. **External Hold-out (40 unseen strategies)**: Mean $\Delta = -0.0435$. The general aggregate advantage does **not** transfer to the holdout pool without fine-tuning.
3. **Library without Cyclers**: Mean $\Delta = -0.0408$. The model is reliant on exploiting structured/cycler patterns.
4. **Cyclers with Jitter (1%, 3%)**: $\Delta = -0.758$ and $-0.815$. Jitter severely destabilizes the pattern recognizer.

---

## Robustness: PARTIAL INVARIANCE
- **Match Lengths (50, 100, 200, 1000 turns)**: Sign invariant across all lengths ($\Delta$ remains consistently negative on the baseline subset).
- **Payoff Matrix (Donation Game)**: $\Delta = +0.0071$ (positive sign preserved).
- **Power Sweep**: Monotonic decrease in $p$-value ($3.9 \times 10^{-3} \to 1.3 \times 10^{-7} \to 6.6 \times 10^{-10}$).
- **Multi-seed**: Significant seed variance (Seed 42 is $-0.035$, while Seeds 43–45 show strong $+0.42$ gains on target reciprocators).
- **Jackknife**: 28 of 32 folds (87.5%) preserve sign (falls short of 95% threshold).

---

## Stats: MULTIPLE TESTING SURVIVORS
Out of 15 pre-registered hypotheses tested under Holm-Bonferroni correction ($FWER \le 0.05$):
- **Surviving positive effects**: `TwoTitsForTat` ($p=1.27 \times 10^{-4}$), `Gradual` ($p=4.26 \times 10^{-4}$), `HardProber` ($p=4.16 \times 10^{-4}$), `TitForTat` ($p=3.83 \times 10^{-3}$), and `Calculator` ($p=0.0452$).
- **Surviving negative effects**: Field Pack at 0% ($p=4.75 \times 10^{-5}$), Field Pack at 1% ($p=7.20 \times 10^{-5}$), and `Random` ($p=2.89 \times 10^{-3}$).
- **Aggregate 5% and 10% field effects**: Do not survive Holm-Bonferroni or BH-FDR correction ($p > 0.20$).

---

## What We Claim (Verified Facts)
1. Against strict and gradual reciprocators (`TwoTitsForTat`, `Gradual`, `Calculator`, `TitForTat`), `ZeroResp v5.6` achieves a statistically significant, Holm-Bonferroni-surviving improvement of $+0.10$ to $+0.37$ SPT at 5% noise.
2. The mechanism prevents mutual retaliation cascades against `HardProber`, producing a verified improvement of $+0.187$ SPT (correcting the preliminary estimate of $+0.346$).
3. The model exhibits complete determinism and passes all Phase 0 integrity checks without code fall-through.

---

## What We Do NOT Claim (Explicitly Refuted)
1. We do **NOT** claim an aggregate win across the entire field pack: at 0% and 1% noise, the model exhibits a statistically significant regression ($-0.04$ to $-0.05$ SPT) due to warmup delays.
2. We do **NOT** claim $+0.35$ on `HardProber` (empirically bounded at $+0.19$ under 30 paired seeds).
3. We do **NOT** claim generalization to unseen holdout strategies or jittered cyclers, where the model performs worse than `v5.3`.
4. We do **NOT** claim independent efficacy of the isolated pulsed harvest or stopcock mechanisms at 5% noise, as neither crossed the pre-registered $>0.02$ ablation threshold over `v5.4`.
