# ZDB Phase 2 — Ablation Study

## Target Opponents Breakdown (at 5% Noise, Reps=12)

| Opponent | v5.4 Baseline | v5.6 Full | Δ (v5.6 - v5.4) | Drop when No Impulse | Drop when No Stopcock | Drop when No EarlyExit |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **HardProber** | 2.5492 | 2.5500 | +0.0008 | -0.0004 | +0.0000 | +0.0000 |
| **TwoTitsForTat** | 2.6463 | 2.6463 | +0.0000 | +0.0000 | +0.0000 | +0.0000 |
| **Gradual** | 2.3433 | 2.3413 | -0.0021 | +0.0000 | +0.0000 | +0.0000 |
| **Calculator** | 2.4479 | 2.4875 | +0.0396 | +0.0000 | +0.0000 | +0.0000 |
| **TrickyCooperator** | 3.8883 | 3.8967 | +0.0083 | +0.0000 | +0.0000 | +0.0000 |
| **ZDExtort2** | 1.6825 | 1.6650 | -0.0175 | +0.0000 | +0.0000 | +0.0000 |

## Mechanism Health Check (Pre-registered criteria)

* **Rule**: If disabling mechanism changes Δ by ≤ 0.02 across all targets → declared **DEAD CODE**.
* **Rule**: Each mechanism must explain ≥30% of effect on ≥1 target opponent.

- **impulse**: Max effect = 0.0004 on HardProber → **DEAD CODE (Effect ≤ 0.02)**
- **stopcock**: Max effect = 0.0000 on None → **DEAD CODE (Effect ≤ 0.02)**
- **earlyexit**: Max effect = 0.0000 on None → **DEAD CODE (Effect ≤ 0.02)**
