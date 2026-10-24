"""Direct comparative benchmark: ZeroResp v5.3 vs ZeroResp v5.5."""
from __future__ import annotations

import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import axelrod as axl
from zeroresp import ZeroResp as ZeroRespV53
from zeroresp_v55 import ZeroRespV55Full as ZeroRespV55

COMPARE_OPPONENTS = [
    "Cooperator",
    "Defector",
    "TitForTat",
    "Grudger",
    "TitFor2Tats",
    "Two Tits For Tat",
    "Bully",
    "Soft Joss",
    "Prober",
    "Hard Prober",
    "Punisher",
    "Slow Tit For Two Tats 2",
    "Contrite Tit For Tat",
    "Gradual",
    "Tricky Cooperator",
    "Calculator",
]

def run_comparison(turns=200, reps=5, seed=42, noise_levels=(0.0, 0.01, 0.05, 0.10)):
    opp_classes = []
    by_name = {s.__name__: s for s in axl.strategies}
    for s in axl.strategies:
        by_name[s.name] = s
    
    for name in COMPARE_OPPONENTS:
        if name in by_name:
            opp_classes.append(by_name[name])
        else:
            print(f"Warning: {name} not found in axelrod")

    print(f"Starting comparison: v5.3 vs v5.5 across noise levels {noise_levels}")
    print(f"Turns: {turns}, Repetitions: {reps}, Seed: {seed}")
    print("=" * 70)

    results = {}

    for noise in noise_levels:
        t0 = time.time()
        print(f"\n--- Testing Noise Level: {noise*100:.1f}% ---")
        
        v53_spt_list = []
        v55_spt_list = []
        opp_diffs = {}

        # 1. H2H against selected opponents
        for opp_cls in opp_classes:
            opp_name = getattr(opp_cls, "name", opp_cls.__name__)
            
            # v5.3
            m_v53 = 0.0
            for r in range(reps):
                match = axl.Match((ZeroRespV53(), opp_cls()), turns=turns, seed=seed + r, noise=noise)
                match.play()
                m_v53 += sum(s[0] for s in match.scores()) / turns
            m_v53 /= reps

            # v5.5
            m_v55 = 0.0
            for r in range(reps):
                match = axl.Match((ZeroRespV55(), opp_cls()), turns=turns, seed=seed + r, noise=noise)
                match.play()
                m_v55 += sum(s[0] for s in match.scores()) / turns
            m_v55 /= reps

            v53_spt_list.append(m_v53)
            v55_spt_list.append(m_v55)
            opp_diffs[opp_name] = (m_v53, m_v55, m_v55 - m_v53)

        # 2. Self-match
        sm_53 = 0.0
        for r in range(reps):
            m = axl.Match((ZeroRespV53(), ZeroRespV53()), turns=turns, seed=seed + r, noise=noise)
            m.play()
            sm_53 += sum(s[0] for s in m.scores()) / turns
        sm_53 /= reps

        sm_55 = 0.0
        for r in range(reps):
            m = axl.Match((ZeroRespV55(), ZeroRespV55()), turns=turns, seed=seed + r, noise=noise)
            m.play()
            sm_55 += sum(s[0] for s in m.scores()) / turns
        sm_55 /= reps

        avg_53 = sum(v53_spt_list) / len(v53_spt_list)
        avg_55 = sum(v55_spt_list) / len(v55_spt_list)
        delta_avg = avg_55 - avg_53

        results[noise] = {
            "avg_v53": avg_53,
            "avg_v55": avg_55,
            "delta": delta_avg,
            "self_v53": sm_53,
            "self_v55": sm_55,
            "opp_diffs": opp_diffs,
            "elapsed": time.time() - t0,
        }

        print(f"Noise {noise*100:4.1f}% | Mean SPT: v5.3 = {avg_53:.4f}, v5.5 = {avg_55:.4f} | Δ = {delta_avg:+.4f} ({(delta_avg/avg_53)*100:+.2f}%) | Self: {sm_53:.2f} -> {sm_55:.2f}")

    print("\n" + "=" * 70)
    print("DETAILED OPPONENT BREAKDOWN (at 5% noise):")
    res_05 = results.get(0.05)
    if res_05:
        sorted_opps = sorted(res_05["opp_diffs"].items(), key=lambda x: x[1][2], reverse=True)
        print(f"{'Opponent':<28} | {'v5.3 SPT':<9} | {'v5.5 SPT':<9} | {'Delta':<8}")
        print("-" * 62)
        for name, (s53, s55, d) in sorted_opps:
            print(f"{name:<28} | {s53:<9.4f} | {s55:<9.4f} | {d:+8.4f}")

    return results

if __name__ == "__main__":
    run_comparison(turns=200, reps=4, seed=42, noise_levels=(0.0, 0.01, 0.05, 0.10))
