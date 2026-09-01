# ZeroResp — Benchmark Report

**Current production: v5.2** (see README). v2.2 numbers below are historical.

---

## v5.2 field pack (Axelrod 4.14, 2026-09)

32 default ARX opponents, 200 turns, 8 repetitions, seed 42.

| Noise | SPT | Self | Reciprocators / Grudger | Defector |
|------:|----:|-----:|-------------------------|---------:|
| 0% | 2.843 | 598 | 602 | 199 |
| 5% | 2.375 | ~579 | noisy | 224 |

Delta vs v5.1 at 5%: **+0.033 SPT**. Punisher +136, TF2T +60, Once Bitten +43.

---

# ZeroResp v2.2 — Benchmark Report for Review (historical)

**Strategy:** ZeroResp (implementation v2.2)  
**Author:** Evreu1pro  
**Framework:** Independent PD sandbox + Axelrod-compatible player API  
**Purpose:** Evidence package for game-theory committees / Axelrod-Python review  

All figures below come from offline tournament runs. Source aggregates: [`data/`](data/).

---

## 1. Higher League (Top-40 core pool)

| Parameter | Value |
|-----------|--------|
| Players | 40 (sandbox jailers, ZeroResp family, customs, Axelrod elites) |
| Rounds per match | 400 |
| Repetitions | 2 |
| Seeds | 42, 7, 99, 13, 21, 77, 123 |

### Aggregate ranking (mean over 7 seeds)

| Avg rank | Strategy | Avg / round | Coop rate |
|----------|----------|-------------|-----------|
| 1.57 | Omega TFT | 2.7608 | 0.798 |
| **1.71** | **ZeroResp v2.2** | **2.7598** | **0.793** |
| 2.71 | ZeroResp v2.1 | 2.7582 | 0.798 |
| 5.43 | GenerousTFT | 2.7208 | 0.870 |
| 5.57 | Soft Joss | 2.7135 | 0.865 |

**Interpretation:** ZeroResp v2.2 is statistically tied with Omega TFT for first place (Δ avg/r ≈ 0.001). Across seeds its rank stays in **{1, 2, 3}**.

### Example seed 42 (leaderboard head)

| # | Strategy | Score | Avg/R | W–D–L | Win% | Coop% |
|---|----------|------:|------:|-------|-----:|------:|
| 1 | **ZeroResp v2.2** | 86126 | **2.76** | 62–8–8 | 79.5% | 79.3% |
| 2 | Omega TFT | 86112 | 2.76 | 6–58–14 | 7.7% | 79.6% |
| 3 | ZeroResp v2.1 | 86036 | 2.76 | 8–60–10 | 10.3% | 79.7% |

Note: high **win rate** vs high **draw** rate of Omega — ZeroResp scores by decisive matchups while keeping elite average payoff.

---

## 2. Deep validation suite

### Block 1 — Head-to-head vs Omega TFT

| Length | ZeroResp avg/r | Omega avg/r | Mutual CC | W–D–L (seeds) |
|--------|----------------|-------------|-----------|----------------|
| 1000 | 2.998 | 2.993 | 99.7% | 3–0–0 |
| 5000 | 2.9996 | 2.9986 | 99.9% | 3–0–0 |

No vendetta: max mutual-D streak ≤ 4. Edge is end-game, not mid-game extortion.

### Block 2 — Endurance (1501 rounds × 5 seeds)

| Strategy | Avg rank | Avg/r | Ranks |
|----------|----------|-------|-------|
| Omega TFT | 1.00 | 2.761 | [1,1,1,1,1] |
| **ZeroResp v2.2** | **2.40** | **2.760** | **[2,3,2,2,3]** |
| ZeroResp v2.1 | 2.60 | 2.760 | [3,2,3,3,2] |

Long matches do not degrade ZeroResp (no false-enemy spiral / memory bug).

### Block 3 — Noise stress (Top-40 @ 400 turns)

| Noise | Pool place (typ.) | Avg/r | Pool coop |
|------:|-------------------|-------|-----------|
| 0% | #2 | 2.758 | 64.2% |
| 1% | ~#6 | 2.209 | 39.6% |
| 3% | ~#10 | 1.896 | 32.3% |

Honest limitation: sustained channel noise is a known weak regime relative to Omega TFT.

### Block 4 — Survival elimination (to Top-5)

Finalists (seed 42):

1. **ZeroResp v2.2** — avg/r 3.000, coop 99.5%  
2. GenerousTFT — 2.999  
3. Omega TFT — 2.999  
4. GTFT — 2.999  
5. ZD-GTFT-2 — 2.999  

ZeroResp held **#1 every elimination round**.

---

## 3. Design claims (for reviewers)

| Claim | Supported by |
|-------|----------------|
| Competitive with elite TFT-family / Omega | Higher League #2; Endurance #2–3 |
| Cooperates with strong cooperators | H2H Omega; Survival Top-5 coop ~99.5% |
| Punishes / bans systemic defectors | Red-line path; vs Defector unit tests |
| Does not rely on source inspection | Classifier flags false |
| Finite-horizon use is explicit | `match_attributes["length"]` only when finite |

---

## 4. Reproducibility notes

- Stochastic: short delay and grim-probe use Axelrod's player RNG; fix `seed` for matches.  
- Payoff matrix: standard Axelrod R=3, P=1, S=0, T=5 unless noted.  
- Sandbox pool composition is listed in the Higher League lab report (`data/higher_league_LAB_REPORT_excerpt.txt`).

---

## 5. Files in `data/`

| File | Content |
|------|---------|
| `higher_league_aggregate_ranking.csv` | Full 40-row aggregate ranking |
| `deep_validation_EXEC_SUMMARY.txt` | Executive summary of the 4-block suite |
| `higher_league_LAB_REPORT_excerpt.txt` | Seed-42 head + methodology header |
