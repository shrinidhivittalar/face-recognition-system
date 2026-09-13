"""Renders evaluation results to JSON and Markdown for README/docs consumption."""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from ml.evaluation.metrics import ThresholdMetrics
from ml.evaluation.pairs import PairEvaluationResult
from ml.evaluation.threshold import ThresholdSelection


def build_report_dict(
    train_result: PairEvaluationResult,
    test_result: PairEvaluationResult,
    selection: ThresholdSelection,
    test_metrics_at_threshold: ThresholdMetrics,
) -> dict:
    return {
        "model": {
            "detector": "YuNet (face_detection_yunet_2023mar.onnx)",
            "recognizer": "SFace (face_recognition_sface_2021dec.onnx)",
            "similarity_metric": "cosine similarity on L2-normalized embeddings",
        },
        "dataset": {
            "source": "LFW verification pairs (logasja/lfw parquet mirror, View 1 protocol)",
            "train_pairs_total": len(train_result.scored_pairs) + len(train_result.failed_pairs),
            "train_pairs_scored": len(train_result.scored_pairs),
            "train_pairs_excluded_face_policy": len(train_result.failed_pairs),
            "test_pairs_total": len(test_result.scored_pairs) + len(test_result.failed_pairs),
            "test_pairs_scored": len(test_result.scored_pairs),
            "test_pairs_excluded_face_policy": len(test_result.failed_pairs),
        },
        "threshold_selection": {
            "method": selection.method,
            "target_far": selection.target_far,
            "chosen_threshold": selection.metrics.threshold,
            "train_far": selection.metrics.far,
            "train_frr": selection.metrics.frr,
            "train_accuracy": selection.metrics.accuracy,
        },
        "held_out_test_performance": asdict(test_metrics_at_threshold),
        "excluded_pairs_sample": (train_result.failed_pairs + test_result.failed_pairs)[:20],
    }


def write_json_report(report: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2))


def render_markdown(report: dict) -> str:
    d = report["dataset"]
    t = report["threshold_selection"]
    p = report["held_out_test_performance"]

    lines = [
        "# Evaluation Results",
        "",
        "## Model",
        f"- Detector: {report['model']['detector']}",
        f"- Recognizer: {report['model']['recognizer']}",
        f"- Similarity metric: {report['model']['similarity_metric']}",
        "",
        "## Dataset",
        f"- Source: {d['source']}",
        f"- Calibration (train) pairs: {d['train_pairs_scored']} scored / {d['train_pairs_total']} total "
        f"({d['train_pairs_excluded_face_policy']} excluded by the exactly-one-face policy)",
        f"- Held-out (test) pairs: {d['test_pairs_scored']} scored / {d['test_pairs_total']} total "
        f"({d['test_pairs_excluded_face_policy']} excluded by the exactly-one-face policy)",
        "",
        "## Threshold Selection (calibrated on the train split)",
        f"- Method: `{t['method']}` (target FAR <= {t['target_far']:.2%})",
        f"- **Chosen threshold: {t['chosen_threshold']:.4f}**",
        f"- Train FAR: {t['train_far']:.2%}",
        f"- Train FRR: {t['train_frr']:.2%}",
        f"- Train accuracy: {t['train_accuracy']:.2%}",
        "",
        "## Held-Out Test Performance (frozen threshold, unseen pairs)",
        f"- FAR: {p['far']:.2%}",
        f"- FRR: {p['frr']:.2%}",
        f"- Accuracy: {p['accuracy']:.2%}",
        f"- Genuine pairs accepted: {p['genuine_accepted']} / {p['genuine_total']}",
        f"- Impostor pairs rejected: {p['impostor_rejected']} / {p['impostor_total']}",
        "",
        "## Known Failure Cases",
        f"- {d['train_pairs_excluded_face_policy'] + d['test_pairs_excluded_face_policy']} pairs across both splits "
        "contained images where the exactly-one-face policy rejected the image "
        "(no face detected, or multiple faces detected) before a similarity score "
        "could even be computed. These are legitimate pipeline rejections, not "
        "matching errors, and are excluded from FAR/FRR.",
        f"- Remaining FAR ({p['far']:.2%}) and FRR ({p['frr']:.2%}) on the held-out "
        "test split represent look-alike/false-acceptance and lighting/pose-driven "
        "false-rejection cases respectively.",
        "",
        "## Limitations",
        "- LFW is celebrity/public-figure photography and skews toward frontal, "
        "well-lit adult faces; real-world enrollment photos may perform worse.",
        "- The threshold is calibrated on LFW pairs, not on this system's actual "
        "enrolled population; re-calibration is recommended if deployed against a "
        "materially different demographic or camera setup.",
        "- No liveness detection: this evaluates recognition accuracy only, not "
        "spoof resistance.",
    ]
    return "\n".join(lines)
