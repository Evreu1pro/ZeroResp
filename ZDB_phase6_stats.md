# ZDB Phase 6 — Formal Statistics & Multiple Testing Corrections

Family size: **15 tests** (5 Field Pack levels + 10 Targeted Opponents at 5% noise).

| Hypothesis / Test | Mean Δ SPT | 95% Bootstrap CI | Cliff's δ | Raw p-val | Holm-Bonferroni p | BH-FDR p | Survives Holm? |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Field Pack Noise  0.0% | -0.0566 | [-0.0690, -0.0445] | -0.80 | 3.1684e-06 | 4.7526e-05 | 3.8585e-05 | **YES (p<0.05)** |
| Field Pack Noise  1.0% | -0.0426 | [-0.0553, -0.0294] | -0.67 | 5.1446e-06 | 7.2025e-05 | 3.8585e-05 | **YES (p<0.05)** |
| Field Pack Noise  3.0% | -0.0178 | [-0.0451, +0.0179] | -0.33 | 9.3011e-03 | 6.5108e-02 | 1.5502e-02 | No |
| Field Pack Noise  5.0% | +0.0108 | [-0.0138, +0.0417] | -0.07 | 8.2358e-01 | 1.0000e+00 | 8.2358e-01 | No |
| Field Pack Noise 10.0% | -0.0100 | [-0.0302, +0.0119] | -0.20 | 2.1293e-01 | 1.0000e+00 | 2.9036e-01 | No |
| Targeted: Calculator (5% noise) | +0.4003 | [+0.0995, +0.6938] | +0.60 | 5.6469e-03 | 4.5175e-02 | 1.0588e-02 | **YES (p<0.05)** |
| Targeted: Gradual (5% noise) | +0.2577 | [+0.1708, +0.3520] | +0.60 | 3.8767e-05 | 4.2644e-04 | 1.1630e-04 | **YES (p<0.05)** |
| Targeted: HardProber (5% noise) | +0.1873 | [+0.0572, +0.3580] | +0.70 | 3.4690e-05 | 4.1628e-04 | 1.1630e-04 | **YES (p<0.05)** |
| Targeted: Random (5% noise) | -0.1902 | [-0.3513, -0.0582] | -0.57 | 2.8905e-04 | 2.8905e-03 | 7.2263e-04 | **YES (p<0.05)** |
| Targeted: TitForTat (5% noise) | +0.1003 | [+0.0095, +0.2340] | +0.47 | 4.2565e-04 | 3.8309e-03 | 9.1211e-04 | **YES (p<0.05)** |
| Targeted: TrickyCooperator (5% noise) | +0.0175 | [-0.1175, +0.1890] | -0.07 | 7.5315e-01 | 1.0000e+00 | 8.0695e-01 | No |
| Targeted: TwoTitsForTat (5% noise) | +0.3718 | [+0.1948, +0.5765] | +0.77 | 9.7920e-06 | 1.2730e-04 | 4.8960e-05 | **YES (p<0.05)** |
| Targeted: ZDExtort2 (5% noise) | +0.0702 | [-0.0170, +0.1748] | -0.03 | 4.6293e-01 | 1.0000e+00 | 5.7867e-01 | No |
| Targeted: ZDExtort2v2 (5% noise) | +0.1275 | [+0.0418, +0.2277] | +0.23 | 3.1226e-02 | 1.8735e-01 | 4.6838e-02 | No |
| Targeted: ZDExtort3 (5% noise) | +0.0173 | [-0.0280, +0.0735] | +0.03 | 5.9335e-01 | 1.0000e+00 | 6.8463e-01 | No |
