"""ZDB Phase 5c: Mechanism Instrumentation of Bimodality on TTFT and Gradual."""
from __future__ import annotations

import csv
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import axelrod as axl
import numpy as np

from zeroresp import ZeroResp as V53
from zeroresp_v54 import ZeroRespV54Full as V54

TURNS = 200
REPS = 30
BASE_SEED = 42

def instrument_match(bot_cls, opp_cls, seed, noise=0.05):
    bot = bot_cls()
    opp = opp_cls()
    match = axl.Match((bot, opp), turns=TURNS, seed=seed, noise=noise)

    red_line_step = None
    first_my_flip_step = None
    first_opp_d_step = None
    tactical_at_end = None
    prefilter_triggered = False

    # Hook or inspect by turns
    match.play()

    # Post-match inspection of bot state
    is_red = getattr(bot, "is_red_line", False)
    final_state = getattr(bot, "_state", None)
    tactical = getattr(bot, "tactical", None)
    my_flips = getattr(bot, "nl_my_flips", 0)
    score = sum(x[0] for x in match.scores()) / TURNS
    opp_score = sum(x[1] for x in match.scores()) / TURNS

    return {
        "score": score,
        "opp_score": opp_score,
        "is_red": is_red,
        "final_state": str(final_state),
        "tactical": tactical,
        "my_flips": my_flips,
        "history_my_d": sum(1 for a in bot.history if a == axl.Action.D),
        "history_opp_d": sum(1 for a in opp.history if a == axl.Action.D),
    }

def run_phase_5c():
    print("=" * 65)
    print("PHASE 5c: BIMODALITY MECHANISM INSTRUMENTATION (TTFT & Gradual)")
    print(f"Noise: 5%, Reps: {REPS}, Turns: {TURNS}")
    print("=" * 65)

    opponents = ["TwoTitsForTat", "Gradual"]
    results = {opp: [] for opp in opponents}

    for opp_name in opponents:
        opp_cls = getattr(axl, opp_name)
        print(f"\nAnalyzing {opp_name} across 30 seeds...")
        for rep in range(REPS):
            seed = BASE_SEED + rep
            d53 = instrument_match(V53, opp_cls, seed=seed)
            d54 = instrument_match(V54, opp_cls, seed=seed)

            delta = d54["score"] - d53["score"]
            results[opp_name].append({
                "seed": seed,
                "delta": delta,
                "v53_score": d53["score"],
                "v54_score": d54["score"],
                "v53_red": d53["is_red"],
                "v54_red": d54["is_red"],
                "v53_my_d": d53["history_my_d"],
                "v54_my_d": d54["history_my_d"],
                "v54_tactical": d54["tactical"],
            })

    out_md = Path("ZDB_phase5c_bimodality.md")
    lines = []
    lines.append("# ZDB Phase 5c — Bimodality Instrumentation Report\n\n")

    for opp_name in opponents:
        data = results[opp_name]
        lines.append(f"## {opp_name}\n\n")
        lines.append("| Seed | Δ SPT | v5.3 SPT | v5.4 SPT | v5.3 RedLine? | v5.4 RedLine? | v5.3 My D | v5.4 My D | v5.4 Tactical |\n")
        lines.append("|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|\n")

        high_gain_count = 0
        parity_count = 0
        v53_red_count = 0
        v54_red_count = 0

        for r in data:
            d = r["delta"]
            if d >= 0.20:
                high_gain_count += 1
            elif abs(d) < 0.10:
                parity_count += 1
            if r["v53_red"]:
                v53_red_count += 1
            if r["v54_red"]:
                v54_red_count += 1

            lines.append(
                f"| {r['seed']} | {d:+.4f} | {r['v53_score']:.4f} | {r['v54_score']:.4f} | "
                f"{r['v53_red']} | {r['v54_red']} | {r['v53_my_d']} | {r['v54_my_d']} | {r['v54_tactical']} |\n"
            )

        lines.append(f"\n**Summary for {opp_name}**:\n")
        lines.append(f"- Seeds with High Gain (Δ ≥ +0.20): {high_gain_count} / 30 ({high_gain_count/30*100:.1f}%)\n")
        lines.append(f"- Seeds with Parity (|Δ| < 0.10): {parity_count} / 30 ({parity_count/30*100:.1f}%)\n")
        lines.append(f"- v5.3 entered RedLine: {v53_red_count} / 30 seeds ({v53_red_count/30*100:.1f}%)\n")
        lines.append(f"- v5.4 entered RedLine: {v54_red_count} / 30 seeds ({v54_red_count/30*100:.1f}%)\n\n---\n\n")

        print(f"{opp_name}: High Gain Seeds = {high_gain_count}/30 | v5.3 RedLine = {v53_red_count}/30 | v5.4 RedLine = {v54_red_count}/30")

    with open(out_md, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"\nSaved bimodality report to {out_md}\n")
    return results

if __name__ == "__main__":
    run_phase_5c()
