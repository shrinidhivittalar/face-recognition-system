"""Selects the operating threshold from calibration (train-split) FAR/FRR sweep results.

Operating-point policy (blueprint section 8 / PRD section 17): prioritize
meaningful Unknown rejection (low FAR) while retaining useful recognition
performance (acceptable FRR). We choose the lowest threshold that keeps FAR at
or below a target ceiling; if no threshold reaches that ceiling, we fall back
to the Equal Error Rate (EER) point so a threshold is still produced from
evidence rather than an arbitrary constant.
"""
from __future__ import annotations

from dataclasses import dataclass

from ml.evaluation.metrics import ThresholdMetrics


@dataclass
class ThresholdSelection:
    metrics: ThresholdMetrics
    method: str  # "far_ceiling" or "eer_fallback"
    target_far: float


def select_operating_threshold(
    sweep: list[ThresholdMetrics], target_far: float = 0.01
) -> ThresholdSelection:
    candidates = [m for m in sweep if m.far <= target_far]
    if candidates:
        best = min(candidates, key=lambda m: m.threshold)
        return ThresholdSelection(metrics=best, method="far_ceiling", target_far=target_far)

    eer_point = min(sweep, key=lambda m: abs(m.far - m.frr))
    return ThresholdSelection(metrics=eer_point, method="eer_fallback", target_far=target_far)
