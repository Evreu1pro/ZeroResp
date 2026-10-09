# ZDB Phase 1 — Core Claim Summary

**Evaluated**: v5.3 vs v5.6 across 32 Field strategies, 30 paired seeds, 200 turns.

| Noise Level | Mean Δ SPT | Median Δ SPT | 95% Bootstrap CI | Wilcoxon p-value | Pre-registered Verdict |
|---:|:---:|:---:|:---:|:---:|:---:|
|  0.0% | -0.05664 | -0.04648 | [-0.06902, -0.04454] | 3.1760e-06 | **FAIL (Drop early-exit warmup)** |
|  1.0% | -0.04256 | -0.04555 | [-0.05529, -0.02943] | 5.1446e-06 | **FAIL** |
|  3.0% | -0.01785 | -0.03305 | [-0.04506, +0.01785] | 9.3011e-03 | **NEUTRAL** |
|  5.0% | +0.01083 | -0.00188 | [-0.01381, +0.04165] | 8.2358e-01 | **NEUTRAL** |
| 10.0% | -0.01000 | -0.02062 | [-0.03015, +0.01185] | 2.1293e-01 | **NEUTRAL** |
