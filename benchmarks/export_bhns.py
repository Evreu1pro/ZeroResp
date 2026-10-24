"""Export BHNS data to CSV (user-requested format) + hardened statistics.

    python benchmarks/export_bhns.py
"""
from __future__ import annotations

import csv
import glob
import json
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "benchmarks" / "results" / "research" / "bhns"

MODELS = ["action", "random", "trembling", "perception"]
LEVELS = [0.01, 0.05, 0.10, 0.20]
KEY_COMBOS = {(m, l) for m in ("action", "random", "trembling") for l in (0.10, 0.20)}


def seeds_for(model, level):
    if model == "perception":
        return range(10) if level in (0.05, 0.10, 0.20) else []
    if (model, level) in KEY_COMBOS:
        return range(30)
    return range(10)


def load():
    rr, tr = {}, {}
    for f in glob.glob(str(R / "rr_*.json")):
        d = json.loads(Path(f).read_text(encoding="utf-8"))
        rr[(d["model"], d["level"], d["seed_i"])] = d
    for f in glob.glob(str(R / "train_*.json")):
        d = json.loads(Path(f).read_text(encoding="utf-8"))
        tr[(d["model"], d["level"], d["seed_i"])] = d
    return rr, tr


def cliffs_delta(a, b):
    gt = sum(1 for x in a for y in b if x > y)
    lt = sum(1 for x in a for y in b if x < y)
    return (gt - lt) / (len(a) * len(b))


def bootstrap_median_ci(vals, n=10000, alpha=0.05):
    rng = np.random.default_rng(11)
    arr = np.array(vals)
    idx = rng.integers(0, len(arr), (n, len(arr)))
    medians = np.median(arr[idx], axis=1)
    return float(np.percentile(medians, 100 * alpha / 2)), float(np.percentile(medians, 100 * (1 - alpha / 2)))


def holm(pvals):
    order = sorted(range(len(pvals)), key=lambda i: pvals[i])
    m = len(pvals)
    adj = [0.0] * m
    prev = 0.0
    for rank, i in enumerate(order):
        adj[i] = max(prev, min(1.0, pvals[i] * (m - rank)))
        prev = adj[i]
    return adj


def bh_fdr(pvals):
    order = sorted(range(len(pvals)), key=lambda i: pvals[i])
    m = len(pvals)
    adj = [0.0] * m
    prev = 1.0
    for rank in range(m - 1, -1, -1):
        i = order[rank]
        val = min(prev, pvals[i] * m / (rank + 1))
        adj[i] = val
        prev = val
    return adj


def export_csv(rr, tr):
    OUT = ROOT / "benchmarks" / "results" / "research"
    # bhns_raw_train.csv
    with open(OUT / "bhns_raw_train.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["run_id", "seed", "noise_model", "noise_level", "pool",
                    "version", "opponent", "payoff", "rounds", "ladder_activated"])
        for (model, level, seed_i), d in sorted(tr.items()):
            for opp, row in d["spt"].items():
                for ver in ("v53", "v52"):
                    w.writerow([f"{model}_{int(level*100)}_{seed_i}", seed_i,
                                model, level, "train", ver, opp,
                                row[ver], 200, row.get("ladder_activated", "")])
    # bhns_raw_holdout.csv: per-player SPT per seed (mini-RR aggregate)
    with open(OUT / "bhns_raw_holdout.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["run_id", "seed", "noise_model", "noise_level", "pool",
                    "version_or_player", "mean_spt", "rank_of_47"])
        for (model, level, seed_i), d in sorted(rr.items()):
            for row in d["rows"]:
                ver = ("v53" if row["is_zr53"] else "v52" if row["is_zr52"] else row["name"])
                w.writerow([f"{model}_{int(level*100)}_{seed_i}", seed_i,
                            model, level, "holdout", ver, row["spt"], row["pos"]])
    # bhns_summary.csv
    with open(OUT / "bhns_summary.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["version", "noise_model", "noise_level", "pool",
                    "n_seeds", "mean", "std", "median", "mean_rank"])
        for (model, level, seed_i), d in sorted(rr.items()):
            pass
        agg = {}
        for (model, level, seed_i), d in sorted(rr.items()):
            for row in d["rows"]:
                ver = ("v53" if row["is_zr53"] else "v52" if row["is_zr52"] else row["name"])
                if row["is_zr53"]:
                    key = ("v5.3", model, level, "holdout")
                elif row["is_zr52"]:
                    key = ("v5.2", model, level, "holdout")
                else:
                    continue
                agg.setdefault(key, {"vals": [], "ranks": []})
                agg[key]["vals"].append(row["spt"])
                agg[key]["ranks"].append(row["pos"])
        for (model, level, seed_i), d in sorted(tr.items()):
            v53 = sum(v["v53"] for v in d["spt"].values()) / len(d["spt"])
            v52 = sum(v["v52"] for v in d["spt"].values()) / len(d["spt"])
            agg.setdefault(("v5.3", model, level, "train"), {"vals": [], "ranks": []})["vals"].append(v53)
            agg.setdefault(("v5.2", model, level, "train"), {"vals": [], "ranks": []})["vals"].append(v52)
        for (ver, model, level, pool), d in sorted(agg.items()):
            vals = d["vals"]
            w.writerow([ver, model, level, pool, len(vals),
                        round(sum(vals) / len(vals), 4),
                        round(float(np.std(vals)), 4),
                        round(float(np.median(vals)), 4),
                        round(sum(d["ranks"]) / len(d["ranks"]), 2) if d["ranks"] else ""])
    print("CSV exported:", OUT / "bhns_raw_train.csv", OUT / "bhns_raw_holdout.csv", OUT / "bhns_summary.csv")


def hardened_stats(rr, tr):
    L = []
    A = L.append
    A("## Укреплённая статистика (ключевые комбинации, n=30 сидов)")
    A("")
    A("Тесты: Wilcoxon signed-rank (exact при отсутствии связок) по сидам; множественная коррекция")
    A("Holm-Bonferroni и BH-FDR по всей семье из 12 train-тестов. Effect size: медианная разница")
    A("SPT с bootstrap 95% CI и Cliff's delta. Единица анализа — средний SPT за сид; сиды — независимые")
    A("реализации шума на фиксированном пуле (jackknife по соперникам ниже проверяет устойчивость знака).")
    A("")
    A("| Модель | Уровень | n | медиана Δ SPT (очки/матч) | 95% CI медианы | Cliff's δ | Wilcoxon p (exact) | p-Holm | p-BH(FDR) | Вердикт |")
    A("|---|---:|---:|---:|---|---:|---:|---:|---:|---|")
    rows = []
    jack = {}
    for model in MODELS:
        for level in LEVELS:
            seeds = sorted(s for (m, l, s) in tr if m == model and l == level)
            if not seeds:
                continue
            per_seed_opp = []
            for s in seeds:
                d = tr[(model, level, s)]
                per_seed_opp.append({opp: v["v53"] - v["v52"] for opp, v in d["spt"].items()})
            all_deltas = [x for d in per_seed_opp for x in d.values()]
            seed_means = [sum(d.values()) / len(d) for d in per_seed_opp]
            diffs = np.array(seed_means)
            med = float(np.median(diffs))
            lo, hi = bootstrap_median_ci(seed_means)
            # Cliff's delta по пулу всех парных дельт против нуля
            delta_stat = cliffs_delta(all_deltas, [0.0] * len(all_deltas))
            try:
                w = stats.wilcoxon(diffs, method="auto")
                p = float(w.pvalue)
            except Exception:
                p = 1.0
            rows.append((model, level, len(diffs), med, (lo, hi), delta_stat, p))
            jack[(model, level)] = per_seed_opp
    pvals = [r[6] for r in rows]
    holm_adj = holm(pvals)
    fdr_adj = bh_fdr(pvals)
    for (model, level, n, med, (lo, hi), cd, p), ph, pf in zip(rows, holm_adj, fdr_adj):
        verdict = ("значимо (Holm)" if ph < 0.05 else "значимо (FDR)" if pf < 0.05 else "незначимо")
        A(f"| {model} | {level*100:.0f}% | {n} | {med:+.2f} | [{lo:+.2f}, {hi:+.2f}] | {cd:+.2f} | {p:.5f} | {ph:.4f} | {pf:.4f} | {verdict} |")
    A("")
    sig_holm = [(m, l) for (m, l, n, med, ci, cd, p), ph in zip(rows, holm_adj) if ph < 0.05]
    A(f"Выживших после Holm-Bonferroni: {len(sig_holm)} из {len(rows)}: {sig_holm}")
    A("")
    A("## Jackknife по соперникам (ключевые комбинации)")
    A("")
    A("Знак медианной дельты при удалении одного соперника (устойчивость = доля удалений, сохраняющих знак):")
    A("")
    A("| Модель | Уровень | Знак полн. выборки | Устойчивость знака | Худший поворот |")
    A("|---|---:|---|---:|---|")
    for model in ("action", "random", "trembling"):
        for level in (0.10, 0.20):
            per_seed_opp = jack.get((model, level))
            if not per_seed_opp:
                continue
            opponents = list(per_seed_opp[0].keys())
            full = float(np.median([sum(d.values()) / len(d) for d in per_seed_opp]))
            full_sign = 1 if full > 0 else -1
            stable = 0
            worst = None
            for drop in opponents:
                sub = [ {o: v for o, v in d.items() if o != drop} for d in per_seed_opp ]
                med = float(np.median([sum(d.values()) / len(d) for d in sub]))
                s = 1 if med > 0 else -1
                if s == full_sign:
                    stable += 1
                if worst is None or abs(med) < abs(worst[1]):
                    worst = (drop, round(med, 2))
            A(f"| {model} | {level*100:.0f}% | {full:+.2f} | {stable}/{len(opponents)} | {worst[0]} ({worst[1]:+.2f}) |")
    A("")
    A("## Perception-flip: falsifiable предсказание")
    A("")
    A("Предсказание: при perception-шуме лестница не видит своих флипов -> не активируется -> v5.3 = v5.2.")
    A("")
    A("| Уровень | n сидов | Δ SPT v5.3−v5.2 (train) | Активаций лестницы | Wilcoxon p |")
    A("|---:|---:|---:|---:|---:|")
    for level in (0.05, 0.10, 0.20):
        seeds = sorted(s for (m, l, s) in tr if m == "perception" and l == level)
        if not seeds:
            continue
        per_seed = []
        activations = 0
        total = 0
        for s in seeds:
            d = tr[("perception", level, s)]
            v53 = sum(v["v53"] for v in d["spt"].values()) / len(d["spt"])
            v52 = sum(v["v52"] for v in d["spt"].values()) / len(d["spt"])
            per_seed.append(v53 - v52)
            activations += sum(1 for v in d["spt"].values() if v.get("ladder_activated"))
            total += len(d["spt"])
        try:
            p = float(stats.wilcoxon(per_seed).pvalue)
        except Exception:
            p = 1.0
        A(f"| {level*100:.0f}% | {len(per_seed)} | {sum(per_seed)/len(per_seed):+.4f} | {activations}/{total} | {p:.4f} |")
    A("")
    return L


def main():
    rr, tr = load()
    export_csv(rr, tr)
    L = hardened_stats(rr, tr)
    # дописать в BHNS_v53.md секцию укреплённой статистики (или создать отдельный файл)
    out = ROOT / "BHNS_v53_hardened.md"
    header = ["# BHNS — укреплённая статистика (дополнение к BHNS_v53.md)", ""]
    out.write_text("\n".join(header + L), encoding="utf-8")
    print("BHNS_v53_hardened.md written:", len(L), "lines")


if __name__ == "__main__":
    main()
