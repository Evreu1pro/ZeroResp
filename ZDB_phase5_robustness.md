# ZDB Phase 5 — Robustness & Invariance Report

## 5.1 Match Length Invariance (Turns: 50, 100, 200, 1000)

- Turns   50: Δ = -0.0730
- Turns  100: Δ = -0.0852
- Turns  200: Δ = -0.0630
- Turns 1000: Δ = -0.0721
**Verdict**: PASS (Sign preserved across ≥2 lengths)

## 5.2 Payoff Invariance (Donation Game R=2, T=3, S=-1, P=0)

- Mean Δ = +0.0071

## 5.3 Sample Power Sweep (Reps: 10, 30, 60 on Target Opponents)

- Reps = 10: Wilcoxon p = 3.9062e-03
- Reps = 30: Wilcoxon p = 1.3039e-07
- Reps = 60: Wilcoxon p = 6.6462e-10

## 5.4 Multi-Seed Invariance (Seeds 42, 43, 44, 45)

- Seed 42: Δ = -0.0350
- Seed 43: Δ = +0.4287
- Seed 44: Δ = +0.4237
- Seed 45: Δ = +0.4325
**Verdict**: MIXED

## 5.5 Jackknife Stability (Leave-One-Out across 32 Opponents)

- Folds preserving sign: 28/32 (87.5%) → **FAIL (87.5% preserved)**

