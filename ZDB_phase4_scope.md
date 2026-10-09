# ZDB Phase 4 — Scope Conditions Report

## 4.1 Perception-Flip Robustness (Reps=30)

- 5% noise: Δ = +0.2041 (Criterion: |Δ| ≤ 0.02) → **FAIL**
- 10% noise: Δ = +0.3486 (Criterion: |Δ| ≤ 0.02) → **FAIL**

## 4.2 External Hold-Out Pool (40 unseen strategies, 5% Noise, Reps=12)

- Mean Δ = -0.0435 → **FAIL (Overfitted to train)**

## 4.3 Library Without Cyclers (Sample of 50 non-cyclers, 5% Noise, Reps=12)

- Mean Δ = -0.0408 → **SCOPE CONDITION (Dependent on periodic/cyclers)**

## 4.4 Cyclers with Jitter (Reps=12)

- 1% Jitter: Δ = -0.7578
- 3% Jitter: Δ = -0.8151

## 4.5 Zero-Determinant Extensions (5% Noise, Reps=12)

- Mean Δ = -0.0100

