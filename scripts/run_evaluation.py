"""Runs the full threshold-calibration + held-out evaluation pipeline.

Usage (from repo root, with the venv active):
    python scripts/run_evaluation.py

Produces:
    docs/EVALUATION.md
    data/evaluation_results.json
    data/score_distribution.png
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ml.evaluation.dataset import load_train_pairs, load_test_pairs
from ml.evaluation.pairs import score_pairs
from ml.evaluation.metrics import compute_metrics_at_threshold, sweep_thresholds
from ml.evaluation.threshold import select_operating_threshold
from ml.evaluation.report import build_report_dict, write_json_report, render_markdown
from ml.model_adapter import FaceRecognitionPipeline


def plot_distributions(scored_pairs, threshold: float, out_path: Path) -> None:
    genuine_scores = [p.score for p in scored_pairs if p.is_genuine]
    impostor_scores = [p.score for p in scored_pairs if not p.is_genuine]

    plt.figure(figsize=(8, 5))
    plt.hist(genuine_scores, bins=40, alpha=0.6, label="Genuine pairs", color="#2b7a3d")
    plt.hist(impostor_scores, bins=40, alpha=0.6, label="Impostor pairs", color="#b23a3a")
    plt.axvline(threshold, color="black", linestyle="--", label=f"Threshold = {threshold:.4f}")
    plt.xlabel("Cosine similarity")
    plt.ylabel("Pair count")
    plt.title("Genuine vs. impostor similarity distributions (held-out test split)")
    plt.legend()
    plt.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_path, dpi=150)
    plt.close()


def main() -> None:
    t0 = time.time()
    print("Loading pipeline (YuNet + SFace)...")
    pipeline = FaceRecognitionPipeline()

    print("Loading train (calibration) pairs...")
    train_image_pairs = load_train_pairs()
    print(f"  {len(train_image_pairs)} pairs loaded")

    print("Loading test (held-out) pairs...")
    test_image_pairs = load_test_pairs()
    print(f"  {len(test_image_pairs)} pairs loaded")

    print("Scoring train pairs (this runs detection+embedding on every image)...")
    train_result = score_pairs(pipeline, train_image_pairs)
    print(f"  scored={len(train_result.scored_pairs)} excluded={len(train_result.failed_pairs)}")

    print("Scoring test pairs...")
    test_result = score_pairs(pipeline, test_image_pairs)
    print(f"  scored={len(test_result.scored_pairs)} excluded={len(test_result.failed_pairs)}")

    print("Sweeping thresholds on train split...")
    sweep = sweep_thresholds(train_result.scored_pairs)
    selection = select_operating_threshold(sweep, target_far=0.01)
    print(f"  method={selection.method} threshold={selection.metrics.threshold:.4f} "
          f"train_far={selection.metrics.far:.2%} train_frr={selection.metrics.frr:.2%}")

    print("Applying frozen threshold to held-out test split...")
    test_metrics = compute_metrics_at_threshold(test_result.scored_pairs, selection.metrics.threshold)
    print(f"  test_far={test_metrics.far:.2%} test_frr={test_metrics.frr:.2%} "
          f"test_accuracy={test_metrics.accuracy:.2%}")

    report = build_report_dict(train_result, test_result, selection, test_metrics)
    write_json_report(report, REPO_ROOT / "data" / "evaluation_results.json")

    markdown = render_markdown(report)
    (REPO_ROOT / "docs" / "EVALUATION.md").write_text(markdown, encoding="utf-8")

    plot_distributions(
        test_result.scored_pairs,
        selection.metrics.threshold,
        REPO_ROOT / "data" / "score_distribution.png",
    )

    print(f"\nDone in {time.time() - t0:.1f}s")
    print(f"Frozen threshold: {selection.metrics.threshold:.4f}")
    print("Wrote docs/EVALUATION.md, data/evaluation_results.json, data/score_distribution.png")


if __name__ == "__main__":
    main()
