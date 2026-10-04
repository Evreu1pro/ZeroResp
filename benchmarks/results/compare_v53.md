# ZeroResp run comparison

- OLD: benchmarks\results\field_20260927_150138.json (pack=field, turns=200, reps=8, seed=42)
- NEW: benchmarks\results\field_20261004_174149.json (pack=field, turns=200, reps=8, seed=42)
- Noise levels: OLD [0, 0.05], NEW [0, 0.05]
- Rules: opponent regressed when delta < -0.15 spt (severe < -0.5); REGRESSION when the rank share got worse, or >= 3 opponents regressed, or any severe drop, or self_match_total_mean fell > 20 pts; otherwise IMPROVED above +0.03 mean spt, else NEUTRAL

---

## Noise 0

### Round-robin rank

| metric | OLD | NEW |
|---|---|---|
| rank | 1 / 33 | 1 / 33 |
| rank share (rank/of, lower is better) | 0.0303 | 0.0303 |
| spt (round-robin) | 96.4850 | 96.4806 |
Share delta: +0.0000 (rank regression when > 0)

### H2H per opponent (spt; delta = NEW - OLD)

Common opponents: 32; only in OLD: -; only in NEW: -

Mean delta: +0.0002

Top 5 improvements
| opponent | OLD | NEW | delta |
|---|---|---|---|
| HardProber | 2.9656 | 2.9694 | +0.0038 |
| Prober2 | 3.0338 | 3.0375 | +0.0037 |
| Prober | 2.9775 | 2.9800 | +0.0025 |
| Calculator | 2.7200 | 2.7219 | +0.0019 |
| Alternator | 2.9350 | 2.9350 | +0.0000 |

Top 5 regressions
| opponent | OLD | NEW | delta |
|---|---|---|---|
| SuspiciousTitForTat | 2.9631 | 2.9581 | -0.0050 |
| Prober3 | 2.9612 | 2.9606 | -0.0006 |
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
- mean h2h delta: +0.0002 (IMPROVED above +0.03)

---

## Noise 0.05

### Round-robin rank

| metric | OLD | NEW |
|---|---|---|
| rank | 1 / 33 | 1 / 33 |
| rank share (rank/of, lower is better) | 0.0303 | 0.0303 |
| spt (round-robin) | 85.4281 | 83.4006 |
Share delta: +0.0000 (rank regression when > 0)

### H2H per opponent (spt; delta = NEW - OLD)

Common opponents: 32; only in OLD: -; only in NEW: -

Mean delta: -0.0789

Top 5 improvements
| opponent | OLD | NEW | delta |
|---|---|---|---|
| GrudgerAlternator | 2.4369 | 2.6194 | +0.1825 |
| Random | 2.6638 | 2.7706 | +0.1068 |
| SoftGrudger | 2.3556 | 2.4069 | +0.0513 |
| FirstByGrofman | 2.9525 | 2.9681 | +0.0156 |
| ContriteTitForTat | 2.7888 | 2.8044 | +0.0156 |

Top 5 regressions
| opponent | OLD | NEW | delta |
|---|---|---|---|
| Punisher | 2.4050 | 1.7312 | -0.6738 |
| TwoTitsForTat | 2.4500 | 1.9038 | -0.5462 |
| HardTitForTat | 2.0475 | 1.5031 | -0.5444 |
| TrickyCooperator | 4.2831 | 4.0688 | -0.2143 |
| Gradual | 2.0656 | 1.8706 | -0.1950 |

Regressed opponents (delta < -0.15): 8
worst first: Punisher, TwoTitsForTat, HardTitForTat, TrickyCooperator, Gradual, SlowTitForTwoTats2, HardTitFor2Tats, Prober
Severe drops (delta < -0.5): 3

### Self match / reciprocators

| metric | OLD | NEW | delta |
|---|---|---|---|
| self_match_total_mean | 550.2 | 590.8 | +40.6 |
| self_match_spt | 2.7512 | 2.9538 | +0.2026 |
| reciprocators_mean_spt | 2.3670 | 2.3231 | -0.0439 |

### Verdict (noise 0.05): **REGRESSION**

- rank share: OK (+0.0000; worse when > 0)
- opponents below -0.15: 8 of 32 (REGRESSION at >= 3)
- severe drops below -0.5: 3 (REGRESSION at >= 1)
- self_match_total_mean delta: +40.6 (REGRESSION below -20)
- mean h2h delta: -0.0789 (IMPROVED above +0.03)

---

## Overall verdict: **REGRESSION**

- noise 0: NEUTRAL
- noise 0.05: REGRESSION
- mean h2h delta over 64 common comparisons: -0.0394

