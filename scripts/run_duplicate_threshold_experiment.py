"""Calibrates a separate threshold for duplicate-enrollment detection.

Why this cannot reuse the identification threshold (0.2975)
-----------------------------------------------------------
Both decisions compare two faces with cosine similarity, but the cost of being
wrong is inverted, so the operating point must be too.

  Identification  - a false accept labels a stranger as an enrolled person.
                    Calibrated at FAR <= 1%.

  Duplicate check - a false accept BLOCKS A NEW PERSON FROM ENROLLING because
                    they resemble someone already in the system. The user
                    cannot proceed at all, and cannot self-diagnose why.
                    A false reject merely lets a duplicate through, which is
                    the pre-existing behaviour and degrades gracefully.

At FAR ~0.86% (the measured held-out rate at 0.2975), roughly 1 in 116
legitimate new enrollments would be refused. That is not an acceptable
enrollment gate, so this script derives a stricter threshold from the same LFW
pairs, prioritising near-zero false blocks over catching every duplicate.

Reuses the existing evaluation harness. Does not modify it, and does not touch
the identification threshold.

Usage (repo root, venv active):
    python scripts/run_duplicate_threshold_experiment.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ml.evaluation.dataset import load_test_pairs, load_train_pairs
from ml.evaluation.metrics import compute_metrics_at_threshold, sweep_thresholds
from ml.evaluation.pairs import score_pairs
from ml.model_adapter import FaceRecognitionPipeline

# The frozen identification threshold, shown only for contrast.
IDENTIFICATION_THRESHOLD = 0.2975

# FAR here means "a genuinely different person is wrongly blocked from
# enrolling". We want this as close to zero as the data can demonstrate.
TARGET_FAR = 0.0


def select_duplicate_threshold(sweep):
    """Lowest threshold achieving the target false-block rate.

    Lowest (not highest) because among thresholds that never wrongly block a
    stranger, the lowest one catches the most real duplicates.
    """
    clean = [m for m in sweep if m.far <= TARGET_FAR]
    if not clean:
        raise SystemExit("No threshold achieved the target FAR; widen the sweep.")
    return min(clean, key=lambda m: m.threshold)


def main() -> None:
    t0 = time.time()
    pipeline = FaceRecognitionPipeline()

    print("Scoring calibration (train) pairs...")
    train = score_pairs(pipeline, load_train_pairs())
    print(f"  scored={len(train.scored_pairs)} excluded={len(train.failed_pairs)}")

    print("Scoring held-out (test) pairs...")
    test = score_pairs(pipeline, load_test_pairs())
    print(f"  scored={len(test.scored_pairs)} excluded={len(test.failed_pairs)}")

    sweep = sweep_thresholds(train.scored_pairs, num_steps=400)
    chosen = select_duplicate_threshold(sweep)

    # What reusing the identification threshold would cost, on the same data.
    reuse_train = compute_metrics_at_threshold(train.scored_pairs, IDENTIFICATION_THRESHOLD)
    reuse_test = compute_metrics_at_threshold(test.scored_pairs, IDENTIFICATION_THRESHOLD)

    held_out = compute_metrics_at_threshold(test.scored_pairs, chosen.threshold)

    def catch_rate(m):
        """Share of true duplicates this threshold would catch."""
        return m.genuine_accepted / m.genuine_total if m.genuine_total else 0.0

    def block_rate(m):
        """Share of distinct people wrongly blocked from enrolling."""
        return m.far

    report = {
        "purpose": "duplicate-enrollment detection threshold",
        "identification_threshold_unchanged": IDENTIFICATION_THRESHOLD,
        "selection": {
            "policy": "lowest threshold with FAR <= target on the calibration split",
            "target_far": TARGET_FAR,
            "chosen_threshold": chosen.threshold,
            "calibration": {
                "wrongly_blocked_rate": block_rate(chosen),
                "duplicate_catch_rate": catch_rate(chosen),
                "impostor_pairs": chosen.impostor_total,
                "genuine_pairs": chosen.genuine_total,
            },
        },
        "held_out_validation": {
            "threshold": chosen.threshold,
            "wrongly_blocked_rate": block_rate(held_out),
            "wrongly_blocked_count": held_out.impostor_total - held_out.impostor_rejected,
            "impostor_pairs": held_out.impostor_total,
            "duplicate_catch_rate": catch_rate(held_out),
            "duplicates_caught": held_out.genuine_accepted,
            "genuine_pairs": held_out.genuine_total,
        },
        "why_not_reuse_identification_threshold": {
            "threshold": IDENTIFICATION_THRESHOLD,
            "calibration_wrongly_blocked_rate": block_rate(reuse_train),
            "held_out_wrongly_blocked_rate": block_rate(reuse_test),
            "held_out_wrongly_blocked_count": reuse_test.impostor_total - reuse_test.impostor_rejected,
            "held_out_duplicate_catch_rate": catch_rate(reuse_test),
        },
    }

    out = REPO_ROOT / "data" / "duplicate_threshold_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2))

    print(f"\nChosen duplicate threshold: {chosen.threshold:.4f}")
    print(f"  calibration : blocked={block_rate(chosen):.3%} caught={catch_rate(chosen):.2%}")
    print(f"  held-out    : blocked={block_rate(held_out):.3%} "
          f"({held_out.impostor_total - held_out.impostor_rejected}/{held_out.impostor_total}) "
          f"caught={catch_rate(held_out):.2%}")
    print(f"\nFor contrast, reusing {IDENTIFICATION_THRESHOLD} as a duplicate gate:")
    print(f"  held-out    : blocked={block_rate(reuse_test):.3%} "
          f"({reuse_test.impostor_total - reuse_test.impostor_rejected}/{reuse_test.impostor_total}) "
          f"caught={catch_rate(reuse_test):.2%}")
    print(f"\nWrote {out.relative_to(REPO_ROOT)}  ({time.time() - t0:.1f}s)")


if __name__ == "__main__":
    main()
