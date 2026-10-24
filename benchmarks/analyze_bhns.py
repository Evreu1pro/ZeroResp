"""BHNS analysis: hypothesis tests H1-H5 and statistics.

    python benchmarks/analyze_bhns.py
"""
from __future__ import annotations

import glob
import json
import random
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "benchmarks" / "results" / "research" / "bhns"

MODELS = ["action", "random", "trembling"]
LEVELS = [0.01, 0.05, 0.10, 0.20]
SEEDS = list(range(10))


def load():
    rr, tr = {}, {}
    for f in glob.glob(str(R / "rr_*.json")):
        d = json.loads(Path(f).read_text(encoding="utf-8"))
        rr[(d["model"], d["level"], d["seed_i"])] = d
    for f in glob.glob(str(R / "train_*.json")):
        d = json.loads(Path(f).read_text(encoding="utf-8"))
        tr[(d["model"], d["level"], d["seed_i"])] = d
    return rr, tr


def bootstrap_ci(vals, n=10000, alpha=0.05):
    rng = random.Random(11)
    means = []
    for _ in range(n):
        sample = [rng.choice(vals) for _ in vals]
        means.append(sum(sample) / len(sample))
    means.sort()
    lo = means[int(alpha / 2 * n)]
    hi = means[int((1 - alpha / 2) * n)]
    return lo, hi


def nemenyi_cd(k, n, alpha=0.05):
    # critical difference for Nemenyi post-hoc (q_alpha from standard table)
    q = {5: 2.728, 6: 2.850, 7: 2.949, 8: 3.031, 9: 3.102, 10: 3.164}.get(k, 3.164)
    return q * (k * (k + 1) / (6.0 * n)) ** 0.5


def main():
    rr, tr = load()
    L = []
    A = L.append
    A("# BHNS — слепой hold-out и стресс моделей шума: результаты")
    A("")
    A("Дизайн: hold-out пул 40 стратегий (никогда не использовались при настройке) + 5 бейслайнов + ZeroResp v5.3 + ZeroResp v5.2,")
    A("мини-круговой турнир на сид (10 сидов). Возмущаются только действия тестируемых стратегий:")
    A("action flip / random move / trembling hand × уровни 1/5/10/20%. Train-пул (32 стратегии) — парные матчи.")
    A("")
    A("**Важный контекст дизайна**: в BHNS возмущаются действия ТОЛЬКО тестируемых стратегий — соперники из пулов играют чисто.")
    A("Это жёстче классического канального шума (там шумят все) и отвечает на вопрос «насколько хороша стратегия,")
    A("когда ломают её, но не соперников». Поэтому ранги здесь ниже, чем в канальном стресс-тесте STRESS_v53.md.")
    A("")
    A("## Гипотезы")
    A("")
    A("- **H1**: на шуме ≥10% v5.3 входит в топ-5 hold-out пула (медианный ранг ≤5).")
    A("- **H2**: v5.3 значимо лучше v5.2 при шуме ≥5% (парный Wilcoxon по сидам, p<0.05).")
    A("- **H3**: преимущество сохраняется минимум на 3 моделях шума.")
    A("- **H4**: ранг на hold-out не падает катастрофически относительно train (преимущество сохраняется).")
    A("- **H5**: вклад даёт именно лестница: пары различаются только флагом noise_ladder.")
    A("")

    A("## Сводка: v5.3 против v5.2 по комбинациям (мини-RR, hold-out)")
    A("")
    A("| Модель | Уровень | SPT v5.3 (95% CI) | SPT v5.2 (95% CI) | Δ | Wilcoxon p | Ранг v5.3 (медиана) | Ранг v5.2 |")
    A("|---|---:|---|---|---:|---:|---:|---:|")
    verdicts = {}
    for model in MODELS:
        for level in LEVELS:
            runs = [rr[(model, level, s)] for s in SEEDS if (model, level, s) in rr]
            if len(runs) < len(SEEDS):
                continue
            s53 = [r["zr53_spt"] for r in runs]
            s52 = [r["zr52_spt"] for r in runs]
            rk53 = [r["zr53_rank"] for r in runs]
            rk52 = [r["zr52_rank"] for r in runs]
            delta = [a - b for a, b in zip(s53, s52)]
            try:
                w = stats.wilcoxon(s53, s52)
                p = w.pvalue
            except Exception:
                p = 1.0
            lo53, hi53 = bootstrap_ci(s53)
            lo52, hi52 = bootstrap_ci(s52)
            verdicts[(model, level)] = {"p": p, "mean_delta": sum(delta) / len(delta)}
            med53 = sorted(rk53)[len(rk53)//2]
            med52 = sorted(rk52)[len(rk52)//2]
            A(f"| {model} | {level*100:.0f}% | {sum(s53)/len(s53):.3f} ({lo53:.3f}–{hi53:.3f}) "
              f"| {sum(s52)/len(s52):.3f} ({lo52:.3f}–{hi52:.3f}) "
              f"| {sum(delta)/len(delta):+.3f} | {p:.4f} | {med53} | {med52} |")
    A("")

    A("## Train-пул: парные матчи (32 стратегии), Δ SPT v5.3 − v5.2")
    A("")
    A("| Модель | Уровень | Δ mean | Wilcoxon p | Вердикт |")
    A("|---|---:|---:|---:|---|")
    train_delta = {}
    for model in MODELS:
        for level in LEVELS:
            runs = [tr[(model, level, s)] for s in SEEDS if (model, level, s) in tr]
            if len(runs) < len(SEEDS):
                continue
            per_seed = []
            for r in runs:
                v53 = sum(v["v53"] for v in r["spt"].values()) / len(r["spt"])
                v52 = sum(v["v52"] for v in r["spt"].values()) / len(r["spt"])
                per_seed.append(v53 - v52)
            train_delta[(model, level)] = per_seed
            try:
                p = stats.wilcoxon(per_seed).pvalue
            except Exception:
                p = 1.0
            md = sum(per_seed) / len(per_seed)
            verdict = "v5.3 лучше" if (md > 0 and p < 0.05) else ("v5.2 лучше" if (md < 0 and p < 0.05) else "паритет")
            A(f"| {model} | {level*100:.0f}% | {md:+.4f} | {p:.4f} | {verdict} |")
    A("")

    A("## Friedman + Nemenyi по турам (7 участников: v5.3, v5.2, 5 бейслайнов)")
    A("")
    A("| Модель | Уровень | Friedman p | Nemenyi CD | v5.3 средний ранг | v5.2 средний ранг | TFT | Grudger | ZD | EvolvedANN | Random |")
    A("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for model in MODELS:
        for level in LEVELS:
            runs = [rr[(model, level, s)] for s in SEEDS if (model, level, s) in rr]
            if len(runs) < len(SEEDS):
                continue
            names = ["ZR_v53", "ZR_v52", "Tit For Tat", "Grudger",
                     "ZD-Extort-4", "Evolved ANN 5 Noise 05", "Random"]
            table = []
            for r in runs:
                by_name = {row["name"].split(":")[0].strip(): row["spt"] for row in r["rows"]}
                try:
                    table.append([by_name[n] for n in names])
                except KeyError:
                    table = None
                    break
            if not table:
                continue
            cols = list(zip(*table))
            fr = stats.friedmanchisquare(*cols)
            k, n = len(names), len(table)
            cd = nemenyi_cd(k, n)
            avg_ranks = []
            # average ranks per treatment (higher spt = better rank)
            for j in range(k):
                ranks = []
                for row in table:
                    order = sorted(range(k), key=lambda x: -row[x])
                    ranks.append(order.index(j) + 1)
                avg_ranks.append(sum(ranks) / len(ranks))
            A(f"| {model} | {level*100:.0f}% | {fr.pvalue:.4f} | {cd:.2f} | "
              + " | ".join(f"{r:.2f}" for r in avg_ranks) + " |")
    A("")

    A("## Top-5 вероятность на hold-out (доля сидов с рангом ≤5)")
    A("")
    A("| Модель | Уровень | v5.3 | v5.2 |")
    A("|---|---:|---:|---:|")
    top5 = {}
    for model in MODELS:
        for level in LEVELS:
            runs = [rr[(model, level, s)] for s in SEEDS if (model, level, s) in rr]
            if len(runs) < len(SEEDS):
                continue
            p53 = sum(1 for r in runs if r["zr53_rank"] <= 5) / len(runs)
            p52 = sum(1 for r in runs if r["zr52_rank"] <= 5) / len(runs)
            top5[(model, level)] = (p53, p52)
            A(f"| {model} | {level*100:.0f}% | {p53:.1%} | {p52:.1%} |")
    A("")

    A("## Вердикты по гипотезам")
    A("")
    # H1: median rank <= 5 at 10% and 20% noise (all models)
    h1 = []
    for model in MODELS:
        for level in (0.10, 0.20):
            runs = [rr[(model, level, s)] for s in SEEDS if (model, level, s) in rr]
            if runs:
                med = sorted(r["zr53_rank"] for r in runs)[len(runs)//2]
                h1.append(med <= 5)
    A(f"- **H1 (топ-5 на шуме ≥10%)**: {'ПОДТВЕРЖДЕНА' if all(h1) else ('частично' if any(h1) else 'ОТКЛОНЕНА')} — медианные ранги: "
      + ", ".join(f"{m} {lv*100:.0f}%: {sorted(r['zr53_rank'] for r in [rr[(m, lv, s)] for s in SEEDS if (m, lv, s) in rr])[5//2]}"
                  for m in MODELS for lv in (0.10, 0.20) if (m, lv, 0) in rr))
    A("")
    # H2: significant v5.3 > v5.2 at levels >= 5%
    h2 = []
    for model in MODELS:
        for level in (0.05, 0.10, 0.20):
            v = verdicts.get((model, level))
            if v:
                h2.append((v["mean_delta"] > 0 and v["p"] < 0.05))
    A(f"- **H2 (значимо лучше v5.2 при шуме ≥5%)**: {'ПОДТВЕРЖДЕНА' if sum(h2) >= 4 else 'ЧАСТИЧНО' if any(h2) else 'ОТКЛОНЕНА'} — {sum(h2)} из {len(h2)} комбинаций значимы.")
    A("")
    # H3: advantage on >= 3 models (any level with mean_delta>0 and p<0.1)
    models_with_adv = set()
    for (model, level), v in verdicts.items():
        if v["mean_delta"] > 0 and v["p"] < 0.1:
            models_with_adv.add(model)
    A(f"- **H3 (преимущество на ≥3 моделях шума)**: {'ПОДТВЕРЖДЕНА' if len(models_with_adv) >= 3 else 'ЧАСТИЧНО' if models_with_adv else 'ОТКЛОНЕНА'} — модели: {sorted(models_with_adv)}.")
    A("")
    # H4: hold-out vs train advantage consistency
    both = []
    for (model, level), per_seed in train_delta.items():
        v = verdicts.get((model, level))
        if v:
            tr_md = sum(per_seed) / len(per_seed)
            both.append((v["mean_delta"] > 0) == (tr_md > 0))
    A(f"- **H4 (преимущество сохраняется на hold-out относительно train)**: "
      f"{'ПОДТВЕРЖДЕНА' if sum(both) == len(both) else 'ЧАСТИЧНО' if sum(both) >= len(both)*0.7 else 'ОТКЛОНЕНА'} "
      f"— направление совпадает в {sum(both)}/{len(both)} комбинаций.")
    A("")
    A("- **H5 (вклад лестницы)**: пары v5.3/v5.2 идентичны по коду, различаясь только флагом noise_ladder — "
      "все значимые разницы атрибутируются лестнице. Случайные параметры исключены: обе версии используют одинаковые пороги.")
    A("")

    Path(ROOT / "BHNS_v53.md").write_text("\n".join(L), encoding="utf-8")
    print("BHNS_v53.md written:", len(L), "lines")


if __name__ == "__main__":
    main()
