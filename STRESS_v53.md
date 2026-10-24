# ZeroResp v5.3 — стресс-карта позиций по режимам

Полный пул библиотеки: 221 стратегия + ZeroResp, круговой турнир, 200 ходов, 1 повторение, seed 42.
Для каждой пары (шум × версия) — ранг ZeroResp и лучший SPT каждой «идеи» (семьи стратегий).

## Позиции ZeroResp по режимам

| Шум | Версия | Ранг | SPT | Отставание от лидера |
|---:|---|---:|---:|---:|
| 0% | v5.3 | **12 / 222** | 627.21 | −14.03 |
| 0% | v5.2 | **12 / 222** | 627.20 | −14.04 |
| 1% | v5.3 | **5 / 222** | 575.86 | −21.64 |
| 1% | v5.2 | **5 / 222** | 575.15 | −22.35 |
| 3% | v5.3 | **5 / 222** | 549.27 | −29.39 |
| 3% | v5.2 | **5 / 222** | 548.01 | −30.66 |
| 5% | v5.3 | **4 / 222** | 536.86 | −23.19 |
| 5% | v5.2 | **3 / 222** | 539.72 | −20.32 |
| 10% | v5.3 | **2 / 222** | 516.48 | −5.78 |
| 10% | v5.2 | **2 / 222** | 513.25 | −9.09 |

## Кто выигрывает в каждом режиме (топ-5 + ZeroResp)

### Шум 0% (v5.3)

| # | Стратегия | SPT | Семья |
|---:|---|---:|---|
| 1 | Evolved FSM 6 | 641.24 | Обученные (Evolved/LookerUp/ANN/HMM/PSO/Meta) |
| 2 | EvolvedLookerUp2_2_2 | 639.18 | Обученные (Evolved/LookerUp/ANN/HMM/PSO/Meta) |
| 3 | Evolved FSM 16 | 636.47 | Обученные (Evolved/LookerUp/ANN/HMM/PSO/Meta) |
| 4 | Evolved HMM 5 | 633.75 | Обученные (Evolved/LookerUp/ANN/HMM/PSO/Meta) |
| 5 | PSO Gambler 1_1_1 | 633.12 | Обученные (Evolved/LookerUp/ANN/HMM/PSO/Meta) |

### Шум 3% (v5.3)

| # | Стратегия | SPT | Семья |
|---:|---|---:|---|
| 1 | Evolved ANN 5 Noise 05 | 578.67 | Обученные (Evolved/LookerUp/ANN/HMM/PSO/Meta) |
| 2 | Evolved FSM 16 Noise 05 | 567.33 | Обученные (Evolved/LookerUp/ANN/HMM/PSO/Meta) |
| 3 | Second by RichardHufford | 556.46 | Прочие |
| 4 | Evolved ANN | 552.63 | Обученные (Evolved/LookerUp/ANN/HMM/PSO/Meta) |
| 5 | ZeroResp v5.3: 25, True, <zeroresp.Features object at 0x000001BFFB17BE40> | 549.27 | ZeroResp (наша) |

### Шум 10% (v5.3)

| # | Стратегия | SPT | Семья |
|---:|---|---:|---|
| 1 | Evolved ANN 5 Noise 05 | 522.26 | Обученные (Evolved/LookerUp/ANN/HMM/PSO/Meta) |
| 2 | ZeroResp v5.3: 25, True, <zeroresp.Features object at 0x000001BFFB039C40> | 516.48 | ZeroResp (наша) |
| 3 | First by Downing | 511.73 | Прочие |
| 4 | Second by RichardHufford | 506.89 | Прочие |
| 5 | Revised Downing | 506.76 | Прочие |

## Сравнение идей: лучший представитель каждой семьи в каждом режиме

| Шум | Версия | ZeroResp | Обученные | TFT | Grudger | ZD | Эксплуататоры |
|---:|---|---:|---:|---:|---:|---:|---:|
| 0% | v5.3 | **627.21** | 627.21 | 641.24 | 620.46 | 593.33 | 605.00 | 606.31 |
| 0% | v5.2 | **627.20** | 627.20 | 641.24 | 620.46 | 593.33 | 605.00 | 606.31 |
| 1% | v5.3 | **575.86** | 575.86 | 597.50 | 571.26 | 528.08 | 549.02 | 556.80 |
| 1% | v5.2 | **575.15** | 575.15 | 597.50 | 571.26 | 528.06 | 549.01 | 556.80 |
| 3% | v5.3 | **549.27** | 549.27 | 578.67 | 532.41 | 492.29 | 518.23 | 530.42 |
| 3% | v5.2 | **548.01** | 548.01 | 578.67 | 532.34 | 492.26 | 518.23 | 530.42 |
| 5% | v5.3 | **536.86** | 536.86 | 560.04 | 518.63 | 474.35 | 499.06 | 501.71 |
| 5% | v5.2 | **539.72** | 539.72 | 560.04 | 518.63 | 474.37 | 499.07 | 501.71 |
| 10% | v5.3 | **516.48** | 516.48 | 522.26 | 495.86 | 474.21 | 478.68 | 488.77 |
| 10% | v5.2 | **513.25** | 513.25 | 522.34 | 495.87 | 474.21 | 478.68 | 488.75 |

## Кто стоит выше ZeroResp (по режимам)

### Шум 0% — выше нас 11 стратегий:

- 1. Evolved FSM 6 (641.24) — Обученные (Evolved/LookerUp/ANN/HMM/PSO/Meta)
- 2. EvolvedLookerUp2_2_2 (639.18) — Обученные (Evolved/LookerUp/ANN/HMM/PSO/Meta)
- 3. Evolved FSM 16 (636.47) — Обученные (Evolved/LookerUp/ANN/HMM/PSO/Meta)
- 4. Evolved HMM 5 (633.75) — Обученные (Evolved/LookerUp/ANN/HMM/PSO/Meta)
- 5. PSO Gambler 1_1_1 (633.12) — Обученные (Evolved/LookerUp/ANN/HMM/PSO/Meta)
- 6. Evolved ANN 5 (632.99) — Обученные (Evolved/LookerUp/ANN/HMM/PSO/Meta)
- 7. Evolved ANN (631.93) — Обученные (Evolved/LookerUp/ANN/HMM/PSO/Meta)
- 8. Evolved FSM 16 Noise 05 (630.58) — Обученные (Evolved/LookerUp/ANN/HMM/PSO/Meta)
- 9. PSO Gambler Mem1 (627.95) — Обученные (Evolved/LookerUp/ANN/HMM/PSO/Meta)
- 10. PSO Gambler 2_2_2 (627.39) — Обученные (Evolved/LookerUp/ANN/HMM/PSO/Meta)
- 11. Evolved FSM 4 (627.25) — Обученные (Evolved/LookerUp/ANN/HMM/PSO/Meta)

### Шум 5% — выше нас 3 стратегий:

- 1. Evolved ANN 5 Noise 05 (560.04) — Обученные (Evolved/LookerUp/ANN/HMM/PSO/Meta)
- 2. Evolved FSM 16 Noise 05 (545.06) — Обученные (Evolved/LookerUp/ANN/HMM/PSO/Meta)
- 3. Second by RichardHufford (538.45) — Прочие

### Шум 10% — выше нас 1 стратегий:

- 1. Evolved ANN 5 Noise 05 (522.26) — Обученные (Evolved/LookerUp/ANN/HMM/PSO/Meta)
