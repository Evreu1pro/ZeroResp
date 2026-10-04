# ZeroResp run comparison

- OLD: benchmarks\results\verify\v52\field_20261004_205724.json (pack=field, turns=200, reps=8, seed=42)
- NEW: benchmarks\results\verify\v53\field_20261004_205725.json (pack=field, turns=200, reps=8, seed=42)
- Noise levels: OLD [0, 0.05], NEW [0, 0.05]
- Rules: opponent regressed when delta < -0.15 spt (severe < -0.5); REGRESSION when the rank share got worse, or >= 3 opponents regressed, or any severe drop, or self_match_total_mean fell > 20 pts; otherwise IMPROVED above +0.03 mean spt, else NEUTRAL

---

## Noise 0

### Round-robin rank

| metric | OLD | NEW |
|---|---|---|
| rank | 1 / 33 | 1 / 33 |
| rank share (rank/of, lower is better) | 0.0303 | 0.0303 |
| spt (round-robin) | 96.4813 | 96.4856 |
Share delta: +0.0000 (rank regression when > 0)

### H2H per opponent (spt; delta = NEW - OLD)

Common opponents: 32; only in OLD: -; only in NEW: -

Mean delta: +0.0003

Top 5 improvements
| opponent | OLD | NEW | delta |
|---|---|---|---|
| SuspiciousTitForTat | 2.9625 | 2.9675 | +0.0050 |
| Calculator | 2.7181 | 2.7219 | +0.0038 |
| Prober2 | 3.0300 | 3.0325 | +0.0025 |
| HardProber | 2.9681 | 2.9688 | +0.0007 |
| Alternator | 2.9350 | 2.9350 | +0.0000 |

Top 5 regressions
| opponent | OLD | NEW | delta |
|---|---|---|---|
| Prober | 2.9762 | 2.9750 | -0.0012 |
| Prober3 | 2.9631 | 2.9619 | -0.0012 |
| Alternator | 2.9350 | 2.9350 | +0.0000 |
| Bully | 4.8750 | 4.8750 | +0.0000 |
| ContriteTitForTat | 3.0100 | 3.0100 | +0.0000 |

Regressed opponents (delta < -0.15): 0
Severe drops (delta < -0.5): 0

### Self match / reciprocators

| metric | OLD | NEW | delta |
|---|---|---|---|
| self_match_total_mean | 598.0 | 598.0 | +0.0 |
| self_match_spt | 2.9900 | 2.9900 | +0.0000 |
| reciprocators_mean_spt | 3.0100 | 3.0100 | +0.0000 |

### Verdict (noise 0): **NEUTRAL**

- rank share: OK (+0.0000; worse when > 0)
- opponents below -0.15: 0 of 32 (REGRESSION at >= 3)
- severe drops below -0.5: 0 (REGRESSION at >= 1)
- self_match_total_mean delta: +0.0 (REGRESSION below -20)
- mean h2h delta: +0.0003 (IMPROVED above +0.03)

---

## Noise 0.05

### Round-robin rank

| metric | OLD | NEW |
|---|---|---|
| rank | 1 / 33 | 1 / 33 |
| rank share (rank/of, lower is better) | 0.0303 | 0.0303 |
| spt (round-robin) | 85.4250 | 85.1975 |
Share delta: +0.0000 (rank regression when > 0)

### H2H per opponent (spt; delta = NEW - OLD)

Common opponents: 32; only in OLD: -; only in NEW: -

Mean delta: +0.0059

Top 5 improvements
| opponent | OLD | NEW | delta |
|---|---|---|---|
| HardProber | 1.9106 | 2.2587 | +0.3481 |
| FirstByGrofman | 2.9525 | 3.0106 | +0.0581 |
| HardTitForTat | 2.0475 | 2.0769 | +0.0294 |
| Punisher | 2.4050 | 2.4319 | +0.0269 |
| SoftGrudger | 2.3556 | 2.3787 | +0.0231 |

Top 5 regressions
| opponent | OLD | NEW | delta |
|---|---|---|---|
| TrickyCooperator | 4.2831 | 4.0475 | -0.2356 |
| GrudgerAlternator | 2.4369 | 2.4162 | -0.0207 |
| Grudger | 1.2300 | 1.2188 | -0.0112 |
| OnceBitten | 2.7519 | 2.7463 | -0.0056 |
| HardTitFor2Tats | 2.9663 | 2.9612 | -0.0051 |

Regressed opponents (delta < -0.15): 1
worst first: TrickyCooperator
Severe drops (delta < -0.5): 0

### Self match / reciprocators

| metric | OLD | NEW | delta |
|---|---|---|---|
| self_match_total_mean | 550.2 | 592.5 | +42.3 |
| self_match_spt | 2.7512 | 2.9625 | +0.2113 |
| reciprocators_mean_spt | 2.3670 | 2.3654 | -0.0016 |

### Verdict (noise 0.05): **NEUTRAL**

- rank share: OK (+0.0000; worse when > 0)
- opponents below -0.15: 1 of 32 (REGRESSION at >= 3)
- severe drops below -0.5: 0 (REGRESSION at >= 1)
- self_match_total_mean delta: +42.3 (REGRESSION below -20)
- mean h2h delta: +0.0059 (IMPROVED above +0.03)

---

## Overall verdict: **NEUTRAL**

- noise 0: NEUTRAL
- noise 0.05: NEUTRAL
- mean h2h delta over 64 common comparisons: +0.0031

