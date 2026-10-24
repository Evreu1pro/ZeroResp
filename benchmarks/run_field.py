"""Local field benchmark runner for ZeroResp.

Fast local feedback loop: run round-robin rank + per-opponent H2H +
self-match for ZeroResp against curated opponent packs at any noise level.

Examples:
    python benchmarks/run_field.py --pack field --turns 200 --reps 8 --seed 42 --noise 0 5
    python benchmarks/run_field.py --pack full --turns 100 --reps 1 --noise 0
    python benchmarks/run_field.py --vs TitForTat Grudger Joss --noise 0 1 3 5 10

Outputs JSON + Markdown into benchmarks/results/ (or --out dir).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import axelrod as axl

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from zeroresp import Features, ZeroResp  # noqa: E402

C, D = axl.Action.C, axl.Action.D

# Classic field pack: reciprocators, exploiters, noise players, recognizers.
FIELD_PACK = [
    "Cooperator", "Defector", "TitForTat", "Grudger", "Random", "Alternator",
    "TitFor2Tats", "Two Tits For Tat", "Suspicious Tit For Tat", "Bully",
    "GTFT", "Soft Joss", "Prober", "Prober2", "Prober3",
    "Calculator", "Handshake", "Once Bitten", "Punisher",
    "Hard Tit For Tat", "Hard Tit For 2 Tats",
    "Soft Grudger", "Firm But Fair", "Tricky Cooperator", "First by Grofman",
    "Contrite Tit For Tat", "Slow Tit For Two Tats 2", "Gradual",
    "ShortMem", "GrudgerAlternator", "Hard Prober", "Tricky Defector",
]

RECIPIROCATORS = ["TitForTat", "Grudger", "TitFor2Tats", "GTFT",
                  "Contrite Tit For Tat", "Firm But Fair", "Gradual"]


def build_pack(name: str) -> list:
    by_name: dict = {}
    for s in axl.strategies:
        by_name[s.__name__] = s
        by_name.setdefault(s.name, s)  # display name, e.g. "Two Tits For Tat"
    if name == "field":
        names = FIELD_PACK
    elif name == "basic":
        names = ["Cooperator", "Defector", "TitForTat", "Grudger", "Random",
                 "Alternator", "Joss", "Bully", "Prober", "Calculator"]
    elif name == "full":
        # Every short-run-time strategy (excludes long_run_time and cheaters).
        names = [s.__name__ for s in axl.short_run_time_strategies
                 if not getattr(s, "classifier", {}).get("long_run_time")]
    elif name == "all":
        names = [s.__name__ for s in axl.strategies]
    else:
        names = [n.strip() for n in name.split(",") if n.strip()]
    missing = [n for n in names if n not in by_name]
    if missing:
        raise SystemExit(f"Unknown strategies: {missing}")
    seen, out = set(), []
    for n in names:
        cls = by_name[n]
        if cls not in seen:
            seen.add(cls)
            out.append(cls)
    return out


def h2h(player_factory, opp_factory, turns, reps, seed, noise, length=None):
    """ZeroResp vs one opponent; returns per-rep score-per-turn lists."""
    attrs = {"length": length} if length is not None else None
    my_spt, opp_spt = [], []
    for rep in range(reps):
        match = axl.Match(
            (player_factory(), opp_factory()),
            turns=turns, seed=seed + rep, noise=noise,
            match_attributes=attrs,
        )
        match.play()
        scores = match.scores()  # per-turn (my, opp) pairs
        my_spt.append(sum(s[0] for s in scores) / turns)
        opp_spt.append(sum(s[1] for s in scores) / turns)
    return my_spt, opp_spt


def run_round_robin(pack, turns, reps, seed, noise, zr_factory=None):
    zr_factory = zr_factory or ZeroResp
    players = [zr_factory()] + [cls() for cls in pack]
    tournament = axl.Tournament(
        players, turns=turns, repetitions=reps, seed=seed, noise=noise,
    )
    results = tournament.play(progress_bar=False)
    zr_idx = next(i for i, p in enumerate(players) if isinstance(p, ZeroResp))
    # results.scores[i] = total round-robin score per repetition
    totals = results.scores[zr_idx]
    mean_spt = sum(totals) / len(totals) / turns
    zr_rank = results.ranking.index(zr_idx) + 1
    return {
        "rank": zr_rank,
        "of": len(players),
        "spt_round_robin": round(mean_spt, 4),
        "ranked_head": [(n, i) for i, n in enumerate(results.ranked_names)
                        if i < 8 or n.startswith("ZeroResp")],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pack", default="field",
                    help="field | basic | full | all | comma-separated names")
    ap.add_argument("--vs", nargs="*", default=None,
                    help="run H2H only against these strategies")
    ap.add_argument("--turns", type=int, default=200)
    ap.add_argument("--reps", type=int, default=8)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--noise", type=float, nargs="*", default=[0.0],
                    help="noise levels, e.g. 0 0.05 0.1")
    ap.add_argument("--out", default=str(ROOT / "benchmarks" / "results"))
    ap.add_argument("--no-ladder", action="store_true",
                    help="run v5.2 behavior (Features.noise_ladder=False)")
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    report = {"config": vars(args), "runs": []}
    t0 = time.time()
    def zr_factory():
        if args.no_ladder:
            return ZeroResp(features=Features(noise_ladder=False))
        return ZeroResp()

    if args.vs:
        pack = build_pack(",".join(args.vs))
    else:
        pack = build_pack(args.pack)

    for noise in args.noise:
        run: dict = {"noise": noise}

        if not args.vs:
            run["round_robin"] = run_round_robin(pack, args.turns, args.reps,
                                                 args.seed, noise,
                                                 zr_factory=zr_factory)

        per_opp = {}
        for cls in pack:
            my_spt, _ = h2h(zr_factory, cls, args.turns, args.reps, args.seed, noise,
                            length=args.turns)
            per_opp[cls.__name__] = round(sum(my_spt) / len(my_spt), 4)
        run["h2h_spt"] = per_opp

        # self-match (two independent ZeroResp instances)
        my_spt, opp_spt = h2h(zr_factory, zr_factory, args.turns, args.reps,
                              args.seed, noise, length=args.turns)
        run["self_match_spt"] = round(sum(my_spt) / len(my_spt), 4)
        run["self_match_total_mean"] = round(
            sum(my_spt) * args.turns / len(my_spt), 1)

        recip = [v for k, v in per_opp.items() if k in RECIPIROCATORS]
        if recip:
            run["reciprocators_mean_spt"] = round(sum(recip) / len(recip), 4)

        report["runs"].append(run)

    elapsed = time.time() - t0
    report["elapsed_sec"] = round(elapsed, 1)

    stamp = time.strftime("%Y%m%d_%H%M%S")
    json_path = out_dir / f"field_{stamp}.json"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Markdown digest
    lines = [f"# ZeroResp local field run — {stamp}",
             f"turns={args.turns} reps={args.reps} seed={args.seed} "
             f"elapsed={elapsed:.0f}s", ""]
    for run in report["runs"]:
        lines.append(f"## noise {run['noise']}")
        if "round_robin" in run:
            rr = run["round_robin"]
            lines.append(f"- rank **{rr['rank']} / {rr['of']}**, "
                         f"SPT(round-robin) {rr['spt_round_robin']}")
        lines.append(f"- self-match: {run['self_match_total_mean']} / "
                     f"{args.turns} per 1 match")
        if "reciprocators_mean_spt" in run:
            lines.append(f"- reciprocators mean SPT: "
                         f"{run['reciprocators_mean_spt']}")
        lines.append("")
        for name, spt in sorted(run["h2h_spt"].items(), key=lambda x: -x[1]):
            lines.append(f"| {name} | {spt} |")
        lines.append("")
    md_path = out_dir / f"field_{stamp}.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(report, indent=2)[:3000])
    print(f"\nSaved: {json_path}\nSaved: {md_path}")


if __name__ == "__main__":
    main()
