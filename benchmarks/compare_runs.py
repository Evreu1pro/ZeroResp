#!/usr/bin/env python3
"""Compare two ZeroResp field-run reports produced by benchmarks/run_field.py.

Usage:
    python benchmarks/compare_runs.py OLD.json NEW.json [--md out.md] [--threshold 0.15]

The reports are compared per noise level (intersection of their "runs"):

1. Round-robin rank OLD vs NEW. When pool sizes ("of") differ, the rank
   share (rank/of, lower is better) is compared instead of the raw rank.
2. h2h_spt: per-opponent delta (NEW - OLD), top-5 improvements and top-5
   regressions. An opponent counts as regressed when delta < -threshold.
3. self_match_total_mean and reciprocators_mean_spt deltas.
4. Verdict per noise and overall:
   REGRESSION - rank share got worse, or >= 3 opponents with delta below
                -threshold, or any opponent with delta below -0.5, or
                self_match_total_mean fell by more than 20 points;
   IMPROVED   - otherwise, when the mean h2h delta is above +0.03;
   NEUTRAL    - otherwise.

The Markdown report goes to stdout (and to --md file if given).
Exit code: 1 if any verdict is REGRESSION, 0 otherwise.

Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SEVERE_DELTA = 0.5       # any opponent below this -> REGRESSION (fixed)
SELF_DROP_LIMIT = 20.0   # self_match_total_mean drop in points -> REGRESSION
IMPROVE_BAR = 0.03       # mean h2h delta above this -> IMPROVED
TOP_N = 5                # entries in the improvement/regression top lists
MAX_NAMED = 15           # cap for long opponent name lists
EPS = 1e-9

SELF_METRICS = (         # (key, decimals) shown in the self-match table
    ("self_match_total_mean", 1),
    ("self_match_spt", 4),
    ("reciprocators_mean_spt", 4),
)


# --------------------------------------------------------------- helpers

def noise_key(noise) -> float:
    """Canonical key so noise levels from different files always match."""
    return round(float(noise), 6)


def fmt_noise(key: float) -> str:
    return f"{key:g}"


def fmt_delta(value, nd: int = 4) -> str:
    return "-" if value is None else f"{value:+.{nd}f}"


def fmt_val(value, nd: int = 4) -> str:
    return "-" if value is None else f"{value:.{nd}f}"


def named_list(prefix: str, names) -> str:
    if not names:
        return f"{prefix}: -"
    shown = names[:MAX_NAMED]
    tail = f" (+{len(names) - MAX_NAMED} more)" if len(names) > MAX_NAMED else ""
    return f"{prefix}: {', '.join(shown)}{tail}"


def load_report(path: Path):
    if not path.is_file():
        raise SystemExit(f"File not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SystemExit(f"Cannot read {path}: {exc}")
    if not isinstance(data, dict) or not isinstance(data.get("runs"), list):
        raise SystemExit(f"{path} does not look like a run_field.py report")
    runs = {}
    for run in data["runs"]:
        if isinstance(run, dict) and "noise" in run:
            runs[noise_key(run["noise"])] = run
    return data, runs


def config_brief(data) -> str:
    cfg = data.get("config") or {}
    bits = [f"{key}={cfg[key]}" for key in ("pack", "turns", "reps", "seed")
            if cfg.get(key) is not None]
    if cfg.get("vs"):
        bits.append("vs=" + ",".join(cfg["vs"]))
    return ", ".join(bits) if bits else "config n/a"


# ------------------------------------------------------------- sections

def rank_section(old_rr, new_rr):
    """Rank comparison. Returns (rank_worse: bool|None, share_delta, lines)."""
    lines = ["### Round-robin rank", ""]
    if old_rr is None and new_rr is None:
        lines += ["No round-robin data in either report.", ""]
        return None, None, lines
    if old_rr is None or new_rr is None:
        missing = "OLD" if old_rr is None else "NEW"
        lines += [f"No round-robin data in {missing}; comparison skipped.", ""]
        return None, None, lines

    def share(rr):
        rank, of = rr.get("rank"), rr.get("of")
        if (isinstance(rank, (int, float)) and isinstance(of, (int, float))
                and of > 0):
            return rank / of
        return None

    o_share, n_share = share(old_rr), share(new_rr)
    lines += ["| metric | OLD | NEW |", "|---|---|---|"]
    lines.append(f"| rank | {old_rr.get('rank', '?')} / {old_rr.get('of', '?')} "
                 f"| {new_rr.get('rank', '?')} / {new_rr.get('of', '?')} |")
    if o_share is not None and n_share is not None:
        lines.append(f"| rank share (rank/of, lower is better) "
                     f"| {o_share:.4f} | {n_share:.4f} |")
    lines.append(f"| spt (round-robin) "
                 f"| {fmt_val(old_rr.get('spt_round_robin'))} "
                 f"| {fmt_val(new_rr.get('spt_round_robin'))} |")

    if o_share is None or n_share is None:
        lines += ["Share unavailable (missing rank/of) - no rank check.", ""]
        return None, None, lines
    share_delta = n_share - o_share
    lines += [f"Share delta: {fmt_delta(share_delta)} "
              f"(rank regression when > 0)", ""]
    return share_delta > EPS, share_delta, lines


def h2h_section(old_h, new_h, thr):
    """Per-opponent H2H deltas. Returns (deltas, regressed, severe, mean, lines)."""
    lines = ["### H2H per opponent (spt; delta = NEW - OLD)", ""]
    common = sorted(set(old_h) & set(new_h))
    only_old = sorted(set(old_h) - set(new_h))
    only_new = sorted(set(new_h) - set(old_h))
    deltas = {name: new_h[name] - old_h[name] for name in common}
    mean_delta = sum(deltas.values()) / len(deltas) if deltas else None

    lines.append(f"Common opponents: {len(common)}; "
                 f"{named_list('only in OLD', only_old)}; "
                 f"{named_list('only in NEW', only_new)}")
    lines += ["", f"Mean delta: {fmt_delta(mean_delta)}", ""]

    improvements = sorted(((d, n) for n, d in deltas.items()),
                          key=lambda t: (-t[0], t[1]))[:TOP_N]
    regressions = sorted(((d, n) for n, d in deltas.items()),
                         key=lambda t: (t[0], t[1]))[:TOP_N]
    for title, items in ((f"Top {TOP_N} improvements", improvements),
                         (f"Top {TOP_N} regressions", regressions)):
        lines.append(title)
        if items:
            lines += ["| opponent | OLD | NEW | delta |", "|---|---|---|---|"]
            for d, name in items:
                lines.append(f"| {name} | {fmt_val(old_h[name])} "
                             f"| {fmt_val(new_h[name])} | {fmt_delta(d)} |")
        else:
            lines.append("(none)")
        lines.append("")

    regressed = sorted(((d, n) for n, d in deltas.items() if d < -thr),
                       key=lambda t: (t[0], t[1]))
    severe = [item for item in regressed if item[0] < -SEVERE_DELTA]
    lines.append(f"Regressed opponents (delta < -{thr:g}): {len(regressed)}")
    if regressed:
        lines.append(named_list("worst first", [name for _, name in regressed]))
    lines.append(f"Severe drops (delta < -{SEVERE_DELTA:g}): {len(severe)}")
    lines.append("")
    return deltas, regressed, severe, mean_delta, lines


def self_section(old_run, new_run):
    """Self-match / reciprocators deltas. Returns (delta_map, lines)."""
    lines = ["### Self match / reciprocators", "",
             "| metric | OLD | NEW | delta |", "|---|---|---|---|"]
    out = {}
    for key, nd in SELF_METRICS:
        o, n = old_run.get(key), new_run.get(key)
        delta = (n - o) if isinstance(o, (int, float)) \
            and isinstance(n, (int, float)) else None
        out[key] = delta
        lines.append(f"| {key} | {fmt_val(o, nd)} | {fmt_val(n, nd)} "
                     f"| {fmt_delta(delta, nd)} |")
    lines.append("")
    return out, lines


def verdict_section(label, rank_worse, share_delta, regressed, severe,
                    self_deltas, mean_delta, n_common, thr):
    self_delta = self_deltas.get("self_match_total_mean")
    if rank_worse or len(regressed) >= 3 or severe or (
            self_delta is not None and self_delta < -SELF_DROP_LIMIT):
        verdict = "REGRESSION"
    elif mean_delta is not None and mean_delta > IMPROVE_BAR:
        verdict = "IMPROVED"
    else:
        verdict = "NEUTRAL"

    lines = [f"### Verdict (noise {label}): **{verdict}**", ""]
    if rank_worse is None:
        lines.append("- rank share: n/a")
    else:
        lines.append(f"- rank share: {'WORSE' if rank_worse else 'OK'} "
                     f"({fmt_delta(share_delta)}; worse when > 0)")
    lines.append(f"- opponents below -{thr:g}: {len(regressed)} of {n_common} "
                 f"(REGRESSION at >= 3)")
    lines.append(f"- severe drops below -{SEVERE_DELTA:g}: {len(severe)} "
                 f"(REGRESSION at >= 1)")
    lines.append(f"- self_match_total_mean delta: {fmt_delta(self_delta, 1)} "
                 f"(REGRESSION below -{SELF_DROP_LIMIT:g})")
    lines.append(f"- mean h2h delta: {fmt_delta(mean_delta)} "
                 f"(IMPROVED above +{IMPROVE_BAR:g})")
    lines.append("")
    return verdict, lines


def noise_section(key, old_run, new_run, thr):
    lines = [f"## Noise {fmt_noise(key)}", ""]
    rank_worse, share_delta, rank_lines = rank_section(
        old_run.get("round_robin"), new_run.get("round_robin"))
    deltas, regressed, severe, mean_delta, h2h_lines = h2h_section(
        old_run.get("h2h_spt") or {}, new_run.get("h2h_spt") or {}, thr)
    self_deltas, self_lines = self_section(old_run, new_run)
    lines += rank_lines + h2h_lines + self_lines
    verdict, verdict_lines = verdict_section(
        fmt_noise(key), rank_worse, share_delta, regressed, severe,
        self_deltas, mean_delta, len(deltas), thr)
    lines += verdict_lines
    return verdict, list(deltas.values()), lines


# ----------------------------------------------------------------- main

def build_report(old_path, new_path, thr):
    old_data, old_runs = load_report(old_path)
    new_data, new_runs = load_report(new_path)

    lines = ["# ZeroResp run comparison", ""]
    lines.append(f"- OLD: {old_path} ({config_brief(old_data)})")
    lines.append(f"- NEW: {new_path} ({config_brief(new_data)})")
    lines.append(f"- Noise levels: OLD "
                 f"[{', '.join(fmt_noise(k) for k in sorted(old_runs))}], NEW "
                 f"[{', '.join(fmt_noise(k) for k in sorted(new_runs))}]")
    lines.append(f"- Rules: opponent regressed when delta < -{thr:g} spt "
                 f"(severe < -{SEVERE_DELTA:g}); REGRESSION when the rank share "
                 f"got worse, or >= 3 opponents regressed, or any severe drop, "
                 f"or self_match_total_mean fell > {SELF_DROP_LIMIT:g} pts; "
                 f"otherwise IMPROVED above +{IMPROVE_BAR:g} mean spt, "
                 f"else NEUTRAL")
    lines.append("")

    common = sorted(set(old_runs) & set(new_runs))
    if not common:
        lines.append("## Overall verdict: **N/A**")
        lines.append("")
        lines.append("No common noise levels between the reports.")
        return lines, "NEUTRAL"

    per_noise, all_deltas = [], []
    for key in common:
        verdict, deltas, section = noise_section(
            key, old_runs[key], new_runs[key], thr)
        per_noise.append((fmt_noise(key), verdict))
        all_deltas.extend(deltas)
        lines += ["---", ""] + section

    overall_mean = sum(all_deltas) / len(all_deltas) if all_deltas else None
    if any(v == "REGRESSION" for _, v in per_noise):
        overall = "REGRESSION"
    elif any(v == "IMPROVED" for _, v in per_noise) or (
            overall_mean is not None and overall_mean > IMPROVE_BAR):
        overall = "IMPROVED"
    else:
        overall = "NEUTRAL"

    lines += ["---", "", f"## Overall verdict: **{overall}**", ""]
    lines += [f"- noise {label}: {verdict}" for label, verdict in per_noise]
    lines.append(f"- mean h2h delta over {len(all_deltas)} common comparisons: "
                 f"{fmt_delta(overall_mean)}")
    lines.append("")
    return lines, overall


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Compare two run_field.py JSON reports and flag regressions.",
        epilog="Example: python benchmarks/compare_runs.py "
               "benchmarks/results/field_20260927_150138.json "
               "benchmarks/results/field_20260927_155301.json")
    ap.add_argument("old", type=Path,
                    help="OLD report JSON (run_field.py output)")
    ap.add_argument("new", type=Path,
                    help="NEW report JSON (run_field.py output)")
    ap.add_argument("--md", type=Path, default=None,
                    help="also write the report to this Markdown file")
    ap.add_argument("--threshold", type=float, default=0.15,
                    help="per-opponent h2h regression threshold in spt "
                         "(default: 0.15)")
    args = ap.parse_args(argv)
    if args.threshold <= 0:
        ap.error("--threshold must be positive")

    lines, overall = build_report(args.old, args.new, args.threshold)
    text = "\n".join(lines)
    print(text)
    if args.md is not None:
        args.md.parent.mkdir(parents=True, exist_ok=True)
        args.md.write_text(text + "\n", encoding="utf-8")
    return 1 if overall == "REGRESSION" else 0


if __name__ == "__main__":
    sys.exit(main())
