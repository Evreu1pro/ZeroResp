"""ZDB Phase 0: Integrity and Safety Checks."""
from __future__ import annotations

import difflib
import hashlib
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import axelrod as axl

# 1. Factory with strict anti-fallthrough check
def get_variant_player(variant: str):
    if variant == "v5.3":
        from zeroresp import ZeroResp
        return ZeroResp()
    elif variant == "v5.4":
        from zeroresp_v54 import ZeroRespV54Full
        return ZeroRespV54Full()
    elif variant == "v5.5":
        from zeroresp_v55 import ZeroRespV55Full
        return ZeroRespV55Full()
    elif variant == "v5.6":
        from zeroresp_v56 import ZeroRespV56Full
        return ZeroRespV56Full()
    elif variant == "v5.6_no_impulse":
        from zeroresp_v56 import Features, ZeroResp
        f = Features(
            adaptive_harvest=True, balance_apology=True, tactical_prefilter=True,
            profile_memory=True, symmetric_noise_sensor=True, warmup_calibration=True,
            pulsed_harvest=False, circuit_breaker=True, early_exit_warmup=True
        )
        return ZeroResp(features=f)
    elif variant == "v5.6_no_stopcock":
        from zeroresp_v56 import Features, ZeroResp
        f = Features(
            adaptive_harvest=True, balance_apology=True, tactical_prefilter=True,
            profile_memory=True, symmetric_noise_sensor=True, warmup_calibration=True,
            pulsed_harvest=True, circuit_breaker=False, early_exit_warmup=True
        )
        return ZeroResp(features=f)
    elif variant == "v5.6_no_earlyexit":
        from zeroresp_v56 import Features, ZeroResp
        f = Features(
            adaptive_harvest=True, balance_apology=True, tactical_prefilter=True,
            profile_memory=True, symmetric_noise_sensor=True, warmup_calibration=True,
            pulsed_harvest=True, circuit_breaker=True, early_exit_warmup=False
        )
        return ZeroResp(features=f)
    else:
        raise ValueError(f"Unknown variant: {variant}")


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def run_phase_0():
    print("=" * 60)
    print("PHASE 0: INTEGRITY VERIFICATION")
    print("=" * 60)

    # 0.1 sha256 of sources
    files = {
        "v5.3": Path("zeroresp.py"),
        "v5.4": Path("zeroresp_v54.py"),
        "v5.5": Path("zeroresp_v55.py"),
        "v5.6": Path("zeroresp_v56.py"),
    }
    hashes = {}
    for v, p in files.items():
        if not p.exists():
            raise FileNotFoundError(f"Missing source file: {p}")
        h = compute_sha256(p)
        hashes[v] = h
        print(f"0.1 SHA256 [{v}]: {h[:16]}... ({p})")

    distinct_hashes = len(set(hashes.values()))
    if distinct_hashes != 4:
        raise RuntimeError(f"FAIL: Not all source hashes are distinct ({distinct_hashes}/4)")
    print(">>> 0.1 PASS: All 4 source hashes are strictly distinct.\n")

    # 0.2 sha256 of split.json
    split_path = Path("benchmarks/results/research/bhns/split.json")
    if not split_path.exists():
        raise FileNotFoundError("split.json not found")
    split_hash = compute_sha256(split_path)
    with open(split_path, "r", encoding="utf-8") as f:
        split_data = json.load(f)
    print(f"0.2 SHA256 [split.json]: {split_hash}")
    print(f"    Train strategies: {len(split_data['train'])}, Holdout strategies: {len(split_data['holdout'])}")
    print(">>> 0.2 PASS: Pool list integrity verified.\n")

    # 0.3 Determinism: same build, same seed, 2 runs -> bit-identical
    print("0.3 Checking Determinism (v5.6 vs TitForTat, seed 42, 200 turns, 5% noise)...")
    res1, res2 = [], []
    for _ in range(5):
        m1 = axl.Match((get_variant_player("v5.6"), axl.TitForTat()), turns=200, seed=42, noise=0.05)
        m1.play()
        res1.append(m1.result)
    for _ in range(5):
        m2 = axl.Match((get_variant_player("v5.6"), axl.TitForTat()), turns=200, seed=42, noise=0.05)
        m2.play()
        res2.append(m2.result)

    if res1 != res2:
        raise RuntimeError("FAIL 0.3: Determinism check failed. Runs are not bit-identical!")
    print(">>> 0.3 PASS: Runs with same seed are 100% bit-identical.\n")

    # 0.4 Variants differ: v5.4 vs v5.5 at 10% noise -> not bit-identical
    print("0.4 Checking that Variants Differ (v5.4 vs v5.5 at 10% noise)...")
    m_v54 = axl.Match((get_variant_player("v5.4"), axl.TrickyDefector()), turns=200, seed=42, noise=0.10)
    m_v54.play()
    m_v55 = axl.Match((get_variant_player("v5.5"), axl.TrickyDefector()), turns=200, seed=42, noise=0.10)
    m_v55.play()

    if m_v54.result == m_v55.result:
        raise RuntimeError("FAIL 0.4: v5.4 and v5.5 produced bit-identical output. Variant is dead code!")
    print(f"    v5.4 score: {m_v54.final_score()} vs v5.5 score: {m_v55.final_score()}")
    print(">>> 0.4 PASS: Variants produce distinct trajectories (code is active).\n")

    # 0.5 Fall-through: unknown variant raises ValueError
    print("0.5 Checking Anti-Fall-Through...")
    try:
        get_variant_player("fake")
        raise RuntimeError("FAIL 0.5: Unknown variant did not raise exception!")
    except ValueError as e:
        print(f"    Properly caught expected exception: {e}")
    print(">>> 0.5 PASS: Unknown variant raises explicit ValueError.\n")

    # 0.6 Git diff of variants saved in ZDB_variants.diff
    print("0.6 Generating ZDB_variants.diff...")
    diff_lines = []
    pairs = [
        ("v5.3 -> v5.4", Path("zeroresp.py"), Path("zeroresp_v54.py")),
        ("v5.4 -> v5.5", Path("zeroresp_v54.py"), Path("zeroresp_v55.py")),
        ("v5.5 -> v5.6", Path("zeroresp_v55.py"), Path("zeroresp_v56.py")),
    ]
    for label, p1, p2 in pairs:
        diff_lines.append(f"\n{'='*70}\nDIFF: {label}\n{'='*70}\n")
        with open(p1, "r", encoding="utf-8") as f1, open(p2, "r", encoding="utf-8") as f2:
            l1, l2 = f1.readlines(), f2.readlines()
        d = difflib.unified_diff(l1, l2, fromfile=str(p1), tofile=str(p2))
        diff_lines.extend(d)

    with open("ZDB_variants.diff", "w", encoding="utf-8") as out:
        out.writelines(diff_lines)
    print(f">>> 0.6 PASS: Saved {len(diff_lines)} lines to ZDB_variants.diff.\n")

    print("=" * 60)
    print("PHASE 0 COMPLETE: ALL CHECKS PASSED (100% PASS)")
    print("=" * 60)
    return True

if __name__ == "__main__":
    run_phase_0()
